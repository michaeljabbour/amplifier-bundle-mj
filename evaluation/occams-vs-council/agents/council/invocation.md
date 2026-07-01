# Driving the "council" variant

Same single-turn shape as the other variants, but this variant's headline capability
is the review **panel**, so we drive the agent to use it: produce the design, convene
the council on it, and revise. This also validates that the 7-lens panel composes and
convenes inside a fresh DTU.

## CRITICAL: run the seeded task verbatim — do NOT invent or retype it

The exact task text is already saved inside the DTU at `/workspace/instructions.txt`.
Build the run prompt by concatenating that file with the council instruction below —
always `cat` the seeded file; never retype or substitute a task from memory.

## Step 1 — build the augmented prompt from the seeded task, then launch in background

```
{ cat /workspace/instructions.txt; cat <<'PROMPT'

Before finalizing: convene the full review council on your design. Run the council on
/workspace/design.md (use the council-here skill, or load_skill council-here), let
every lens weigh in, save the synthesized panel verdict to /workspace/council-review.md,
then revise /workspace/design.md to address the panel's findings.
PROMPT
} > /workspace/eval-prompt.txt

cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "$(cat /workspace/eval-prompt.txt)" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

## Step 2 — poll until the sentinel appears

Sleep ~30s between checks. Be EXTRA patient — the council fans out ~7 isolated
sub-sessions, so this variant can take notably longer (up to ~40 minutes):

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

## Step 3 — confirm the deliverables and conclude

```
cat /workspace/eval-run.out; echo '--- design.md ---'; cat /workspace/design.md 2>/dev/null; echo '--- council-review.md ---'; cat /workspace/council-review.md 2>/dev/null
```

- `success` — `EXIT:0` and `/workspace/design.md` exists and is non-empty.
- In your summary, note the SUBJECT of design.md (to catch any task mismatch), whether
  `/workspace/council-review.md` was produced (confirms the panel convened), and how
  many lenses appeared in it.
- `failure` — non-zero exit, or no design.md.

Do NOT judge design quality yourself — the grader does that.
