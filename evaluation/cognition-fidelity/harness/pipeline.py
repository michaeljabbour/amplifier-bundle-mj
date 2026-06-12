"""The per-sample pipeline: generate -> neutralize -> judge -> map, plus the
per-(probe, arm) majority vote.

Every model call is cached (see cache.py) keyed by its full identity, so a
crashed run resumes without redoing completed work. This module is pure logic +
cached I/O; orchestration/parallelism lives in run_phase1.py.
"""

from __future__ import annotations

import json
import re
from collections import Counter

import cache
import llm
import prompts
from config import (
    ARM_MAX_TOKENS,
    ARM_MODEL,
    ARM_TEMPERATURE,
    CALL_MAP,
    JUDGE_MAX_TOKENS,
    JUDGE_MODEL,
    JUDGE_TEMPERATURE,
    NEUTRALIZER_MAX_TOKENS,
    NEUTRALIZER_MODEL,
    NEUTRALIZER_TEMPERATURE,
)

VALID_CALLS = ("defect", "not_defect", "unclear")


# ---------------------------------------------------------------------------
# Stage 1 — generate a raw arm review
# ---------------------------------------------------------------------------
def generate_review(probe: dict, arm: str, sample: int, system_prompt: str) -> str:
    user = prompts.build_user_message(probe)
    key = cache.make_key(
        "generate",
        ARM_MODEL,
        probe["probe_id"],
        arm,
        sample,
        system_prompt + "\n##USER##\n" + user,
    )
    cached = cache.get(key)
    if cached is not None:
        return cached
    text = llm.call_anthropic(
        model=ARM_MODEL,
        system=system_prompt,
        user=user,
        temperature=ARM_TEMPERATURE,
        max_tokens=ARM_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "generate",
            "arm": arm,
            "probe_id": probe["probe_id"],
            "sample": sample,
        },
    )
    return text


# ---------------------------------------------------------------------------
# Stage 2 — voice-neutralize (different model family)
# ---------------------------------------------------------------------------
def neutralize_review(probe: dict, arm: str, sample: int, raw_text: str) -> str:
    user = f"{prompts.NEUTRALIZE_INSTRUCTION}\n\n---\n{raw_text}\n---"
    key = cache.make_key(
        "neutralize", NEUTRALIZER_MODEL, probe["probe_id"], arm, sample, user
    )
    cached = cache.get(key)
    if cached is not None:
        return cached
    text = llm.call_openai(
        model=NEUTRALIZER_MODEL,
        system=prompts.NEUTRALIZE_SYSTEM,
        user=user,
        temperature=NEUTRALIZER_TEMPERATURE,
        max_tokens=NEUTRALIZER_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "neutralize",
            "arm": arm,
            "probe_id": probe["probe_id"],
            "sample": sample,
        },
    )
    return text


# ---------------------------------------------------------------------------
# Stage 3 — blind judge -> strict JSON
# ---------------------------------------------------------------------------
def _parse_judge_json(text: str) -> dict:
    """Extract the first JSON object and normalize the call field.

    Robust to code fences and surrounding prose. Falls back to 'unclear'.
    """
    cleaned = text.strip()
    # Strip ``` / ```json fences if present.
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.MULTILINE
    ).strip()
    obj = None
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                obj = json.loads(match.group(0))
            except json.JSONDecodeError:
                obj = None
    if not isinstance(obj, dict):
        return {"call": "unclear", "evidence": "", "parse_error": True, "raw": text}
    call = str(obj.get("call", "unclear")).strip().lower()
    if call not in VALID_CALLS:
        call = "unclear"
    evidence = obj.get("evidence", "")
    if not isinstance(evidence, str):
        evidence = str(evidence)
    return {"call": call, "evidence": evidence}


def judge_review(probe: dict, arm: str, sample: int, neutralized_text: str) -> dict:
    user = prompts.build_judge_prompt(probe, neutralized_text)
    key = cache.make_key("judge", JUDGE_MODEL, probe["probe_id"], arm, sample, user)
    cached = cache.get(key)
    if cached is None:
        cached = llm.call_openai(
            model=JUDGE_MODEL,
            system=prompts.JUDGE_SYSTEM,
            user=user,
            temperature=JUDGE_TEMPERATURE,
            max_tokens=JUDGE_MAX_TOKENS,
        )
        cache.put(
            key,
            cached,
            meta={
                "stage": "judge",
                "arm": arm,
                "probe_id": probe["probe_id"],
                "sample": sample,
            },
        )
    return _parse_judge_json(cached)


# ---------------------------------------------------------------------------
# Full per-sample flow
# ---------------------------------------------------------------------------
def run_sample(probe: dict, arm: str, sample: int, system_prompt: str) -> dict:
    """Generate -> neutralize -> judge -> map for one (probe, arm, sample)."""
    raw = generate_review(probe, arm, sample, system_prompt)
    neutralized = neutralize_review(probe, arm, sample, raw)
    judge = judge_review(probe, arm, sample, neutralized)
    mapped_call = CALL_MAP.get(judge["call"], "unclear")
    return {
        "probe_id": probe["probe_id"],
        "pair_id": probe.get("pair_id"),
        "polarity": probe.get("polarity"),
        "domain": probe.get("domain"),
        "correct_call": probe.get("correct_call"),
        "arm": arm,
        "sample": sample,
        "raw": raw,
        "neutralized": neutralized,
        "judge": judge,
        "mapped_call": mapped_call,
    }


# ---------------------------------------------------------------------------
# Majority vote over a probe/arm's samples
# ---------------------------------------------------------------------------
def majority_vote(mapped_calls: list[str]) -> tuple[str, bool]:
    """Return (majority_call, all_agree).

    Votes over {flag, withhold} only; 'unclear' samples abstain. A strict
    majority wins; an empty/tied decisive set -> 'unclear'. all_agree is True
    only when every sample produced the identical mapped call.
    """
    all_agree = len(set(mapped_calls)) == 1 and len(mapped_calls) > 0
    decisive = [c for c in mapped_calls if c in ("flag", "withhold")]
    if not decisive:
        return "unclear", all_agree
    counts = Counter(decisive)
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "unclear", all_agree  # tie
    return top[0][0], all_agree


def summarize_probe_arm(probe: dict, arm: str, samples: list[dict]) -> dict:
    """Collapse a probe/arm's samples to one majority call + correctness."""
    mapped_calls = [
        s["mapped_call"] for s in sorted(samples, key=lambda s: s["sample"])
    ]
    majority_call, all_agree = majority_vote(mapped_calls)
    correct = majority_call == probe.get("correct_call")
    return {
        "probe_id": probe["probe_id"],
        "pair_id": probe.get("pair_id"),
        "polarity": probe.get("polarity"),
        "domain": probe.get("domain"),
        "inverted_corpus": probe.get("inverted_corpus"),
        "correct_call": probe.get("correct_call"),
        "arm": arm,
        "sample_calls": mapped_calls,
        "majority_call": majority_call,
        "correct": correct,
        "unclear": majority_call == "unclear",
        "self_consistent": all_agree,
    }
