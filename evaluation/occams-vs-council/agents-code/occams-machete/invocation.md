# Driving the "regular" variant on a CODE task

Single non-interactive turn: the agent modifies the seeded repo in /workspace to
implement the feature. Success = it ran to completion and changed the repo; the grader
judges quality. The exact task is at `/workspace/instructions.txt` — run it verbatim
(always `cat` it; never retype or invent a task).

## Step 0 — snapshot the seeded repo so changes can be diffed later

```
cd /workspace && git init -q && git add -A && git -c user.email=eval@local -c user.name=eval commit -qm baseline && echo baseline-committed
```

## Step 1 — launch the task in the background

```
cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "$(cat /workspace/instructions.txt)" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

## Step 2 — poll until the sentinel appears (sleep ~30s; patient up to ~25 min)

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

Do NOT conclude while it prints `RUNNING`. A sub-session is expected, not an error.

## Step 3 — confirm and conclude

```
cd /workspace && git add -A; echo '--- diff stat ---'; git diff HEAD --stat; echo '--- tests ---'; python3 tests/test_checkout.py 2>&1 | tail -5
```

- verdict `success` — sentinel shows `EXIT:0` and `git diff HEAD` shows changes to the repo.
- verdict `failure` — non-zero exit, or the repo is unchanged.

In your summary note: lines changed, any NEW files added, and whether the tests pass.
Do NOT judge code quality yourself — the grader does that.
