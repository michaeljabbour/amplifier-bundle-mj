"""Robust parser for the structured tail block every arm is asked to emit:

    GRIT: <0|1|2|3>
    DIRECTION: <ship-as-is|tweak|redesign|kill>
    CONCERN: <one line>
    READ: <2-4 sentences>

The parser is deliberately forgiving (models wrap labels in **bold**, backticks,
add stray punctuation, or reorder lines) but records every field it could not
recover so Stage-1 can count parse failures rather than silently coercing them.

It also splits the raw answer into the prose *body* (everything before the block)
so Stage-1 can voice-neutralize only the free-form text (body + CONCERN + READ),
leaving the categorical GRIT/DIRECTION untouched.
"""

from __future__ import annotations

import re

from config import VALID_DIRECTIONS

# Label matchers: tolerate leading markdown (*, #, -, >), bold/backtick wrappers,
# and a colon or dash separator. Case-insensitive, anchored at line start.
_LABEL = r"[ \t>*#`\-]*\**`?{name}`?\**\s*[:\-]\s*"


def _label_re(name: str) -> re.Pattern[str]:
    return re.compile(_LABEL.format(name=name), re.IGNORECASE)


_GRIT_RE = re.compile(
    _LABEL.format(name="GRIT") + r".*?([0-3])", re.IGNORECASE | re.DOTALL
)
_DIR_RE = re.compile(
    _LABEL.format(name="DIRECTION")
    + r".*?(ship[\s\-]?as[\s\-]?is|tweak|redesign|kill)",
    re.IGNORECASE | re.DOTALL,
)
_CONCERN_RE = _label_re("CONCERN")
_READ_RE = _label_re("READ")
_GRIT_LINE_RE = _label_re("GRIT")


def _normalize_direction(raw: str) -> str | None:
    token = raw.strip().lower().replace(" ", "-").replace("_", "-")
    token = re.sub(r"-+", "-", token)
    return token if token in VALID_DIRECTIONS else None


def _capture_field(text: str, label_re: re.Pattern[str]) -> str | None:
    """Return the text following a label up to the next known label or blank gap."""
    m = label_re.search(text)
    if not m:
        return None
    rest = text[m.end() :]
    # Stop at the next labelled field (CONCERN/READ/GRIT/DIRECTION) if present.
    stop = re.search(
        r"\n[ \t>*#`\-]*\**`?(GRIT|DIRECTION|CONCERN|READ)`?\**\s*[:\-]",
        rest,
        re.IGNORECASE,
    )
    chunk = rest[: stop.start()] if stop else rest
    chunk = chunk.strip().strip("*` ").strip()
    return chunk or None


def parse_block(raw_text: str) -> dict:
    """Parse the structured tail. Returns grit/direction/concern/read plus a list
    of parse_errors and the prose `body` (text before the GRIT block)."""
    errors: list[str] = []

    grit_match = _GRIT_RE.search(raw_text)
    grit = int(grit_match.group(1)) if grit_match else None
    if grit is None:
        errors.append("grit")

    dir_match = _DIR_RE.search(raw_text)
    direction = _normalize_direction(dir_match.group(1)) if dir_match else None
    if direction is None:
        errors.append("direction")

    concern = _capture_field(raw_text, _CONCERN_RE)
    if concern is None:
        errors.append("concern")

    read = _capture_field(raw_text, _READ_RE)
    if read is None:
        errors.append("read")

    # Body = everything before the structured block (first GRIT label).
    block_anchor = _GRIT_LINE_RE.search(raw_text)
    body = (
        raw_text[: block_anchor.start()].strip() if block_anchor else raw_text.strip()
    )

    return {
        "grit": grit,
        "direction": direction,
        "concern": concern,
        "read": read,
        "body": body,
        "parse_errors": errors,
        "parse_ok": not errors,
    }


def free_form_text(parsed: dict) -> str:
    """The voice-bearing text to neutralize: prose body + CONCERN + READ.

    GRIT/DIRECTION are categorical tokens and are intentionally excluded so the
    neutralizer cannot perturb the structured call.
    """
    parts: list[str] = []
    if parsed.get("body"):
        parts.append(parsed["body"])
    if parsed.get("concern"):
        parts.append(f"CONCERN: {parsed['concern']}")
    if parsed.get("read"):
        parts.append(f"READ: {parsed['read']}")
    return "\n\n".join(parts).strip()
