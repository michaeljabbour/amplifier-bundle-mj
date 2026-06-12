"""Design-fidelity Phase-2 — STAGE 2 scorer (RUN LATER, once MJ's form is filled).

Pipeline:
  1. Parse MJ's blind form (MJ-DESIGN-FORM.md): per Dxx -> {grit, direction,
     load-bearing concern, read}.
  2. Map Dxx -> scenario_id via config.DXX_TO_SCENARIO. The form is BLIND (no
     scenario_id, shuffled, with 4 hidden duplicates), so the mapping is VERIFIED
     here by exact title-match against scenarios_design.json. Duplicate pairs
     (S02/S05/S08/S11) are reconciled into one MJ ground-truth per scenario and
     an intra-rater reliability report is emitted.
  3. From a Stage-1 runs/<ts>/raw.jsonl, compute per scenario x arm MAJORITY
     {grit, direction, concern} over the 3 samples.
  4. Composite agreement vs MJ per scenario x arm = mean of three binary matches:
       grit-exact + direction-exact + concern-match (semantic, via an LLM grader).
     -> a score in {0, 1/3, 2/3, 1}.
  5. Report per-arm composite (mean over scenarios), plus per-dimension breakdown.
  6. HOOKS (not implemented) for the secondary A/B Bradley-Terry ranking grader.

NOTE: This script is import-safe. The only network calls are the concern-match
grader (gpt-4.1), made when run with a real MJ form + a Stage-1 raw.jsonl.

    python phase2_score.py --run runs/<ts> [--form ../MJ-DESIGN-FORM.md]
    python phase2_score.py --run runs/<ts> --no-grader   # exact-match only, no LLM
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import _bootstrap  # noqa: F401 — wires the cognition harness onto sys.path

import cache  # type: ignore
import llm  # type: ignore

from config import (
    ARMS,
    CACHE_DIR,
    DXX_TO_SCENARIO,
    GRADER_MAX_TOKENS,
    GRADER_MODEL,
    GRADER_TEMPERATURE,
    MJ_FORM_PATH,
    SCENARIOS_PATH,
    VALID_DIRECTIONS,
)

# ---------------------------------------------------------------------------
# 1. Parse MJ's blind form
# ---------------------------------------------------------------------------
_DXX_HEADER_RE = re.compile(r"^##\s+(D\d{2})\s*$", re.MULTILINE)


def _parse_field(block: str, label: str) -> str | None:
    """Grab the value after a `- <label>:` bullet, up to the next bullet/blank."""
    pat = re.compile(
        rf"^[ \t]*[-*]\s*{re.escape(label)}\s*:\s*(.*?)(?=\n[ \t]*[-*]\s*\w|\n\s*\n|\Z)",
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    m = pat.search(block)
    if not m:
        return None
    val = m.group(1).strip()
    return val or None


def _coerce_grit(raw: str | None) -> int | None:
    if raw is None:
        return None
    m = re.search(r"[0-3]", raw)
    return int(m.group(0)) if m else None


def _coerce_direction(raw: str | None) -> str | None:
    if raw is None:
        return None
    token = raw.strip().lower().replace(" ", "-").replace("_", "-")
    token = re.sub(r"-+", "-", token)
    for d in VALID_DIRECTIONS:
        if d in token:
            return d
    return None


def parse_mj_form(form_path: Path) -> dict[str, dict]:
    """Return {Dxx: {title, grit, direction, concern, read}} for every filled block."""
    text = form_path.read_text(encoding="utf-8")
    matches = list(_DXX_HEADER_RE.finditer(text))
    out: dict[str, dict] = {}
    for i, m in enumerate(matches):
        dxx = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        # The first bold line in the block is the scenario title.
        title_m = re.search(r"\*\*(.+?)\*\*", block)
        title = title_m.group(1).strip() if title_m else None
        out[dxx] = {
            "title": title,
            "grit": _coerce_grit(_parse_field(block, "grit")),
            "direction": _coerce_direction(_parse_field(block, "direction")),
            "concern": _parse_field(block, "load-bearing concern"),
            "read": _parse_field(block, "read"),
        }
    return out


# ---------------------------------------------------------------------------
# 2. Verify Dxx -> scenario_id by title, reconcile duplicates
# ---------------------------------------------------------------------------
def load_scenarios(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenarios = data["scenarios"] if isinstance(data, dict) else data
    return {s["scenario_id"]: s for s in scenarios}


def verify_mapping(mj_blocks: dict[str, dict], scenarios: dict[str, dict]) -> list[str]:
    """Cross-check config.DXX_TO_SCENARIO against the form's titles. Returns a list
    of human-readable mismatch warnings (empty == clean)."""
    warnings: list[str] = []
    for dxx, block in mj_blocks.items():
        sid = DXX_TO_SCENARIO.get(dxx)
        if sid is None:
            warnings.append(f"{dxx}: no entry in DXX_TO_SCENARIO")
            continue
        sc = scenarios.get(sid)
        if sc is None:
            warnings.append(f"{dxx}->{sid}: scenario_id not found in scenarios file")
            continue
        ftitle = (block.get("title") or "").strip().lower()
        stitle = sc["title"].strip().lower()
        if ftitle and ftitle != stitle:
            warnings.append(
                f"{dxx}->{sid}: form title {block.get('title')!r} != scenario title {sc['title']!r}"
            )
    return warnings


def reconcile_mj_truth(mj_blocks: dict[str, dict]) -> tuple[dict[str, dict], list[str]]:
    """Collapse Dxx reads to one MJ truth per scenario_id, reconciling duplicates.

    Intra-rater rule (pre-registration §4): both members of a duplicate pair must
    match on grit AND direction. A discrepancy is reported (and the FIRST read is
    used as the working truth pending an MJ re-read)."""
    by_sid: dict[str, list[tuple[str, dict]]] = {}
    for dxx in sorted(mj_blocks):
        sid = DXX_TO_SCENARIO.get(dxx)
        if sid:
            by_sid.setdefault(sid, []).append((dxx, mj_blocks[dxx]))

    truth: dict[str, dict] = {}
    reliability: list[str] = []
    for sid, reads in by_sid.items():
        first = reads[0][1]
        truth[sid] = first
        if len(reads) > 1:
            grits = {r["grit"] for _, r in reads}
            dirs = {r["direction"] for _, r in reads}
            tag = " / ".join(d for d, _ in reads)
            if len(grits) > 1 or len(dirs) > 1:
                reliability.append(
                    f"DISCREPANCY {sid} ({tag}): grit={sorted(g for g in grits if g is not None)} "
                    f"direction={sorted(d for d in dirs if d)} -> re-read needed"
                )
            else:
                reliability.append(f"OK {sid} ({tag}): duplicate reads agree")
    return truth, reliability


# ---------------------------------------------------------------------------
# 3. Per scenario x arm majority over the 3 samples
# ---------------------------------------------------------------------------
def load_raw(run_dir: Path) -> list[dict]:
    raw_path = run_dir / "raw.jsonl"
    if not raw_path.exists():
        raise FileNotFoundError(f"No raw.jsonl in {run_dir}")
    return [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _mode(values: list) -> object | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    counts = Counter(vals).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return None  # tie -> unclear
    return counts[0][0]


def majority_by_scenario_arm(records: list[dict]) -> dict[tuple[str, str], dict]:
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in records:
        groups.setdefault((r["scenario_id"], r["arm"]), []).append(r)

    out: dict[tuple[str, str], dict] = {}
    for (sid, arm), recs in groups.items():
        recs = sorted(recs, key=lambda r: r.get("sample", 0))
        maj_grit = _mode([r.get("grit") for r in recs])
        maj_dir = _mode([r.get("direction") for r in recs])
        # Representative concern: from a sample agreeing with the majority direction,
        # else the first non-null concern. (Free text has no exact-mode majority.)
        concern = None
        for r in recs:
            if r.get("direction") == maj_dir and r.get("concern"):
                concern = r["concern"]
                break
        if concern is None:
            concern = next((r["concern"] for r in recs if r.get("concern")), None)
        out[(sid, arm)] = {
            "scenario_id": sid,
            "arm": arm,
            "grit": maj_grit,
            "direction": maj_dir,
            "concern": concern,
            "n_samples": len(recs),
            "sample_grits": [r.get("grit") for r in recs],
            "sample_directions": [r.get("direction") for r in recs],
        }
    return out


# ---------------------------------------------------------------------------
# 4. Concern semantic-match grader (LLM, gpt-4.1)
# ---------------------------------------------------------------------------
CONCERN_GRADER_SYSTEM = "You are a careful classifier. You output only the requested JSON object and nothing else."
CONCERN_GRADER_TEMPLATE = (
    "Two reviewers each named the SINGLE load-bearing concern that decides a design call. "
    "Do they identify the SAME underlying decisive factor (semantically equivalent), even if "
    "worded differently?\n\n"
    "REVIEWER A (reference): «{mj_concern}»\n"
    "REVIEWER B (candidate): «{arm_concern}»\n\n"
    'Output STRICT JSON: {{"match": true|false, "reason": "<short>"}}'
)


def _parse_grader_json(text: str) -> bool:
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE
    ).strip()
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        obj = json.loads(m.group(0)) if m else {}
    return bool(obj.get("match", False))


def concern_match(
    sid: str, arm: str, mj_concern: str | None, arm_concern: str | None
) -> bool:
    if not mj_concern or not arm_concern:
        return False
    user = CONCERN_GRADER_TEMPLATE.format(
        mj_concern=mj_concern, arm_concern=arm_concern
    )
    key = cache.make_key("design_concern_grade", GRADER_MODEL, sid, arm, 0, user)
    cached = cache.get(key, cache_dir=CACHE_DIR)
    if cached is None:
        cached = llm.call_openai(
            model=GRADER_MODEL,
            system=CONCERN_GRADER_SYSTEM,
            user=user,
            temperature=GRADER_TEMPERATURE,
            max_tokens=GRADER_MAX_TOKENS,
        )
        cache.put(
            key,
            cached,
            meta={"stage": "design_concern_grade", "scenario_id": sid, "arm": arm},
            cache_dir=CACHE_DIR,
        )
    return _parse_grader_json(cached)


# ---------------------------------------------------------------------------
# 5. Composite scoring
# ---------------------------------------------------------------------------
def score(
    majorities: dict[tuple[str, str], dict],
    mj_truth: dict[str, dict],
    use_grader: bool,
) -> dict:
    per_cell: list[dict] = []
    for (sid, arm), maj in sorted(majorities.items()):
        truth = mj_truth.get(sid)
        if truth is None:
            continue
        grit_exact = int(maj["grit"] is not None and maj["grit"] == truth["grit"])
        dir_exact = int(
            maj["direction"] is not None and maj["direction"] == truth["direction"]
        )
        if use_grader:
            concern_ok = int(
                concern_match(sid, arm, truth.get("concern"), maj.get("concern"))
            )
        else:
            concern_ok = 0  # exact-match-only mode leaves concern unscored
        composite = (grit_exact + dir_exact + concern_ok) / 3.0
        per_cell.append(
            {
                "scenario_id": sid,
                "arm": arm,
                "grit_exact": grit_exact,
                "direction_exact": dir_exact,
                "concern_match": concern_ok,
                "composite": composite,
                "mj": {k: truth.get(k) for k in ("grit", "direction", "concern")},
                "arm_majority": {
                    k: maj.get(k) for k in ("grit", "direction", "concern")
                },
            }
        )

    per_arm: dict[str, dict] = {}
    for arm in ARMS:
        cells = [c for c in per_cell if c["arm"] == arm]
        if not cells:
            continue
        n = len(cells)
        per_arm[arm] = {
            "n_scenarios": n,
            "composite": sum(c["composite"] for c in cells) / n,
            "grit_exact_rate": sum(c["grit_exact"] for c in cells) / n,
            "direction_exact_rate": sum(c["direction_exact"] for c in cells) / n,
            "concern_match_rate": sum(c["concern_match"] for c in cells) / n,
        }
    return {"per_cell": per_cell, "per_arm": per_arm, "grader_used": use_grader}


# ---------------------------------------------------------------------------
# 6. A/B Bradley-Terry ranking hooks (SECONDARY — NOT IMPLEMENTED)
# ---------------------------------------------------------------------------
def assemble_ab_inputs(records: list[dict], mj_truth: dict[str, dict]) -> list[dict]:
    """HOOK: build the per-scenario bundle a blind A/B grader would rank — the 6
    arms' neutralized reads + MJ's neutralized read as the alignment reference.

    TODO (handoff): MJ's read must ALSO be voice-neutralized with the same
    neutralizer (gpt-4.1) before ranking — Stage 1 neutralizes only the arm reads.
    Add an `mj_neutralized` field per scenario before wiring this up.
    """
    raise NotImplementedError(
        "A/B assembly is a secondary, not-yet-built step. See docstring TODO: "
        "neutralize MJ's reads, then emit {scenario_id, mj_neutralized, "
        "arm_neutralized[arm]} bundles for the ranking grader."
    )


def bradley_terry_rank(ab_comparisons: list[dict]) -> dict:
    """HOOK: fit Bradley-Terry arm strengths from pairwise-decomposed A/B rankings,
    with scenario-cluster bootstrap CIs (B=2000), per the pre-registration §6.

    TODO (handoff): implement BT MLE + cluster bootstrap; report strength gaps
    MACHETE-vs-HOLISTIC and MACHETE-vs-each-sibling. This is corroborating, not
    confirmatory — the primary endpoint is the structured composite above.
    """
    raise NotImplementedError(
        "Bradley-Terry A/B ranking is a secondary step; not yet implemented."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _render_report(result: dict, reliability: list[str], warnings: list[str]) -> str:
    lines = ["# Design-fidelity Phase-2 — Stage-2 scores", ""]
    if warnings:
        lines += ["## Mapping warnings", *[f"- {w}" for w in warnings], ""]
    lines += [
        "## Intra-rater reliability (duplicates)",
        *[f"- {r}" for r in reliability],
        "",
    ]
    lines += [
        "## Per-arm composite agreement vs MJ",
        "",
        "| arm | n | composite | grit-exact | direction-exact | concern-match |",
        "|-----|---|-----------|------------|-----------------|---------------|",
    ]
    for arm in ARMS:
        a = result["per_arm"].get(arm)
        if not a:
            continue
        lines.append(
            f"| {arm} | {a['n_scenarios']} | {a['composite']:.3f} | "
            f"{a['grit_exact_rate']:.3f} | {a['direction_exact_rate']:.3f} | {a['concern_match_rate']:.3f} |"
        )
    if not result["grader_used"]:
        lines += [
            "",
            "_(--no-grader: concern-match forced to 0; composite is grit+direction only.)_",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Design-fidelity Phase-2 Stage-2 scorer.")
    ap.add_argument(
        "--run", required=True, help="Stage-1 run dir containing raw.jsonl."
    )
    ap.add_argument(
        "--form", default=str(MJ_FORM_PATH), help="MJ's filled design form."
    )
    ap.add_argument(
        "--scenarios", default=str(SCENARIOS_PATH), help="Scenario JSON path."
    )
    ap.add_argument(
        "--no-grader",
        action="store_true",
        help="Skip LLM concern grader (exact-match only).",
    )
    args = ap.parse_args(argv)

    run_dir = Path(args.run)
    form_path = Path(args.form)
    scenarios = load_scenarios(Path(args.scenarios))

    mj_blocks = parse_mj_form(form_path)
    unfilled = [
        d for d, b in mj_blocks.items() if b["grit"] is None and b["direction"] is None
    ]
    if unfilled:
        print(
            f"[WARN] {len(unfilled)} form blocks look UNFILLED ({', '.join(unfilled)}). "
            "Stage 2 is meant to run AFTER MJ fills the form.",
            file=sys.stderr,
        )

    warnings = verify_mapping(mj_blocks, scenarios)
    mj_truth, reliability = reconcile_mj_truth(mj_blocks)

    records = load_raw(run_dir)
    majorities = majority_by_scenario_arm(records)
    result = score(majorities, mj_truth, use_grader=not args.no_grader)

    (run_dir / "scores.json").write_text(
        json.dumps(
            {
                "result": result,
                "reliability": reliability,
                "mapping_warnings": warnings,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = _render_report(result, reliability, warnings)
    (run_dir / "scores.md").write_text(report, encoding="utf-8")
    print(report)
    print(
        f"Wrote {run_dir / 'scores.json'} and {run_dir / 'scores.md'}", file=sys.stderr
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
