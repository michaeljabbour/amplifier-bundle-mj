"""Static configuration for the design-fidelity Phase-2 harness.

This harness REUSES the cognition-fidelity harness's resilient LLM client
(`llm.py`), content-addressed cache (`cache.py`), and the voice-neutralizer
prompt constants (`prompts.py`). Those modules are imported off-path from the
sibling cognition harness; see `_bootstrap.py` for the sys.path wiring.

This module is import-safe: nothing here makes a network call or reads anything
except resolving path constants. It also intentionally defines the handful of
constants the reused cognition modules import `from config import ...`
(BACKOFF_*, MAX_RETRIES, CACHE_DIR, MJ_PROFILE_PATH, MJ_REVIEWER_PATH) so that
when they resolve `config` to *this* file they find everything they need and
point at *this* harness's cache directory.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HARNESS_DIR: Path = Path(__file__).resolve().parent
# harness/ -> design-fidelity/ -> evaluation/ -> <repo root>
DESIGN_DIR: Path = HARNESS_DIR.parent
EVAL_DIR: Path = DESIGN_DIR.parent
REPO_ROOT: Path = EVAL_DIR.parent

# Reused cognition-fidelity harness (source of llm.py / cache.py / prompts.py).
COGNITION_HARNESS_DIR: Path = EVAL_DIR / "cognition-fidelity" / "harness"

# Inputs (frozen artifacts)
ARMS_DIR: Path = HARNESS_DIR / "arms"
SCENARIOS_PATH: Path = DESIGN_DIR / "scenarios" / "scenarios_design.json"
MJ_FORM_PATH: Path = DESIGN_DIR / "MJ-DESIGN-FORM.md"

# Provenance of the MACHETE arm (also imported by the reused cognition prompts
# module, which does `from config import MJ_PROFILE_PATH, MJ_REVIEWER_PATH`).
MJ_PROFILE_PATH: Path = REPO_ROOT / "context" / "mj-profile.md"
MJ_REVIEWER_PATH: Path = REPO_ROOT / "agents" / "mj-reviewer.md"

# Outputs / working dirs
CACHE_DIR: Path = HARNESS_DIR / "cache"
RUNS_DIR: Path = HARNESS_DIR / "runs"

# ---------------------------------------------------------------------------
# Models (same provider/model as the cognition harness)
# ---------------------------------------------------------------------------
ARM_MODEL: str = "claude-fable-5"  # Anthropic — all six arms (re-run 2026-07-07; was claude-sonnet-4-5)
NEUTRALIZER_MODEL: str = "gpt-5.5"  # OpenAI — voice neutralization (different family; was gpt-4.1)
GRADER_MODEL: str = "gpt-5.5"  # OpenAI — concern semantic-match grader (Stage 2; was gpt-4.1)

# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
ARM_TEMPERATURE: float = 0.7
ARM_MAX_TOKENS: int = 2000
NEUTRALIZER_TEMPERATURE: float = 0.0
NEUTRALIZER_MAX_TOKENS: int = 1800
GRADER_TEMPERATURE: float = 0.0
GRADER_MAX_TOKENS: int = 300

DEFAULT_SAMPLES: int = 3

# ---------------------------------------------------------------------------
# Concurrency / resilience (consumed by the reused llm.py via `from config`)
# ---------------------------------------------------------------------------
MAX_WORKERS: int = 8
MAX_RETRIES: int = 6
BACKOFF_BASE_SECONDS: float = 2.0
BACKOFF_MAX_SECONDS: float = 60.0

# Print a progress line every N completed samples.
PROGRESS_EVERY: int = 20

# ---------------------------------------------------------------------------
# Arms (6) — same base model, only the system prompt (arms/<CODE>.md) differs
# ---------------------------------------------------------------------------
ARMS: tuple[str, ...] = ("NATIVE", "COS", "COE", "ROB", "HOLISTIC", "MACHETE")


def arm_path(code: str) -> Path:
    return ARMS_DIR / f"{code}.md"


# ---------------------------------------------------------------------------
# Structured-call vocabulary (the four axes MJ also fills in)
# ---------------------------------------------------------------------------
VALID_GRIT: tuple[int, ...] = (0, 1, 2, 3)
VALID_DIRECTIONS: tuple[str, ...] = ("ship-as-is", "tweak", "redesign", "kill")

# ---------------------------------------------------------------------------
# Common task appended to EVERY arm (identical across arms). This is the only
# instruction that asks for the structured GRIT/DIRECTION/CONCERN/READ block;
# it lives in the user message so it is provably byte-identical for all 6 arms.
# ---------------------------------------------------------------------------
COMMON_TASK: str = (
    "Review this design decision, then end your answer with EXACTLY this block:\n"
    "GRIT: <0|1|2|3>   (0=none/ship-as-is, 1=surface/local-reversible, "
    "2=structural/bounded reshape, 3=foundational/system-wide, hard to reverse)\n"
    "DIRECTION: <ship-as-is|tweak|redesign|kill>\n"
    "CONCERN: <the single load-bearing factor, one line>\n"
    "READ: <2-4 sentences of your reasoning>"
)

# Per-scenario user message: artifact + question + the common task.
USER_TEMPLATE: str = (
    "DESIGN SCENARIO — {title} (domain: {domain}, depth: {depth})\n\n"
    "{artifact}\n\n"
    "QUESTION: {question}\n\n"
    "{common_task}"
)

# ---------------------------------------------------------------------------
# Dxx -> scenario_id mapping (for Stage 2 / scoring the blind MJ form).
#
# The MJ form (MJ-DESIGN-FORM.md) is BLIND: it presents 16 items D01..D16 in a
# shuffled order with NO scenario_id, including 4 hidden duplicates of the
# scenarios listed in scenarios_design.json["duplicate_plan"] (S02, S05, S08,
# S11). The map below was recovered by exact title-match between each Dxx block
# and the scenario titles. phase2_score.py VERIFIES this mapping at runtime by
# re-matching titles (and re-deriving the duplicate set), and will fail loudly
# if the form's titles ever drift from this table.
#
# HANDOFF / TODO: if the form is ever re-issued with reworded titles (truly
# blind, title-stripped), this static table is the authoritative fallback —
# update it here and keep phase2_score.py's title-verification as the guard.
# ---------------------------------------------------------------------------
DXX_TO_SCENARIO: dict[str, str] = {
    "D01": "S07",  # Move from per-seat to usage-based pricing
    "D02": "S01",  # Shared notification platform across three teams
    "D03": "S11",  # Introduce a lightweight code-review policy
    "D04": "S04",  # Date-formatting helper in a PR
    "D05": "S09",  # Split a consumer app into creator and browser modes
    "D06": "S02",  # Add a graph database for connection-path queries
    "D07": "S12",  # Impose a Slack channel taxonomy
    "D08": "S05",  # Retry/timeout config for a payment gateway client
    "D09": "S08",  # Sunset a low-usage Reports module
    "D10": "S02",  # (duplicate) Add a graph database for connection-path queries
    "D11": "S06",  # Aging feature flag and its dead branch
    "D12": "S11",  # (duplicate) Introduce a lightweight code-review policy
    "D13": "S03",  # API versioning before a breaking change
    "D14": "S05",  # (duplicate) Retry/timeout config for a payment gateway client
    "D15": "S10",  # Replace daily standup with async check-ins
    "D16": "S08",  # (duplicate) Sunset a low-usage Reports module
}
