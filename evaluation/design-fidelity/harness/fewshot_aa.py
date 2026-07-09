"""Few-shot campaign DEV phase -- STEP 1: A/A stability gate (runs BEFORE the LOO sweep).

Per FEWSHOT-CAMPAIGN-CHARTER.md ADOPTED AMENDMENTS, defect (2): the A/A stability
check must run before the LOO sweep, because K=11 few-shot is a different sampling
regime than the short prompts the earlier hill-climb A/A calibration measured.

Design: longest config (K=11, full-read) on the V3FS family. LOO-consistent
prompts (for scenario s use the exemplar block built from the other 11). Two
INDEPENDENT groups (group A = fresh samples 0,1,2; group B = fresh samples 3,4,5),
3 samples x 12 scenarios each = 72 total claude-fable-5 calls, distinct cache tags
per group. Judge everything gpt-4.1 (uniform extractor + concern-match, imported
from phase2_analyze.py). Per scenario: majority-of-3 -> composite vs MJ_TRUTH.
F = p90(|composite_B - composite_A|) over the 12 scenarios.

  F < 0.08                 -> PASS. Proceed to Step 2 with all 10 configs x 2 families.
  F >= 0.08                -> drop the full-read FORMAT everywhere (both arm families);
                               re-A/A the longest surviving config (K=11, compact).
    re-A/A F < 0.08         -> PASS. Proceed to Step 2 with the 5 compact-only
                               configs x 2 families.
    re-A/A F >= 0.08 too    -> STOP. "no sweep possible." Write outcome to the ledger.

Outputs:
  runs/fewshot_loo/aa_gate_raw.jsonl        (72 or 144 fresh generations)
  runs/fewshot_loo/aa_gate_extractions.jsonl
  runs/fewshot_loo/aa_gate_results.json     (F value(s) + decision + surviving configs)
  ../fewshot/LEDGER.jsonl                    (append: aa_check entry/entries)

Usage:
    python fewshot_aa.py
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import _bootstrap  # noqa: F401

import numpy as np

import fewshot_common as fc
from config import DESIGN_DIR, MAX_WORKERS, RUNS_DIR

OUT_DIR = RUNS_DIR / "fewshot_loo"
AA_RAW_PATH = OUT_DIR / "aa_gate_raw.jsonl"
AA_EXTRACT_PATH = OUT_DIR / "aa_gate_extractions.jsonl"
AA_RESULTS_PATH = OUT_DIR / "aa_gate_results.json"

FEWSHOT_DIR = DESIGN_DIR / "fewshot"
LEDGER_PATH = FEWSHOT_DIR / "LEDGER.jsonl"

F_GATE = 0.08
GROUPS = {"A": (0, 1, 2), "B": (3, 4, 5)}


def _append_ledger(entry: dict) -> None:
    FEWSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _run_group(
    config: dict,
    family: str,
    group_label: str,
    samples: tuple[int, ...],
    scenarios: dict[str, dict],
    bank: dict[str, dict],
    family_base: str,
    raw_records: list[dict],
) -> None:
    tag = f"aa|{family}|{config['id']}|group{group_label}"
    tasks = [(sid, sample) for sid in fc.SCENARIO_ORDER for sample in samples]

    def _work(task):
        sid, sample = task
        sc = scenarios[sid]
        system_prompt = fc.build_system_prompt(
            family_base, bank, scenarios, config, sid
        )
        user = fc.build_user_message(sc)
        text = fc.generate(sc, sample, tag, system_prompt, user)
        return {
            "scenario_id": sid,
            "family": family,
            "config_id": config["id"],
            "group": group_label,
            "sample": sample,
            "raw_text": text,
        }

    done = 0
    total = len(tasks)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(futs):
            done += 1
            try:
                raw_records.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                sid, sample = futs[fut]
                print(
                    f"[ERROR] aa gen {tag} sid={sid} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                raw_records.append(
                    {
                        "scenario_id": sid,
                        "family": family,
                        "config_id": config["id"],
                        "group": group_label,
                        "sample": sample,
                        "raw_text": "",
                        "error": str(exc),
                    }
                )
            if done % 12 == 0 or done == total:
                print(f"  [{tag}] ... {done}/{total} generations", file=sys.stderr)


def run_aa_for_config(
    config: dict,
    family: str,
    scenarios: dict[str, dict],
    bank: dict[str, dict],
    raw_records: list[dict],
) -> dict:
    family_base = fc.load_arm_base(family)
    print(
        f"[A/A] family={family} config={config['id']} -- 2 groups x 3 samples x 12 scenarios = 72 calls",
        file=sys.stderr,
    )
    for group_label, samples in GROUPS.items():
        _run_group(
            config,
            family,
            group_label,
            samples,
            scenarios,
            bank,
            family_base,
            raw_records,
        )

    # Extraction
    by_group_scenario: dict[str, dict[str, list[dict]]] = {
        "A": {s: [] for s in fc.SCENARIO_ORDER},
        "B": {s: [] for s in fc.SCENARIO_ORDER},
    }
    my_records = [
        r
        for r in raw_records
        if r["family"] == family and r["config_id"] == config["id"]
    ]
    for r in my_records:
        by_group_scenario[r["group"]][r["scenario_id"]].append(r)

    def _extract_all(group_label: str):
        tag = f"aa|{family}|{config['id']}|group{group_label}"

        def _work(rec):
            ex = fc.extract_one(
                rec["scenario_id"], tag, rec["sample"], rec.get("raw_text") or ""
            )
            rec["x_grit"], rec["x_direction"], rec["x_concern"] = (
                ex["grit"],
                ex["direction"],
                ex["concern"],
            )
            return rec

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futs = [
                pool.submit(_work, r)
                for group_recs in by_group_scenario[group_label].values()
                for r in group_recs
            ]
            for fut in as_completed(futs):
                fut.result()

    for group_label in GROUPS:
        _extract_all(group_label)

    # Majority + composite per scenario per group
    per_scenario = []
    for sid in fc.SCENARIO_ORDER:
        maj_a = fc.majority_of(by_group_scenario["A"][sid])
        maj_b = fc.majority_of(by_group_scenario["B"][sid])
        cell_a = fc.score_cell(sid, f"aa|{family}|{config['id']}|groupA", maj_a)
        cell_b = fc.score_cell(sid, f"aa|{family}|{config['id']}|groupB", maj_b)
        diff = cell_b["composite"] - cell_a["composite"]
        per_scenario.append(
            {
                "scenario_id": sid,
                "group_a": cell_a,
                "group_b": cell_b,
                "diff_b_minus_a": diff,
            }
        )

    diffs = [c["diff_b_minus_a"] for c in per_scenario]
    abs_diffs = [abs(d) for d in diffs]
    f_p90 = float(np.percentile(abs_diffs, 90))
    mean_abs_diff = float(np.mean(abs_diffs))
    mean_diff = float(np.mean(diffs))

    return {
        "family": family,
        "config_id": config["id"],
        "per_scenario": per_scenario,
        "diff_vector": diffs,
        "mean_diff": mean_diff,
        "mean_abs_diff": mean_abs_diff,
        "F_p90_abs_diff": f_p90,
        "gate_pass": f_p90 < F_GATE,
        "composite_mean_a": float(
            np.mean([c["group_a"]["composite"] for c in per_scenario])
        ),
        "composite_mean_b": float(
            np.mean([c["group_b"]["composite"] for c in per_scenario])
        ),
    }


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FEWSHOT_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = fc.load_scenarios()
    bank = fc.load_exemplar_bank()
    raw_records: list[dict] = []

    # ---- Step 1: longest config = K11_full, V3FS family ----
    config_k11_full = fc.CONFIG_BY_ID["K11_full"]
    aa_1 = run_aa_for_config(config_k11_full, "V3FS", scenarios, bank, raw_records)
    print(
        json.dumps(
            {
                "stage": "aa_1",
                "config": "K11_full",
                "family": "V3FS",
                "F_p90": round(aa_1["F_p90_abs_diff"], 4),
                "pass": aa_1["gate_pass"],
            },
            indent=2,
        )
    )
    _append_ledger(
        {
            "campaign": "fewshot_dev",
            "entry": "aa_check",
            "stage": "aa_1",
            "family": "V3FS",
            "config_id": "K11_full",
            "F_p90_abs_diff": aa_1["F_p90_abs_diff"],
            "mean_diff": aa_1["mean_diff"],
            "gate_pass": aa_1["gate_pass"],
            "gate_threshold": F_GATE,
        }
    )

    aa_2 = None
    decision: str
    surviving_configs: list[dict]

    if aa_1["gate_pass"]:
        decision = "proceed_all_10_configs"
        surviving_configs = fc.CONFIGS
    else:
        print(
            f"[A/A] STEP 1 BREACH (F={aa_1['F_p90_abs_diff']:.4f} >= {F_GATE}). "
            "Dropping full-read format everywhere; re-A/A the longest survivor (K11_compact).",
            file=sys.stderr,
        )
        config_k11_compact = fc.CONFIG_BY_ID["K11_compact"]
        aa_2 = run_aa_for_config(
            config_k11_compact, "V3FS", scenarios, bank, raw_records
        )
        print(
            json.dumps(
                {
                    "stage": "aa_2",
                    "config": "K11_compact",
                    "family": "V3FS",
                    "F_p90": round(aa_2["F_p90_abs_diff"], 4),
                    "pass": aa_2["gate_pass"],
                },
                indent=2,
            )
        )
        _append_ledger(
            {
                "campaign": "fewshot_dev",
                "entry": "aa_check",
                "stage": "aa_2",
                "family": "V3FS",
                "config_id": "K11_compact",
                "F_p90_abs_diff": aa_2["F_p90_abs_diff"],
                "mean_diff": aa_2["mean_diff"],
                "gate_pass": aa_2["gate_pass"],
                "gate_threshold": F_GATE,
                "note": "re-A/A after Step-1 breach dropped the full-read format",
            }
        )
        if aa_2["gate_pass"]:
            decision = "proceed_compact_only_5_configs"
            surviving_configs = [c for c in fc.CONFIGS if c["format"] == "compact"]
            assert len(surviving_configs) == 5
        else:
            decision = "stop_no_sweep_possible"
            surviving_configs = []

    with AA_RAW_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            raw_records,
            key=lambda r: (r["config_id"], r["group"], r["scenario_id"], r["sample"]),
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {AA_RAW_PATH} ({len(raw_records)} records).", file=sys.stderr)

    with AA_EXTRACT_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            raw_records,
            key=lambda r: (r["config_id"], r["group"], r["scenario_id"], r["sample"]),
        ):
            fh.write(
                json.dumps(
                    {
                        "scenario_id": rec["scenario_id"],
                        "config_id": rec["config_id"],
                        "group": rec["group"],
                        "sample": rec["sample"],
                        "x_grit": rec.get("x_grit"),
                        "x_direction": rec.get("x_direction"),
                        "x_concern": rec.get("x_concern"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    elapsed = time.time() - t0
    results = {
        "campaign": "fewshot_dev_aa_gate",
        "gate_threshold": F_GATE,
        "aa_1": aa_1,
        "aa_2": aa_2,
        "decision": decision,
        "surviving_configs": [c["id"] for c in surviving_configs],
        "elapsed_seconds": elapsed,
    }
    AA_RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {AA_RESULTS_PATH}", file=sys.stderr)

    _append_ledger(
        {
            "campaign": "fewshot_dev",
            "entry": "aa_check_decision",
            "decision": decision,
            "surviving_configs": [c["id"] for c in surviving_configs],
        }
    )

    if decision == "stop_no_sweep_possible":
        print(
            "\n[STOP] no sweep possible -- A/A breached on both the full-read and compact K=11 configs.",
            file=sys.stderr,
        )
        _append_ledger(
            {
                "campaign": "fewshot_dev",
                "entry": "dev_gate",
                "decision": "outcome_4_no_sweep_possible",
                "reason": "A/A stability breach on both K11_full and K11_compact V3FS configs",
            }
        )

    print(f"\nDone in {elapsed:.1f}s. Decision: {decision}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
