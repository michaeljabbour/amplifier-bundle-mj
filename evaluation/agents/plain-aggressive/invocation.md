# Driving the Amplifier agent

This agent is the Amplifier CLI. The eval is a SINGLE, non-interactive
reduction turn: the agent is asked to clean up /workspace/flowforge.

## IMPORTANT: the turn can take many minutes

A real reduction turn takes several minutes. Do NOT run `amplifier run` as a
single blocking command -- it will hit a command timeout and you will wrongly
conclude failure. Instead launch it in the BACKGROUND with a completion
sentinel and POLL until it finishes.

## Step 1 -- launch in the background

**Prepend the following STANCE to the user's message** before running
(i.e. run `amplifier run "<STANCE> <the user's message>"`):

> Be aggressive: maximize how much you remove. Collapse every abstraction, wrapper, facade, and indirection layer that is not strictly necessary. Strip it down hard.

Redirect output to a file and write a sentinel when it exits:

```
cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "Be aggressive: maximize how much you remove. Collapse every abstraction, wrapper, facade, and indirection layer that is not strictly necessary. Strip it down hard. <the user'\''s message>" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

If the user's message contains a double quote, first write it to
`/workspace/eval-prompt.txt` and use `amplifier run "$(cat /workspace/eval-prompt.txt)"`.

## Step 2 -- poll until the sentinel appears

Repeat this check, sleeping ~30s between checks, for as long as it takes (be
patient -- up to ~25 minutes):

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

Do NOT conclude while it still prints `RUNNING`. Keep polling.

## Step 3 -- read the answer and conclude

Once you see `COMPLETE`, read the full output:

```
cat /workspace/eval-run.out
```

Then conclude:

- verdict `success` -- the sentinel shows `EXIT:0` and the output describes
  changes made to /workspace/flowforge
- verdict `failure` -- the sentinel shows a non-zero exit, or the output is
  an error with no work performed
