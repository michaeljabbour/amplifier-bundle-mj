"""Few-shot campaign DEV phase -- STEP 2 (LOO sweep) + STEP 3 (DEV GATE) + writeup.

Runs only if runs/fewshot_loo/aa_gate_results.json says the A/A gate passed
(decision != "stop_no_sweep_possible"). For each surviving config x each of the
two arm families (V3FS, NATFS): for each of the 12 scenarios s, build the
few-shot system prompt from exemplars drawn ONLY from the other 11 (per the
config's K/selection/format), generate 3 samples on claude-fable-5, take the
majority {grit,direction,concern}, score composite vs MJ_TRUTH (uniform gpt-4.1
extractor + concern-match judge, byte-identical to phase2_analyze.py).

DEV GATE (V3FS family only, pre-registered):
  Champion per-scenario baseline = A/A calibration's fresh Group-B composites
  (harness/runs/aa_calibration/aa_results.json -> results.fable.per_scenario[*].group_b),
  recomputed from aa_raw.jsonl if that file is absent.
  PASS requires BOTH:
    (a) best V3FS config's LOO composite mean >= 0.667 (champion 0.556 + ~4/36
        winner's-curse margin)
    (b) that config's per-scenario losses to champion <= 2
  Ties within 1/36 -> prefer smaller K, then compact format.
  NATFS results are reported as dev-attribution (descriptive, no gate): best
  NATFS composite vs best V3FS composite.

Outputs:
  runs/fewshot_loo/loo_raw.jsonl, loo_extractions.jsonl, loo_results.json
  ../fewshot/DEV-RESULTS.md
  ../fewshot/LEDGER.jsonl (append: 1 entry per config x family + 1 dev_gate entry)

Usage:
    python fewshot_loo.py
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
LOO_RAW_PATH = OUT_DIR / "loo_raw.jsonl"
LOO_EXTRACT_PATH = OUT_DIR / "loo_extractions.jsonl"
LOO_RESULTS_PATH = OUT_DIR / "loo_results.json"
AA_RESULTS_PATH = OUT_DIR / "aa_gate_results.json"

FEWSHOT_DIR = DESIGN_DIR / "fewshot"
LEDGER_PATH = FEWSHOT_DIR / "LEDGER.jsonl"
DEV_RESULTS_MD_PATH = FEWSHOT_DIR / "DEV-RESULTS.md"

CHAMPION_RESULTS_PATH = RUNS_DIR / "aa_calibration" / "aa_results.json"
CHAMPION_RAW_PATH = RUNS_DIR / "aa_calibration" / "aa_raw.jsonl"
CHAMPION_MODEL_KEY = "fable"
CHAMPION_SAMPLES = (3, 4, 5)

DEV_GATE_COMPOSITE_FLOOR = 0.667
DEV_GATE_MAX_LOSSES = 2
TIE_MARGIN = 1.0 / 36.0
SAMPLES = (0, 1, 2)


def _append_ledger(entry: dict) -> None:
    FEWSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Champion baseline (reused verbatim from the A/A calibration run's Group B)
# ---------------------------------------------------------------------------
def load_champion_baseline() -> dict[str, dict]:
    if CHAMPION_RESULTS_PATH.exists():
        data = json.loads(CHAMPION_RESULTS_PATH.read_text(encoding="utf-8"))
        if list(data.get("group_b_samples", [])) == list(CHAMPION_SAMPLES):
            per_scenario = data["results"][CHAMPION_MODEL_KEY]["per_scenario"]
            out = {c["scenario_id"]: c["group_b"] for c in per_scenario}
            missing = set(fc.SCENARIO_ORDER) - set(out)
            if not missing:
                return out
        print(
            "[WARN] aa_results.json present but shape unexpected; recomputing from aa_raw.jsonl",
            file=sys.stderr,
        )
    # Fallback: recompute from aa_raw.jsonl (fresh Group-B MACHETE generations).
    print(f"[Champion] recomputing baseline from {CHAMPION_RAW_PATH}", file=sys.stderr)
    records = [
        json.loads(line)
        for line in CHAMPION_RAW_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_scenario: dict[str, list[dict]] = {sid: [] for sid in fc.SCENARIO_ORDER}
    for r in records:
        if r.get("model_key") != CHAMPION_MODEL_KEY or r.get("arm") != "MACHETE":
            continue
        if r.get("sample") not in CHAMPION_SAMPLES:
            continue
        by_scenario[r["scenario_id"]].append(r)
    out = {}
    for sid, recs in by_scenario.items():
        assert len(recs) == 3, f"champion recompute {sid}: expected 3, got {len(recs)}"
        for r in recs:
            ex = fc.extract_one(
                sid,
                f"champion_recompute_{CHAMPION_MODEL_KEY}",
                r["sample"],
                r.get("raw_text") or "",
            )
            r["x_grit"], r["x_direction"], r["x_concern"] = (
                ex["grit"],
                ex["direction"],
                ex["concern"],
            )
        maj = fc.majority_of(recs)
        cell = fc.score_cell(sid, f"champion_recompute_{CHAMPION_MODEL_KEY}", maj)
        out[sid] = cell
    return out


# ---------------------------------------------------------------------------
# LOO generation + scoring for one (config, family) pair
# ---------------------------------------------------------------------------
def run_loo_for_config(
    config: dict,
    family: str,
    scenarios: dict[str, dict],
    bank: dict[str, dict],
    family_base: str,
    raw_records: list[dict],
) -> dict:
    tag = f"loo|{family}|{config['id']}"
    tasks = [(sid, sample) for sid in fc.SCENARIO_ORDER for sample in SAMPLES]
    print(
        f"[LOO] family={family} config={config['id']} -- 12 scenarios x 3 samples = 36 calls",
        file=sys.stderr,
    )

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
            "sample": sample,
            "raw_text": text,
        }

    my_records: list[dict] = []
    done = 0
    total = len(tasks)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(futs):
            done += 1
            try:
                my_records.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                sid, sample = futs[fut]
                print(
                    f"[ERROR] loo gen {tag} sid={sid} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                my_records.append(
                    {
                        "scenario_id": sid,
                        "family": family,
                        "config_id": config["id"],
                        "sample": sample,
                        "raw_text": "",
                        "error": str(exc),
                    }
                )
            if done % 12 == 0 or done == total:
                print(f"  [{tag}] ... {done}/{total} generations", file=sys.stderr)

    # Extraction
    def _extract_work(rec):
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
        futs2 = [pool.submit(_extract_work, r) for r in my_records]
        for fut in as_completed(futs2):
            fut.result()

    raw_records.extend(my_records)

    by_scenario: dict[str, list[dict]] = {sid: [] for sid in fc.SCENARIO_ORDER}
    for r in my_records:
        by_scenario[r["scenario_id"]].append(r)
    for sid in fc.SCENARIO_ORDER:
        assert len(by_scenario[sid]) == 3, (
            f"{tag} {sid}: expected 3, got {len(by_scenario[sid])}"
        )

    per_scenario = []
    for sid in fc.SCENARIO_ORDER:
        recs = by_scenario[sid]
        maj = fc.majority_of(recs)
        cell = fc.score_cell(sid, tag, maj)
        sample_grits = [r["x_grit"] for r in recs]
        sample_directions = [r["x_direction"] for r in recs]
        grit_extract_fail = any(g is None for g in sample_grits)
        direction_extract_fail = any(d is None for d in sample_directions)
        grit_tie = maj["grit"] is None and not grit_extract_fail
        direction_tie = maj["direction"] is None and not direction_extract_fail
        cell["sample_grits"] = sample_grits
        cell["sample_directions"] = sample_directions
        cell["grit_extract_fail"] = grit_extract_fail
        cell["direction_extract_fail"] = direction_extract_fail
        cell["grit_majority_tie"] = grit_tie
        cell["direction_majority_tie"] = direction_tie
        per_scenario.append(cell)

    composite_mean = float(np.mean([c["composite"] for c in per_scenario]))
    grit_exact_rate = float(np.mean([c["grit_exact"] for c in per_scenario]))
    direction_exact_rate = float(np.mean([c["direction_exact"] for c in per_scenario]))
    concern_match_rate = float(np.mean([c["concern_match"] for c in per_scenario]))
    extract_failures = sum(
        1 for c in per_scenario if c["grit_extract_fail"] or c["direction_extract_fail"]
    )
    majority_ties = sum(
        1 for c in per_scenario if c["grit_majority_tie"] or c["direction_majority_tie"]
    )

    return {
        "family": family,
        "config_id": config["id"],
        "K": config["K"],
        "selection": config["selection"],
        "format": config["format"],
        "composite_mean": composite_mean,
        "grit_exact_rate": grit_exact_rate,
        "direction_exact_rate": direction_exact_rate,
        "concern_match_rate": concern_match_rate,
        "extract_failures": extract_failures,
        "majority_ties": majority_ties,
        "per_scenario": per_scenario,
    }


# ---------------------------------------------------------------------------
# DEV GATE: pick best V3FS config, compare to champion baseline
# ---------------------------------------------------------------------------
def pick_best(results: list[dict]) -> dict:
    """Highest composite_mean; ties within TIE_MARGIN -> smaller K, then compact format."""
    best = max(results, key=lambda r: r["composite_mean"])
    tied = [
        r
        for r in results
        if abs(r["composite_mean"] - best["composite_mean"]) < TIE_MARGIN
    ]
    if len(tied) > 1:
        tied.sort(key=lambda r: (r["K"], 0 if r["format"] == "compact" else 1))
        best = tied[0]
    return best


def dev_gate(v3fs_results: list[dict], champion: dict[str, dict]) -> dict:
    best = pick_best(v3fs_results)
    champion_composites = {sid: champion[sid]["composite"] for sid in fc.SCENARIO_ORDER}
    champion_mean = float(np.mean(list(champion_composites.values())))

    losses = []
    for cell in best["per_scenario"]:
        sid = cell["scenario_id"]
        if cell["composite"] < champion_composites[sid]:
            losses.append(sid)

    composite_ok = best["composite_mean"] >= DEV_GATE_COMPOSITE_FLOOR
    losses_ok = len(losses) <= DEV_GATE_MAX_LOSSES
    gate_pass = composite_ok and losses_ok

    return {
        "best_config_id": best["config_id"],
        "best_composite_mean": best["composite_mean"],
        "champion_composite_mean": champion_mean,
        "champion_per_scenario": champion_composites,
        "composite_floor": DEV_GATE_COMPOSITE_FLOOR,
        "composite_ok": composite_ok,
        "losses_to_champion": losses,
        "n_losses": len(losses),
        "max_losses_allowed": DEV_GATE_MAX_LOSSES,
        "losses_ok": losses_ok,
        "gate_pass": gate_pass,
        "outcome": "challenger_frozen" if gate_pass else "outcome_4_no_dev_signal",
    }


def render_dev_results_md(
    aa_gate: dict,
    v3fs_results: list[dict],
    natfs_results: list[dict],
    gate: dict | None,
    stopped: bool,
) -> str:
    lines = ["# Few-shot campaign -- DEV phase results", ""]

    lines += ["## Step 1 -- A/A stability gate", ""]
    aa1 = aa_gate["aa_1"]
    lines.append(
        f"- aa_1 (K11_full, V3FS): F(p90 |diff|) = {aa1['F_p90_abs_diff']:.4f}, "
        f"mean diff = {aa1['mean_diff']:.4f}, gate {'PASS' if aa1['gate_pass'] else 'BREACH'} (< 0.08 required)"
    )
    if aa_gate.get("aa_2"):
        aa2 = aa_gate["aa_2"]
        lines.append(
            f"- aa_2 (K11_compact, V3FS, re-A/A after aa_1 breach): F(p90 |diff|) = {aa2['F_p90_abs_diff']:.4f}, "
            f"mean diff = {aa2['mean_diff']:.4f}, gate {'PASS' if aa2['gate_pass'] else 'BREACH'}"
        )
    lines.append(f"- **Decision: {aa_gate['decision']}**")
    lines.append("")

    if stopped:
        lines += [
            "## STOP -- no sweep possible",
            "",
            "A/A stability breached on both the K=11 full-read and K=11 compact V3FS "
            'configs. Per the pre-registered stop rule ("F >= 0.08 -> drop the full-read '
            "family, re-A/A longest survivor (K=11 compact); if that breaches too -> STOP, "
            "report 'no sweep possible'\"), the LOO sweep does NOT run. Step 2 (10-config x "
            "2-family sweep) and Step 3 (dev gate) are both skipped -- there is nothing to "
            "report there. Campaign closes here at zero MJ cost (no lock-set authoring, no "
            "MJ reads collected).",
            "",
            "### Per-scenario detail (why it breached)",
            "",
        ]
        for stage_key, label in (
            ("aa_1", "aa_1 (K11_full)"),
            ("aa_2", "aa_2 (K11_compact)"),
        ):
            stage = aa_gate.get(stage_key)
            if not stage:
                continue
            lines.append(
                f"**{label}** -- composite_mean A={stage['composite_mean_a']:.3f}, "
                f"B={stage['composite_mean_b']:.3f}, F(p90)={stage['F_p90_abs_diff']:.4f}"
            )
            lines.append("")
            lines.append(
                "| scenario | group A (grit/dir/concern-match/composite) | group B | diff (B-A) |"
            )
            lines.append("|---|---|---|---|")
            for c in stage["per_scenario"]:
                sid = c["scenario_id"]
                ga, gb = c["group_a"], c["group_b"]
                gam = ga["majority"]
                gbm = gb["majority"]
                lines.append(
                    f"| {sid} | g={gam['grit']},d={gam['direction']},cm={ga['concern_match']},"
                    f"comp={ga['composite']:.3f} | g={gbm['grit']},d={gbm['direction']},"
                    f"cm={gb['concern_match']},comp={gb['composite']:.3f} | "
                    f"{c['diff_b_minus_a']:+.3f} |"
                )
            lines.append("")
        lines += [
            "Both K=11 A/A checks show individual scenarios swinging the composite by a full "
            "1/3 or 2/3 between two identically-configured fresh sample groups (e.g. S02 in "
            "aa_1; S09/S10/S11 in aa_2), i.e. the direction majority itself flips 3-sample "
            "vote between runs. This confirms the charter's defect (2) concern: a K=11 "
            "few-shot prompt is a materially different sampling regime than the short prompts "
            "the original hill-climb A/A measured, and it is NOT stable enough at n=3 samples "
            "to support a LOO dev sweep.",
            "",
        ]
        return "\n".join(lines) + "\n"

    lines += ["## Step 2 -- LOO sweep: full 10-config x 2-family table", ""]
    lines += [
        "| config | family | K | selection | format | composite | grit-exact | dir-exact | concern-match | extract-fails | majority-ties |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    all_results = sorted(
        v3fs_results + natfs_results, key=lambda r: (r["family"], -r["composite_mean"])
    )
    for r in all_results:
        lines.append(
            f"| {r['config_id']} | {r['family']} | {r['K']} | {r['selection']} | {r['format']} | "
            f"{r['composite_mean']:.3f} | {r['grit_exact_rate']:.3f} | {r['direction_exact_rate']:.3f} | "
            f"{r['concern_match_rate']:.3f} | {r['extract_failures']} | {r['majority_ties']} |"
        )
    lines.append("")

    lines += ["## Step 3 -- DEV GATE (V3FS family only)", ""]
    if gate is not None:
        lines += [
            f"- Best V3FS config: **{gate['best_config_id']}** (LOO composite = {gate['best_composite_mean']:.3f})",
            f"- Champion (MACHETE, A/A Group-B, fable-5) composite = {gate['champion_composite_mean']:.3f}",
            f"- (a) composite >= {gate['composite_floor']:.3f}: {'YES' if gate['composite_ok'] else 'NO'} "
            f"({gate['best_composite_mean']:.3f})",
            f"- (b) per-scenario losses to champion <= {gate['max_losses_allowed']}: "
            f"{'YES' if gate['losses_ok'] else 'NO'} ({gate['n_losses']} losses: {', '.join(gate['losses_to_champion']) or 'none'})",
            f"- **Gate verdict: {'PASS -- ' + gate['best_config_id'] + ' frozen as the challenger' if gate['gate_pass'] else 'FAIL -- outcome 4, campaign closes at zero MJ cost'}**",
            "",
        ]

    lines += ["## Attribution readout (descriptive, no gate)", ""]
    best_v3fs = pick_best(v3fs_results)
    best_natfs = pick_best(natfs_results) if natfs_results else None
    if best_natfs is not None:
        lines += [
            f"- Best V3FS config: {best_v3fs['config_id']} @ {best_v3fs['composite_mean']:.3f}",
            f"- Best NATFS config: {best_natfs['config_id']} @ {best_natfs['composite_mean']:.3f}",
            f"- Gap (V3FS - NATFS) = {best_v3fs['composite_mean'] - best_natfs['composite_mean']:.3f}",
            "",
        ]

    lines += ["## Anomalies", ""]
    any_anom = False
    for r in all_results:
        if r["extract_failures"] or r["majority_ties"]:
            any_anom = True
            lines.append(
                f"- {r['family']}/{r['config_id']}: {r['extract_failures']} extract failure(s), "
                f"{r['majority_ties']} majority tie(s)"
            )
    if not any_anom:
        lines.append("- none observed across the LOO sweep")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FEWSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if not AA_RESULTS_PATH.exists():
        print(
            f"[ERROR] {AA_RESULTS_PATH} not found. Run fewshot_aa.py first.",
            file=sys.stderr,
        )
        return 1
    aa_gate = json.loads(AA_RESULTS_PATH.read_text(encoding="utf-8"))

    if aa_gate["decision"] == "stop_no_sweep_possible":
        print(
            "[STOP] A/A gate says no sweep possible. Writing DEV-RESULTS.md and exiting.",
            file=sys.stderr,
        )
        md = render_dev_results_md(aa_gate, [], [], None, stopped=True)
        DEV_RESULTS_MD_PATH.write_text(md, encoding="utf-8")
        return 0

    surviving_ids = aa_gate["surviving_configs"]
    surviving_configs = [fc.CONFIG_BY_ID[cid] for cid in surviving_ids]
    print(
        f"[LOO] {len(surviving_configs)} surviving configs x 2 families = {len(surviving_configs) * 2} runs",
        file=sys.stderr,
    )

    scenarios = fc.load_scenarios()
    bank = fc.load_exemplar_bank()
    family_bases = {fam: fc.load_arm_base(fam) for fam in fc.ARM_FAMILIES}

    raw_records: list[dict] = []
    v3fs_results: list[dict] = []
    natfs_results: list[dict] = []

    for config in surviving_configs:
        for family in fc.ARM_FAMILIES:
            r = run_loo_for_config(
                config, family, scenarios, bank, family_bases[family], raw_records
            )
            if family == "V3FS":
                v3fs_results.append(r)
            else:
                natfs_results.append(r)
            _append_ledger(
                {
                    "campaign": "fewshot_dev",
                    "entry": "config_result",
                    "family": family,
                    "config_id": config["id"],
                    "K": config["K"],
                    "selection": config["selection"],
                    "format": config["format"],
                    "composite_mean": r["composite_mean"],
                    "grit_exact_rate": r["grit_exact_rate"],
                    "direction_exact_rate": r["direction_exact_rate"],
                    "concern_match_rate": r["concern_match_rate"],
                    "extract_failures": r["extract_failures"],
                    "majority_ties": r["majority_ties"],
                }
            )

    with LOO_RAW_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            raw_records,
            key=lambda r: (r["family"], r["config_id"], r["scenario_id"], r["sample"]),
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {LOO_RAW_PATH} ({len(raw_records)} records).", file=sys.stderr)

    with LOO_EXTRACT_PATH.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            raw_records,
            key=lambda r: (r["family"], r["config_id"], r["scenario_id"], r["sample"]),
        ):
            fh.write(
                json.dumps(
                    {
                        "family": rec["family"],
                        "config_id": rec["config_id"],
                        "scenario_id": rec["scenario_id"],
                        "sample": rec["sample"],
                        "x_grit": rec.get("x_grit"),
                        "x_direction": rec.get("x_direction"),
                        "x_concern": rec.get("x_concern"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Wrote {LOO_EXTRACT_PATH}.", file=sys.stderr)

    print("[Champion] loading baseline ...", file=sys.stderr)
    champion = load_champion_baseline()

    gate = dev_gate(v3fs_results, champion)
    print(json.dumps({"dev_gate": gate}, indent=2))
    _append_ledger(
        {
            "campaign": "fewshot_dev",
            "entry": "dev_gate",
            **gate,
        }
    )

    elapsed = time.time() - t0
    results = {
        "campaign": "fewshot_dev_loo",
        "aa_gate": aa_gate,
        "surviving_configs": surviving_ids,
        "v3fs_results": v3fs_results,
        "natfs_results": natfs_results,
        "champion_baseline": champion,
        "dev_gate": gate,
        "elapsed_seconds": elapsed,
    }
    LOO_RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {LOO_RESULTS_PATH}", file=sys.stderr)

    md = render_dev_results_md(
        aa_gate, v3fs_results, natfs_results, gate, stopped=False
    )
    DEV_RESULTS_MD_PATH.write_text(md, encoding="utf-8")
    print(f"Wrote {DEV_RESULTS_MD_PATH}", file=sys.stderr)

    print(f"\nDone in {elapsed:.1f}s.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
