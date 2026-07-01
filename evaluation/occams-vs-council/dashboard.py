#!/usr/bin/env python3
"""Render a self-contained HTML dashboard from an occams-vs-council run.

Reads the run's aggregate.json (produced by aggregate.py) and writes dashboard.html
next to it. Lean on purpose: two summary tables (score-by-scenario, dimension
heatmap), a per-trial table with sanity flags, and a plain-language verdict.

Usage:  python3 dashboard.py <run_dir>   # defaults to newest run with aggregate.json
"""
from __future__ import annotations
import json, sys, os, glob, html
from pathlib import Path

DIM_LABEL = {
    "D1_restraint": "Restraint", "D2_premise_interrogation": "Premise?",
    "D3_first_principles_soundness": "Soundness", "D4_failure_and_cost_awareness": "Failure/Cost",
    "D5_goal_fidelity": "Goal fidelity", "D6_actionability": "Actionable",
    "D7_decision_clarity": "Decision", "D8_signal_to_noise": "Signal/Noise",
}
DIMS = list(DIM_LABEL)

def color(v):
    if v is None: return "#333"
    # red (0) -> amber (.75) -> green (1)
    v = max(0.0, min(1.0, float(v)))
    if v < 0.75: r, g = 200, int(120 * (v / 0.75))
    else: r, g = int(200 * (1 - (v - 0.75) / 0.25)), 170
    return f"rgb({r},{g},60)"

def newest():
    base = Path(os.path.expanduser("~/.amplifier/evaluation/occams-vs-council"))
    cands = sorted(glob.glob(str(base / "*" / "aggregate.json")))
    return Path(cands[-1]).parent if cands else base

def main():
    run = Path(sys.argv[1]) if len(sys.argv) > 1 else newest()
    agg = json.loads((run / "aggregate.json").read_text())
    variants, scenarios, rows = agg["variants"], agg["scenarios"], agg["rows"]
    pvs, pvd, pv = agg["per_variant_scenario"], agg["per_variant_dimension"], agg["per_variant_overall"]
    mism, unsc = agg["mismatches"], agg["unscored"]

    def esc(x): return html.escape(str(x))
    H = []
    H.append(f"""<!doctype html><meta charset=utf-8><title>occams-vs-council — {esc(run.name)}</title>
<style>
 body{{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:32px;max-width:1100px}}
 h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:16px;margin:28px 0 10px;color:#9ecbff}}
 .sub{{color:#8a90a0;margin-bottom:18px}}
 table{{border-collapse:collapse;width:100%;margin:6px 0 18px}}
 th,td{{padding:7px 10px;text-align:center;border:1px solid #262a33}} th{{background:#171a21;color:#c8ccd6}}
 td.l,th.l{{text-align:left}} .var{{font-weight:600;color:#fff}}
 .banner{{padding:10px 14px;border-radius:8px;margin:10px 0;font-weight:600}}
 .ok{{background:#123a1c;color:#9be8a6}} .bad{{background:#3a1212;color:#ff9c9c}}
 .cell{{color:#0c0e12;font-weight:600}} small{{color:#8a90a0;font-weight:400}}
 .note{{color:#c8ccd6;background:#171a21;border-left:3px solid #9ecbff;padding:10px 14px;border-radius:4px}}
</style>
<h1>occams-vs-council — design-discipline evaluation</h1>
<div class=sub>run <code>{esc(run.name)}</code> · {len(rows)} trials · 3 setups × 3 scenarios × up to 3 trials</div>""")

    # sanity banner
    if mism or unsc:
        H.append(f"<div class='banner bad'>⚠ Sanity: {len(mism)} prompt/scenario mismatch(es), {len(unsc)} unscored — excluded from means. See per-trial table.</div>")
    else:
        H.append("<div class='banner ok'>✓ Sanity: every trial answered its assigned scenario; all trials scored.</div>")

    # overall by scenario
    H.append("<h2>Overall score by scenario <small>(mean, n trials; excludes flagged)</small></h2><table>")
    H.append("<tr><th class=l>setup</th>" + "".join(f"<th>{esc(s)}</th>" for s in scenarios) + "<th>overall</th></tr>")
    for v in variants:
        tds = []
        for s in scenarios:
            cell = pvs.get(f"{v}|{s}")
            if cell and cell[0] is not None:
                tds.append(f"<td style='background:{color(cell[0])}' class=cell>{cell[0]:.2f}<br><small>n={cell[1]}</small></td>")
            else: tds.append("<td>—</td>")
        ov = pv.get(v)
        tds.append(f"<td style='background:{color(ov)}' class=cell>{ov:.2f}</td>" if ov is not None else "<td>—</td>")
        H.append(f"<tr><td class='l var'>{esc(v)}</td>{''.join(tds)}</tr>")
    H.append("</table>")

    # dimension heatmap
    H.append("<h2>By quality dimension <small>(mean 0–1 across scenarios+trials)</small></h2><table>")
    H.append("<tr><th class=l>setup</th>" + "".join(f"<th>{esc(DIM_LABEL[d])}</th>" for d in DIMS) + "</tr>")
    for v in variants:
        tds = []
        for d in DIMS:
            val = pvd.get(f"{v}|{d}")
            tds.append(f"<td style='background:{color(val)}' class=cell>{val:.2f}</td>" if val is not None else "<td>—</td>")
        H.append(f"<tr><td class='l var'>{esc(v)}</td>{''.join(tds)}</tr>")
    H.append("</table>")

    # per-trial
    H.append("<h2>Per-trial detail</h2><table>")
    H.append("<tr><th class=l>trial</th><th>setup</th><th>scenario</th><th>score</th><th>subject</th><th>panel?</th><th>state</th><th>flag</th></tr>")
    for r in sorted(rows, key=lambda x: (x['variant'] or '', x['scenario'] or '', x['trial'])):
        flag = "⚠ mismatch" if r["mismatch"] else ("⚠ unscored" if r["overall"] is None else "")
        sc = f"{r['overall']:.2f}" if r["overall"] is not None else "—"
        bg = color(r["overall"]) if (r["overall"] is not None and not r["mismatch"]) else "#333"
        panel = "✓" if r.get("council_review") else ""
        H.append(f"<tr><td class=l><small>{esc(r['trial'])}</small></td><td>{esc(r['variant'])}</td><td>{esc(r['scenario'])}</td>"
                 f"<td style='background:{bg}' class=cell>{sc}</td><td>{esc(r.get('subject'))}</td><td>{panel}</td>"
                 f"<td><small>{esc(r['state'])}</small></td><td style='color:#ff9c9c'>{flag}</td></tr>")
    H.append("</table>")

    # auto verdict (plain language)
    ov_sorted = sorted([(v, pv[v]) for v in variants if pv.get(v) is not None], key=lambda x: -x[1])
    H.append("<h2>Read of the results</h2><div class=note>")
    if ov_sorted:
        best = ov_sorted[0]
        H.append(f"Highest overall: <b>{esc(best[0])}</b> ({best[1]:.2f}). ")
        # council vs machete
        c, m = pv.get("council"), pv.get("occams-machete")
        if c is not None and m is not None:
            if m > c: H.append(f"Plain <b>occams-machete</b> ({m:.2f}) edged out the full <b>council</b> ({c:.2f}) overall. ")
            elif c > m: H.append(f"The full <b>council</b> ({c:.2f}) beat plain <b>occams-machete</b> ({m:.2f}) overall. ")
            else: H.append(f"council and occams-machete tied ({c:.2f}). ")
        d8 = {v: pvd.get(f"{v}|D8_signal_to_noise") for v in variants}
        if d8.get("council") is not None:
            H.append(f"Signal/Noise (conciseness) — council {d8['council']:.2f}, occams-machete {d8.get('occams-machete')}, regular {d8.get('regular')}.")
    H.append("</div>")
    H.append(f"<p class=sub>Generated from aggregate.json. Raw trials, transcripts, and per-dimension reasoning live under the run directory.</p>")

    out = run / "dashboard.html"
    out.write_text("\n".join(H), encoding="utf-8")
    print(f"[wrote {out}]")

if __name__ == "__main__":
    main()
