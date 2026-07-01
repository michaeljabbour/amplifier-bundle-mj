#!/usr/bin/env python3
"""Aggregate an occams-vs-council run into a variant x scenario x dimension view.

The stock harness writes a flat per-trial list; this pivots it. It also runs a
SANITY CHECK: for every trial it compares the design.md's apparent subject to the
scenario it was supposed to answer, and flags mismatches (the class of bug that
produced false 0.0s in the first pass).

Usage:  python3 aggregate.py <run_dir>            # defaults to newest run
Outputs (next to the run):  aggregate.json, aggregate.md   (+ prints a summary)
"""
from __future__ import annotations
import json, sys, glob, os, statistics, re
from pathlib import Path

DIMS = ["D1_restraint","D2_premise_interrogation","D3_first_principles_soundness",
        "D4_failure_and_cost_awareness","D5_goal_fidelity","D6_actionability",
        "D7_decision_clarity","D8_signal_to_noise"]

# expected subject keywords per scenario, for the mismatch sanity check
EXPECT = {
    "s1-yagni":    {"good": ["plugin","import","integration","csv"], "label": "data-import/plugin"},
    "s2-shouldwe": {"good": ["wiki","recommend","engagement","knowledge"], "label": "wiki-recommender"},
    "s3-reduce":   {"good": ["expense","reimburse"], "label": "expense-tracker"},
}

def newest_run() -> Path:
    base = Path(os.path.expanduser("~/.amplifier/evaluation/occams-vs-council"))
    runs = sorted([p for p in base.glob("*/") if (p/"trials").is_dir() or (p/"summary.json").exists()])
    return runs[-1] if runs else base

def find(trial: Path, name: str):
    hits = glob.glob(str(trial/"**"/name), recursive=True)
    return Path(hits[0]) if hits else None

def crit_scores(gr: dict) -> dict:
    """Per-criterion (points_awarded, max) from grader_result.json evaluations[].rubric_scores.
    All rubric dimensions in this eval are max 5 points."""
    out = {}
    for ev in gr.get("evaluations", []):
        for k, v in (ev.get("rubric_scores") or {}).items():
            if isinstance(v, dict) and "points_awarded" in v:
                try:
                    out[k] = (float(v["points_awarded"]), 5.0)
                except Exception:
                    pass
    return out

def design_subject(trial: Path):
    d = find(trial, "design.md")
    if not d: return None, {}
    txt = d.read_text(errors="ignore").lower()
    counts = {"plugin/import": len(re.findall(r"plugin|import|integration", txt)),
              "wiki/recommend": len(re.findall(r"wiki|recommend|engagement", txt)),
              "expense": len(re.findall(r"expense", txt))}
    return max(counts, key=counts.get), counts

def main():
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_run()
    trials = sorted((run/"trials").glob("*/"))
    rows = []
    for t in trials:
        st = json.loads((t/"state.json").read_text()) if (t/"state.json").exists() else {}
        agent, task = st.get("agent_id"), st.get("task_id")
        gr_path = find(t, "grader_result.json")
        gr = json.loads(gr_path.read_text()) if gr_path else {}
        overall = gr.get("overall_score")
        cs = crit_scores(gr)
        subj, counts = design_subject(t)
        exp = EXPECT.get(task, {})
        # mismatch = the design.md's dominant subject isn't the expected one for this scenario
        expect_bucket = {"s1-yagni": "plugin/import", "s2-shouldwe": "wiki/recommend", "s3-reduce": "expense"}.get(task)
        mismatch = expect_bucket is not None and subj is not None and subj != expect_bucket
        rows.append({"trial": t.name, "variant": agent, "scenario": task, "state": st.get("state"),
                     "overall": overall, "dims": {k:(cs.get(k) or (None,None)) for k in DIMS},
                     "subject": subj, "expected": exp.get("label"), "mismatch": mismatch,
                     "council_review": bool(find(t,"council-review.md"))})

    # aggregates (only trustworthy trials: completed, scored, not mismatched)
    def ok(r): return r["state"]=="completed" and r["overall"] is not None and not r["mismatch"]
    variants = sorted({r["variant"] for r in rows if r["variant"]})
    scenarios = sorted({r["scenario"] for r in rows if r["scenario"]})

    per_vs = {}   # (variant,scenario) -> mean overall
    for v in variants:
        for s in scenarios:
            vals = [r["overall"] for r in rows if r["variant"]==v and r["scenario"]==s and ok(r)]
            per_vs[(v,s)] = (round(statistics.mean(vals),3) if vals else None, len(vals))
    per_vd = {}   # (variant,dim) -> mean normalized (0-1)
    for v in variants:
        for d in DIMS:
            vals=[]
            for r in rows:
                if r["variant"]==v and ok(r):
                    pa,mx = r["dims"][d]
                    if pa is not None and mx: vals.append(pa/mx)
            per_vd[(v,d)] = round(statistics.mean(vals),3) if vals else None
    per_v = {v: (round(statistics.mean([r["overall"] for r in rows if r["variant"]==v and ok(r)]),3)
                 if [r for r in rows if r["variant"]==v and ok(r)] else None) for v in variants}

    result = {"run": str(run), "n_trials": len(rows), "variants": variants, "scenarios": scenarios,
              "rows": rows, "per_variant_scenario": {f"{k[0]}|{k[1]}":v for k,v in per_vs.items()},
              "per_variant_dimension": {f"{k[0]}|{k[1]}":v for k,v in per_vd.items()},
              "per_variant_overall": per_v,
              "mismatches": [r["trial"] for r in rows if r["mismatch"]],
              "unscored": [r["trial"] for r in rows if r["overall"] is None]}
    (run/"aggregate.json").write_text(json.dumps(result, indent=2))

    # markdown + console
    L=[]
    L.append(f"# occams-vs-council — aggregate\n\nrun: `{run.name}`  ·  trials: {len(rows)}\n")
    L.append("## Overall by scenario (mean score, n trials)\n")
    L.append("| variant | " + " | ".join(scenarios) + " | overall |")
    L.append("|---|" + "---|"*(len(scenarios)+1))
    for v in variants:
        cells=[]
        for s in scenarios:
            m,n = per_vs[(v,s)]; cells.append(f"{m} (n={n})" if m is not None else "—")
        L.append(f"| {v} | " + " | ".join(cells) + f" | {per_v[v]} |")
    L.append("\n## By dimension (mean 0–1, across scenarios+trials)\n")
    L.append("| variant | " + " | ".join(d.replace('_',' ')[:14] for d in DIMS) + " |")
    L.append("|---|" + "---|"*len(DIMS))
    for v in variants:
        L.append(f"| {v} | " + " | ".join(str(per_vd[(v,d)]) for d in DIMS) + " |")
    if result["mismatches"]:
        L.append("\n## ⚠️ SANITY: prompt/scenario mismatches (excluded)\n")
        for tr in result["mismatches"]: L.append(f"- {tr}")
    if result["unscored"]:
        L.append("\n## ⚠️ unscored / errored trials\n")
        for tr in result["unscored"]: L.append(f"- {tr}")
    md="\n".join(L)+"\n"
    (run/"aggregate.md").write_text(md)
    print(md)
    print(f"[wrote {run/'aggregate.json'} and {run/'aggregate.md'}]")

if __name__ == "__main__":
    main()
