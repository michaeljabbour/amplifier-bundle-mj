#!/usr/bin/env python3
"""Aggregate and compare 3-arm trial results from a harness run.

Reads the run output tree produced by `amplifier_evaluation.harness.run.run()`
and produces per-task comparisons for the 3-arm flowforge evaluation.

Task: reduce-hard
  Arms:       plain-timid, plain-aggressive, machete
  Dimensions: green-and-honest, recall, precision  (+ overall)
  Extras:     multiplicative composite per arm;
              recovered gap = machete_composite − max(plain_composites).

Task: refuse-red
  Arms:       plain-timid, machete  (plain-aggressive did not run this task)
  Dimension:  refusal-on-red-baseline  (+ overall)

Output layout consumed by this module:

    <output_dir>/
        trials/
            {agent_id}__{task_id}__trial-{n}/
                state.json      <- .grader.{overall_score, evaluations, status}

Usage as a library (called by harness.py):

    from analyze import analyze
    md_text, json_text = analyze(output_dir)

Usage as a standalone CLI:

    python3 analyze.py <output_dir>
    # writes comparison.md + comparison.json inside <output_dir> and prints the table.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


# ── Data loading ──────────────────────────────────────────────────────────────


def _load_trial_states(output_dir: Path) -> list[dict[str, Any]]:
    """Walk trials/ and return parsed state.json records (skips unreadable files)."""
    trials_root = output_dir / "trials"
    records: list[dict[str, Any]] = []
    if not trials_root.is_dir():
        return records
    for trial_dir in sorted(trials_root.iterdir()):
        state_path = trial_dir / "state.json"
        if not state_path.is_file():
            continue
        try:
            record: dict[str, Any] = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"[analyze] warn: could not read {state_path}: {exc}",
                file=sys.stderr,
            )
            continue
        records.append(record)
    return records


# ── Aggregation ───────────────────────────────────────────────────────────────


def _aggregate(
    records: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, list[dict[str, Any]]]],  # scores[task_id][agent_id]
    list[tuple[str, str]],  # skipped [(trial_id, reason)]
]:
    """Partition records into usable grader results and skipped entries."""
    # scores[task_id][agent_id] = list of grader dicts from completed trials
    scores: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    skipped: list[tuple[str, str]] = []

    for rec in records:
        trial_id = rec.get("trial_id", "?")
        state = rec.get("state", "?")
        grader = rec.get("grader")

        if state != "completed":
            skipped.append((trial_id, f"state={state}"))
            continue
        if not grader or grader.get("status") != "ok":
            reason = (
                f"grader status={grader.get('status')}" if grader else "grader missing"
            )
            skipped.append((trial_id, reason))
            continue

        task_id = rec.get("task_id", "unknown")
        agent_id = rec.get("agent_id", "unknown")
        scores[task_id][agent_id].append(grader)

    return scores, skipped


# ── Per-task stats ────────────────────────────────────────────────────────────


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _task_stats(
    task_scores: dict[str, list[dict[str, Any]]],
    agents: list[str],
) -> dict[str, Any]:
    """Compute per-agent stats for one task."""
    # Collect all evaluation names + weights from available data.
    eval_meta: dict[str, float] = {}  # name -> weight
    for graders in task_scores.values():
        for g in graders:
            for ev in g.get("evaluations", []):
                if ev.get("name"):
                    eval_meta[ev["name"]] = float(ev.get("weight", 0.0))

    stats: dict[str, Any] = {"agents": {}, "evaluations": list(eval_meta.keys())}

    for agent in agents:
        graders = task_scores.get(agent, [])
        n = len(graders)
        if n == 0:
            stats["agents"][agent] = {"n": 0, "overall": None, "evaluations": {}}
            continue

        overall_scores = [g["overall_score"] for g in graders]
        eval_scores: dict[str, list[float]] = defaultdict(list)
        for g in graders:
            for ev in g.get("evaluations", []):
                name = ev.get("name")
                if name:
                    eval_scores[name].append(float(ev.get("score", 0.0)))

        stats["agents"][agent] = {
            "n": n,
            "overall": _mean(overall_scores),
            "evaluations": {
                name: _mean(eval_scores.get(name, [])) for name in eval_meta
            },
        }

    stats["eval_meta"] = eval_meta
    return stats


# ── Composite and recovered gap ───────────────────────────────────────────────

# Dimensions whose product forms the multiplicative composite for reduce-hard.
_COMPOSITE_DIMS = ["green-and-honest", "recall", "precision"]


def _compute_composite(agent_stats: dict[str, Any]) -> float | None:
    """Multiplicative composite: green-and-honest × recall × precision.

    Returns None if any dimension is missing (arm had no trials or dim absent).
    """
    evals = agent_stats.get("evaluations", {})
    vals = [evals.get(d) for d in _COMPOSITE_DIMS]
    if any(v is None for v in vals):
        return None
    result = 1.0
    for v in vals:
        result *= v  # type: ignore[operator]
    return result


# ── Formatting helpers ────────────────────────────────────────────────────────


def _fmt(v: float | None) -> str:
    if v is None or v != v:  # None or NaN
        return "\u2014"  # em dash
    return f"{v:.3f}"


def _fmt_signed(v: float | None) -> str:
    if v is None or v != v:
        return "\u2014"
    return f"{v:+.3f}"


# ── Task-specific table renderers ─────────────────────────────────────────────


def _render_reduce_hard_table(
    task_id: str,
    task_stats: dict[str, Any],
    agents: list[str],
) -> str:
    """Render reduce-hard: 3-arm table with per-axis rows, composite, and recovered gap."""
    lines: list[str] = []
    lines.append(f"\n## Task: `{task_id}`\n")

    eval_meta: dict[str, float] = task_stats.get("eval_meta", {})

    # Fixed dimension order: composite dims first, then any extras.
    ordered_dims = [d for d in _COMPOSITE_DIMS if d in eval_meta]
    extra_dims = [
        d
        for d in sorted(eval_meta, key=lambda n: (-eval_meta[n], n))
        if d not in ordered_dims
    ]

    # Table header: columns are the three arms.
    header_parts = ["Evaluation", "Weight"] + [
        f"{a} (n={task_stats['agents'].get(a, {}).get('n', 0)})" for a in agents
    ]
    lines.append("| " + " | ".join(header_parts) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")

    # Per-dimension rows.
    for name in ordered_dims + extra_dims:
        weight = eval_meta.get(name, 0.0)
        vals = [
            _fmt(task_stats["agents"].get(a, {}).get("evaluations", {}).get(name))
            for a in agents
        ]
        lines.append(f"| `{name}` | {weight:.2f} | " + " | ".join(vals) + " |")

    # Overall row.
    overall_vals = [
        _fmt(task_stats["agents"].get(a, {}).get("overall")) for a in agents
    ]
    lines.append("| **overall** | \u2014 | " + " | ".join(overall_vals) + " |")

    # Multiplicative composite row (one value per arm).
    composites = {
        a: _compute_composite(task_stats["agents"].get(a, {})) for a in agents
    }
    composite_vals = [_fmt(composites.get(a)) for a in agents]
    lines.append("| **composite** | \u2014 | " + " | ".join(composite_vals) + " |")

    # Recovered-gap row: machete_composite − max(plain composites).
    # Shown in the machete column; plain arm cells show "—".
    plain_agents = [a for a in agents if a != "machete"]
    _plain_raw = [composites.get(a) for a in plain_agents]
    plain_composites: list[float] = [v for v in _plain_raw if v is not None]
    machete_comp = composites.get("machete")

    recovered_gap: float | None = None
    if machete_comp is not None and plain_composites:
        recovered_gap = machete_comp - max(plain_composites)

    recovered_cells = ["\u2014" for _ in agents]
    if "machete" in agents:
        recovered_cells[agents.index("machete")] = _fmt_signed(recovered_gap)
    lines.append("| **recovered-gap** | \u2014 | " + " | ".join(recovered_cells) + " |")

    lines.append("")
    return "\n".join(lines)


def _render_refuse_red_table(
    task_id: str,
    task_stats: dict[str, Any],
    arms: list[str],
) -> str:
    """Render refuse-red: 2-arm table (plain-timid, machete)."""
    lines: list[str] = []
    lines.append(f"\n## Task: `{task_id}`\n")

    eval_meta: dict[str, float] = task_stats.get("eval_meta", {})

    header_parts = ["Evaluation", "Weight"] + [
        f"{a} (n={task_stats['agents'].get(a, {}).get('n', 0)})" for a in arms
    ]
    lines.append("| " + " | ".join(header_parts) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")

    for name in sorted(eval_meta, key=lambda n: (-eval_meta[n], n)):
        weight = eval_meta[name]
        vals = [
            _fmt(task_stats["agents"].get(a, {}).get("evaluations", {}).get(name))
            for a in arms
        ]
        lines.append(f"| `{name}` | {weight:.2f} | " + " | ".join(vals) + " |")

    overall_vals = [_fmt(task_stats["agents"].get(a, {}).get("overall")) for a in arms]
    lines.append("| **overall** | \u2014 | " + " | ".join(overall_vals) + " |")
    lines.append("")

    return "\n".join(lines)


def _render_generic_table(
    task_id: str,
    task_stats: dict[str, Any],
    agents: list[str],
) -> str:
    """Fallback: generic table for unknown task IDs."""
    lines: list[str] = []
    lines.append(f"\n## Task: `{task_id}`\n")

    eval_meta: dict[str, float] = task_stats.get("eval_meta", {})

    header_parts = ["Evaluation", "Weight"] + [
        f"{a} (n={task_stats['agents'].get(a, {}).get('n', 0)})" for a in agents
    ]
    lines.append("| " + " | ".join(header_parts) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_parts)) + " |")

    for name in sorted(eval_meta, key=lambda n: (-eval_meta[n], n)):
        weight = eval_meta[name]
        vals = [
            _fmt(task_stats["agents"].get(a, {}).get("evaluations", {}).get(name))
            for a in agents
        ]
        lines.append(f"| `{name}` | {weight:.2f} | " + " | ".join(vals) + " |")

    overall_vals = [
        _fmt(task_stats["agents"].get(a, {}).get("overall")) for a in agents
    ]
    lines.append("| **overall** | \u2014 | " + " | ".join(overall_vals) + " |")
    lines.append("")

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

# Canonical agent display order (timid → aggressive → machete).
_AGENTS = ["plain-timid", "plain-aggressive", "machete"]
# Arms that ran refuse-red (plain-aggressive is not in the SELECTION for that task).
_REFUSE_RED_ARMS = ["plain-timid", "machete"]


def analyze(output_dir: Path | str) -> tuple[str, str]:
    """Read a harness run output tree and return (comparison_md, comparison_json).

    Skips failed/cancelled/ungraded trials and notes them in both outputs.
    Never raises — defensive against missing or malformed files.

    reduce-hard: renders a 3-arm table with green-and-honest / recall / precision
      rows, overall, multiplicative composite per arm, and recovered gap
      (machete_composite − max(plain-timid_composite, plain-aggressive_composite)).

    refuse-red: renders a 2-arm table (plain-timid, machete) with
      refusal-on-red-baseline + overall.
    """
    output_dir = Path(output_dir).resolve()
    records = _load_trial_states(output_dir)
    scores, skipped = _aggregate(records)

    tasks = sorted(scores.keys())

    # ── JSON payload ──────────────────────────────────────────────────────────
    comparison: dict[str, Any] = {
        "tasks": {},
        "skipped_trials": [{"trial_id": t, "reason": r} for t, r in skipped],
    }

    # ── Markdown output ───────────────────────────────────────────────────────
    md_lines: list[str] = ["# Occam\u2019s Machete \u2014 3-Arm Evaluation Results\n"]

    if skipped:
        preview = ", ".join(f"`{t}`" for t, _ in skipped[:5])
        if len(skipped) > 5:
            preview += f" \u2026 (+{len(skipped) - 5} more)"
        md_lines.append(
            f"> **{len(skipped)} trial(s) skipped** (failed / cancelled / no grade):"
            f" {preview}\n"
        )

    if not tasks:
        md_lines.append("_No completed, graded trials found in this run._\n")
        return "\n".join(md_lines), json.dumps(comparison, indent=2)

    for task_id in tasks:
        if task_id == "reduce-hard":
            t_stats = _task_stats(scores[task_id], _AGENTS)

            # Per-arm composites.
            composites = {
                a: _compute_composite(t_stats["agents"].get(a, {})) for a in _AGENTS
            }

            # Recovered gap: machete vs best plain arm.
            _raw = [composites.get(a) for a in ["plain-timid", "plain-aggressive"]]
            plain_comps: list[float] = [v for v in _raw if v is not None]
            machete_comp = composites.get("machete")
            recovered_gap: float | None = None
            if machete_comp is not None and plain_comps:
                recovered_gap = machete_comp - max(plain_comps)

            comparison["tasks"][task_id] = {
                "agents": {
                    a: {
                        "n": t_stats["agents"].get(a, {}).get("n", 0),
                        "overall": t_stats["agents"].get(a, {}).get("overall"),
                        "evaluations": t_stats["agents"]
                        .get(a, {})
                        .get("evaluations", {}),
                        "composite": composites.get(a),
                    }
                    for a in _AGENTS
                },
                "evaluation_weights": t_stats.get("eval_meta", {}),
                "recovered_gap": recovered_gap,
            }
            md_lines.append(_render_reduce_hard_table(task_id, t_stats, _AGENTS))

        elif task_id == "refuse-red":
            t_stats = _task_stats(scores[task_id], _REFUSE_RED_ARMS)
            comparison["tasks"][task_id] = {
                "agents": {
                    a: {
                        "n": t_stats["agents"].get(a, {}).get("n", 0),
                        "overall": t_stats["agents"].get(a, {}).get("overall"),
                        "evaluations": t_stats["agents"]
                        .get(a, {})
                        .get("evaluations", {}),
                    }
                    for a in _REFUSE_RED_ARMS
                },
                "evaluation_weights": t_stats.get("eval_meta", {}),
            }
            md_lines.append(
                _render_refuse_red_table(task_id, t_stats, _REFUSE_RED_ARMS)
            )

        else:
            # Fallback for unknown task IDs: show all known agents.
            t_stats = _task_stats(scores[task_id], _AGENTS)
            comparison["tasks"][task_id] = {
                "agents": {
                    a: {
                        "n": t_stats["agents"].get(a, {}).get("n", 0),
                        "overall": t_stats["agents"].get(a, {}).get("overall"),
                        "evaluations": t_stats["agents"]
                        .get(a, {})
                        .get("evaluations", {}),
                    }
                    for a in _AGENTS
                },
                "evaluation_weights": t_stats.get("eval_meta", {}),
            }
            md_lines.append(_render_generic_table(task_id, t_stats, _AGENTS))

    return "\n".join(md_lines), json.dumps(comparison, indent=2)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <output_dir>", file=sys.stderr)
        raise SystemExit(1)
    out = Path(sys.argv[1])
    md_text, json_text = analyze(out)
    (out / "comparison.md").write_text(md_text, encoding="utf-8")
    (out / "comparison.json").write_text(json_text, encoding="utf-8")
    print(md_text)
