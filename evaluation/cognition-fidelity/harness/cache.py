"""Content-addressed cache for every model call.

Key = sha256("stage|model|probe_id|arm|sample|prompt"). Stored as JSON at
cache/<sha>.json so re-runs resume after a crash. Cost is not a concern; the
cache exists only so an interrupted run does not waste completed work.

The cache is intentionally append-only and side-effect free apart from writing
the keyed file. Reads never raise on a corrupt/partial file — they treat it as a
miss so the call is simply redone.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from config import CACHE_DIR


def make_key(
    stage: str,
    model: str,
    probe_id: str,
    arm: str,
    sample: int,
    prompt: str,
) -> str:
    """Stable sha256 over the call's full identity."""
    raw = "|".join([stage, model, probe_id, arm, str(sample), prompt])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _path_for(key: str, cache_dir: Path) -> Path:
    return cache_dir / f"{key}.json"


def get(key: str, cache_dir: Path = CACHE_DIR) -> str | None:
    """Return the cached value string, or None on miss / unreadable entry."""
    path = _path_for(key, cache_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data.get("value")
        return value if isinstance(value, str) else None
    except (json.JSONDecodeError, OSError):
        return None


def put(
    key: str,
    value: str,
    meta: dict | None = None,
    cache_dir: Path = CACHE_DIR,
) -> None:
    """Atomically write the value under the key. meta is stored for auditing."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {"value": value, "meta": meta or {}}
    # Atomic write: temp file in the same dir, then rename.
    fd, tmp_name = tempfile.mkstemp(dir=str(cache_dir), suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with open(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(_path_for(key, cache_dir))
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
