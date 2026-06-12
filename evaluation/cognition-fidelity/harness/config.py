"""Static configuration for the cognition-fidelity Phase-1 harness.

All paths are anchored to this file's location so the harness can be invoked
from any working directory. Nothing here makes a network call or reads the
filesystem at import time except resolving path constants.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HARNESS_DIR: Path = Path(__file__).resolve().parent
# harness/ -> cognition-fidelity/ -> evaluation/ -> <repo root>
COGNITION_DIR: Path = HARNESS_DIR.parent
EVAL_DIR: Path = COGNITION_DIR.parent
REPO_ROOT: Path = EVAL_DIR.parent

# Inputs (frozen artifacts)
DEFAULT_PROBES: Path = COGNITION_DIR / "probes" / "anti_conflation.json"
MJ_PROFILE_PATH: Path = REPO_ROOT / "context" / "mj-profile.md"
MJ_REVIEWER_PATH: Path = REPO_ROOT / "agents" / "mj-reviewer.md"

# Outputs / working dirs
CACHE_DIR: Path = HARNESS_DIR / "cache"
RUNS_DIR: Path = HARNESS_DIR / "runs"

# ---------------------------------------------------------------------------
# Models (confirmed live)
# ---------------------------------------------------------------------------
ARM_MODEL: str = "claude-sonnet-4-5"  # Anthropic — all three arms
NEUTRALIZER_MODEL: str = "gpt-4.1"  # OpenAI — voice neutralization
JUDGE_MODEL: str = "gpt-4.1"  # OpenAI — blind judge (different family)

# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
ARM_TEMPERATURE: float = 0.7
ARM_MAX_TOKENS: int = 2000
NEUTRALIZER_TEMPERATURE: float = 0.0
NEUTRALIZER_MAX_TOKENS: int = 1800
JUDGE_TEMPERATURE: float = 0.0
JUDGE_MAX_TOKENS: int = 300

DEFAULT_SAMPLES: int = 3

# ---------------------------------------------------------------------------
# Concurrency / resilience
# ---------------------------------------------------------------------------
MAX_WORKERS: int = 8
MAX_RETRIES: int = 6
BACKOFF_BASE_SECONDS: float = 2.0
BACKOFF_MAX_SECONDS: float = 60.0

# ---------------------------------------------------------------------------
# Arms / domain constants
# ---------------------------------------------------------------------------
ARMS: tuple[str, ...] = ("lens", "baseline", "style_only")

# Canonical mapping from the judge's 3-way call to the probe call space.
CALL_MAP: dict[str, str] = {
    "defect": "flag",
    "not_defect": "withhold",
    "unclear": "unclear",
}

# Analysis: if lens and style-only are within this many accuracy points on the
# reason-present stratum, the apparatus may be measuring style, not reasoning.
INVALIDATION_THRESHOLD: float = 0.10
