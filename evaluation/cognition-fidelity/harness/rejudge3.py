#!/usr/bin/env python3
"""Re-judge cached arm outputs with a 3-WAY rubric (defect / question / not_defect).

Phase-1a used a binary {defect, not_defect} judge. That conflates the
anti-conflation guard's prescribed move -- "downgrade to a QUESTION, not a
verdict" -- with "it's fine (not_defect)". This re-judge separates them, using
the SAME cached, voice-neutralized arm outputs (no arm re-runs)."""
import json, os, sys, hashlib, concurrent.futures as cf
from pathlib import Path
from collections import defaultdict, Counter
from openai import OpenAI

RUN = Path(sys.argv[1])
PROBES = json.load(open(Path(__file__).parent.parent / "probes" / "anti_conflation.json"))
POL = {p["probe_id"]: p for p in PROBES}
client = OpenAI()
CACHE = RUN / "rejudge3_cache"; CACHE.mkdir(exist_ok=True)

RUBRIC = (
    "You are classifying the CONCLUSION of a software/design review. The reviewer was asked "
    "whether a specific flagged item is a genuine defect. Classify the reviewer's bottom-line into "
    "exactly one of:\n"
    '- "defect": concludes it IS a genuine mistake that should be fixed.\n'
    '- "question": declines to rule it a defect WITHOUT more evidence/intent — raises it as a '
    'question, says investigate first, "not a verdict", or "needs clarification".\n'
    '- "not_defect": concludes it is acceptable / fine / a deliberate trade-off; no change needed.\n'
    "Output ONLY strict JSON: {\"call\":\"defect|question|not_defect\",\"evidence\":\"<=12 words\"}."
)

def judge(text):
    key = hashlib.sha256(("rj3|"+text).encode()).hexdigest()
    cf_ = CACHE / f"{key}.json"
    if cf_.exists():
        return json.loads(cf_.read_text())
    r = client.chat.completions.create(
        model="gpt-4.1", temperature=0, max_tokens=60,
        messages=[{"role": "system", "content": RUBRIC},
                  {"role": "user", "content": "REVIEW CONCLUSION:\n" + text[-1500:]}],
    )
    out = r.choices[0].message.content.strip()
    try:
        s = out[out.index("{"):out.rindex("}")+1]; d = json.loads(s)
        call = d.get("call", "unclear")
    except Exception:
        call = "unclear"
    if call not in ("defect", "question", "not_defect"):
        call = "unclear"
    res = {"call": call}
    cf_.write_text(json.dumps(res))
    return res

rows = [json.loads(l) for l in open(RUN / "raw.jsonl")]
rows = [r for r in rows if r.get("neutralized")]
print(f"re-judging {len(rows)} cached samples 3-way ...")
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(judge, r["neutralized"]): i for i, r in enumerate(rows)}
    for n, f in enumerate(cf.as_completed(futs), 1):
        rows[futs[f]]["rj3"] = f.result()["call"]
        if n % 40 == 0: print(f"  {n}/{len(rows)}")

# majority vote per (probe, arm)
votes = defaultdict(list)
for r in rows:
    votes[(r["probe_id"], r["arm"])].append(r["rj3"])
call = {}
for k, v in votes.items():
    c = Counter(x for x in v if x != "unclear")
    call[k] = c.most_common(1)[0][0] if c else "unclear"

arms = ["baseline", "lens", "style_only"]
def ids(pol): return [p["probe_id"] for p in PROBES if p["polarity"] == pol]
present, absent = ids("reason_present"), ids("reason_absent")

def dist(arm, idlist):
    c = Counter(call[(pid, arm)] for pid in idlist)
    return {k: c.get(k, 0) for k in ("defect", "question", "not_defect", "unclear")}

print("\n=== REASON-PRESENT (documented reason -> faithful = NOT 'defect') ===")
print(f"{'arm':11s} {'avoid_defect':>12s} | defect question not_defect unclear")
out = {"present": {}, "absent": {}}
for a in arms:
    d = dist(a, present); avoid = (d["question"] + d["not_defect"]) / len(present)
    out["present"][a] = {"avoid_defect": avoid, **d}
    print(f"{a:11s} {avoid*100:11.1f}% | {d['defect']:6d} {d['question']:8d} {d['not_defect']:10d} {d['unclear']:7d}")

print("\n=== REASON-ABSENT (no reason -> falsely_cleared='not_defect' is the real error) ===")
print(f"{'arm':11s} {'defect':>7s} {'question':>9s} {'falsely_cleared':>16s} {'unclear':>8s}")
for a in arms:
    d = dist(a, absent)
    out["absent"][a] = {"falsely_cleared": d["not_defect"]/len(absent), **d}
    print(f"{a:11s} {d['defect']:6d}  {d['question']:8d}  {d['not_defect']:15d}  {d['unclear']:7d}")

# McNemar lens vs baseline on reason-present avoid-defect
def correct_present(arm, pid): return call[(pid, arm)] in ("question", "not_defect")
b = sum(correct_present("lens", p) and not correct_present("baseline", p) for p in present)
c = sum((not correct_present("lens", p)) and correct_present("baseline", p) for p in present)
from math import comb
n = b + c; p_two = min(1.0, 2*sum(comb(n, k) for k in range(0, min(b, c)+1))/(2**n)) if n else 1.0
print(f"\n=== McNemar (reason-present, avoid-defect): b(lens>base)={b} c(base>lens)={c} exact p={p_two:.4f} ===")
out["mcnemar_present_avoid_defect"] = {"b": b, "c": c, "p": p_two}
json.dump(out, open(RUN / "rejudge3.json", "w"), indent=2)
print("\nwrote", RUN / "rejudge3.json")
