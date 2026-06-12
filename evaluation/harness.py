#!/usr/bin/env python3
"""3-arm harness for the occams-machete bundle evaluation.

Runs five (agent, task) pairs using the stock
`amplifier_evaluation.harness.run.run()` entry point:

    plain-timid      x  reduce-hard
    plain-aggressive x  reduce-hard
    machete          x  reduce-hard
    plain-timid      x  refuse-red
    machete          x  refuse-red

Independent variable: AGENT stance + bundle composition.
  plain-timid:      no occams-machete, conservative stance.
  plain-aggressive: no occams-machete, aggressive stance.
  machete:          occams-machete installed, machete discipline stance.
Environment variable: TASK (reduce-hard starts green; refuse-red has a
pre-existing failing test committed to HEAD).

After the run, analyze.analyze() computes per-task 3-arm comparisons and
writes comparison.md / comparison.json alongside the standard run artifacts.

Invoked by run.sh, which provisions the Gitea mirrors and supplies
GITEA_URL / GITEA_TOKEN. See run.sh for the surrounding setup.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from amplifier_evaluation.harness.run import run

# analyze.py is a sibling module (same directory as this script).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402

log = logging.getLogger("occams-machete")

# All five (agent_id, task_id) pairs to evaluate.
# agent_id must match `name:` in agents/<agent>/meta.yaml.
# task_id  must match `name:` in tasks/<task>/meta.yaml.
SELECTION: list[tuple[str, str]] = [
    ("plain-timid", "reduce-hard"),
    ("plain-aggressive", "reduce-hard"),
    ("machete", "reduce-hard"),
    ("plain-timid", "refuse-red"),
    ("machete", "refuse-red"),
]


async def _run(args: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    agents_dir = here / "agents"
    tasks_dir = here / "tasks"
    output = Path(args.output)

    # Derive GITEA_HOST (netloc only, no scheme) so provision setup_cmds
    # can construct authenticated clone URLs: http://admin:TOKEN@HOST/repo.
    # e.g. GITEA_URL="http://localhost:10110" -> GITEA_HOST="localhost:10110"
    parsed = urlparse(args.gitea_url)
    gitea_host = parsed.netloc  # "localhost:10110"

    launch_variables = {
        "GITEA_URL": args.gitea_url,
        "GITEA_TOKEN": args.gitea_token,
        "GITEA_HOST": gitea_host,
    }

    log.info(
        "starting run: agents=%s tasks=%s selection=%s trials=%d parallel=%d",
        agents_dir,
        tasks_dir,
        SELECTION,
        args.trials,
        args.max_parallel,
    )

    run_result = await run(
        agents_dir=agents_dir,
        tasks_dir=tasks_dir,
        selection=SELECTION,
        output_dir=output,
        trials_per_pair=args.trials,
        max_parallel=args.max_parallel,
        launch_variables=launch_variables,
    )

    log.info("run finished: %s", run_result.summary_counts)

    # Compute A/B comparison and persist alongside the run artifacts.
    comparison_md, comparison_json = analyze.analyze(output)
    (output / "comparison.md").write_text(comparison_md, encoding="utf-8")
    (output / "comparison.json").write_text(comparison_json, encoding="utf-8")
    print("\n" + comparison_md)
    log.info("results written to: %s", output)

    failed = sum(1 for t in run_result.trials if t.state == "failed")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, help="run output directory")
    ap.add_argument(
        "--gitea-url", required=True, help="Gitea base URL, e.g. http://localhost:10110"
    )
    ap.add_argument("--gitea-token", required=True, help="Gitea admin token")
    ap.add_argument(
        "--trials",
        type=int,
        default=2,
        help="trials per (agent,task) pair (default: 2)",
    )
    ap.add_argument(
        "--max-parallel", type=int, default=4, help="max concurrent trials (default: 4)"
    )
    ap.add_argument("--log-level", default="INFO", help="logging level (default: INFO)")
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
