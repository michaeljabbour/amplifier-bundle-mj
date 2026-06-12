"""Phase-1 analysis: McNemar exact, Clopper-Pearson CIs, flip-rate, Cohen's h,
self-consistency, and the style-only invalidation check.

Pure Python + scipy + numpy. Consumes the per-probe records produced by
run_phase1.py (one record per (probe, arm)) and emits a results dict plus a
human-readable markdown report. Can also be run as a CLI against an existing
per_probe.json.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scipy.stats import beta, binomtest

from config import INVALIDATION_THRESHOLD

ALPHA = 0.05


# ---------------------------------------------------------------------------
# Small statistical primitives
# ---------------------------------------------------------------------------
def clopper_pearson(k: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Exact (Clopper-Pearson) two-sided CI for a binomial proportion.

    Uses the Beta-quantile form. Handles the k=0 and k=n boundary cases.
    """
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return (lo, hi)


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions."""
    phi1 = 2 * math.asin(math.sqrt(max(0.0, min(1.0, p1))))
    phi2 = 2 * math.asin(math.sqrt(max(0.0, min(1.0, p2))))
    return phi1 - phi2


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact-binomial McNemar p over the b+c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    return float(binomtest(b, n, 0.5, alternative="two-sided").pvalue)


# ---------------------------------------------------------------------------
# Record indexing helpers
# ---------------------------------------------------------------------------
def _index(records: list[dict]) -> dict[tuple[str, str], dict]:
    """Map (arm, probe_id) -> record."""
    return {(r["arm"], r["probe_id"]): r for r in records}


def _by_arm_polarity(records: list[dict], arm: str, polarity: str) -> list[dict]:
    return [r for r in records if r["arm"] == arm and r["polarity"] == polarity]


def _accuracy_block(records: list[dict], arm: str, polarity: str) -> dict:
    subset = _by_arm_polarity(records, arm, polarity)
    n = len(subset)
    k = sum(1 for r in subset if r["correct"])
    acc = (k / n) if n else 0.0
    lo, hi = clopper_pearson(k, n)
    return {
        "n": n,
        "correct": k,
        "accuracy": acc,
        "ci95": [lo, hi],
        "unclear": sum(1 for r in subset if r["unclear"]),
    }


# ---------------------------------------------------------------------------
# Top-level analysis
# ---------------------------------------------------------------------------
def analyze(records: list[dict]) -> dict:
    arms = sorted({r["arm"] for r in records})
    idx = _index(records)

    rp_ids = sorted(
        {r["probe_id"] for r in records if r["polarity"] == "reason_present"}
    )
    ra_ids = sorted(
        {r["probe_id"] for r in records if r["polarity"] == "reason_absent"}
    )
    pair_ids = sorted({r["pair_id"] for r in records if r.get("pair_id") is not None})

    # ---- Per-arm accuracy (both strata, separately) ----
    per_arm: dict[str, dict] = {}
    for arm in arms:
        arm_recs = [r for r in records if r["arm"] == arm]
        per_arm[arm] = {
            "reason_present": _accuracy_block(records, arm, "reason_present"),
            "reason_absent": _accuracy_block(records, arm, "reason_absent"),
            "unclear_total": sum(1 for r in arm_recs if r["unclear"]),
            "self_consistency": (
                sum(1 for r in arm_recs if r.get("self_consistent")) / len(arm_recs)
                if arm_recs
                else 0.0
            ),
            "n_total": len(arm_recs),
        }

    # ---- Primary: McNemar exact, lens vs baseline on reason_present ----
    mcnemar: dict = {}
    if "lens" in arms and "baseline" in arms:
        b = c = both_right = both_wrong = 0
        for pid in rp_ids:
            lr = idx.get(("lens", pid))
            br = idx.get(("baseline", pid))
            if lr is None or br is None:
                continue
            lo, bo = lr["correct"], br["correct"]
            if lo and not bo:
                b += 1
            elif (not lo) and bo:
                c += 1
            elif lo and bo:
                both_right += 1
            else:
                both_wrong += 1
        mcnemar = {
            "n_reason_present": len(rp_ids),
            "b_lens_right_baseline_wrong": b,
            "c_lens_wrong_baseline_right": c,
            "both_right": both_right,
            "both_wrong": both_wrong,
            "discordant": b + c,
            "p_value_two_sided_exact": mcnemar_exact(b, c),
        }

    # ---- flip-rate per arm: correct on BOTH polarities of a pair ----
    flip_rate: dict[str, dict] = {}
    for arm in arms:
        n_pairs = 0
        both_correct = 0
        for pid in pair_ids:
            members = [
                r for r in records if r["arm"] == arm and r.get("pair_id") == pid
            ]
            present = [r for r in members if r["polarity"] == "reason_present"]
            absent = [r for r in members if r["polarity"] == "reason_absent"]
            if not present or not absent:
                continue
            n_pairs += 1
            if all(r["correct"] for r in present) and all(r["correct"] for r in absent):
                both_correct += 1
        flip_rate[arm] = {
            "n_pairs": n_pairs,
            "correct_both_polarities": both_correct,
            "flip_rate": (both_correct / n_pairs) if n_pairs else 0.0,
        }

    # ---- lens false-withhold rate on reason_absent ----
    false_withhold = None
    if "lens" in arms:
        lens_absent = _by_arm_polarity(records, "lens", "reason_absent")
        n_abs = len(lens_absent)
        fw = sum(1 for r in lens_absent if r["majority_call"] == "withhold")
        false_withhold = {
            "n_reason_absent": n_abs,
            "false_withholds": fw,
            "rate": (fw / n_abs) if n_abs else 0.0,
        }

    # ---- style-only vs lens on reason_present + invalidation check ----
    invalidation = None
    if "lens" in arms and "style_only" in arms:
        lens_acc = per_arm["lens"]["reason_present"]["accuracy"]
        style_acc = per_arm["style_only"]["reason_present"]["accuracy"]
        diff = lens_acc - style_acc
        risk = diff  # convenience alias for the lens-vs-style gap
        invalidation = {
            "lens_accuracy": lens_acc,
            "style_only_accuracy": style_acc,
            "difference": diff,
            "abs_difference": abs(diff),
            "threshold": INVALIDATION_THRESHOLD,
            "invalidation_risk": abs(diff) < INVALIDATION_THRESHOLD,
            "note": (
                "style may explain the effect"
                if abs(risk) < INVALIDATION_THRESHOLD
                else "lens separates from style"
            ),
        }

    # ---- Cohen's h + risk difference, lens vs baseline (reason_present) ----
    effect = None
    if "lens" in arms and "baseline" in arms:
        p_lens = per_arm["lens"]["reason_present"]["accuracy"]
        p_base = per_arm["baseline"]["reason_present"]["accuracy"]
        effect = {
            "lens_accuracy": p_lens,
            "baseline_accuracy": p_base,
            "risk_difference": p_lens - p_base,
            "cohens_h": cohens_h(p_lens, p_base),
        }

    return {
        "arms": arms,
        "counts": {
            "reason_present": len(rp_ids),
            "reason_absent": len(ra_ids),
            "pairs": len(pair_ids),
        },
        "per_arm": per_arm,
        "mcnemar_primary": mcnemar,
        "flip_rate": flip_rate,
        "lens_false_withhold": false_withhold,
        "style_invalidation": invalidation,
        "effect_lens_vs_baseline": effect,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------
def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _ci(block: dict) -> str:
    lo, hi = block["ci95"]
    return f"[{_pct(lo)}, {_pct(hi)}]"


def render_markdown(results: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    lines: list[str] = []
    lines.append("# Cognition-Fidelity Phase 1 — Results")
    lines.append("")
    if meta:
        lines.append("## Run metadata")
        lines.append("")
        for key, val in meta.items():
            lines.append(f"- **{key}**: {val}")
        lines.append("")

    counts = results["counts"]
    lines.append(
        f"Probes: **{counts['reason_present']}** reason-present, "
        f"**{counts['reason_absent']}** reason-absent, "
        f"**{counts['pairs']}** minimal pairs."
    )
    lines.append("")

    # Accuracy table
    lines.append("## Per-arm accuracy (strata reported separately)")
    lines.append("")
    lines.append(
        "| Arm | Reason-present acc (95% CI) | Reason-absent acc (95% CI) | "
        "Unclear | Self-consistency |"
    )
    lines.append("| --- | --- | --- | --- | --- |")
    for arm in results["arms"]:
        pa = results["per_arm"][arm]
        rp = pa["reason_present"]
        ra = pa["reason_absent"]
        lines.append(
            f"| {arm} | {_pct(rp['accuracy'])} {_ci(rp)} ({rp['correct']}/{rp['n']}) "
            f"| {_pct(ra['accuracy'])} {_ci(ra)} ({ra['correct']}/{ra['n']}) "
            f"| {pa['unclear_total']} | {_pct(pa['self_consistency'])} |"
        )
    lines.append("")

    # McNemar
    mc = results.get("mcnemar_primary") or {}
    if mc:
        lines.append(
            "## Primary test — McNemar exact (lens vs baseline, reason-present)"
        )
        lines.append("")
        lines.append(f"- n (paired) = {mc['n_reason_present']}")
        lines.append(
            f"- **b** (lens right, baseline wrong) = {mc['b_lens_right_baseline_wrong']}"
        )
        lines.append(
            f"- **c** (lens wrong, baseline right) = {mc['c_lens_wrong_baseline_right']}"
        )
        lines.append(
            f"- both right = {mc['both_right']}, both wrong = {mc['both_wrong']}"
        )
        lines.append(f"- discordant (b+c) = {mc['discordant']}")
        lines.append(f"- **two-sided exact p = {mc['p_value_two_sided_exact']:.4g}**")
        lines.append("")

    # Effect size
    eff = results.get("effect_lens_vs_baseline")
    if eff:
        lines.append("## Effect size (lens vs baseline, reason-present)")
        lines.append("")
        lines.append(f"- risk difference = {_pct(eff['risk_difference'])}")
        lines.append(f"- Cohen's h = {eff['cohens_h']:.3f}")
        lines.append("")

    # Flip-rate
    fr = results.get("flip_rate") or {}
    if fr:
        lines.append("## Flip-rate (correct on BOTH polarities across pairs)")
        lines.append("")
        lines.append("| Arm | Pairs | Correct-both | Flip-rate |")
        lines.append("| --- | --- | --- | --- |")
        for arm in results["arms"]:
            block = fr.get(arm)
            if block:
                lines.append(
                    f"| {arm} | {block['n_pairs']} | "
                    f"{block['correct_both_polarities']} | {_pct(block['flip_rate'])} |"
                )
        lines.append("")

    # False-withhold
    fw = results.get("lens_false_withhold")
    if fw:
        lines.append("## Lens false-withhold rate (reason-absent — should be LOW)")
        lines.append("")
        lines.append(
            f"- {fw['false_withholds']}/{fw['n_reason_absent']} = "
            f"**{_pct(fw['rate'])}**"
        )
        lines.append("")

    # Invalidation
    inv = results.get("style_invalidation")
    if inv:
        lines.append("## Style-only control (negative control)")
        lines.append("")
        lines.append(f"- lens reason-present acc = {_pct(inv['lens_accuracy'])}")
        lines.append(
            f"- style-only reason-present acc = {_pct(inv['style_only_accuracy'])}"
        )
        lines.append(
            f"- |lens − style-only| = {_pct(inv['abs_difference'])} "
            f"(threshold {_pct(inv['threshold'])})"
        )
        if inv["invalidation_risk"]:
            lines.append("")
            lines.append("> ⚠ INVALIDATION RISK: style may explain the effect.")
        lines.append("")

    # Plain-English summary
    lines.append("## Summary")
    lines.append("")
    lines.append(_plain_summary(results))
    lines.append("")
    return "\n".join(lines)


def _plain_summary(results: dict) -> str:
    parts: list[str] = []
    pa = results["per_arm"]
    if "lens" in pa and "baseline" in pa:
        lens = pa["lens"]["reason_present"]["accuracy"]
        base = pa["baseline"]["reason_present"]["accuracy"]
        parts.append(
            f"On the reason-present stratum the lens scored {_pct(lens)} versus the "
            f"baseline's {_pct(base)}"
        )
        mc = results.get("mcnemar_primary") or {}
        if mc:
            parts[-1] += (
                f"; the paired McNemar exact test gave p = "
                f"{mc['p_value_two_sided_exact']:.4g} over {mc['discordant']} "
                f"discordant pairs (b={mc['b_lens_right_baseline_wrong']}, "
                f"c={mc['c_lens_wrong_baseline_right']})"
            )
        parts[-1] += "."
    fw = results.get("lens_false_withhold")
    if fw:
        parts.append(
            f"The lens false-withheld on {_pct(fw['rate'])} of reason-absent twins, "
            f"indicating it is {'NOT ' if fw['rate'] < 0.5 else ''}a degenerate "
            f"always-withholder."
        )
    inv = results.get("style_invalidation")
    if inv:
        if inv["invalidation_risk"]:
            parts.append(
                "The style-only control scored close to the lens, so style alone may "
                "explain the effect — treat the result as INVALID until separated."
            )
        else:
            parts.append(
                f"The style-only control trailed the lens by {_pct(inv['abs_difference'])}, "
                "supporting that reasoning discipline (not voice) drives the lift."
            )
    return " ".join(parts) if parts else "Insufficient arms present for a summary."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Analyze Phase-1 per-probe records.")
    ap.add_argument("per_probe", help="Path to per_probe.json")
    ap.add_argument("--out-json", default=None, help="Write results.json here")
    ap.add_argument("--out-md", default=None, help="Write results.md here")
    args = ap.parse_args()

    records = json.loads(Path(args.per_probe).read_text(encoding="utf-8"))
    results = analyze(records)
    md = render_markdown(results)

    if args.out_json:
        Path(args.out_json).write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if args.out_md:
        Path(args.out_md).write_text(md, encoding="utf-8")
    if not args.out_json and not args.out_md:
        print(md)


if __name__ == "__main__":
    main()
