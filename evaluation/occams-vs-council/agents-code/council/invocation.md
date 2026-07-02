# Driving the "council" variant on a CODE task

Same single-turn shape as the other code variants, but this variant's headline
capability is the review panel, so we drive the agent to convene it on its actual
implementation. The exact task is at `/workspace/instructions.txt` — always `cat` it;
never retype or invent a task.

## Step 0 — snapshot the seeded repo so changes can be diffed later

```
cd /workspace && git init -q && git add -A && git -c user.email=eval@local -c user.name=eval commit -qm baseline && echo baseline-committed
```

## Step 1 — build the augmented prompt from the seeded task, then launch in background

```
{ cat /workspace/instructions.txt; cat <<'PROMPT'

After implementing, convene the full review council on your implementation: run the
council (council-here, or load_skill council-here) on your changes (git diff), let every
lens weigh in, save the synthesized panel verdict to /workspace/council-review.md, then
revise the code to address the panel's findings. Ensure `python3 tests/test_checkout.py`
still passes.
PROMPT
} > /workspace/eval-prompt.txt

cd /workspace && rm -f eval-run.out eval-run.done && \
nohup bash -lc 'PATH=/root/.local/bin:$PATH amplifier run "$(cat /workspace/eval-prompt.txt)" > /workspace/eval-run.out 2>&1; echo "EXIT:$?" > /workspace/eval-run.done' >/dev/null 2>&1 &
echo launched
```

## Step 2 — poll until the sentinel appears

Sleep ~30s between checks. Be EXTRA patient — the council fans out ~7 isolated
sub-sessions, so this can take notably longer (up to ~40 minutes):

```
if [ -f /workspace/eval-run.done ]; then echo "COMPLETE $(cat /workspace/eval-run.done)"; else echo RUNNING; tail -c 200 /workspace/eval-run.out 2>/dev/null; fi
```

## Step 3 — confirm and conclude

```
cd /workspace && git add -A; echo '--- diff stat ---'; git diff HEAD --stat; echo '--- tests ---'; python3 tests/test_checkout.py 2>&1 | tail -5; echo '--- council-review.md ---'; head -c 400 /workspace/council-review.md 2>/dev/null
```

- `success` — `EXIT:0` and `git diff HEAD` shows changes.
- In your summary note: lines changed, any NEW files, whether tests pass, and whether
  `/workspace/council-review.md` was produced (confirms the panel convened).
- `failure` — non-zero exit, or the repo is unchanged.

Do NOT judge code quality yourself — the grader does that.
