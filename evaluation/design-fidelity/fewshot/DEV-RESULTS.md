# Few-shot campaign -- DEV phase results

## Step 1 -- A/A stability gate

- aa_1 (K11_full, V3FS): F(p90 |diff|) = 0.3000, mean diff = 0.0000, gate BREACH (< 0.08 required)
- aa_2 (K11_compact, V3FS, re-A/A after aa_1 breach): F(p90 |diff|) = 0.6333, mean diff = -0.0278, gate BREACH
- **Decision: stop_no_sweep_possible**

## STOP -- no sweep possible

A/A stability breached on both the K=11 full-read and K=11 compact V3FS configs. Per the pre-registered stop rule ("F >= 0.08 -> drop the full-read family, re-A/A longest survivor (K=11 compact); if that breaches too -> STOP, report 'no sweep possible'"), the LOO sweep does NOT run. Step 2 (10-config x 2-family sweep) and Step 3 (dev gate) are both skipped -- there is nothing to report there. Campaign closes here at zero MJ cost (no lock-set authoring, no MJ reads collected).

### Per-scenario detail (why it breached)

**aa_1 (K11_full)** -- composite_mean A=0.694, B=0.694, F(p90)=0.3000

| scenario | group A (grit/dir/concern-match/composite) | group B | diff (B-A) |
|---|---|---|---|
| S01 | g=1,d=kill,cm=1,comp=0.667 | g=1,d=kill,cm=1,comp=0.667 | +0.000 |
| S02 | g=2,d=redesign,cm=1,comp=0.333 | g=1,d=redesign,cm=1,comp=0.667 | +0.333 |
| S03 | g=2,d=tweak,cm=0,comp=0.000 | g=2,d=tweak,cm=0,comp=0.000 | +0.000 |
| S04 | g=0,d=ship-as-is,cm=1,comp=1.000 | g=0,d=ship-as-is,cm=1,comp=1.000 | +0.000 |
| S05 | g=1,d=ship-as-is,cm=1,comp=1.000 | g=1,d=ship-as-is,cm=1,comp=1.000 | +0.000 |
| S06 | g=1,d=tweak,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=1.000 | +0.000 |
| S07 | g=2,d=redesign,cm=1,comp=1.000 | g=2,d=redesign,cm=1,comp=1.000 | +0.000 |
| S08 | g=1,d=kill,cm=1,comp=0.667 | g=1,d=kill,cm=1,comp=0.667 | +0.000 |
| S09 | g=2,d=redesign,cm=1,comp=1.000 | g=2,d=redesign,cm=1,comp=1.000 | +0.000 |
| S10 | g=1,d=tweak,cm=1,comp=0.333 | g=1,d=tweak,cm=0,comp=0.000 | -0.333 |
| S11 | g=1,d=tweak,cm=0,comp=0.333 | g=1,d=tweak,cm=0,comp=0.333 | +0.000 |
| S12 | g=1,d=tweak,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=1.000 | +0.000 |

**aa_2 (K11_compact)** -- composite_mean A=0.806, B=0.778, F(p90)=0.6333

| scenario | group A (grit/dir/concern-match/composite) | group B | diff (B-A) |
|---|---|---|---|
| S01 | g=1,d=kill,cm=1,comp=0.667 | g=1,d=kill,cm=1,comp=0.667 | +0.000 |
| S02 | g=1,d=redesign,cm=1,comp=0.667 | g=1,d=redesign,cm=1,comp=0.667 | +0.000 |
| S03 | g=1,d=redesign,cm=0,comp=0.333 | g=1,d=redesign,cm=0,comp=0.333 | +0.000 |
| S04 | g=0,d=ship-as-is,cm=1,comp=1.000 | g=0,d=ship-as-is,cm=1,comp=1.000 | +0.000 |
| S05 | g=1,d=ship-as-is,cm=1,comp=1.000 | g=1,d=ship-as-is,cm=1,comp=1.000 | +0.000 |
| S06 | g=1,d=tweak,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=1.000 | +0.000 |
| S07 | g=2,d=redesign,cm=1,comp=1.000 | g=2,d=redesign,cm=1,comp=1.000 | +0.000 |
| S08 | g=1,d=kill,cm=1,comp=0.667 | g=1,d=kill,cm=1,comp=0.667 | +0.000 |
| S09 | g=1,d=tweak,cm=1,comp=0.333 | g=2,d=redesign,cm=1,comp=1.000 | +0.667 |
| S10 | g=0,d=kill,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=0.333 | -0.667 |
| S11 | g=1,d=ship-as-is,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=0.667 | -0.333 |
| S12 | g=1,d=tweak,cm=1,comp=1.000 | g=1,d=tweak,cm=1,comp=1.000 | +0.000 |

Both K=11 A/A checks show individual scenarios swinging the composite by a full 1/3 or 2/3 between two identically-configured fresh sample groups (e.g. S02 in aa_1; S09/S10/S11 in aa_2), i.e. the direction majority itself flips 3-sample vote between runs. This confirms the charter's defect (2) concern: a K=11 few-shot prompt is a materially different sampling regime than the short prompts the original hill-climb A/A measured, and it is NOT stable enough at n=3 samples to support a LOO dev sweep.

