"""Round 2, Tier-1b SCREEN use #2 (FINAL screen) — hill-climb campaign, design-fidelity
mj-reviewer lens.

This is a repeat of round 1 with three NEW variants
(harness/arms_variants/{V4_DIRCAL,V5_STAGE,V6_MERGE}.md), adapted MINIMALLY from
round1_tier1b.py (arm list + output paths + run tag only — pipeline, prompts, gate,
champion source, and MJ reference are unchanged and verified identical to round 1).

Evaluates 3 challenger variants against the champion baseline, PAIRED per scenario, on
the frozen 12 scenarios, using the PRIMARY model per the amended protocol (see
../HILL-CLIMB-PLAN.md AMENDMENT + ledger round-0 protocol_amendment): claude-fable-5 ONLY.

Per the task brief, this is screen use #2 of 2 (Tier-1b screen budget is EXHAUSTED after
this run, per HILL-CLIMB-PLAN.md MAX 2 USES per campaign).

Pipeline is adapted verbatim from aa_calibration.py's Group-B machinery:
  - identical prompt assembly (USER_TEMPLATE + COMMON_TASK) to phase2_run.py
  - fresh-sample generation on claude-fable-5 (no temperature; llm.py drops it)
  - gpt-4.1 uniform extraction using phase2_analyze.EXTRACT_SYSTEM/EXTRACT_TEMPLATE
    (imported directly, byte-identical, not re-typed)
  - gpt-4.1 concern-match judge using phase2_analyze.CONCERN_SYSTEM/CONCERN_TEMPLATE
  - majority vote over 3 samples -> composite = mean(grit_exact, direction_exact,
    concern_match) in {0, 1/3, 2/3, 1}

Champion baseline (paired side): the FRESH champion composites already computed in
harness/runs/aa_calibration/aa_results.json -> results.fable.per_scenario[*].group_b
(claude-fable-5, samples 3,4,5 — generated fresh in the A/A run with the exact same
MACHETE system prompt / prompt assembly / judge). Reused as-is, no regeneration.

Cache keys are content-addressed over (stage, model, scenario_id, arm, sample, prompt);
arm = the variant code (V4_DIRCAL / V5_STAGE / V6_MERGE), which is what keeps these
108 fresh calls from colliding with the champion's MACHETE cache entries or each other.

PRE-REGISTERED GATE (per variant, paired vs champion, on fable-5):
  PASS requires ALL of:
    (a) net wins W-L >= 5 across the 12 scenarios (win = variant composite > champion)
    (b) mean paired gain >= 0.08
    (c) concern-match losses <= 1 (scenarios where champion concern-matched and the
        variant did not)

Outputs:
  runs/round2_tier1b/round2_raw.jsonl          (108 fresh generations)
  runs/round2_tier1b/round2_extractions.jsonl  (108 gpt-4.1 extractions, audit trail)
  runs/round2_tier1b/round2_results.json       (all numbers)
  ../hillclimb/ROUND2.md                        (writeup)
  ../hillclimb/LEDGER.jsonl                     (append: 1 entry/variant + round decision,
                                                  noting screen budget now EXHAUSTED)

Usage:
    python round2_tier1b.py
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import _bootstrap  # noqa: F401 — wires the cognition harness onto sys.path

import cache  # type: ignore
import llm  # type: ignore

import numpy as np

from config import (
    ARM_MAX_TOKENS,
    ARM_TEMPERATURE,
    CACHE_DIR,
    COMMON_TASK,
    DESIGN_DIR,
    HARNESS_DIR,
    MAX_WORKERS,
    RUNS_DIR,
    SCENARIOS_PATH,
    USER_TEMPLATE,
)

# Reuse the analyzer's prompts/helpers verbatim (byte-identical extractor + concern-match
# prompts; only the model name changes, same as aa_calibration.py).
import phase2_analyze as p2a  # type: ignore

CAMPAIGN_JUDGE_MODEL = "gpt-4.1"
MODEL_NAME = "claude-fable-5"

VARIANTS: dict[str, str] = {
    "V4_DIRCAL": "V4_DIRCAL.md",
    "V5_STAGE": "V5_STAGE.md",
    "V6_MERGE": "V6_MERGE.md",
}
VARIANTS_DIR = HARNESS_DIR / "arms_variants"
SAMPLES = (0, 1, 2)
SCENARIO_ORDER = [f"S{i:02d}" for i in range(1, 13)]

# MJ reference (frozen ground truth for THIS campaign — verbatim, identical to
# aa_calibration.py's MJ_TRUTH and the task's reference block).
MJ_TRUTH: dict[str, tuple[int, str, str]] = {
    "S01": (
        0,
        "kill",
        "solution without a felt problem; duplication found by audit not by anyone living with it",
    ),
    "S02": (
        1,
        "kill",
        "cheap in-stack (Postgres) options unexhausted vs a new datastore nobody can operate",
    ),
    "S03": (
        1,
        "ship-as-is",
        "measured review-latency + rubber-stamp incidents met by a minimal reversible remedy",
    ),
    "S04": (
        0,
        "ship-as-is",
        "proportionality — tested two-call-site helper for a 15-person internal dashboard",
    ),
    "S05": (
        1,
        "ship-as-is",
        "incident-validated fix; idempotent; config-only and trivially reversible",
    ),
    "S06": (
        1,
        "tweak",
        "the dead branch is no longer a viable rollback — 11 months unexercised",
    ),
    "S07": (
        2,
        "redesign",
        "irreversible revenue-model bet with zero metering and zero willingness-to-pay evidence",
    ),
    "S08": (
        0,
        "kill",
        "revenue concentration — the 8% are top revenue decile and cite it in renewals",
    ),
    "S09": (
        2,
        "redesign",
        "3-month irreversible nav rework justified only by qualitative evidence; cheaper testable alt exists",
    ),
    "S10": (0, "kill", "no measured problem; the standup is where blockers surface"),
    "S11": (1, "ship-as-is", "measured pain met by a minimal reversible policy"),
    "S12": (
        1,
        "tweak",
        "cost-benefit — pinned index solves the only observed pain for near-zero ongoing cost",
    ),
}

OUT_DIR = RUNS_DIR / "round2_tier1b"
RAW_PATH = OUT_DIR / "round2_raw.jsonl"
EXTRACT_PATH = OUT_DIR / "round2_extractions.jsonl"
RESULTS_PATH = OUT_DIR / "round2_results.json"

CHAMPION_RESULTS_PATH = RUNS_DIR / "aa_calibration" / "aa_results.json"
CHAMPION_MODEL_KEY = "fable"  # PRIMARY per amended protocol
CHAMPION_SAMPLES = (3, 4, 5)  # A/A run's fresh Group-B samples

HILLCLIMB_DIR = DESIGN_DIR / "hillclimb"
ROUND2_MD_PATH = HILLCLIMB_DIR / "ROUND2.md"
LEDGER_PATH = HILLCLIMB_DIR / "LEDGER.jsonl"

GATE_MEAN_GAIN = 0.08
GATE_NET_WINS = 5
GATE_CONCERN_LOSS_MAX = 1


# ---------------------------------------------------------------------------
# Scenario / prompt loading (identical assembly to phase2_run.py / aa_calibration.py)
# ---------------------------------------------------------------------------
def load_scenarios() -> dict[str, dict]:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"] if isinstance(data, dict) else data
    return {sc["scenario_id"]: sc for sc in scenarios}


def build_user_message(scenario: dict) -> str:
    return USER_TEMPLATE.format(
        title=scenario["title"],
        domain=scenario["domain"],
        depth=scenario["depth"],
        artifact=scenario["artifact"],
        question=scenario["question"],
        common_task=COMMON_TASK,
    )


def load_variant_system(code: str) -> str:
    path = VARIANTS_DIR / VARIANTS[code]
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Variant prompt empty: {path}")
    return text


# ---------------------------------------------------------------------------
# Champion baseline: reuse fresh Group-B composites from the A/A calibration run.
# ---------------------------------------------------------------------------
def load_champion_baseline() -> dict[str, dict]:
    data = json.loads(CHAMPION_RESULTS_PATH.read_text(encoding="utf-8"))
    assert list(data["group_b_samples"]) == list(CHAMPION_SAMPLES), (
        f"expected champion group_b samples {CHAMPION_SAMPLES}, got {data['group_b_samples']}"
    )
    per_scenario = data["results"][CHAMPION_MODEL_KEY]["per_scenario"]
    out: dict[str, dict] = {}
    for c in per_scenario:
        out[c["scenario_id"]] = c["group_b"]
    missing = set(SCENARIO_ORDER) - set(out)
    assert not missing, f"champion baseline missing scenarios: {missing}"
    return out


# ---------------------------------------------------------------------------
# Fresh generation — EXACT same call shape as phase2_run.generate() / aa_calibration.
# ---------------------------------------------------------------------------
def generate_fresh(
    scenario: dict, sample: int, arm_code: str, system_prompt: str, user: str
) -> str:
    key = cache.make_key(
        "design_generate",
        MODEL_NAME,
        scenario["scenario_id"],
        arm_code,
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
        temperature=ARM_TEMPERATURE,  # llm.py drops it for fable models
        max_tokens=ARM_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "design_generate",
            "campaign": "round2_tier1b",
            "arm": arm_code,
            "model": MODEL_NAME,
            "scenario_id": scenario["scenario_id"],
            "sample": sample,
        },
        cache_dir=CACHE_DIR,
    )
    return text


def run_generation(
    scenarios: dict[str, dict], variant_systems: dict[str, str]
) -> list[dict]:
    tasks = [
        (vc, sid, sample)
        for vc in VARIANTS
        for sid in SCENARIO_ORDER
        for sample in SAMPLES
    ]
    total = len(tasks)
    print(
        f"[Generate] {total} fresh calls (3 variants x 12 scenarios x 3 samples) on {MODEL_NAME} ...",
        file=sys.stderr,
    )
    results: list[dict] = []
    done = 0

    def _work(task):
        vc, sid, sample = task
        sc = scenarios[sid]
        user = build_user_message(sc)
        text = generate_fresh(sc, sample, vc, variant_systems[vc], user)
        return {
            "scenario_id": sid,
            "variant": vc,
            "model": MODEL_NAME,
            "sample": sample,
            "raw_text": text,
        }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(future_map):
            done += 1
            try:
                results.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                vc, sid, sample = future_map[fut]
                print(
                    f"[ERROR] gen variant={vc} sid={sid} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                results.append(
                    {
                        "scenario_id": sid,
                        "variant": vc,
                        "model": MODEL_NAME,
                        "sample": sample,
                        "raw_text": "",
                        "error": str(exc),
                    }
                )
            if done % 12 == 0 or done == total:
                print(f"  ... {done}/{total} generations complete", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Uniform gpt-4.1 extraction (byte-identical prompt to phase2_analyze.py)
# ---------------------------------------------------------------------------
def extract_one(sid: str, tag: str, sample: int, raw_text: str) -> dict:
    user = p2a.EXTRACT_TEMPLATE.format(review=raw_text or "")
    key = cache.make_key(
        "round2_design_extract_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, sample, user
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
                "stage": "round2_design_extract_v1",
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


def run_extraction(records: list[dict]) -> None:
    total = len(records)
    print(
        f"[Extract] gpt-4.1 uniform extraction over {total} records ...",
        file=sys.stderr,
    )
    done = 0

    def _work(rec):
        ex = extract_one(
            rec["scenario_id"], rec["variant"], rec["sample"], rec.get("raw_text") or ""
        )
        rec["x_grit"], rec["x_direction"], rec["x_concern"] = (
            ex["grit"],
            ex["direction"],
            ex["concern"],
        )
        return rec

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = [pool.submit(_work, r) for r in records]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 24 == 0 or done == total:
                print(f"  ... {done}/{total} extractions complete", file=sys.stderr)


# ---------------------------------------------------------------------------
# Majority vote per (scenario, variant) over 3 samples — same logic as
# aa_calibration.majority_of / phase2_analyze._mode.
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
        "round2_design_concern_grade_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, 0, user
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
            meta={
                "stage": "round2_design_concern_grade_v1",
                "scenario_id": sid,
                "tag": tag,
            },
            cache_dir=CACHE_DIR,
        )
    try:
        obj = p2a._extract_json(cached)
    except (json.JSONDecodeError, AttributeError):
        obj = {}
    return int(bool(obj.get("match", False)))


# ---------------------------------------------------------------------------
# Per-variant scoring, paired vs champion baseline.
# ---------------------------------------------------------------------------
def score_variant(
    vc: str, champion: dict[str, dict], by_scenario: dict[str, list[dict]]
) -> dict:
    print(
        f"[Score:{vc}] concern-matching (gpt-4.1) for {len(SCENARIO_ORDER)} scenarios ...",
        file=sys.stderr,
    )
    per_scenario = []
    for sid in SCENARIO_ORDER:
        mj_g, mj_d, mj_c = MJ_TRUTH[sid]
        maj = majority_of(by_scenario[sid])

        ge = int(maj["grit"] is not None and maj["grit"] == mj_g)
        de = int(maj["direction"] is not None and maj["direction"] == mj_d)
        cm = concern_match(sid, f"{vc}_{MODEL_NAME}", mj_c, maj["concern"])
        comp = (ge + de + cm) / 3.0

        champ = champion[sid]
        diff = comp - champ["composite"]
        escalation = maj["grit"] is not None and maj["grit"] > mj_g
        concern_loss = bool(champ.get("concern_match") == 1 and cm == 0)

        # Distinguish TRUE extractor parse failure (a sample's raw_text yielded no
        # parseable grit/direction at all) from a MAJORITY TIE (every sample parsed
        # fine individually, but the 3 samples disagreed with no plurality winner,
        # so majority_of()/_mode() returns None). Both surface as maj[...] is None,
        # but they are different findings and must not be conflated in the report.
        sample_grits = [r["x_grit"] for r in by_scenario[sid]]
        sample_directions = [r["x_direction"] for r in by_scenario[sid]]
        grit_extract_fail = any(g is None for g in sample_grits)
        direction_extract_fail = any(d is None for d in sample_directions)
        grit_tie = maj["grit"] is None and not grit_extract_fail
        direction_tie = maj["direction"] is None and not direction_extract_fail

        per_scenario.append(
            {
                "scenario_id": sid,
                "mj": {"grit": mj_g, "direction": mj_d, "concern": mj_c},
                "variant_majority": maj,
                "sample_grits": sample_grits,
                "sample_directions": sample_directions,
                "grit_extract_fail": grit_extract_fail,
                "direction_extract_fail": direction_extract_fail,
                "grit_majority_tie": grit_tie,
                "direction_majority_tie": direction_tie,
                "variant": {
                    "grit_exact": ge,
                    "direction_exact": de,
                    "concern_match": cm,
                    "composite": comp,
                },
                "champion": champ,
                "diff_variant_minus_champion": diff,
                "escalation": escalation,
                "concern_loss_vs_champion": concern_loss,
            }
        )

    diffs = [c["diff_variant_minus_champion"] for c in per_scenario]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = sum(1 for d in diffs if d == 0)
    net_wins = wins - losses
    mean_gain = float(np.mean(diffs))
    concern_losses = sum(1 for c in per_scenario if c["concern_loss_vs_champion"])
    escalation_count = sum(1 for c in per_scenario if c["escalation"])
    # TRUE per-sample extraction failures (raw_text yielded no parseable value at all).
    extract_failures = sum(
        1 for c in per_scenario if c["grit_extract_fail"] or c["direction_extract_fail"]
    )
    # Majority-vote ties: every sample parsed fine individually, but 3 samples split
    # with no plurality winner on grit and/or direction.
    majority_ties = sum(
        1 for c in per_scenario if c["grit_majority_tie"] or c["direction_majority_tie"]
    )

    grit_exact_n = sum(c["variant"]["grit_exact"] for c in per_scenario)
    direction_exact_n = sum(c["variant"]["direction_exact"] for c in per_scenario)
    concern_match_n = sum(c["variant"]["concern_match"] for c in per_scenario)
    composite_mean = float(np.mean([c["variant"]["composite"] for c in per_scenario]))
    champion_composite_mean = float(
        np.mean([c["champion"]["composite"] for c in per_scenario])
    )

    gate_pass = (
        net_wins >= GATE_NET_WINS
        and mean_gain >= GATE_MEAN_GAIN
        and concern_losses <= GATE_CONCERN_LOSS_MAX
    )

    return {
        "variant": vc,
        "model": MODEL_NAME,
        "composite_mean": composite_mean,
        "champion_composite_mean": champion_composite_mean,
        "grit_exact_of_12": grit_exact_n,
        "direction_exact_of_12": direction_exact_n,
        "concern_match_of_12": concern_match_n,
        "escalation_count": escalation_count,
        "extract_failures": extract_failures,
        "majority_ties": majority_ties,
        "per_scenario": per_scenario,
        "diff_vector": diffs,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "net_wins": net_wins,
        "mean_gain": mean_gain,
        "concern_losses": concern_losses,
        "gate": {
            "net_wins_threshold": GATE_NET_WINS,
            "mean_gain_floor": GATE_MEAN_GAIN,
            "concern_loss_max": GATE_CONCERN_LOSS_MAX,
            "net_wins_ok": net_wins >= GATE_NET_WINS,
            "mean_gain_ok": mean_gain >= GATE_MEAN_GAIN,
            "concern_losses_ok": concern_losses <= GATE_CONCERN_LOSS_MAX,
        },
        "gate_pass": gate_pass,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HILLCLIMB_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = load_scenarios()
    assert set(scenarios) == set(SCENARIO_ORDER), "scenario set mismatch"

    variant_systems = {vc: load_variant_system(vc) for vc in VARIANTS}
    for vc, txt in variant_systems.items():
        print(
            f"Loaded variant {vc}: {len(txt)} chars ({VARIANTS[vc]})", file=sys.stderr
        )

    champion = load_champion_baseline()
    print(
        f"Loaded champion baseline (fable-5, A/A group B samples {CHAMPION_SAMPLES}) "
        f"from {CHAMPION_RESULTS_PATH}",
        file=sys.stderr,
    )

    # ---- Generate 108 fresh arm calls ----
    records = run_generation(scenarios, variant_systems)
    with RAW_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            records, key=lambda r: (r["variant"], r["scenario_id"], r["sample"])
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {RAW_PATH} ({len(records)} records).", file=sys.stderr)

    by_variant_scenario: dict[str, dict[str, list[dict]]] = {
        vc: {sid: [] for sid in SCENARIO_ORDER} for vc in VARIANTS
    }
    for r in records:
        by_variant_scenario[r["variant"]][r["scenario_id"]].append(r)
    for vc in VARIANTS:
        for sid in SCENARIO_ORDER:
            n = len(by_variant_scenario[vc][sid])
            assert n == 3, f"{vc} {sid}: expected 3 records, got {n}"

    # ---- Uniform gpt-4.1 extraction over all 108 records ----
    run_extraction(records)
    with EXTRACT_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            records, key=lambda r: (r["variant"], r["scenario_id"], r["sample"])
        ):
            fh.write(
                json.dumps(
                    {
                        "scenario_id": rec["scenario_id"],
                        "variant": rec["variant"],
                        "sample": rec["sample"],
                        "x_grit": rec["x_grit"],
                        "x_direction": rec["x_direction"],
                        "x_concern": rec["x_concern"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Wrote {EXTRACT_PATH} ({len(records)} extractions).", file=sys.stderr)

    # ---- Score each variant, paired vs champion ----
    per_variant_results = {}
    for vc in VARIANTS:
        per_variant_results[vc] = score_variant(vc, champion, by_variant_scenario[vc])

    elapsed = time.time() - t0
    results = {
        "campaign": "round2_tier1b_screen_2",
        "tier": "1b",
        "round": 2,
        "campaign_judge_model": CAMPAIGN_JUDGE_MODEL,
        "model": MODEL_NAME,
        "variants": list(VARIANTS),
        "samples": list(SAMPLES),
        "n_scenarios": len(SCENARIO_ORDER),
        "champion_source": {
            "results_json": str(CHAMPION_RESULTS_PATH),
            "model_key": CHAMPION_MODEL_KEY,
            "group": "B",
            "samples": list(CHAMPION_SAMPLES),
        },
        "champion_composite_mean": float(
            np.mean([champion[sid]["composite"] for sid in SCENARIO_ORDER])
        ),
        "gate": {
            "net_wins_threshold": GATE_NET_WINS,
            "mean_gain_floor": GATE_MEAN_GAIN,
            "concern_loss_max": GATE_CONCERN_LOSS_MAX,
            "note": "PASS requires ALL of: net wins >=5, mean paired gain >=0.08, concern-match losses <=1",
        },
        "results": per_variant_results,
        "elapsed_seconds": elapsed,
    }
    RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {RESULTS_PATH}", file=sys.stderr)

    for vc in VARIANTS:
        r = per_variant_results[vc]
        print(
            json.dumps(
                {
                    "variant": vc,
                    "composite_mean": round(r["composite_mean"], 4),
                    "champion_composite_mean": round(r["champion_composite_mean"], 4),
                    "net_wins": r["net_wins"],
                    "mean_gain": round(r["mean_gain"], 4),
                    "concern_losses": r["concern_losses"],
                    "grit_exact_of_12": r["grit_exact_of_12"],
                    "direction_exact_of_12": r["direction_exact_of_12"],
                    "concern_match_of_12": r["concern_match_of_12"],
                    "escalation_count": r["escalation_count"],
                    "extract_failures": r["extract_failures"],
                    "majority_ties": r["majority_ties"],
                    "gate_pass": r["gate_pass"],
                },
                indent=2,
            )
        )

    print(f"\nDone in {elapsed:.1f}s.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
