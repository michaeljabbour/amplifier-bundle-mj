#!/usr/bin/env bash
# occams-vs-council evaluation runner.
#
#   ./run-smoke.sh smoke   # pipeline validation: regular variant only, 1 trial
#   ./run-smoke.sh full    # the real run: all 3 variants (regular/occams-machete/council)
#
# Results are written OUTSIDE the repo (they hold keys/transcripts): default
#   ~/.amplifier/evaluation/occams-vs-council/<run-id>/
#
# Env overrides: ANTHROPIC_API_KEY (or ~/.amplifier/keys.env), MAX_PARALLEL,
#   TRIALS, EVAL_LIB (path to amplifier-bundle-evaluation checkout).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
EV="${EVAL_LIB:-$HOME/dev/amplifier-bundle-evaluation}"
RESULTS_ROOT="${RESULTS_ROOT:-$HOME/.amplifier/evaluation/occams-vs-council}"
MAX_PARALLEL="${MAX_PARALLEL:-4}"
TRIALS="${TRIALS:-1}"
MODE="${1:-smoke}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

command -v amplifier-digital-twin >/dev/null || die "amplifier-digital-twin not on PATH"
command -v uv >/dev/null || die "uv not on PATH"
docker info >/dev/null 2>&1 || die "Docker is not running"
[ -d "$EV" ] || die "amplifier-bundle-evaluation not found at $EV (set EVAL_LIB)"
[ -f "$HOME/.amplifier/keys.env" ] && { set -a; . "$HOME/.amplifier/keys.env"; set +a; }
[ -n "${ANTHROPIC_API_KEY:-}" ] || die "ANTHROPIC_API_KEY not set and not in ~/.amplifier/keys.env"

# The amplifier-evaluation library pins editable ../amplifier-core and
# ../amplifier-foundation as sources, which can be version-mismatched against the
# live ecosystem. Install it into an ISOLATED venv against core+foundation @main
# instead, so the harness imports regardless of the dev checkouts' state.
VENV="${EVAL_VENV:-$HERE/.venv-eval}"
PYBIN="$VENV/bin/python"
if ! "$PYBIN" -c "import amplifier_evaluation" >/dev/null 2>&1; then
  log "bootstrapping isolated harness venv at $VENV"
  uv venv "$VENV" >/dev/null
  uv pip install --python "$PYBIN" \
    "amplifier-core @ git+https://github.com/microsoft/amplifier-core@main" \
    "amplifier-foundation @ git+https://github.com/microsoft/amplifier-foundation@main" \
    "click>=8,<9" "pyyaml>=6,<7"
  uv pip install --python "$PYBIN" --no-deps -e "$EV"
fi
"$PYBIN" -c "import amplifier_evaluation" || die "amplifier_evaluation still not importable"

case "$MODE" in
  smoke) VARIANTS=(regular); TASKS=(s1-yagni) ;;
  full)  VARIANTS=(regular occams-machete council); TASKS=(s1-yagni s2-shouldwe s3-reduce) ;;
  *) die "usage: run-smoke.sh [smoke|full]" ;;
esac

PAIRS=(); for a in "${VARIANTS[@]}"; do for t in "${TASKS[@]}"; do PAIRS+=(--pair "$a:$t"); done; done
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RESULTS_ROOT"
log "mode=$MODE variants=[${VARIANTS[*]}] tasks=[${TASKS[*]}] pairs=${#PAIRS[@]} trials=$TRIALS parallel=$MAX_PARALLEL"
log "results -> $RESULTS_ROOT/$RUN_ID"

"$PYBIN" -m amplifier_evaluation run \
  --agents-dir "$HERE/agents" \
  --tasks-dir  "$HERE/tasks" \
  "${PAIRS[@]}" \
  --output-dir "$RESULTS_ROOT" \
  --run-id "$RUN_ID" \
  --max-parallel "$MAX_PARALLEL" \
  --trials-per-pair "$TRIALS" \
  --verbose

log "done. results: $RESULTS_ROOT/$RUN_ID (summary.json, trials/)"
