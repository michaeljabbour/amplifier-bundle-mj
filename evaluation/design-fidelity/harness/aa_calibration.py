"""A/A calibration — pure noise-floor measurement for the design-fidelity hill-climb.

Purpose (see ../HILL-CLIMB-PLAN.md, "TIER 0 — FREEZE"): before spending any budget
climbing, measure how much the eval swings when NOTHING changes — the SAME champion
arm (MACHETE) scored twice from independent samples. If that noise floor F is not
comfortably below the pre-registered gate (mean gain >= max(0.08, F)), the hill is
not measurable at this sample size and climbing would just be chasing sampling noise.

Design (frozen, matches the plan's "A/A CALIBRATION" line):
  Group A: the EXISTING champion MACHETE samples 0-2, reused verbatim (raw_text)
           from the two frozen Phase-2 runs:
             fable  -> runs/20260707_034211/raw.jsonl
             sonnet -> runs/20260612_135125/raw.jsonl
  Group B: FRESH MACHETE samples 3,4,5 for BOTH models, generated here with the
           EXACT SAME prompt assembly as phase2_run.py (arms/MACHETE.md system
           prompt + USER_TEMPLATE + COMMON_TASK), through the same shared cache
           (the sample index 3/4/5 makes these fresh cache keys, not hits against
           the existing samples 0-2).
  Judge:  uniform gpt-4.1 for EVERYTHING — the same extractor prompt/logic and the
          same CONCERN_SYSTEM/CONCERN_TEMPLATE concern-match judge as
          phase2_analyze.py, imported directly from that module so the prompts are
          byte-identical (not re-typed), just pointed at gpt-4.1 instead of
          whatever GRADER_MODEL/EXTRACTOR_MODEL config.py currently has pinned.

Per scenario per group per model: majority {grit,direction,concern} over the 3
samples -> composite = mean(grit_exact, direction_exact, concern_match) in
{0, 1/3, 2/3, 1}. Paired diff d_s = composite_B - composite_A over the 12
scenarios. Report mean diff, mean |diff|, F = p90(|diff|), the 12-value diff
vector, and net-wins (d_s>0 counted as a win, d_s<0 a loss).

Outputs:
  runs/aa_calibration/aa_raw.jsonl   (the 72 fresh Group-B generations only)
  runs/aa_calibration/aa_results.json (everything numeric, both models)

Usage:
    python aa_calibration.py
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
    arm_path,
)

# Reuse the analyzer's prompts/helpers verbatim (byte-identical extractor +
# concern-match prompts; only the model name changes for this campaign).
import phase2_analyze as p2a  # type: ignore

CAMPAIGN_JUDGE_MODEL = "gpt-4.1"

ARM = "MACHETE"
MODELS: dict[str, str] = {
    "fable": "claude-fable-5",
    "sonnet": "claude-sonnet-4-5",  # PRIMARY
}
GROUP_A_RUN_DIR: dict[str, str] = {
    "fable": "20260707_034211",
    "sonnet": "20260612_135125",
}
GROUP_A_SAMPLES = (0, 1, 2)
GROUP_B_SAMPLES = (3, 4, 5)

SCENARIO_ORDER = [f"S{i:02d}" for i in range(1, 13)]

# MJ reference (frozen ground truth for THIS campaign — verbatim from the task).
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

OUT_DIR = RUNS_DIR / "aa_calibration"
AA_RAW_PATH = OUT_DIR / "aa_raw.jsonl"
AA_RESULTS_PATH = OUT_DIR / "aa_results.json"

HILLCLIMB_DIR = DESIGN_DIR / "hillclimb"
AA_MD_PATH = HILLCLIMB_DIR / "AA-CALIBRATION.md"
LEDGER_PATH = HILLCLIMB_DIR / "LEDGER.jsonl"

GATE_FLOOR = 0.08  # pre-registered Tier-1b margin (see HILL-CLIMB-PLAN.md)
GATE_NET_WINS = 5


# ---------------------------------------------------------------------------
# Scenario / prompt loading (identical assembly to phase2_run.py)
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


def load_machete_system() -> str:
    text = arm_path(ARM).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Arm prompt empty: {arm_path(ARM)}")
    return text


# ---------------------------------------------------------------------------
# Group A: reuse existing champion raw_text (samples 0-2), no new calls.
# ---------------------------------------------------------------------------
def load_group_a(model_key: str) -> dict[str, list[dict]]:
    run_dir = HARNESS_DIR / "runs" / GROUP_A_RUN_DIR[model_key]
    raw_path = run_dir / "raw.jsonl"
    records = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_scenario: dict[str, list[dict]] = {sid: [] for sid in SCENARIO_ORDER}
    for r in records:
        if r["arm"] != ARM:
            continue
        if r["sample"] not in GROUP_A_SAMPLES:
            continue
        by_scenario[r["scenario_id"]].append(r)
    for sid, recs in by_scenario.items():
        assert len(recs) == 3, (
            f"Group A {model_key} {sid}: expected 3 records, got {len(recs)}"
        )
    return by_scenario


# ---------------------------------------------------------------------------
# Group B: fresh generation — EXACT same call shape as phase2_run.generate().
# ---------------------------------------------------------------------------
def generate_fresh(
    scenario: dict, model_name: str, sample: int, system_prompt: str, user: str
) -> str:
    key = cache.make_key(
        "design_generate",
        model_name,
        scenario["scenario_id"],
        ARM,
        sample,
        system_prompt + "\n##USER##\n" + user,
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is not None:
        return cached
    text = llm.call_anthropic(
        model=model_name,
        system=system_prompt,
        user=user,
        temperature=ARM_TEMPERATURE,  # sonnet uses it; llm.py drops it for fable models
        max_tokens=ARM_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "design_generate",
            "campaign": "aa_calibration",
            "arm": ARM,
            "model": model_name,
            "scenario_id": scenario["scenario_id"],
            "sample": sample,
        },
        cache_dir=CACHE_DIR,
    )
    return text


def run_group_b(scenarios: dict[str, dict], system_prompt: str) -> list[dict]:
    tasks = [
        (sid, model_key, model_name, sample)
        for sid in SCENARIO_ORDER
        for model_key, model_name in MODELS.items()
        for sample in GROUP_B_SAMPLES
    ]
    total = len(tasks)
    print(
        f"[Group B] generating {total} fresh MACHETE samples (samples 3,4,5 x 2 models x 12 scenarios) ...",
        file=sys.stderr,
    )
    results: list[dict] = []
    done = 0

    def _work(task):
        sid, model_key, model_name, sample = task
        sc = scenarios[sid]
        user = build_user_message(sc)
        text = generate_fresh(sc, model_name, sample, system_prompt, user)
        return {
            "scenario_id": sid,
            "model_key": model_key,
            "model": model_name,
            "arm": ARM,
            "sample": sample,
            "group": "B",
            "raw_text": text,
        }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(future_map):
            done += 1
            try:
                results.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                sid, model_key, model_name, sample = future_map[fut]
                print(
                    f"[ERROR] gen sid={sid} model={model_key} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                results.append(
                    {
                        "scenario_id": sid,
                        "model_key": model_key,
                        "model": model_name,
                        "arm": ARM,
                        "sample": sample,
                        "group": "B",
                        "raw_text": "",
                        "error": str(exc),
                    }
                )
            if done % 12 == 0 or done == total:
                print(f"  ... {done}/{total} Group-B samples complete", file=sys.stderr)
    return results


# ---------------------------------------------------------------------------
# Uniform gpt-4.1 extraction (byte-identical prompt to phase2_analyze.py)
# ---------------------------------------------------------------------------
def extract_one(sid: str, tag: str, sample: int, raw_text: str) -> dict:
    user = p2a.EXTRACT_TEMPLATE.format(review=raw_text or "")
    key = cache.make_key(
        "aa_design_extract_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, sample, user
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
                "stage": "aa_design_extract_v1",
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


def run_extraction(all_records: list[dict]) -> None:
    total = len(all_records)
    print(
        f"[Extract] gpt-4.1 uniform extraction over {total} records (Group A + Group B, both models) ...",
        file=sys.stderr,
    )
    done = 0

    def _work(rec):
        tag = f"{ARM}_{rec['model_key']}_{rec['group']}"
        ex = extract_one(
            rec["scenario_id"], tag, rec["sample"], rec.get("raw_text") or ""
        )
        rec["x_grit"] = ex["grit"]
        rec["x_direction"] = ex["direction"]
        rec["x_concern"] = ex["concern"]
        return rec

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = [pool.submit(_work, r) for r in all_records]
        for fut in as_completed(futs):
            fut.result()
            done += 1
            if done % 24 == 0 or done == total:
                print(f"  ... {done}/{total} extractions complete", file=sys.stderr)


# ---------------------------------------------------------------------------
# Majority vote per (scenario, model, group) — same logic as phase2_analyze._mode
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
        "aa_design_concern_grade_v1", CAMPAIGN_JUDGE_MODEL, sid, tag, 0, user
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
                "stage": "aa_design_concern_grade_v1",
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
# Per-model scoring
# ---------------------------------------------------------------------------
def score_model(
    model_key: str, group_a: dict[str, list[dict]], group_b: dict[str, list[dict]]
) -> dict:
    print(
        f"[Score:{model_key}] concern-matching (gpt-4.1) for {len(SCENARIO_ORDER)} scenarios x 2 groups ...",
        file=sys.stderr,
    )
    per_scenario = []
    for sid in SCENARIO_ORDER:
        mj_g, mj_d, mj_c = MJ_TRUTH[sid]

        maj_a = majority_of(group_a[sid])
        maj_b = majority_of(group_b[sid])

        ge_a = int(maj_a["grit"] is not None and maj_a["grit"] == mj_g)
        de_a = int(maj_a["direction"] is not None and maj_a["direction"] == mj_d)
        cm_a = concern_match(sid, f"{ARM}_{model_key}_A", mj_c, maj_a["concern"])
        comp_a = (ge_a + de_a + cm_a) / 3.0

        ge_b = int(maj_b["grit"] is not None and maj_b["grit"] == mj_g)
        de_b = int(maj_b["direction"] is not None and maj_b["direction"] == mj_d)
        cm_b = concern_match(sid, f"{ARM}_{model_key}_B", mj_c, maj_b["concern"])
        comp_b = (ge_b + de_b + cm_b) / 3.0

        per_scenario.append(
            {
                "scenario_id": sid,
                "mj": {"grit": mj_g, "direction": mj_d, "concern": mj_c},
                "group_a": {
                    "majority": maj_a,
                    "grit_exact": ge_a,
                    "direction_exact": de_a,
                    "concern_match": cm_a,
                    "composite": comp_a,
                },
                "group_b": {
                    "majority": maj_b,
                    "grit_exact": ge_b,
                    "direction_exact": de_b,
                    "concern_match": cm_b,
                    "composite": comp_b,
                },
                "diff_b_minus_a": comp_b - comp_a,
            }
        )

    diffs = [c["diff_b_minus_a"] for c in per_scenario]
    abs_diffs = [abs(d) for d in diffs]
    mean_diff = float(np.mean(diffs))
    mean_abs_diff = float(np.mean(abs_diffs))
    f_p90 = float(np.percentile(abs_diffs, 90))
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = sum(1 for d in diffs if d == 0)
    net_wins = wins - losses

    gate_threshold = max(GATE_FLOOR, f_p90)
    gate_would_pass = (net_wins >= GATE_NET_WINS) and (mean_diff >= gate_threshold)

    if f_p90 < GATE_FLOOR:
        measurability = "MEASURABLE (F < 0.08 — pre-registered gate margin stands)"
    elif f_p90 < 0.30:
        measurability = f"MEASURABLE AT REDUCED SENSITIVITY (F={f_p90:.4f} >= 0.08 — gate must rise to F for this model)"
    else:
        measurability = f"NOT RELIABLY MEASURABLE (F={f_p90:.4f} is a large fraction of the 0..1 composite range — recommend ABORT / more samples before climbing on this model)"

    return {
        "model_key": model_key,
        "model": MODELS[model_key],
        "composite_mean_a": float(
            np.mean([c["group_a"]["composite"] for c in per_scenario])
        ),
        "composite_mean_b": float(
            np.mean([c["group_b"]["composite"] for c in per_scenario])
        ),
        "per_scenario": per_scenario,
        "diff_vector": diffs,
        "mean_diff": mean_diff,
        "mean_abs_diff": mean_abs_diff,
        "F_p90_abs_diff": f_p90,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "net_wins": net_wins,
        "gate_threshold_used": gate_threshold,
        "gate_would_pass_under_noise": gate_would_pass,
        "net_wins_fraction_of_gate": net_wins / GATE_NET_WINS,
        "mean_diff_fraction_of_gate": (mean_diff / gate_threshold)
        if gate_threshold
        else None,
        "measurability_verdict": measurability,
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
    system_prompt = load_machete_system()
    print(
        f"Loaded {len(scenarios)} scenarios; MACHETE system prompt {len(system_prompt)} chars.",
        file=sys.stderr,
    )

    # ---- Group A: reuse existing champion samples ----
    group_a: dict[str, dict[str, list[dict]]] = {}
    for model_key in MODELS:
        group_a[model_key] = load_group_a(model_key)
        print(
            f"[Group A] {model_key}: loaded 36 reused MACHETE records (12 scenarios x 3 samples) from "
            f"runs/{GROUP_A_RUN_DIR[model_key]}/raw.jsonl",
            file=sys.stderr,
        )

    # ---- Group B: fresh generation (72 calls) ----
    b_records = run_group_b(scenarios, system_prompt)
    with AA_RAW_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            b_records, key=lambda r: (r["scenario_id"], r["model_key"], r["sample"])
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(
        f"Wrote {AA_RAW_PATH} ({len(b_records)} fresh Group-B records).",
        file=sys.stderr,
    )

    group_b: dict[str, dict[str, list[dict]]] = {
        mk: {sid: [] for sid in SCENARIO_ORDER} for mk in MODELS
    }
    for r in b_records:
        group_b[r["model_key"]][r["scenario_id"]].append(r)
    for mk in MODELS:
        for sid in SCENARIO_ORDER:
            n = len(group_b[mk][sid])
            assert n == 3, f"Group B {mk} {sid}: expected 3 records, got {n}"

    # ---- Uniform gpt-4.1 extraction over ALL records (A + B, both models) ----
    all_records: list[dict] = []
    for model_key in MODELS:
        for sid in SCENARIO_ORDER:
            for r in group_a[model_key][sid]:
                all_records.append(
                    {
                        "scenario_id": sid,
                        "model_key": model_key,
                        "group": "A",
                        "sample": r["sample"],
                        "raw_text": r.get("raw_text") or "",
                    }
                )
            for r in group_b[model_key][sid]:
                all_records.append(
                    {
                        "scenario_id": sid,
                        "model_key": model_key,
                        "group": "B",
                        "sample": r["sample"],
                        "raw_text": r.get("raw_text") or "",
                    }
                )
    run_extraction(all_records)

    # re-attach extractions back onto group_a/group_b record lists
    ex_index = {
        (r["model_key"], r["group"], r["scenario_id"], r["sample"]): r
        for r in all_records
    }
    for model_key in MODELS:
        for sid in SCENARIO_ORDER:
            for r in group_a[model_key][sid]:
                ex = ex_index[(model_key, "A", sid, r["sample"])]
                r["x_grit"], r["x_direction"], r["x_concern"] = (
                    ex["x_grit"],
                    ex["x_direction"],
                    ex["x_concern"],
                )
            for r in group_b[model_key][sid]:
                ex = ex_index[(model_key, "B", sid, r["sample"])]
                r["x_grit"], r["x_direction"], r["x_concern"] = (
                    ex["x_grit"],
                    ex["x_direction"],
                    ex["x_concern"],
                )

    # ---- Score each model ----
    per_model_results = {}
    for model_key in MODELS:
        per_model_results[model_key] = score_model(
            model_key, group_a[model_key], group_b[model_key]
        )

    elapsed = time.time() - t0
    results = {
        "campaign": "aa_calibration",
        "campaign_judge_model": CAMPAIGN_JUDGE_MODEL,
        "arm": ARM,
        "models": MODELS,
        "group_a_source_runs": GROUP_A_RUN_DIR,
        "group_a_samples": list(GROUP_A_SAMPLES),
        "group_b_samples": list(GROUP_B_SAMPLES),
        "gate": {
            "net_wins_threshold": GATE_NET_WINS,
            "mean_gain_floor": GATE_FLOOR,
            "note": "gate = net wins >= 5 AND mean gain >= max(0.08, F)",
        },
        "primary_model": "sonnet",
        "results": per_model_results,
        "elapsed_seconds": elapsed,
    }
    AA_RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {AA_RESULTS_PATH}", file=sys.stderr)

    for model_key in MODELS:
        r = per_model_results[model_key]
        print(
            json.dumps(
                {
                    "model": model_key,
                    "composite_mean_a": round(r["composite_mean_a"], 4),
                    "composite_mean_b": round(r["composite_mean_b"], 4),
                    "mean_diff": round(r["mean_diff"], 4),
                    "mean_abs_diff": round(r["mean_abs_diff"], 4),
                    "F_p90": round(r["F_p90_abs_diff"], 4),
                    "wins": r["wins"],
                    "losses": r["losses"],
                    "ties": r["ties"],
                    "net_wins": r["net_wins"],
                    "measurability": r["measurability_verdict"],
                },
                indent=2,
            )
        )

    print(f"\nDone in {elapsed:.1f}s.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
