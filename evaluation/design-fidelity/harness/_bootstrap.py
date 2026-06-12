"""Wire the sibling cognition-fidelity harness onto sys.path so we can REUSE its
resilient LLM client (`llm`), content-addressed cache (`cache`), and the
voice-neutralizer prompt constants (`prompts`).

Import-order contract (do not reorder):
- THIS harness directory is sys.path[0] (the running script's dir), so
  `import config` always resolves to *our* config.py.
- We APPEND the cognition harness dir, so `import llm` / `import cache` /
  `import prompts` fall through to the cognition modules. Those modules do
  `from config import ...` — which resolves to *our* config (sys.path[0] wins),
  and our config deliberately defines every constant they need (BACKOFF_*,
  MAX_RETRIES, CACHE_DIR, MJ_PROFILE_PATH, MJ_REVIEWER_PATH). Net effect: their
  battle-tested code runs against *our* cache directory and *our* config.

Importing this module has no side effects beyond the sys.path mutation; it makes
no network calls and needs no API keys.
"""

from __future__ import annotations

import sys

from config import COGNITION_HARNESS_DIR

_cog = str(COGNITION_HARNESS_DIR)
if _cog not in sys.path:
    # Append (not insert-0) so our own config.py keeps priority.
    sys.path.append(_cog)

if not COGNITION_HARNESS_DIR.exists():  # fail loud, not silently degraded
    raise RuntimeError(
        f"Cognition-fidelity harness not found at {COGNITION_HARNESS_DIR}. "
        "This Phase-2 harness reuses its llm.py / cache.py / prompts.py."
    )
