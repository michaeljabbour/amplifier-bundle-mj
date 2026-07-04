#!/usr/bin/env bash
# Occam's Machete A/B evaluation runner.
#
# Runs the 4 (agent, task) pairs against the current committed code:
#   baseline x reduce-green   machete x reduce-green
#   baseline x reduce-red     machete x reduce-red
#
# Sets up TWO Gitea mirror repos:
#   admin/amplifier-bundle-occams-machete  (current HEAD of this working dir)
#   admin/pulse-fixture                    (evaluation/fixtures/pulse, fresh init)
#
# The task profiles' url_rewrites redirect amplifier-bundle-occams-machete
# clones to the local mirror, so the machete agent installs current committed
# code. The pulse-fixture is cloned directly by each provision step.
#
# Idempotent: re-running refreshes mirrors and writes a fresh dated run.
#
# Usage:
#   ./run.sh
#   ./run.sh --trials 3 --max-parallel 2
#
# Environment overrides:
#   AMPLIFIER_GITEA_ID   pick a specific Gitea instance (default: first/new)
#   ANTHROPIC_API_KEY    required; falls back to ~/.amplifier/keys.env
#
# Prerequisites:
#   amplifier-digital-twin, amplifier-gitea, git, python3, docker on PATH
#   Docker daemon running
#   amplifier_evaluation importable (the bundle .venv is auto-activated if present)

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# This suite lives at evaluation/reduction-ab/, so the repo root is two levels up.
BUNDLE_ROOT="$(cd "$HERE/../.." && pwd)"

# Evaluation bundle cache: where amplifier_evaluation is installed.
EVAL_BUNDLE_ROOT="/Users/michaeljabbour/.amplifier/cache/amplifier-bundle-evaluation-bb6fbc97ac7dfcb1"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }

# ---- 0. preflight --------------------------------------------------------
log "preflight checks"
command -v amplifier-digital-twin >/dev/null || die "amplifier-digital-twin not on PATH"
command -v amplifier-gitea >/dev/null || die "amplifier-gitea not on PATH"
command -v git >/dev/null || die "git not on PATH"
command -v python3 >/dev/null || die "python3 not on PATH"
command -v docker >/dev/null || die "docker not on PATH"
docker info >/dev/null 2>&1 || die "Docker is not running"

# Resolve a Python interpreter that can `import amplifier_evaluation`. Try, in
# order: the eval bundle's own venv (dev monorepo layout), the installed
# `amplifier` app tool venv (which ships amplifier_evaluation + core +
# foundation), then system python3.
PYEVAL=""
_can_import() { [ -n "$1" ] && [ -x "$1" ] && "$1" -c "import amplifier_evaluation" 2>/dev/null; }
for cand in \
    "$EVAL_BUNDLE_ROOT/.venv/bin/python" \
    "$HOME/.local/share/uv/tools/amplifier/bin/python" \
    "$(command -v amplifier >/dev/null 2>&1 && sed -n '1s/^#!//p' "$(command -v amplifier)")" \
    "$(command -v python3)"; do
    if _can_import "$cand"; then PYEVAL="$cand"; break; fi
done
[ -n "$PYEVAL" ] || die "amplifier_evaluation not importable in any candidate python (eval .venv, amplifier tool venv, system python3)"
log "harness python: $PYEVAL"

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$HOME/.amplifier/keys.env" ]; then
    set -a; . "$HOME/.amplifier/keys.env"; set +a
fi
[ -n "${ANTHROPIC_API_KEY:-}" ] || die "ANTHROPIC_API_KEY not set and not in ~/.amplifier/keys.env"

# ---- 1. gitea: discover, create, or start --------------------------------
log "ensuring a Gitea instance is running"
GITEA_ID="${AMPLIFIER_GITEA_ID:-}"
if [ -z "$GITEA_ID" ]; then
    GITEA_ID="$(amplifier-gitea list | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["id"] if d else "")')"
fi
if [ -z "$GITEA_ID" ]; then
    log "no gitea instance found, creating one on port 10110"
    GITEA_ID="$(amplifier-gitea create --port 10110 | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
fi
STATUS_JSON="$(amplifier-gitea status "$GITEA_ID")"
RUNNING="$(echo "$STATUS_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["container_running"])')"
if [ "$RUNNING" != "True" ]; then
    log "starting stopped gitea container amplifier-gitea-$GITEA_ID"
    docker start "amplifier-gitea-$GITEA_ID" >/dev/null
    sleep 4
fi
GITEA_PORT="$(echo "$STATUS_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["port"])')"
GITEA_TOKEN="$(amplifier-gitea token "$GITEA_ID" | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')"
# Host-side URL (used by this script's curl/push, which run on the Mac host).
GITEA_URL="http://localhost:$GITEA_PORT"
# Container-facing URL: the DTU runs inside the colima/incus VM, a SEPARATE VM
# from Docker-Desktop (where Gitea publishes its port). From inside an incus
# container, localhost/incus-gateway do NOT reach Gitea; the Mac host is
# reachable via the lima host gateway (default 192.168.5.2). Override with
# DTU_HOST_GATEWAY if your topology differs.
DTU_GITEA_URL="http://${DTU_HOST_GATEWAY:-192.168.5.2}:$GITEA_PORT"
log "gitea host-side: $GITEA_URL  container-facing: $DTU_GITEA_URL  id=$GITEA_ID"

# Helper: create a Gitea repo if it doesn't exist.
ensure_repo() {
    local name="$1" code
    code="$(curl -sS -H "Authorization: token $GITEA_TOKEN" \
        "$GITEA_URL/api/v1/repos/admin/$name" -o /dev/null -w '%{http_code}')"
    if [ "$code" != "200" ]; then
        log "creating admin/$name"
        curl -sS -X POST "$GITEA_URL/api/v1/admin/users/admin/repos" \
            -H "Authorization: token $GITEA_TOKEN" -H "Content-Type: application/json" \
            -d "{\"name\":\"$name\",\"default_branch\":\"main\",\"auto_init\":false}" -o /dev/null
    fi
}

# Helper: force-push the current HEAD to admin/<repo> main branch.
push_main() {
    git -c credential.helper= push --force \
        "http://admin:$GITEA_TOKEN@localhost:$GITEA_PORT/admin/$1.git" \
        "HEAD:refs/heads/main" >/dev/null 2>&1
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---- 2a. mirror occams-machete (current working tree HEAD) ---------------
log "mirroring occams-machete -> admin/amplifier-bundle-occams-machete"
ensure_repo "amplifier-bundle-occams-machete"
# Full history: Gitea rejects pushing a shallow clone ("shallow update not allowed").
git clone --quiet "$BUNDLE_ROOT" "$WORK/machete"
(
    cd "$WORK/machete"
    push_main "amplifier-bundle-occams-machete"
)
log "occams-machete mirror ready"

# ---- 2b. mirror pulse-fixture -------------------------------------------
log "mirroring pulse-fixture -> admin/pulse-fixture"
ensure_repo "pulse-fixture"
# Copy to a temp dir so we never git-init inside the source tree.
cp -r "$HERE/fixtures/pulse" "$WORK/pulse"
(
    cd "$WORK/pulse"
    # Remove caches not wanted in the fixture repo (respects existing .gitignore too).
    find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
    git init -q
    git -c user.email=eval@local -c user.name=eval add -A
    git -c user.email=eval@local -c user.name=eval commit -q -m "seed pulse fixture"
    push_main "pulse-fixture"
)
log "pulse-fixture mirror ready"

# ---- 2c. mirror flowforge-fixture ----------------------------------------
log "mirroring flowforge-fixture -> admin/flowforge-fixture"
ensure_repo "flowforge-fixture"
# Copy to a temp dir so we never git-init inside the source tree.
cp -r "$HERE/fixtures/flowforge" "$WORK/flowforge"
(
    cd "$WORK/flowforge"
    # Remove caches not wanted in the fixture repo (respects existing .gitignore too).
    find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
    git init -q
    git -c user.email=eval@local -c user.name=eval add -A
    git -c user.email=eval@local -c user.name=eval commit -q -m "seed flowforge fixture"
    push_main "flowforge-fixture"
)
log "flowforge-fixture mirror ready"

# ---- 3. output dir -------------------------------------------------------
OUT="${HOME}/.amplifier/evaluation/occams-machete/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$OUT"

# ---- 4. run harness -------------------------------------------------------
log "running harness, output=$OUT"
"$PYEVAL" "$HERE/harness.py" \
    --output "$OUT" \
    --gitea-url "$DTU_GITEA_URL" \
    --gitea-token "$GITEA_TOKEN" \
    "$@"
HARNESS_EXIT=$?

log "harness exit: $HARNESS_EXIT"
log "results: $OUT"
log "  - trials/              per-trial state.json, ai_user.json, extraction/, grader/"
log "  - comparison.md/.json  A/B metric comparison (baseline vs machete, per task)"
log "  - summary.json         run summary with per-trial states"
exit "$HARNESS_EXIT"
