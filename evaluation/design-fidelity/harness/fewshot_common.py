"""Shared machinery for the few-shot fidelity campaign -- DEV phase.

Builds K/selection/format exemplar-augmented system prompts for the two arm
families (V3FS = harness/arms_variants/V3_COSHYBRID.md + exemplars, NATFS =
harness/arms/NATIVE.md + exemplars), generates on claude-fable-5, and scores
with the SAME uniform gpt-4.1 extractor + concern-match judge used by
aa_calibration.py / round1_tier1b.py (imported directly from phase2_analyze,
byte-identical prompts). All plumbing (prompt assembly, generation, cache,
majority vote, composite) is intentionally the existing machinery, extended
only with the exemplar-block builder below.

Config space (10 unique, frozen -- FEWSHOT-CAMPAIGN-CHARTER.md ADOPTED
AMENDMENTS): K in {4,8,11} x selection in {random(seed=42), quadrant-diverse}
x format in {compact, full}; K=11 collapses selection (uses all 11 LOO-
available exemplars regardless of "selection"), so there are 8 + 2 = 10
configs total.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import _bootstrap  # noqa: F401 -- wires the cognition harness onto sys.path

import cache  # type: ignore
import llm  # type: ignore

from config import (
    ARM_MAX_TOKENS,
    ARM_TEMPERATURE,
    ARMS_DIR,
    CACHE_DIR,
    COMMON_TASK,
    DESIGN_DIR,
    HARNESS_DIR,
    SCENARIOS_PATH,
    USER_TEMPLATE,
)

import phase2_analyze as p2a  # type: ignore

CAMPAIGN_JUDGE_MODEL = "gpt-4.1"  # pinned for this campaign, per charter (same as aa_calibration/round1_tier1b)
MODEL_NAME = "claude-fable-5"

FEWSHOT_DIR = DESIGN_DIR / "fewshot"
EXEMPLAR_BANK_PATH = FEWSHOT_DIR / "exemplar_bank.json"

VARIANTS_DIR = HARNESS_DIR / "arms_variants"
ARM_FAMILY_PATH: dict[str, Path] = {
    "V3FS": VARIANTS_DIR / "V3_COSHYBRID.md",
    "NATFS": ARMS_DIR / "NATIVE.md",
}
ARM_FAMILIES: tuple[str, ...] = ("V3FS", "NATFS")

SCENARIO_ORDER = [f"S{i:02d}" for i in range(1, 13)]

# Canonical quadrant cell order (matches phase2_analyze.py's quad_names).
QUADRANT_ORDER: list[tuple[str, str]] = [
    ("deep", "technical"),
    ("shallow", "technical"),
    ("deep", "non_technical"),
    ("shallow", "non_technical"),
]

SELECTION_SEED = 42

MJ_TRUTH = p2a.MJ_TRUTH  # frozen ground truth, identical source as round1_tier1b.py


# ---------------------------------------------------------------------------
# Scenario / exemplar-bank loading
# ---------------------------------------------------------------------------
def load_scenarios() -> dict[str, dict]:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"] if isinstance(data, dict) else data
    return {sc["scenario_id"]: sc for sc in scenarios}


def load_arm_base(family: str) -> str:
    text = ARM_FAMILY_PATH[family].read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Arm family base empty: {family}")
    return text


def load_exemplar_bank() -> dict[str, dict]:
    data = json.loads(EXEMPLAR_BANK_PATH.read_text(encoding="utf-8"))
    bank = {ex["scenario_id"]: ex for ex in data["exemplars"]}
    assert set(bank) == set(SCENARIO_ORDER), (
        f"exemplar bank scenario mismatch: {sorted(bank)}"
    )
    return bank


def build_user_message(scenario: dict) -> str:
    return USER_TEMPLATE.format(
        title=scenario["title"],
        domain=scenario["domain"],
        depth=scenario["depth"],
        artifact=scenario["artifact"],
        question=scenario["question"],
        common_task=COMMON_TASK,
    )


# ---------------------------------------------------------------------------
# Config enumeration (10 unique, frozen)
# ---------------------------------------------------------------------------
def enumerate_configs() -> list[dict]:
    configs: list[dict] = []
    for K in (4, 8):
        for selection in ("random", "quaddiv"):
            for fmt in ("compact", "full"):
                configs.append(
                    {
                        "id": f"K{K}_{selection}_{fmt}",
                        "K": K,
                        "selection": selection,
                        "format": fmt,
                    }
                )
    for fmt in ("full", "compact"):
        configs.append({"id": f"K11_{fmt}", "K": 11, "selection": "na", "format": fmt})
    assert len(configs) == 10, f"expected 10 unique configs, got {len(configs)}"
    return configs


CONFIGS: list[dict] = enumerate_configs()
CONFIG_BY_ID: dict[str, dict] = {c["id"]: c for c in CONFIGS}


# ---------------------------------------------------------------------------
# Deterministic exemplar ordering (pre-enumerated, no hand-tuning on results)
# ---------------------------------------------------------------------------
def _random_order(seed: int = SELECTION_SEED) -> list[str]:
    rng = random.Random(seed)
    order = SCENARIO_ORDER[:]
    rng.shuffle(order)
    return order


def _quaddiv_order(scenarios: dict[str, dict], seed: int = SELECTION_SEED) -> list[str]:
    """Round-robin over the four depth x domain cells, seeded order within each cell."""
    rng = random.Random(seed)
    cells: dict[tuple[str, str], list[str]] = {q: [] for q in QUADRANT_ORDER}
    for sid in SCENARIO_ORDER:
        q = (scenarios[sid]["depth"], scenarios[sid]["domain"])
        cells[q].append(sid)
    for q in QUADRANT_ORDER:
        rng.shuffle(cells[q])
    order: list[str] = []
    for i in range(3):  # each cell has exactly 3 scenarios
        for q in QUADRANT_ORDER:
            order.append(cells[q][i])
    return order


def build_selection_order(scenarios: dict[str, dict], selection: str) -> list[str]:
    if selection == "random":
        return _random_order()
    if selection == "quaddiv":
        return _quaddiv_order(scenarios)
    if (
        selection == "na"
    ):  # K=11: selection collapses, order is irrelevant (all 11 used)
        return SCENARIO_ORDER[:]
    raise ValueError(f"unknown selection: {selection}")


def select_loo_exemplars(
    scenarios: dict[str, dict], config: dict, target_sid: str
) -> list[str]:
    """LOO exemplar sids for `target_sid` under `config` -- drawn only from the other 11."""
    order = build_selection_order(scenarios, config["selection"])
    pool = [sid for sid in order if sid != target_sid]
    assert len(pool) == 11
    K = config["K"]
    if K >= 11:
        return pool
    return pool[:K]


# ---------------------------------------------------------------------------
# Exemplar formatting
# ---------------------------------------------------------------------------
def _truncate_words(text: str, n: int = 45) -> str:
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[:n]) + "\u2026"


def format_exemplar(ex: dict, idx: int, fmt: str) -> str:
    title = ex["title"]
    if fmt == "full":
        body = (
            f"{ex['artifact']}\n\n"
            f"QUESTION: {ex['question']}\n\n"
            f"GRIT: {ex['grit']}\n"
            f"DIRECTION: {ex['direction']}\n"
            f"CONCERN: {ex['concern']}\n"
            f"READ: {ex['read']}"
        )
    elif fmt == "compact":
        body = (
            f"{_truncate_words(ex['artifact'])}\n\n"
            f"GRIT: {ex['grit']}\n"
            f"DIRECTION: {ex['direction']}\n"
            f"CONCERN: {ex['concern']}"
        )
    else:
        raise ValueError(f"unknown format: {fmt}")
    return f"Example {idx} \u2014 {title}\n{body}"


EXEMPLAR_HEADER = "Worked examples of the reviewer's actual calls on prior situations:"
EXEMPLAR_FOOTER = "Now review the new situation below the same way."


def build_exemplar_block(
    bank: dict[str, dict], scenarios: dict[str, dict], config: dict, target_sid: str
) -> str:
    sids = select_loo_exemplars(scenarios, config, target_sid)
    parts = [EXEMPLAR_HEADER]
    for i, sid in enumerate(sids, 1):
        parts.append(format_exemplar(bank[sid], i, config["format"]))
    parts.append(EXEMPLAR_FOOTER)
    return "\n\n".join(parts)


def build_system_prompt(
    family_base: str,
    bank: dict[str, dict],
    scenarios: dict[str, dict],
    config: dict,
    target_sid: str,
) -> str:
    block = build_exemplar_block(bank, scenarios, config, target_sid)
    return f"{family_base}\n\n{block}"


# ---------------------------------------------------------------------------
# Generation (claude-fable-5) -- cache key includes tag (family+config+group)
# ---------------------------------------------------------------------------
def generate(
    scenario: dict, sample: int, tag: str, system_prompt: str, user: str
) -> str:
    key = cache.make_key(
        "fewshot_generate",
        MODEL_NAME,
        scenario["scenario_id"],
        tag,
        sample,
        system_prompt + "\n##USER##\n" + user,
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is not None:
        return cached
    text = llm.call_anthropic(
        model=MODEL_NAME,
        system=system_prompt,
        user=user,
        temperature=ARM_TEMPERATURE,  # dropped by llm.py for fable models
        max_tokens=ARM_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "fewshot_generate",
            "campaign": "fewshot_dev",
            "tag": tag,
            "model": MODEL_NAME,
            "scenario_id": scenario["scenario_id"],
            "sample": sample,
        },
        cache_dir=CACHE_DIR,
    )
    return text


# ---------------------------------------------------------------------------
# Uniform gpt-4.1 extraction (byte-identical prompt to phase2_analyze.py)
# ---------------------------------------------------------------------------
def extract_one(sid: str, tag: str, sample: int, raw_text: str) -> dict:
    user = p2a.EXTRACT_TEMPLATE.format(review=raw_text or "")
    key = cache.make_key(
        "fewshot_extract_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, sample, user
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=CAMPAIGN_JUDGE_MODEL,
            system=p2a.EXTRACT_SYSTEM,
            user=user,
            temperature=0.0,
            max_tokens=300,
        )
        cache.put(
            key,
            cached,
            meta={
                "stage": "fewshot_extract_v1",
                "scenario_id": sid,
                "tag": tag,
                "sample": sample,
            },
            cache_dir=CACHE_DIR,
        )
    try:
        obj = p2a._extract_json(cached)
    except (json.JSONDecodeError, AttributeError):
        obj = {}
    g = obj.get("grit")
    g = (
        int(g)
        if isinstance(g, (int, float)) or (isinstance(g, str) and g.strip().isdigit())
        else None
    )
    if g not in (0, 1, 2, 3):
        g = None
    d = obj.get("direction")
    d = (
        d.strip().lower().replace(" ", "-").replace("_", "-")
        if isinstance(d, str)
        else None
    )
    if d not in p2a.VALID_DIR:
        d = None
    c = obj.get("concern")
    c = c.strip() if isinstance(c, str) and c.strip() else None
    return {"grit": g, "direction": d, "concern": c}


# ---------------------------------------------------------------------------
# Majority vote over 3 samples (identical logic to round1_tier1b.majority_of)
# ---------------------------------------------------------------------------
def majority_of(records: list[dict]) -> dict:
    recs = sorted(records, key=lambda r: r.get("sample", 0))
    mg = p2a._mode([r["x_grit"] for r in recs])
    md = p2a._mode([r["x_direction"] for r in recs])
    concern = None
    for r in recs:
        if r["x_direction"] == md and r.get("x_concern"):
            concern = r["x_concern"]
            break
    if concern is None:
        concern = next((r["x_concern"] for r in recs if r.get("x_concern")), None)
    return {"grit": mg, "direction": md, "concern": concern}


# ---------------------------------------------------------------------------
# Uniform gpt-4.1 concern-match judge (byte-identical prompt to phase2_analyze.py)
# ---------------------------------------------------------------------------
def concern_match(sid: str, tag: str, mj_c: str | None, arm_c: str | None) -> int:
    if not mj_c or not arm_c:
        return 0
    user = p2a.CONCERN_TEMPLATE.format(mj=mj_c, arm=arm_c)
    key = cache.make_key(
        "fewshot_concern_grade_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, 0, user
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=CAMPAIGN_JUDGE_MODEL,
            system=p2a.CONCERN_SYSTEM,
            user=user,
            temperature=0.0,
            max_tokens=300,
        )
        cache.put(
            key,
            cached,
            meta={"stage": "fewshot_concern_grade_v1", "scenario_id": sid, "tag": tag},
            cache_dir=CACHE_DIR,
        )
    try:
        obj = p2a._extract_json(cached)
    except (json.JSONDecodeError, AttributeError):
        obj = {}
    return int(bool(obj.get("match", False)))


# ---------------------------------------------------------------------------
# Composite scoring for one (scenario, majority) cell vs MJ_TRUTH
# ---------------------------------------------------------------------------
def score_cell(sid: str, tag: str, maj: dict) -> dict:
    mj_g, mj_d, mj_c = MJ_TRUTH[sid]
    ge = int(maj["grit"] is not None and maj["grit"] == mj_g)
    de = int(maj["direction"] is not None and maj["direction"] == mj_d)
    cm = concern_match(sid, tag, mj_c, maj.get("concern"))
    comp = (ge + de + cm) / 3.0
    return {
        "scenario_id": sid,
        "mj": {"grit": mj_g, "direction": mj_d, "concern": mj_c},
        "majority": maj,
        "grit_exact": ge,
        "direction_exact": de,
        "concern_match": cm,
        "composite": comp,
    }
