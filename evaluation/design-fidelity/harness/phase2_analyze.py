"""Design-fidelity Phase-2 — frozen scoring + inference (uniform LLM re-extraction).

This script REPLACES the brittle regex pre-parse in raw.jsonl. For EVERY record
it calls a gpt-4.1 extractor (different model family than the claude arms) that
reads raw_text and returns {grit, direction, concern} under uniform rules. All
model calls are content-addressed cached (key includes raw_text), so re-runs are
free.

Pipeline:
  1. Uniform LLM extraction (gpt-4.1) of grit/direction/concern from raw_text.
  2. Majority vote per (scenario, arm) over 3 samples.
  3. Per scenario x arm: grit_exact, direction_exact, concern_match (gpt-4.1
     semantic judge vs MJ). composite = mean of the three in {0,1/3,2/3,1}.
  4. PRIMARY: paired one-sided Wilcoxon MACHETE>NATIVE + exact sign test +
     mean paired diff + 95% bootstrap CI (B=2000) + >=2-scenario margin.
  5. SPECIFICITY: MACHETE vs HOLISTIC (paired diff + sign test).
  6. Per-arm composite + per-dimension table; per-quadrant descriptive.
  7. A/B ranking: neutralize MJ's 12 reads (gpt-4.1 neutralizer), blind claude
     ranker reads MJ + 6 arms neutralized, ranks 6 by alignment. 3 order-
     randomized trials -> consensus mean-rank per scenario -> Friedman + W.

Outputs:
  runs/<ts>/phase2_results.json
  ../PHASE2-DESIGN-RESULTS.md
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from pathlib import Path

import _bootstrap  # noqa: F401  — wires cognition harness onto sys.path

import cache  # type: ignore
import llm  # type: ignore
import prompts as cog_prompts  # type: ignore

import numpy as np
from scipy.stats import wilcoxon, binomtest, friedmanchisquare

from config import (
    ARMS,
    CACHE_DIR,
    GRADER_MODEL,        # gpt-4.1
    GRADER_TEMPERATURE,
    GRADER_MAX_TOKENS,
    NEUTRALIZER_MODEL,   # gpt-4.1
    NEUTRALIZER_TEMPERATURE,
    NEUTRALIZER_MAX_TOKENS,
    ARM_MODEL,           # claude-sonnet-4-5  (ranker = different family from gpt-4.1)
)

EXTRACTOR_MODEL = "gpt-5.5"  # re-run 2026-07-07; was gpt-4.1
RANKER_MODEL = ARM_MODEL  # follows ARM_MODEL (claude-fable-5) — different family from the gpt-5.5 neutralizer
import sys as _sys

_default_run = "20260612_135125"
RUN_DIR = Path(
    _sys.argv[1] if len(_sys.argv) > 1 else str(Path(__file__).resolve().parent / "runs" / _default_run)
).resolve()
OUT_MD = Path(__file__).resolve().parent.parent / "PHASE2-DESIGN-RESULTS.md"
SCENARIO_ORDER = [f"S{i:02d}" for i in range(1, 13)]
VALID_DIR = ("ship-as-is", "tweak", "redesign", "kill")

# ---------------------------------------------------------------------------
# MJ ground truth (frozen, from the task / MJ-DESIGN-FORM.md reconciled reads)
# ---------------------------------------------------------------------------
MJ_TRUTH = {
    "S01": (0, "kill", "solution without a felt problem; duplication found by an audit not by anyone living with it"),
    "S02": (1, "kill", "cheap in-stack (Postgres) options unexhausted vs a datastore nobody can operate"),
    "S03": (1, "ship-as-is", "measured review-latency + rubber-stamp incidents met by a minimal reversible remedy"),
    "S04": (0, "ship-as-is", "proportionality — tested two-call-site helper for a 15-person internal dashboard"),
    "S05": (1, "ship-as-is", "incident-validated fix; idempotent; config-only and trivially reversible"),
    "S06": (1, "tweak", "the dead branch is no longer a viable rollback — 11 months unexercised"),
    "S07": (2, "redesign", "irreversible revenue-model bet with zero metering and zero willingness-to-pay evidence"),
    "S08": (0, "kill", "revenue concentration — the 8% are top revenue decile and cite it in renewals"),
    "S09": (2, "redesign", "3-month irreversible nav rework justified only by qualitative evidence; cheaper testable alt exists"),
    "S10": (0, "kill", "no measured problem; the standup is where blockers surface"),
    "S11": (1, "ship-as-is", "measured pain met by a minimal reversible policy"),
    "S12": (1, "tweak", "cost-benefit — pinned index solves the only observed pain for near-zero ongoing cost"),
}

# MJ's full reads (verbatim from MJ-DESIGN-FORM.md, first occurrence per scenario)
# needed for the A/B ranking (neutralized as the alignment reference).
MJ_READS = {
    "S01": "Platformization makes three independently-shipping teams hostage to a shared release cadence and a live-traffic migration, in exchange for fixing pain nobody reported. The coordination tax almost certainly exceeds the cost of 40% duplicated code. If the retry-logic duplication itches, extract a small shared library teams can adopt voluntarily — that captures most of the value at none of the coupling. Kill the central service.",
    "S02": "Adding Neo4j plus a CDC sync pipeline for a 5%-beta feature is a permanent operational surface bought before anyone tried indexing, query reshaping, caching, or a precomputed edge-closure table in Postgres — where the team's expertise actually is. Kill the proposal for now; timebox a week of in-Postgres optimization, and only reopen the graph-DB conversation if the budget provably can't be met.",
    "S03": "This is the right-sized response: the incidents prove the informal approach stopped scaling, and everything proposed (SLA target, soft size cap, rotation) is lightweight and trivially revertible if it turns out to be bureaucracy. Ship it, revisit in a month.",
    "S04": "All three reviewer notes are gold-plating at this blast radius: 'yesterday/tomorrow' is unrequested scope, localization is irrelevant for an internal admin tool, and the clock-freeze testing pattern is standard and already working. Injecting now() is a fine nice-to-have if the author wants it, but none of this should block merge.",
    "S05": "Exponential backoff with jitter, a sane timeout, and fewer retries is the textbook fix for retry-driven pool exhaustion, and idempotency keys remove the double-charge risk. Sanity-check 8s against the gateway's real p99 before shipping, but this is exactly the kind of low-risk, incident-driven change you approve without ceremony.",
    "S06": "Remove the flag and the old checkout path. The 'in case we roll back' rationale is illusory: code that hasn't run against a year of changes isn't a safety net, it's a trap, and meanwhile it taxes every reader (as this new hire just demonstrated). Git history is the real rollback. Local, reversible cleanup — good first task for the new hire.",
    "S07": "The pain signal (large prospects balking at per-seat) is real, but the proposal jumps straight to the heaviest possible answer. Reshape it: run a WTP study, build minimal metering as shadow instrumentation, and pilot a hybrid (platform fee + usage) with a handful of large new deals. Commit to the full switch only after the pilot shows billing predictability doesn't tank retention — CS's churn worry is exactly what killed this for other companies.",
    "S08": "Monthly open-rate is the wrong metric: the module is cheap to run, stable, and load-bearing for your biggest contracts. Sunsetting it with no replacement trades one engineer of capacity for renewal risk on top-decile accounts — a terrible exchange rate. Kill the sunset; if the maintenance cost rankles, scope a lighter replacement first and migrate before retiring anything.",
    "S09": "The cohort insight is plausible but a 200-person qual study can't carry a bet this size against nervous-leadership DAU risk. Reshape the plan: run the behavioral cohort analysis to confirm the split exists in usage data, ship incremental feed personalization as an A/B first, and keep the mode-split as the follow-on if personalization moves nothing. Same destination, staged risk.",
    "S10": "This is change driven by a manager's general sentiment, not evidence, and the cost it would pay (losing the one reliable blocker-surfacing point, per the seniors) is concrete while the benefit (15 minutes) is trivial for a co-located single-timezone team. Don't replace it. If meeting load is the real complaint, audit the whole calendar — the daily standup is the wrong target.",
    "S11": "The incidents settle the 'is this bureaucracy?' debate: the informal system already failed in production. Every element proposed is soft, cheap, and revertible. Adopt it as written and review whether it helped in 4–6 weeks.",
    "S12": "Adopt the cheap pieces: pinned channel index and an onboarding shortlist. Skip the enforced naming convention and archive policy — that's ongoing curation overhead for a 12-person team whose members 'mostly find what they need.' If the team doubles, revisit.",
}

QUADRANT = {  # (depth, domain) read from scenarios_design.json
    "S01": ("deep", "technical"), "S02": ("deep", "technical"), "S03": ("deep", "technical"),
    "S04": ("shallow", "technical"), "S05": ("shallow", "technical"), "S06": ("shallow", "technical"),
    "S07": ("deep", "non_technical"), "S08": ("deep", "non_technical"), "S09": ("deep", "non_technical"),
    "S10": ("shallow", "non_technical"), "S11": ("shallow", "non_technical"), "S12": ("shallow", "non_technical"),
}

# ---------------------------------------------------------------------------
# JSON helper
# ---------------------------------------------------------------------------
def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        return json.loads(m.group(0)) if m else {}


# ---------------------------------------------------------------------------
# 1. Uniform LLM extractor (gpt-4.1)  — cached by raw_text content
# ---------------------------------------------------------------------------
EXTRACT_SYSTEM = "You are a careful classifier. You output only the requested JSON object and nothing else."
EXTRACT_TEMPLATE = (
    "A senior reviewer reviewed a design proposal. Read their review verbatim and extract THREE things "
    "as strict JSON. Apply these rules identically regardless of formatting (markdown, bold, hedging):\n\n"
    "1. grit (int 0|1|2|3): the blast-radius of the change the reviewer RECOMMENDS.\n"
    "   0 = none / ship as-is (no change).\n"
    "   1 = surface / local, reversible tweak.\n"
    "   2 = structural / bounded reshape of a module or section.\n"
    "   3 = foundational / system-wide, hard to reverse.\n\n"
    "2. direction (one of: \"ship-as-is\"|\"tweak\"|\"redesign\"|\"kill\"): the reviewer's VERDICT ON THE "
    "PROPOSAL. If the proposal is to remove/sunset/replace something and the reviewer says DON'T do it "
    "(keep it), that is \"kill\" (they are killing the proposal). If the reviewer endorses the proposal "
    "as-is, that is \"ship-as-is\". If they endorse with minor local edits, \"tweak\". If they call for a "
    "bounded-or-larger reshape, \"redesign\". Pick the single PRIMARY verdict even if hedged/qualified.\n\n"
    "3. concern (one line): the single load-bearing factor that decides the call for the reviewer.\n\n"
    "REVIEW:\n{review}\n\n"
    'Output STRICT JSON: {{"grit": 0|1|2|3, "direction": "ship-as-is"|"tweak"|"redesign"|"kill", "concern": "<one line>"}}'
)


def extract_one(rec: dict) -> dict:
    raw = rec.get("raw_text") or ""
    sid, arm, sample = rec["scenario_id"], rec["arm"], rec.get("sample", 0)
    user = EXTRACT_TEMPLATE.format(review=raw)
    # content-addressed: raw_text is in the prompt -> key changes if text changes
    key = cache.make_key("design_extract_v1", EXTRACTOR_MODEL, sid, arm, sample, user)
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=EXTRACTOR_MODEL, system=EXTRACT_SYSTEM, user=user,
            temperature=0.0, max_tokens=300,
        )
        cache.put(key, cached, meta={"stage": "design_extract_v1", "scenario_id": sid, "arm": arm, "sample": sample}, cache_dir=CACHE_DIR)
    obj = _extract_json(cached)
    g = obj.get("grit")
    g = int(g) if isinstance(g, (int, float)) or (isinstance(g, str) and g.strip().isdigit()) else None
    if g not in (0, 1, 2, 3):
        g = None
    d = obj.get("direction")
    d = d.strip().lower().replace(" ", "-").replace("_", "-") if isinstance(d, str) else None
    if d not in VALID_DIR:
        d = None
    c = obj.get("concern")
    c = c.strip() if isinstance(c, str) and c.strip() else None
    return {"grit": g, "direction": d, "concern": c}


# ---------------------------------------------------------------------------
# 2. Majority vote per (scenario, arm)
# ---------------------------------------------------------------------------
def _mode(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    counts = Counter(vals).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return None
    return counts[0][0]


# ---------------------------------------------------------------------------
# 3. Concern semantic match judge (gpt-4.1)
# ---------------------------------------------------------------------------
CONCERN_SYSTEM = "You are a careful classifier. You output only the requested JSON object and nothing else."
CONCERN_TEMPLATE = (
    "Two reviewers each named the SINGLE load-bearing concern that decides a design call. "
    "Do they identify the SAME underlying decisive factor (semantically equivalent), even if worded differently?\n\n"
    "REVIEWER A (reference): «{mj}»\n"
    "REVIEWER B (candidate): «{arm}»\n\n"
    'Output STRICT JSON: {{"match": true|false, "reason": "<short>"}}'
)


def concern_match(sid: str, arm: str, mj_c: str | None, arm_c: str | None) -> int:
    if not mj_c or not arm_c:
        return 0
    user = CONCERN_TEMPLATE.format(mj=mj_c, arm=arm_c)
    key = cache.make_key("design_concern_grade_v1", GRADER_MODEL, sid, arm, 0, user)
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=GRADER_MODEL, system=CONCERN_SYSTEM, user=user,
            temperature=GRADER_TEMPERATURE, max_tokens=GRADER_MAX_TOKENS,
        )
        cache.put(key, cached, meta={"stage": "design_concern_grade_v1", "scenario_id": sid, "arm": arm}, cache_dir=CACHE_DIR)
    return int(bool(_extract_json(cached).get("match", False)))


# ---------------------------------------------------------------------------
# A/B ranking helpers
# ---------------------------------------------------------------------------
def neutralize_mj(sid: str, read: str) -> str:
    user = f"{cog_prompts.NEUTRALIZE_INSTRUCTION}\n\n---\n{read}\n---"
    key = cache.make_key("design_neutralize_mj_v1", NEUTRALIZER_MODEL, sid, "MJ", 0, user)
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=NEUTRALIZER_MODEL, system=cog_prompts.NEUTRALIZE_SYSTEM, user=user,
            temperature=NEUTRALIZER_TEMPERATURE, max_tokens=NEUTRALIZER_MAX_TOKENS,
        )
        cache.put(key, cached, meta={"stage": "design_neutralize_mj_v1", "scenario_id": sid}, cache_dir=CACHE_DIR)
    return cached


RANKER_SYSTEM = (
    "You are a careful, impartial evaluator. Do NOT explain your reasoning or write any preamble. "
    "Your entire response must be ONLY the requested JSON object and nothing else."
)
RANKER_TEMPLATE = (
    "A reference reviewer (R) gave a design judgment. Below are {k} candidate reviews labeled by letter. "
    "Rank the candidates from MOST aligned to LEAST aligned with the reference reviewer's judgment "
    "(same recommended action, same blast-radius, same load-bearing reasoning). "
    "Every letter must appear exactly once.\n\n"
    "REFERENCE REVIEWER (R):\n{mj}\n\n"
    "CANDIDATES:\n{candidates}\n\n"
    "Respond with ONLY this JSON object, no other text, no reasoning:\n"
    '{{"ranking": [<letters best-to-worst>]}}  e.g. {{"ranking": ["C","A","E","B","F","D"]}}'
)


def rank_trial(sid: str, mj_neut: str, arm_neut: dict[str, str], trial: int) -> dict[str, int] | None:
    """Returns {arm: rank(1=best)} for one order-randomized trial, or None on failure."""
    arms = list(arm_neut.keys())
    rng = random.Random(f"{sid}|{trial}")
    order = arms[:]
    rng.shuffle(order)
    letters = [chr(ord("A") + i) for i in range(len(order))]
    letter_to_arm = dict(zip(letters, order))
    cand_block = "\n\n".join(f"[{ltr}]\n{arm_neut[letter_to_arm[ltr]]}" for ltr in letters)
    user = RANKER_TEMPLATE.format(k=len(order), mj=mj_neut, candidates=cand_block)
    key = cache.make_key("design_ab_rank_v2", RANKER_MODEL, sid, f"trial{trial}", 0, user)
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_anthropic(
            model=RANKER_MODEL, system=RANKER_SYSTEM, user=user,
            temperature=0.0, max_tokens=1500,
        )
        cache.put(key, cached, meta={"stage": "design_ab_rank_v2", "scenario_id": sid, "trial": trial}, cache_dir=CACHE_DIR)
    obj = _extract_json(cached)
    ranking = obj.get("ranking")
    if not isinstance(ranking, list):
        return None
    ranking = [str(x).strip().upper().strip("[]") for x in ranking]
    if sorted(ranking) != sorted(letters):
        return None
    return {letter_to_arm[l]: pos + 1 for pos, l in enumerate(ranking)}


# ---------------------------------------------------------------------------
# bootstrap CI
# ---------------------------------------------------------------------------
def bootstrap_ci(diffs: list[float], B: int = 2000, seed: int = 12345):
    rng = np.random.default_rng(seed)
    arr = np.array(diffs, dtype=float)
    n = len(arr)
    means = np.array([rng.choice(arr, size=n, replace=True).mean() for _ in range(B)])
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    records = [json.loads(l) for l in (RUN_DIR / "raw.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(records) == 216, f"expected 216, got {len(records)}"

    # ---- 1. uniform extraction ----
    print(f"Extracting {len(records)} records via {EXTRACTOR_MODEL} ...")
    for i, rec in enumerate(records):
        ex = extract_one(rec)
        rec["x_grit"], rec["x_direction"], rec["x_concern"] = ex["grit"], ex["direction"], ex["concern"]
        if (i + 1) % 36 == 0:
            print(f"  ... {i+1}/{len(records)}")

    n_extract_fail = sum(1 for r in records if r["x_grit"] is None or r["x_direction"] is None)
    # compare against the brittle pre-parse for the bias note
    preparse_fail_by_arm = Counter(r["arm"] for r in records if not r.get("parse_ok", True))

    # ---- 2. majority per (scenario, arm) ----
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        groups.setdefault((r["scenario_id"], r["arm"]), []).append(r)

    majority: dict[tuple[str, str], dict] = {}
    rep_neut: dict[tuple[str, str], str] = {}  # representative neutralized review for A/B
    for (sid, arm), recs in groups.items():
        recs = sorted(recs, key=lambda r: r.get("sample", 0))
        mg = _mode([r["x_grit"] for r in recs])
        md = _mode([r["x_direction"] for r in recs])
        # representative concern + neutralized text: a sample matching majority direction, else first
        concern = None
        rep = None
        for r in recs:
            if r["x_direction"] == md and r.get("x_concern"):
                concern = r["x_concern"]
                rep = r.get("neutralized_review") or ""
                break
        if concern is None:
            concern = next((r["x_concern"] for r in recs if r.get("x_concern")), None)
        if rep is None:
            rep = next((r.get("neutralized_review") for r in recs if r.get("neutralized_review")), recs[0].get("neutralized_review") or "")
        majority[(sid, arm)] = {"grit": mg, "direction": md, "concern": concern}
        rep_neut[(sid, arm)] = rep

    # ---- 3. per-cell scoring ----
    print("Grading concern matches via gpt-4.1 ...")
    per_cell = []
    for sid in SCENARIO_ORDER:
        mj_g, mj_d, mj_c = MJ_TRUTH[sid]
        for arm in ARMS:
            maj = majority[(sid, arm)]
            ge = int(maj["grit"] is not None and maj["grit"] == mj_g)
            de = int(maj["direction"] is not None and maj["direction"] == mj_d)
            cm = concern_match(sid, arm, mj_c, maj["concern"])
            comp = (ge + de + cm) / 3.0
            per_cell.append({
                "scenario_id": sid, "arm": arm,
                "grit_exact": ge, "direction_exact": de, "concern_match": cm,
                "composite": comp,
                "mj": {"grit": mj_g, "direction": mj_d, "concern": mj_c},
                "arm_majority": maj,
            })

    cell = {(c["scenario_id"], c["arm"]): c for c in per_cell}

    # composite matrix arm -> [12 scenario composites]
    comp_mat = {arm: [cell[(sid, arm)]["composite"] for sid in SCENARIO_ORDER] for arm in ARMS}

    # ---- 4. per-arm table ----
    per_arm = {}
    for arm in ARMS:
        cells = [cell[(sid, arm)] for sid in SCENARIO_ORDER]
        n = len(cells)
        per_arm[arm] = {
            "n_scenarios": n,
            "composite": sum(c["composite"] for c in cells) / n,
            "grit_exact_rate": sum(c["grit_exact"] for c in cells) / n,
            "direction_exact_rate": sum(c["direction_exact"] for c in cells) / n,
            "concern_match_rate": sum(c["concern_match"] for c in cells) / n,
        }

    # ---- 5. PRIMARY: MACHETE > NATIVE ----
    m = np.array(comp_mat["MACHETE"])
    nat = np.array(comp_mat["NATIVE"])
    diffs = (m - nat).tolist()
    nonzero = [d for d in diffs if d != 0]
    n_machete_better = sum(1 for d in diffs if d > 0)
    n_native_better = sum(1 for d in diffs if d < 0)
    n_tie = sum(1 for d in diffs if d == 0)

    # one-sided Wilcoxon (greater). zero_method='wilcoxon' drops zeros.
    if nonzero:
        try:
            w_stat, w_p = wilcoxon(m, nat, alternative="greater", zero_method="wilcox")
            w_stat, w_p = float(w_stat), float(w_p)
        except ValueError:
            w_stat, w_p = float("nan"), 1.0
    else:
        w_stat, w_p = float("nan"), 1.0
    # exact sign test (one-sided greater) over non-tied pairs
    n_eff = n_machete_better + n_native_better
    sign_p = float(binomtest(n_machete_better, n_eff, 0.5, alternative="greater").pvalue) if n_eff else 1.0
    mean_diff = float(np.mean(diffs))
    ci_lo, ci_hi = bootstrap_ci(diffs)
    margin_net = n_machete_better - n_native_better

    primary = {
        "test": "paired one-sided Wilcoxon signed-rank, MACHETE > NATIVE, n=12 scenarios",
        "machete_composite_mean": float(m.mean()),
        "native_composite_mean": float(nat.mean()),
        "per_scenario_diffs": diffs,
        "wilcoxon_stat": w_stat,
        "wilcoxon_p_one_sided": w_p,
        "n_machete_better": n_machete_better,
        "n_native_better": n_native_better,
        "n_tie": n_tie,
        "sign_test_p_one_sided": sign_p,
        "mean_paired_diff": mean_diff,
        "bootstrap_ci95": [ci_lo, ci_hi],
        "net_scenario_margin": margin_net,
        "meets_2_scenario_margin": margin_net >= 2,
    }

    # ---- 6. SPECIFICITY: MACHETE vs HOLISTIC ----
    hol = np.array(comp_mat["HOLISTIC"])
    sdiffs = (m - hol).tolist()
    s_mb = sum(1 for d in sdiffs if d > 0)
    s_hb = sum(1 for d in sdiffs if d < 0)
    s_tie = sum(1 for d in sdiffs if d == 0)
    s_neff = s_mb + s_hb
    s_sign_p = float(binomtest(s_mb, s_neff, 0.5, alternative="greater").pvalue) if s_neff else 1.0
    try:
        sw_stat, sw_p = wilcoxon(m, hol, alternative="greater", zero_method="wilcox")
        sw_stat, sw_p = float(sw_stat), float(sw_p)
    except ValueError:
        sw_stat, sw_p = float("nan"), 1.0
    specificity = {
        "machete_mean": float(m.mean()), "holistic_mean": float(hol.mean()),
        "mean_paired_diff": float(np.mean(sdiffs)),
        "per_scenario_diffs": sdiffs,
        "n_machete_better": s_mb, "n_holistic_better": s_hb, "n_tie": s_tie,
        "sign_test_p_one_sided": s_sign_p,
        "wilcoxon_stat": sw_stat, "wilcoxon_p_one_sided": sw_p,
    }

    # ---- 7. per-quadrant (descriptive, n=3) ----
    quad_names = [("deep", "technical"), ("shallow", "technical"), ("deep", "non_technical"), ("shallow", "non_technical")]
    per_quadrant = {}
    for q in quad_names:
        sids = [s for s in SCENARIO_ORDER if QUADRANT[s] == q]
        qkey = f"{q[0]}/{q[1]}"
        per_quadrant[qkey] = {
            "scenarios": sids,
            "arm_composite": {arm: float(np.mean([cell[(s, arm)]["composite"] for s in sids])) for arm in ARMS},
        }

    # ---- 8. A/B ranking ----
    print("Neutralizing MJ reads + running blind claude ranker (3 trials) ...")
    mj_neut = {sid: neutralize_mj(sid, MJ_READS[sid]) for sid in SCENARIO_ORDER}
    n_trials = 3
    ab_per_scenario = {}   # sid -> {arm: consensus_mean_rank}
    ab_trial_detail = {}
    for sid in SCENARIO_ORDER:
        arm_neut = {arm: rep_neut[(sid, arm)] for arm in ARMS}
        trials = []
        for t in range(n_trials):
            r = rank_trial(sid, mj_neut[sid], arm_neut, t)
            if r is not None:
                trials.append(r)
        ab_trial_detail[sid] = trials
        if trials:
            consensus = {arm: float(np.mean([tr[arm] for tr in trials])) for arm in ARMS}
        else:
            consensus = {arm: float("nan") for arm in ARMS}
        ab_per_scenario[sid] = consensus

    # per-arm overall mean rank
    ab_mean_rank = {arm: float(np.mean([ab_per_scenario[s][arm] for s in SCENARIO_ORDER])) for arm in ARMS}
    # Friedman over consensus ranks (12 scenarios x 6 arms)
    arm_columns = [[ab_per_scenario[s][arm] for s in SCENARIO_ORDER] for arm in ARMS]
    fr_stat, fr_p = friedmanchisquare(*arm_columns)
    n_blocks, k_arms = 12, len(ARMS)
    kendall_w = float(fr_stat / (n_blocks * (k_arms - 1)))
    # MACHETE rank position among arms (1=best mean rank)
    sorted_arms = sorted(ARMS, key=lambda a: ab_mean_rank[a])
    machete_rank_position = sorted_arms.index("MACHETE") + 1

    ab = {
        "n_trials": n_trials,
        "ranker_model": RANKER_MODEL,
        "neutralizer_model": NEUTRALIZER_MODEL,
        "mean_rank_per_arm": ab_mean_rank,
        "consensus_rank_per_scenario": ab_per_scenario,
        "friedman_stat": float(fr_stat),
        "friedman_p": float(fr_p),
        "kendall_w": kendall_w,
        "arms_best_to_worst": sorted_arms,
        "machete_rank_position": machete_rank_position,
    }

    # ---- assemble + write ----
    results = {
        "run_dir": str(RUN_DIR),
        "extractor_model": EXTRACTOR_MODEL,
        "n_records": len(records),
        "n_extraction_failures": n_extract_fail,
        "preparse_failures_by_arm": dict(preparse_fail_by_arm),
        "mj_self_consistency": {
            "duplicates": ["S02", "S05", "S08", "S11"],
            "grit_agreement": "4/4", "direction_agreement": "4/4",
            "note": "stated per task; not recomputed",
        },
        "mj_truth": {s: {"grit": MJ_TRUTH[s][0], "direction": MJ_TRUTH[s][1], "concern": MJ_TRUTH[s][2]} for s in SCENARIO_ORDER},
        "per_cell": per_cell,
        "per_arm": per_arm,
        "primary_machete_vs_native": primary,
        "specificity_machete_vs_holistic": specificity,
        "per_quadrant": per_quadrant,
        "ab_ranking": ab,
    }

    (RUN_DIR / "phase2_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    # extraction detail for audit
    (RUN_DIR / "phase2_extractions.jsonl").write_text(
        "\n".join(json.dumps({
            "scenario_id": r["scenario_id"], "arm": r["arm"], "sample": r["sample"],
            "x_grit": r["x_grit"], "x_direction": r["x_direction"], "x_concern": r["x_concern"],
            "preparse_grit": r.get("grit"), "preparse_direction": r.get("direction"),
            "preparse_parse_ok": r.get("parse_ok"),
        }, ensure_ascii=False) for r in records), encoding="utf-8")

    print(f"\nWrote {RUN_DIR/'phase2_results.json'}")
    print(json.dumps({
        "per_arm_composite": {a: round(per_arm[a]["composite"], 4) for a in ARMS},
        "primary_wilcoxon_p": w_p, "sign_p": sign_p, "mean_diff": round(mean_diff, 4),
        "ci": [round(ci_lo, 4), round(ci_hi, 4)], "net_margin": margin_net,
        "machete_vs_holistic_diff": round(specificity["mean_paired_diff"], 4),
        "ab_mean_rank": {a: round(ab_mean_rank[a], 3) for a in ARMS},
        "friedman_p": round(float(fr_p), 5), "kendall_w": round(kendall_w, 4),
    }, indent=2))


if __name__ == "__main__":
    main()
