"""Design-fidelity Phase-2 — STAGE 1 runner (generate + neutralize).

For each scenario (12) x arm (6) x N samples (default 3) = 216 calls:
  1. render [arm system prompt] + [scenario artifact + question + common task],
  2. call the base arm model (claude-sonnet-4-5 — same as the cognition harness),
  3. robustly parse the GRIT/DIRECTION/CONCERN/READ tail (record parse failures),
  4. voice-NEUTRALIZE the free-form text (prose body + CONCERN + READ) with the
     cognition harness's neutralizer (gpt-4.1, a different model family),
  5. append one record to runs/<ts>/raw.jsonl.

Every model call is cached by prompt hash (reusing the cognition harness cache),
so a crashed run resumes without redoing completed work. Parallelism via a
ThreadPoolExecutor; per-call retry/backoff lives in the reused llm.py.

This DOES make live API calls when run (needs ANTHROPIC_API_KEY + OPENAI_API_KEY).
Stage 2 (scoring vs MJ's filled form) is a separate script, phase2_score.py.

Usage:
    python phase2_run.py [--limit N] [--samples 3] [--arms NATIVE,MACHETE]
    python phase2_run.py --check-only      # assemble + validate, no API calls
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import _bootstrap  # noqa: F401 — wires the cognition harness onto sys.path

# Reused from the cognition-fidelity harness (resolved via _bootstrap):
import cache  # type: ignore
import llm  # type: ignore
import prompts as cog_prompts  # type: ignore  # NEUTRALIZE_SYSTEM / NEUTRALIZE_INSTRUCTION

import parse
from config import (
    ARM_MAX_TOKENS,
    ARM_MODEL,
    ARM_TEMPERATURE,
    ARMS,
    CACHE_DIR,
    COMMON_TASK,
    DEFAULT_SAMPLES,
    MAX_WORKERS,
    NEUTRALIZER_MAX_TOKENS,
    NEUTRALIZER_MODEL,
    NEUTRALIZER_TEMPERATURE,
    PROGRESS_EVERY,
    RUNS_DIR,
    SCENARIOS_PATH,
    USER_TEMPLATE,
    arm_path,
)

REQUIRED_SCENARIO_FIELDS = (
    "scenario_id",
    "depth",
    "domain",
    "title",
    "artifact",
    "question",
)


# ---------------------------------------------------------------------------
# Loading / validation
# ---------------------------------------------------------------------------
def load_scenarios(path: Path, limit: int | None) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenarios = data["scenarios"] if isinstance(data, dict) else data
    if not isinstance(scenarios, list):
        raise ValueError(f"Scenario file {path} must contain a 'scenarios' array.")
    for i, sc in enumerate(scenarios):
        missing = [f for f in REQUIRED_SCENARIO_FIELDS if f not in sc]
        if missing:
            raise ValueError(
                f"Scenario #{i} ({sc.get('scenario_id', '?')}) missing fields: {missing}"
            )
    if limit is not None:
        scenarios = scenarios[:limit]
    return scenarios


def load_arm_systems(arms: tuple[str, ...]) -> dict[str, str]:
    """Read each frozen arm system prompt from arms/<CODE>.md."""
    systems: dict[str, str] = {}
    for code in arms:
        p = arm_path(code)
        if not p.exists():
            raise FileNotFoundError(f"Arm prompt missing: {p}")
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Arm prompt empty: {p}")
        systems[code] = text
    return systems


def build_user_message(scenario: dict) -> str:
    return USER_TEMPLATE.format(
        title=scenario["title"],
        domain=scenario["domain"],
        depth=scenario["depth"],
        artifact=scenario["artifact"],
        question=scenario["question"],
        common_task=COMMON_TASK,
    )


# ---------------------------------------------------------------------------
# Stage-1 per-sample pipeline (generate -> parse -> neutralize)
# ---------------------------------------------------------------------------
def generate(
    scenario: dict, arm: str, sample: int, system_prompt: str, user: str
) -> str:
    key = cache.make_key(
        "design_generate",
        ARM_MODEL,
        scenario["scenario_id"],
        arm,
        sample,
        system_prompt + "\n##USER##\n" + user,
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
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
            "stage": "design_generate",
            "arm": arm,
            "scenario_id": scenario["scenario_id"],
            "sample": sample,
        },
        cache_dir=CACHE_DIR,
    )
    return text


def neutralize(scenario: dict, arm: str, sample: int, free_form: str) -> str:
    if not free_form.strip():
        return ""
    user = f"{cog_prompts.NEUTRALIZE_INSTRUCTION}\n\n---\n{free_form}\n---"
    key = cache.make_key(
        "design_neutralize",
        NEUTRALIZER_MODEL,
        scenario["scenario_id"],
        arm,
        sample,
        user,
    )
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is not None:
        return cached
    text = llm.call_openai(
        model=NEUTRALIZER_MODEL,
        system=cog_prompts.NEUTRALIZE_SYSTEM,
        user=user,
        temperature=NEUTRALIZER_TEMPERATURE,
        max_tokens=NEUTRALIZER_MAX_TOKENS,
    )
    cache.put(
        key,
        text,
        meta={
            "stage": "design_neutralize",
            "arm": arm,
            "scenario_id": scenario["scenario_id"],
            "sample": sample,
        },
        cache_dir=CACHE_DIR,
    )
    return text


def run_sample(scenario: dict, arm: str, sample: int, system_prompt: str) -> dict:
    user = build_user_message(scenario)
    raw = generate(scenario, arm, sample, system_prompt, user)
    parsed = parse.parse_block(raw)
    free_form = parse.free_form_text(parsed)
    neutralized = neutralize(scenario, arm, sample, free_form)
    return {
        "scenario_id": scenario["scenario_id"],
        "depth": scenario.get("depth"),
        "domain": scenario.get("domain"),
        "title": scenario.get("title"),
        "arm": arm,
        "sample": sample,
        "raw_text": raw,
        "grit": parsed["grit"],
        "direction": parsed["direction"],
        "concern": parsed["concern"],
        "read": parsed["read"],
        "neutralized_review": neutralized,
        "parse_ok": parsed["parse_ok"],
        "parse_errors": parsed["parse_errors"],
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def _build_tasks(scenarios: list[dict], arms: tuple[str, ...], samples: int):
    return [(sc, arm, s) for sc in scenarios for arm in arms for s in range(samples)]


def run(
    scenarios: list[dict], arms: tuple[str, ...], samples: int, systems: dict[str, str]
) -> list[dict]:
    tasks = _build_tasks(scenarios, arms, samples)
    total = len(tasks)
    results: list[dict] = []
    done = 0

    def _work(task):
        sc, arm, sample = task
        return run_sample(sc, arm, sample, systems[arm])

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(future_map):
            sc, arm, sample = future_map[fut]
            done += 1
            try:
                results.append(fut.result())
            except Exception as exc:  # noqa: BLE001 — record and continue
                print(
                    f"[ERROR] scenario={sc['scenario_id']} arm={arm} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                results.append(
                    {
                        "scenario_id": sc["scenario_id"],
                        "depth": sc.get("depth"),
                        "domain": sc.get("domain"),
                        "title": sc.get("title"),
                        "arm": arm,
                        "sample": sample,
                        "raw_text": "",
                        "grit": None,
                        "direction": None,
                        "concern": None,
                        "read": None,
                        "neutralized_review": "",
                        "parse_ok": False,
                        "parse_errors": ["error"],
                        "error": str(exc),
                    }
                )
            if done % PROGRESS_EVERY == 0 or done == total:
                n_fail = sum(1 for r in results if not r.get("parse_ok"))
                print(
                    f"  ... {done}/{total} samples complete ({n_fail} parse/error so far)",
                    file=sys.stderr,
                )

    return results


def _write_raw_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            records, key=lambda r: (r["scenario_id"], r["arm"], r["sample"])
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Design-fidelity Phase-2 Stage-1 runner.")
    ap.add_argument(
        "--scenarios", default=str(SCENARIOS_PATH), help="Scenario JSON path."
    )
    ap.add_argument(
        "--limit", type=int, default=None, help="Only run the first N scenarios."
    )
    ap.add_argument(
        "--samples", type=int, default=DEFAULT_SAMPLES, help="Samples per arm."
    )
    ap.add_argument(
        "--arms", default=None, help="Comma-separated arm subset (default: all 6)."
    )
    ap.add_argument(
        "--check-only",
        action="store_true",
        help="Assemble + validate arms/scenarios and print sizes; make NO API calls.",
    )
    args = ap.parse_args(argv)

    arms = tuple(a.strip() for a in args.arms.split(",")) if args.arms else ARMS
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        print(f"[FATAL] unknown arms: {unknown}; valid: {ARMS}", file=sys.stderr)
        return 2

    scenarios_path = Path(args.scenarios)
    if not scenarios_path.exists():
        print(f"[FATAL] scenarios file not found: {scenarios_path}", file=sys.stderr)
        return 2

    scenarios = load_scenarios(scenarios_path, args.limit)
    systems = load_arm_systems(arms)

    print("Arm prompt sizes (chars):", file=sys.stderr)
    for code in arms:
        print(f"  {code:<9} {len(systems[code]):>6}", file=sys.stderr)
    total_calls = len(scenarios) * len(arms) * args.samples
    print(
        f"Scenarios: {len(scenarios)} | arms: {len(arms)} | samples: {args.samples} "
        f"| arm calls: {total_calls} (+ up to {total_calls} neutralize calls)",
        file=sys.stderr,
    )

    if args.check_only:
        print("[check-only] validation OK; no API calls made.", file=sys.stderr)
        return 0

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run dir: {run_dir}", file=sys.stderr)

    print("Generating / neutralizing ...", file=sys.stderr)
    records = run(scenarios, arms, args.samples, systems)
    _write_raw_jsonl(run_dir / "raw.jsonl", records)

    n_fail = sum(1 for r in records if not r.get("parse_ok"))
    meta = {
        "timestamp": ts,
        "scenarios_file": str(scenarios_path),
        "n_scenarios": len(scenarios),
        "arms": list(arms),
        "samples_per_arm": args.samples,
        "arm_model": ARM_MODEL,
        "neutralizer_model": NEUTRALIZER_MODEL,
        "arm_prompt_sizes": {c: len(systems[c]) for c in arms},
        "n_records": len(records),
        "n_parse_failures": n_fail,
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"\nDone. {len(records)} records ({n_fail} parse/error). Artifacts in: {run_dir}",
        file=sys.stderr,
    )
    print("  raw.jsonl, meta.json", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
