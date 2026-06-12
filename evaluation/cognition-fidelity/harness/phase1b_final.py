#!/usr/bin/env python3
"""Phase 1B FINAL scoring — MJ (human) is now the reference standard.
Computes: MJ self-consistency (hidden dups), MJ-vs-construct, and the fidelity gate
(lens-vs-MJ agreement, Clopper-Pearson lower bound > 0.70), vs baseline/style."""
import json, os, sys, hashlib
from pathlib import Path
from collections import defaultdict, Counter
from scipy.stats import beta

RUN = Path("runs/20260612_103958")
PROBES = {p["probe_id"]: p for p in json.load(open("../probes/probes_phase1b.json"))}

# MJ's blind calls (from MJ-FORM.md), normalized
MJ = {
 "Q01":"defect","Q02":"not_defect","Q03":"not_defect","Q04":"defect","Q05":"defect",
 "Q06":"not_defect","Q07":"question","Q08":"not_defect","Q09":"not_defect","Q10":"defect",
 "Q11":"defect","Q12":"not_defect","Q13":"defect","Q14":"not_defect","Q15":"not_defect",
 "Q16":"question","Q17":"not_defect","Q18":"defect","Q19":"question","Q20":"defect",
 "Q21":"not_defect","Q22":"not_defect","Q23":"not_defect","Q24":"defect","Q25":"defect",
 "Q26":"not_defect","Q27":"question","Q28":"not_defect","Q29":"not_defect","Q30":"defect",
 "Q31":"defect","Q32":"defect","Q33":"not_defect","Q34":"not_defect"}
DUPS = {"Q13":"Q01","Q22":"Q06","Q27":"Q07","Q33":"Q17"}  # dup -> original

# rebuild arm per-item majority calls from the run cache
cache = {f[:-5]: json.load(open(RUN/"p1b_cache"/f))["call"] for f in os.listdir(RUN/"p1b_cache")}
def c3(t): return cache.get(hashlib.sha256(("p1b|"+t).encode()).hexdigest(), "unclear")
votes = defaultdict(list)
for l in open(RUN/"raw.jsonl"):
    if not l.strip(): continue
    r = json.loads(l)
    if r.get("neutralized"): votes[(r["probe_id"], r["arm"])].append(c3(r["neutralized"]))
arm_call = {}
for k, v in votes.items():
    c = Counter(x for x in v if x != "unclear"); arm_call[k] = c.most_common(1)[0][0] if c else "unclear"

def cp_low(k, n):  # Clopper-Pearson 95% two-sided lower bound
    return 0.0 if k == 0 else beta.ppf(0.025, k, n-k+1)

gold = [p for p in PROBES if PROBES[p]["kind"] == "gold"]
calib = [p for p in PROBES if PROBES[p]["kind"] == "calibration"]

print("=== (1) MJ self-consistency on hidden duplicates ===")
sc = sum(MJ[d] == MJ[o] for d, o in DUPS.items())
for d, o in DUPS.items():
    print(f"   {d}({MJ[d]}) vs {o}({MJ[o]}): {'consistent' if MJ[d]==MJ[o] else 'DIFFERS'}")
print(f"   self-consistency = {sc}/4 = {sc/4*100:.0f}%  (ceiling on achievable fidelity)")

print("\n=== (2) MJ vs construct expected_call (validates my synthetic labels) ===")
for label, ids in [("gold", gold), ("calibration", calib)]:
    a = sum(MJ[p] == PROBES[p]["expected_call"] for p in ids)
    print(f"   {label}: {a}/{len(ids)} = {a/len(ids)*100:.0f}%")

print("\n=== (3) FIDELITY GATE — agreement with MJ on the 20 gold items ===")
print(f"   {'arm':9s} {'agree/MJ':>9s} {'rate':>6s} {'CP-95% lower':>13s}")
fid = {}
for arm in ["lens", "baseline", "style_only"]:
    a = sum(arm_call.get((p, arm)) == MJ[p] for p in gold)
    low = cp_low(a, len(gold)); fid[arm] = (a, low)
    print(f"   {arm:9s} {a:>5d}/{len(gold)} {a/len(gold)*100:5.0f}% {low*100:11.1f}%")
la, llow = fid["lens"]
print(f"\n   GATE (lens CP lower > 0.70?): lower={llow*100:.1f}%  ->  {'PASS' if llow>0.70 else 'FAIL'}")

print("\n=== (4) per-item (gold): MJ | lens | baseline | construct ===")
print(f"   {'Q':4s} {'domain':12s} {'MJ':11s} {'lens':11s} {'base':11s} {'construct':11s} {'lens=MJ?'}")
for p in sorted(gold):
    pr = PROBES[p]
    print(f"   {p:4s} {pr['domain'][:12]:12s} {MJ[p]:11s} {arm_call.get((p,'lens')):11s} "
          f"{arm_call.get((p,'baseline')):11s} {pr['expected_call']:11s} {'✓' if arm_call.get((p,'lens'))==MJ[p] else '✗'}")

print("\n=== (5) residual clears — lens said not_defect but MJ did NOT ===")
rc = [p for p in gold if arm_call.get((p,"lens"))=="not_defect" and MJ[p]!="not_defect"]
if rc:
    for p in rc: print(f"   {p}: lens=not_defect  MJ={MJ[p]}  ({PROBES[p]['flagged_item'][:60]})")
else:
    print("   NONE — the lens never cleared something MJ flagged or questioned.")

out = {"mj_self_consistency": sc/4,
       "mj_vs_construct_gold": sum(MJ[p]==PROBES[p]["expected_call"] for p in gold)/len(gold),
       "fidelity": {a: {"agree": fid[a][0], "n": len(gold), "cp_lower": fid[a][1]} for a in fid},
       "gate_pass": bool(llow>0.70), "residual_clears": rc}
json.dump(out, open(RUN/"phase1b_final.json","w"), indent=2)
print("\nwrote", RUN/"phase1b_final.json")
