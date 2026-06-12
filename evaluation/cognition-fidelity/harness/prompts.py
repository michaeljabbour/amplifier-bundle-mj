"""Prompt construction for all three arms plus the neutralizer and judge.

The ONLY independent variable across arms is the system prompt; the user message
template is identical for every arm. Keeping every literal here makes the frozen
experiment auditable in one place.
"""

from __future__ import annotations

import re
from pathlib import Path

from config import MJ_PROFILE_PATH, MJ_REVIEWER_PATH

# ---------------------------------------------------------------------------
# Shared appended instruction (lens) + fixed generic task (baseline/style-only)
# ---------------------------------------------------------------------------
BOTTOM_LINE_INSTRUCTION: str = (
    "End with a clear bottom-line: is the flagged item a genuine defect that "
    "should be fixed, or not?"
)

# FIXED generic reviewer system prompt. No profile, no anti-conflation/locality
# guard. This is the fair baseline.
BASELINE_SYSTEM: str = (
    "You are a sharp, experienced senior software/design reviewer. Review what "
    "you're given rigorously and honestly. "
    "End with a clear bottom-line: is the flagged item a genuine defect that "
    "should be fixed, or not?"
)

# Negative control: MJ voice/cadence ONLY, no reasoning discipline / guard.
STYLE_VOICE_SNIPPET: str = (
    "Write in this voice: staccato then expansive; short declarative punches; "
    "parallel two-beats; open on a concrete scene then zoom to the principle; "
    "close short; warm but blunt; no hedging."
)

# ---------------------------------------------------------------------------
# Arm USER message template (identical across all arms)
# ---------------------------------------------------------------------------
USER_TEMPLATE: str = (
    "Review the following {domain} artifact. A reviewer flagged this item as a "
    "possible defect: «{flagged_item}».\n\n"
    "ARTIFACT:\n{artifact}\n\n"
    "Question: Considering everything above, is «{flagged_item}» a genuine "
    "defect/mistake that should be fixed, or not? Explain, then end with your "
    "bottom-line call."
)

# ---------------------------------------------------------------------------
# Voice-neutralization prompt (gpt-4.1), applied to every raw arm output.
# ---------------------------------------------------------------------------
NEUTRALIZE_SYSTEM: str = (
    "You rewrite text in plain, neutral prose without altering its substance."
)
NEUTRALIZE_INSTRUCTION: str = (
    "Rewrite this review in plain neutral prose. Preserve the substantive "
    "conclusion and reasoning EXACTLY; remove all voice, personality, metaphor, "
    "and idiosyncratic phrasing; do not add or change any judgment."
)

# ---------------------------------------------------------------------------
# Blind judge prompt (gpt-4.1). Never told the arm, the correct label, MJ, or
# the hypothesis. Sees only flagged_item + artifact + neutralized review.
# ---------------------------------------------------------------------------
JUDGE_SYSTEM: str = (
    "You are a careful classifier. You output only the requested JSON object and "
    "nothing else."
)
JUDGE_TEMPLATE: str = (
    "You are classifying the conclusion of a review. Did the reviewer conclude "
    "that «{flagged_item}» is a genuine defect/mistake that should be fixed "
    '(call="defect"), or that it is acceptable / not a defect '
    '(call="not_defect")? If no clear conclusion, call="unclear". '
    "Output only the JSON.\n\n"
    "FLAGGED ITEM: «{flagged_item}»\n\n"
    "ARTIFACT:\n{artifact}\n\n"
    "REVIEW:\n{review}\n\n"
    'Output STRICT JSON: {{"call":"defect"|"not_defect"|"unclear",'
    '"evidence":"<short quote>"}}'
)


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block delimited by the first pair of
    --- fences. If no frontmatter is present, return the text unchanged."""
    return re.sub(r"\A---\n.*?\n---\n?", "", text, count=1, flags=re.DOTALL).lstrip()


def build_lens_system(
    profile_path: Path = MJ_PROFILE_PATH,
    reviewer_path: Path = MJ_REVIEWER_PATH,
) -> str:
    """lens system prompt = full mj-profile.md + '\\n\\n' + mj-reviewer.md body
    (frontmatter stripped) + appended bottom-line instruction."""
    profile = profile_path.read_text(encoding="utf-8").rstrip()
    reviewer_body = _strip_frontmatter(
        reviewer_path.read_text(encoding="utf-8")
    ).rstrip()
    return f"{profile}\n\n{reviewer_body}\n\n{BOTTOM_LINE_INSTRUCTION}"


def build_style_only_system() -> str:
    """style-only = MJ voice snippet + the SAME generic reviewer task as baseline.
    Explicitly NO reasoning discipline, NO anti-conflation guard."""
    return f"{STYLE_VOICE_SNIPPET}\n\n{BASELINE_SYSTEM}"


def build_systems() -> dict[str, str]:
    """Return the system prompt for each arm. Reads profile/reviewer from disk."""
    return {
        "lens": build_lens_system(),
        "baseline": BASELINE_SYSTEM,
        "style_only": build_style_only_system(),
    }


def build_user_message(probe: dict) -> str:
    return USER_TEMPLATE.format(
        domain=probe.get("domain", "software"),
        flagged_item=probe["flagged_item"],
        artifact=probe["artifact"],
    )


def build_judge_prompt(probe: dict, neutralized_review: str) -> str:
    return JUDGE_TEMPLATE.format(
        flagged_item=probe["flagged_item"],
        artifact=probe["artifact"],
        review=neutralized_review,
    )
