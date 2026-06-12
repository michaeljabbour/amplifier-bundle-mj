#!/usr/bin/env python3
"""Phase-1B scorer: 3-way grade the FRESH held-out probes vs the construct's
expected_call. Tests GENERALIZATION of the Phase-2 symmetric-guard fix on probes
it was never tuned against. NOT the human-MJ fidelity gate (that requires the human;
the lens judging itself would be circular). The lens arm here = "MJ as the activated
bundle" — a generalization/consistency signal, not independent ground truth."""
import json, os, sys, hashlib, concurrent.futures as cf
from pathlib import Path
from collections import defaultdict, Counter
from openai import OpenAI

RUN = Path(sys.argv[1])
PROBES = json.load(open(Path(__file__).parent.parent / "probes" / "probes_phase1b.json"))
META = {p["probe_id"]: p for p in PROBES}
client = OpenAI()
CACHE = RUN / "p1b_cache"; CACHE.mkdir(exist_ok=True)

RUBRIC = (
    "You are classifying the CONCLUSION of a software/design review of a flagged item. "
    "Classify the reviewer's bottom-line into exactly one of:\n"
    '- "defect": concludes it IS a genuine mistake that should be fixed.\n'
    '- "question": declines to rule it a defect without more evidence/intent — raises it, '
    'says investigate, "not a verdict".\n'
    '- "not_defect": concludes it is acceptable / fine / a deliberate or merit-defensible trade-off.\n'
    'Output ONLY strict JSON: {"call":"defect|question|not_defect","evidence":"<=12 words"}.'
)

def judge(text):
    k = hashlib.sha256(("p1b|" + text).encode()).hexdigest()
    f = CACHE / f"{k}.json"
    if f.exists():
        return json.loads(f.read_text())["call"]
    r = client.chat.completions.create(model="gpt-4.1", temperature=0, max_tokens=60,
        messages=[{"role": "system", "content": RUBRIC},
                  {"role": "user", "content": "REVIEW CONCLUSION:\n" + text[-1500:]}])
    o = r.choices[0].message.content.strip()
    try:
        d = json.loads(o[o.index("{"):o.rindex("}") + 1]); call = d.get("call", "unclear")
    except Exception:
        call = "unclear"
    if call not in ("defect", "question", "not_defect"):
        call = "unclear"
    f.write_text(json.dumps({"call": call}))
    return call

rows = [json.loads(l) for l in open(RUN / "raw.jsonl") if l.strip()]
rows = [r for r in rows if r.get("neutralized")]
print(f"re-judging {len(rows)} samples 3-way ...")
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(judge, r["neutralized"]): i for i, r in enumerate(rows)}
    for n, fu in enumerate(cf.as_completed(futs), 1):
        rows[futs[fu]]["c3"] = fu.result()
        if n % 60 == 0: print(f"  {n}/{len(rows)}")

votes = defaultdict(list)
for r in rows:
    votes[(r["probe_id"], r["arm"])].append(r["c3"])
call = {}
for k, v in votes.items():
    c = Counter(x for x in v if x != "unclear")
    call[k] = c.most_common(1)[0][0] if c else "unclear"

arms = ["baseline", "lens", "style_only"]
gold = [p["probe_id"] for p in PROBES if p["kind"] == "gold"]
calib = [p["probe_id"] for p in PROBES if p["kind"] == "calibration"]
g_present = [p for p in gold if META[p]["polarity"] == "reason_present"]
g_absent = [p for p in gold if META[p]["polarity"] == "reason_absent"]

def acc(arm, ids):
    return sum(call[(p, arm)] == META[p]["expected_call"] for p in ids), len(ids)

out = {"gold": {}, "calibration": {}, "reason_present": {}, "reason_absent": {}}
print("\n=== GOLD (20 fresh) — 3-way accuracy vs construct expected_call ===")
print(f"{'arm':11s} {'overall':>9s} {'present(n=%d)'%len(g_present):>14s} {'absent(n=%d)'%len(g_absent):>13s}")
for a in arms:
    go, gn = acc(a, gold); po, pn = acc(a, g_present); ao, an = acc(a, g_absent)
    out["gold"][a] = {"correct": go, "n": gn, "acc": go / gn}
    print(f"{a:11s} {go}/{gn}={go/gn*100:4.0f}%   {po}/{pn}={po/pn*100:4.0f}%      {ao}/{an}={ao/an*100:4.0f}%")

print("\n=== reason-ABSENT (fresh) — does the fix GENERALIZE? falsely_cleared should be LOW ===")
print(f"{'arm':11s} {'defect':>7s} {'question':>9s} {'falsely_cleared':>16s}")
for a in arms:
    d = Counter(call[(p, a)] for p in g_absent)
    fc = d.get("not_defect", 0)
    out["reason_absent"][a] = {"defect": d.get("defect", 0), "question": d.get("question", 0),
                              "falsely_cleared": fc, "n": len(g_absent), "fc_rate": fc / len(g_absent)}
    print(f"{a:11s} {d.get('defect',0):6d}  {d.get('question',0):8d}  {fc:13d} ({fc/len(g_absent)*100:.0f}%)")

print("\n=== reason-PRESENT (fresh) — avoid-defect should stay high ===")
for a in arms:
    d = Counter(call[(p, a)] for p in g_present)
    avoid = (d.get("question", 0) + d.get("not_defect", 0)) / len(g_present)
    out["reason_present"][a] = {"avoid_defect": avoid, "defect": d.get("defect", 0),
                               "not_defect": d.get("not_defect", 0), "question": d.get("question", 0)}
    print(f"{a:11s} avoid-defect {avoid*100:4.0f}%  (defect {d.get('defect',0)}, q {d.get('question',0)}, clear {d.get('not_defect',0)})")

print("\n=== CALIBRATION (10 clear-cut) — judge/pipeline sanity ===")
for a in arms:
    co, cn = acc(a, calib); out["calibration"][a] = {"correct": co, "n": cn, "acc": co / cn}
    print(f"{a:11s} {co}/{cn} = {co/cn*100:.0f}%")

json.dump(out, open(RUN / "phase1b_results.json", "w"), indent=2)
print("\nwrote", RUN / "phase1b_results.json")
