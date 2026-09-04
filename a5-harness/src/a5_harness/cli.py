from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    HarnessConfig,
    validate_candidate_raw,
    validate_decision,
    validate_eval_raw,
    validate_fixture,
)
from .evidence import EvidenceStore
from .rubric import load_rubric


def main() -> int:
    parser = argparse.ArgumentParser(description="A-5 deterministic core fixture runner")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument(
        "--rubric",
        type=Path,
        help="YAML rubric authority; defaults to rubrics/test-quality-v0.yaml",
    )
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--eval", required=True, dest="eval_path", type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--iteration", type=int, default=1)
    args = parser.parse_args()

    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    fixture_validation = validate_fixture(fixture)
    if not fixture_validation.passed:
        print(json.dumps(fixture_validation.to_dict(), ensure_ascii=False, indent=2))
        return 2

    candidate_raw = args.candidate.read_text(encoding="utf-8")
    eval_raw = args.eval_path.read_text(encoding="utf-8")

    store = EvidenceStore(args.run_dir)
    config = HarnessConfig()

    root = Path(__file__).resolve().parents[2]
    rubric_path = (
        args.rubric.resolve()
        if args.rubric is not None
        else root / "rubrics" / "test-quality-v0.yaml"
    )
    rubric = load_rubric(rubric_path)
    store.write_top_level("input.json", fixture)
    store.write_top_level(
        "manifest.json",
        {
            "run_id": args.run_dir.name,
            "fixture_id": fixture["fixture_id"],
            "iteration": args.iteration,
            "max_iterations": config.max_iterations,
            "rubric_id": rubric.rubric_id,
            "rubric_path": str(rubric.source_path),
            "rubric_weights": rubric.weights,
            "min_total": rubric.min_total,
            "min_axis": rubric.min_axis,
            "mode": "deterministic-offline",
        },
    )
    store.write_raw(args.iteration, "candidate", candidate_raw)

    candidate_validation = validate_candidate_raw(fixture, candidate_raw)
    if candidate_validation.parsed is not None and "CANDIDATE_SCHEMA_FAILED" not in candidate_validation.failure_codes:
        # Parsed evidence is only materialized when parse + schema succeeded.
        # Custom deterministic failures do not block preserving the parsed candidate.
        store.write_parsed(args.iteration, "candidate", candidate_validation.parsed)
    store.write_validation(args.iteration, "candidate-validation", candidate_validation.to_dict())

    store.write_raw(args.iteration, "eval", eval_raw)
    eval_validation = validate_eval_raw(eval_raw)
    if eval_validation.passed and eval_validation.parsed is not None:
        store.write_parsed(args.iteration, "eval", eval_validation.parsed)

    decision = validate_decision(candidate_validation, eval_validation, rubric)
    store.write_validation(args.iteration, "decision-validation", decision.to_dict())

    score_summary = next(
        (item for item in decision.details if item.get("code") == "EVAL_SCORE_SUMMARY"),
        None,
    )
    final = {
        "run_id": args.run_dir.name,
        "status": decision.status,
        "iteration": args.iteration,
        "failure_codes": decision.failure_codes,
        "computed_total": score_summary.get("computed_total") if score_summary else None,
    }
    store.write_top_level("final.json", final)
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if decision.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
