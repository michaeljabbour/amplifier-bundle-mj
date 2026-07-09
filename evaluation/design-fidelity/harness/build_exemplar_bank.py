"""Build fewshot/exemplar_bank.json from MJ's 12 reads (MJ-DESIGN-FORM.md).

Parses all 16 Dxx blocks, maps Dxx -> scenario_id via config.DXX_TO_SCENARIO,
reconciles the 4 duplicate presentations (D10,D12,D14,D16) down to 12 unique
scenarios (first-occurrence wins, same logic as phase2_score.reconcile_mj_truth
-- these duplicates are IGNORED per the charter's "ignore the 4 duplicate
presentations" instruction), and merges in each scenario's quadrant
(depth, domain), artifact and question from scenarios_design.json.

Each exemplar = {scenario_id, quadrant, artifact, question, grit, direction,
concern, read}.

Usage:
    python build_exemplar_bank.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401 -- wires the cognition harness onto sys.path

from config import DXX_TO_SCENARIO, MJ_FORM_PATH, SCENARIOS_PATH

import phase2_score as p2s  # type: ignore

FEWSHOT_DIR = Path(__file__).resolve().parent.parent / "fewshot"
OUT_PATH = FEWSHOT_DIR / "exemplar_bank.json"

SCENARIO_ORDER = [f"S{i:02d}" for i in range(1, 13)]


def main() -> int:
    scenarios = p2s.load_scenarios(SCENARIOS_PATH)
    mj_blocks = p2s.parse_mj_form(MJ_FORM_PATH)
    assert len(mj_blocks) == 16, f"expected 16 Dxx blocks, got {len(mj_blocks)}"

    warnings = p2s.verify_mapping(mj_blocks, scenarios)
    if warnings:
        print("[WARN] mapping warnings:", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    else:
        print(
            "[OK] all 16 Dxx -> scenario_id mappings verified by title match.",
            file=sys.stderr,
        )

    truth, reliability = p2s.reconcile_mj_truth(mj_blocks)
    print("Intra-rater reliability (4 duplicate presentations):", file=sys.stderr)
    for r in reliability:
        print(f"  - {r}", file=sys.stderr)

    assert set(truth) == set(SCENARIO_ORDER), (
        f"expected exactly the 12 scenarios, got {sorted(truth)}"
    )

    exemplars = []
    for sid in SCENARIO_ORDER:
        sc = scenarios[sid]
        t = truth[sid]
        assert (
            t["grit"] is not None
            and t["direction"] is not None
            and t.get("concern")
            and t.get("read")
        ), f"{sid}: incomplete MJ block {t}"
        exemplars.append(
            {
                "scenario_id": sid,
                "title": sc["title"],
                "quadrant": {"depth": sc["depth"], "domain": sc["domain"]},
                "artifact": sc["artifact"],
                "question": sc["question"],
                "grit": t["grit"],
                "direction": t["direction"],
                "concern": t["concern"],
                "read": t["read"],
            }
        )

    out = {
        "source": {
            "mj_form": str(MJ_FORM_PATH),
            "scenarios": str(SCENARIOS_PATH),
            "dxx_to_scenario": DXX_TO_SCENARIO,
            "note": (
                "12 unique exemplars = MJ's 12 reads verbatim. 4 duplicate Dxx "
                "presentations (D10,D12,D14,D16) ignored per charter instruction; "
                "first-occurrence read used as the working truth for each "
                "duplicated scenario (matches phase2_score.reconcile_mj_truth)."
            ),
        },
        "reliability": reliability,
        "mapping_warnings": warnings,
        "exemplars": exemplars,
    }
    FEWSHOT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(exemplars)} exemplars).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
