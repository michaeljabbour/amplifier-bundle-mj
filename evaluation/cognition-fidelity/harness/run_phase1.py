"""Phase-1 cognition-fidelity harness — CLI orchestrator.

Pipeline: 3 arms x N samples (same Claude model, only the system prompt differs)
-> voice-neutralize (GPT) -> blind GPT judge -> map to {flag,withhold,unclear}
-> per-(probe,arm) majority vote -> stats (McNemar exact, CIs, controls).

Every model call is cached so a crashed run resumes. Parallelism via a
ThreadPoolExecutor; per-call retry/backoff lives in llm.py.

Usage:
    python run_phase1.py --probes ../probes/anti_conflation.json [--limit N] [--samples 3]

This script DOES make live API calls when run. It is written but not executed
here (probes not finalized).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pipeline
import prompts
from config import (
    ARMS,
    DEFAULT_PROBES,
    DEFAULT_SAMPLES,
    MAX_WORKERS,
    RUNS_DIR,
)
from stats import analyze, render_markdown

REQUIRED_PROBE_FIELDS = (
    "probe_id",
    "polarity",
    "correct_call",
    "flagged_item",
    "artifact",
)


# ---------------------------------------------------------------------------
# Loading / validation
# ---------------------------------------------------------------------------
def load_probes(path: Path, limit: int | None) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Probe file {path} must contain a JSON array.")
    for i, probe in enumerate(data):
        missing = [f for f in REQUIRED_PROBE_FIELDS if f not in probe]
        if missing:
            raise ValueError(
                f"Probe #{i} ({probe.get('probe_id', '?')}) missing fields: {missing}"
            )
        if probe["polarity"] not in ("reason_present", "reason_absent"):
            raise ValueError(
                f"Probe {probe['probe_id']} bad polarity: {probe['polarity']}"
            )
        if probe["correct_call"] not in ("withhold", "flag"):
            raise ValueError(
                f"Probe {probe['probe_id']} bad correct_call: {probe['correct_call']}"
            )
    if limit is not None:
        data = data[:limit]
    return data


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def _build_tasks(probes: list[dict], samples: int) -> list[tuple[dict, str, int]]:
    tasks: list[tuple[dict, str, int]] = []
    for probe in probes:
        for arm in ARMS:
            for s in range(samples):
                tasks.append((probe, arm, s))
    return tasks


def run(probes: list[dict], samples: int, systems: dict[str, str]) -> list[dict]:
    """Execute every (probe, arm, sample) with bounded parallelism.

    Returns the flat list of completed sample records. Failed tasks are logged
    to stderr and recorded with an 'error' field but never crash the batch.
    """
    tasks = _build_tasks(probes, samples)
    results: list[dict] = []
    total = len(tasks)
    done = 0

    def _work(task: tuple[dict, str, int]) -> dict:
        probe, arm, sample = task
        return pipeline.run_sample(probe, arm, sample, systems[arm])

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {pool.submit(_work, t): t for t in tasks}
        for fut in as_completed(future_map):
            probe, arm, sample = future_map[fut]
            done += 1
            try:
                rec = fut.result()
                results.append(rec)
            except Exception as exc:  # noqa: BLE001 — record and continue
                print(
                    f"[ERROR] probe={probe['probe_id']} arm={arm} sample={sample}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc()
                results.append(
                    {
                        "probe_id": probe["probe_id"],
                        "pair_id": probe.get("pair_id"),
                        "polarity": probe.get("polarity"),
                        "domain": probe.get("domain"),
                        "correct_call": probe.get("correct_call"),
                        "arm": arm,
                        "sample": sample,
                        "error": str(exc),
                        "mapped_call": "unclear",
                        "judge": {"call": "unclear", "evidence": "", "error": True},
                        "raw": "",
                        "neutralized": "",
                    }
                )
            if done % 10 == 0 or done == total:
                print(f"  ... {done}/{total} samples complete", file=sys.stderr)

    return results


def collapse_to_per_probe(
    probes: list[dict], samples_records: list[dict]
) -> list[dict]:
    """Majority-vote each probe/arm group down to one record."""
    probe_by_id = {p["probe_id"]: p for p in probes}
    # group records by (probe_id, arm)
    groups: dict[tuple[str, str], list[dict]] = {}
    for rec in samples_records:
        groups.setdefault((rec["probe_id"], rec["arm"]), []).append(rec)

    per_probe: list[dict] = []
    for (probe_id, arm), recs in sorted(groups.items()):
        probe = probe_by_id[probe_id]
        per_probe.append(pipeline.summarize_probe_arm(probe, arm, recs))
    return per_probe


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------
def _write_raw_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in sorted(
            records, key=lambda r: (r["probe_id"], r["arm"], r["sample"])
        ):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cognition-fidelity Phase-1 harness.")
    ap.add_argument(
        "--probes", default=str(DEFAULT_PROBES), help="Path to probes JSON array."
    )
    ap.add_argument(
        "--limit", type=int, default=None, help="Only run the first N probes."
    )
    ap.add_argument(
        "--samples", type=int, default=DEFAULT_SAMPLES, help="Samples per arm."
    )
    args = ap.parse_args(argv)

    probes_path = Path(args.probes)
    if not probes_path.exists():
        print(f"[FATAL] probes file not found: {probes_path}", file=sys.stderr)
        return 2

    print(f"Loading probes from {probes_path} ...", file=sys.stderr)
    probes = load_probes(probes_path, args.limit)
    print(
        f"  {len(probes)} probes; {len(ARMS)} arms; {args.samples} samples/arm.",
        file=sys.stderr,
    )

    # Build the three system prompts (reads profile + reviewer from disk).
    systems = prompts.build_systems()

    # Run dir
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run dir: {run_dir}", file=sys.stderr)

    # Execute
    print("Generating / neutralizing / judging ...", file=sys.stderr)
    sample_records = run(probes, args.samples, systems)

    # Persist raw
    _write_raw_jsonl(run_dir / "raw.jsonl", sample_records)

    # Collapse + persist per-probe
    per_probe = collapse_to_per_probe(probes, sample_records)
    (run_dir / "per_probe.json").write_text(
        json.dumps(per_probe, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Analyze + persist results
    meta = {
        "timestamp": ts,
        "probes_file": str(probes_path),
        "n_probes": len(probes),
        "samples_per_arm": args.samples,
        "arms": ", ".join(ARMS),
    }
    results = analyze(per_probe)
    results["_meta"] = meta
    (run_dir / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "results.md").write_text(
        render_markdown(results, meta=meta), encoding="utf-8"
    )

    print(f"\nDone. Artifacts in: {run_dir}", file=sys.stderr)
    print("  raw.jsonl, per_probe.json, results.json, results.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
