# Driving the "occams-machete" variant

Identical driving to the baseline — a single non-interactive turn that writes the
design to `/workspace/design.md`. The difference is purely the composed bundle:
occams-machete's hooks proactively surface /machete and the mj-lens, and the agent has
the reducer/reviewer available. We do NOT instruct it to use them — we measure whether
having them available changes the design on the same task.

## CRITICAL: run the seeded task verbatim — do NOT invent or retype it

The exact task text is already saved inside the DTU at `/workspace/instructions.txt`.
You MUST run that file's contents verbatim (always `cat` it). Do NOT retype,
summarize, paraphrase, or substitute any task from memory.

## IMPORTANT: the turn can take many minutes — launch in background and poll

## Step 1 — launch in the background (runs the seeded task file)

```
cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "$(cat /workspace/instructions.txt)" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

## Step 2 — poll until the sentinel appears (sleep ~30s; patient up to ~25 min)

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

## Step 3 — confirm the deliverable and conclude

```
cat /workspace/eval-run.out; echo '--- design.md ---'; cat /workspace/design.md 2>/dev/null
```

- `success` — `EXIT:0` and `/workspace/design.md` exists and is non-empty.
- `failure` — non-zero exit, or no design.md.

In your summary, note the SUBJECT of the design.md so any task mismatch is caught. Do
NOT judge design quality yourself — the grader does that.
