# Driving the "regular" variant

This agent is the Amplifier CLI with amplifier-foundation composed. The eval is a
SINGLE, non-interactive turn: run the task and let it work to completion. The
deliverable is a design written to `/workspace/design.md`.

## CRITICAL: run the seeded task verbatim — do NOT invent or retype it

The exact task text is already saved inside the DTU at `/workspace/instructions.txt`
(the harness put it there). You MUST run that file's contents verbatim. Do NOT retype,
summarize, paraphrase, or substitute any task from memory — always `cat` the file.

## IMPORTANT: the turn can take many minutes — launch in background and poll

## Step 1 — launch in the background (runs the seeded task file)

```
cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "$(cat /workspace/instructions.txt)" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

## Step 2 — poll until the sentinel appears

Repeat, sleeping ~30s between checks, for as long as it takes (be patient — up to
~25 minutes):

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

Do NOT conclude while it still prints `RUNNING`. A sub-session is expected, not an error.

## Step 3 — confirm the deliverable and conclude

```
cat /workspace/eval-run.out; echo '--- design.md ---'; cat /workspace/design.md 2>/dev/null
```

- verdict `success` — the sentinel shows `EXIT:0` and `/workspace/design.md` exists and is non-empty.
- verdict `failure` — non-zero exit, or no design.md produced.

In your summary, note the SUBJECT of the design.md (e.g. "data-import tool", "wiki
engagement", "expense tracker") so any task/prompt mismatch is caught. Do NOT judge
design quality yourself — the grader does that.
