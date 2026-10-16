from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .b6 import (
    EVAL_NUMERIC_CRITERIA,
    decide_b6_pipeline,
    evaluate_b6_validation,
    project_critique_input,
    project_eval_input,
    project_generator_input,
)
from .core import SchemaRegistry, ValidationResult
from .evidence import EvidenceStore
from .live_runner import ClaudeExecutor, _role_call
from .rubric import load_rubric, render_eval_rubric


ROLE_SCHEMA_FILES = {
    "gen": "refactoring-gen.schema.json",
    "critique": "refactoring-critique.schema.json",
    "eval": "refactoring-eval.schema.json",
}


def _json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def _render(template: str, **values: str) -> str:
    rendered = template

    for key, value in values.items():
        rendered = rendered.replace(
            "{{" + key + "}}",
            value,
        )

    return rendered


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(value, dict):
        raise ValueError(
            f"{path} must contain a top-level JSON object"
        )

    return value


def _validate_role_raw(
    raw_text: str,
    schema_registry: SchemaRegistry,
    schema_name: str,
    invalid_code: str,
) -> ValidationResult:
    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        return ValidationResult(
            "REJECT",
            [invalid_code],
            [
                {
                    "code": invalid_code,
                    "reason": "JSON_PARSE_FAILED",
                    "error": str(exc),
                }
            ],
        )

    if not isinstance(parsed, dict):
        return ValidationResult(
            "REJECT",
            [invalid_code],
            [
                {
                    "code": invalid_code,
                    "reason": "TOP_LEVEL_JSON_NOT_OBJECT",
                }
            ],
        )

    errors = schema_registry.errors(
        schema_name,
        parsed,
    )

    if errors:
        return ValidationResult(
            "REJECT",
            [invalid_code],
            [
                {
                    "code": invalid_code,
                    "reason": "SCHEMA_VALIDATION_FAILED",
                    "errors": errors,
                }
            ],
            parsed=parsed,
        )

    return ValidationResult(
        "PASS",
        [],
        [],
        parsed=parsed,
    )


def _proposal_only_gate_evidence(
    gen_validation: ValidationResult,
    critique_validation: ValidationResult,
    eval_validation: ValidationResult,
) -> dict[str, Any]:
    """
    Connect only evidence that actually exists at proposal-only runtime.

    Code-materialization gates intentionally receive no fabricated PASS
    evidence. The frozen B-6 validator will deterministically reject those
    missing gates.
    """

    return {
        "SCHEMA_CHECK": {
            "role_results": {
                "gen": (
                    "PASS"
                    if gen_validation.passed
                    else "FAIL"
                ),
                "critique": (
                    "PASS"
                    if critique_validation.passed
                    else "FAIL"
                ),
                "eval": (
                    "PASS"
                    if eval_validation.passed
                    else "FAIL"
                ),
            },
            "evidence_references": [
                ROLE_SCHEMA_FILES["gen"],
                ROLE_SCHEMA_FILES["critique"],
                ROLE_SCHEMA_FILES["eval"],
            ],
        },
    }


def _decision_summary(
    decision: ValidationResult,
) -> dict[str, Any]:
    for detail in decision.details:
        if detail.get("code") == "B6_FINAL_DECISION":
            return detail

    return {}


def run_pipeline(
    args: argparse.Namespace,
    executor: ClaudeExecutor | None = None,
) -> int:
    root = args.harness_root.resolve()
    b6_root = root / "b6"

    fixture = _load_json(args.fixture.resolve())

    rubric_path = (
        args.rubric.resolve()
        if args.rubric is not None
        else b6_root
        / "rubrics"
        / "refactoring-quality-v0.yaml"
    )

    rubric = load_rubric(
        rubric_path,
        expected_axes=EVAL_NUMERIC_CRITERIA,
    )
    rubric_text = render_eval_rubric(rubric)

    schemas = SchemaRegistry(
        b6_root / "schemas"
    )

    run_id = args.run_id or (
        "b6-"
        + datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )

    run_dir = (root / "runs" / run_id).resolve()
    store = EvidenceStore(run_dir)

    if executor is None:
        executor = ClaudeExecutor(
            executable=args.claude,
            model=args.model,
        )

    store.write_top_level(
        "input.json",
        fixture,
    )

    store.write_top_level(
        "manifest.json",
        {
            "run_id": run_id,
            "fixture_id": fixture["fixture_id"],
            "pipeline": "B-6 Refactoring Pipeline",
            "provider": "claude-code-cli",
            "provider_version": executor.version(),
            "model": args.model or "UNKNOWN",
            "fresh_context_strategy":
                "separate claude -p process per role; "
                "no --continue/--resume",
            "live_ai_call": True,
            "canonical_run": True,
            "code_materialization": False,
            "validation_evidence_policy":
                "proposal-only; no fabricated code gate PASS",
            "rubric_id": rubric.rubric_id,
            "rubric_path": str(rubric.source_path),
            "rubric_weights": rubric.weights,
            "min_total": rubric.min_total,
            "min_axis": rubric.min_axis,
        },
    )

    iteration = 1
    idir = store.iteration_dir(iteration)

    gen_input = project_generator_input(fixture)

    gen_prompt = _render(
        (
            b6_root
            / "prompts"
            / "gen.md"
        ).read_text(encoding="utf-8"),
        GEN_INPUT_JSON=_json_text(gen_input),
        GEN_OUTPUT_SCHEMA_JSON=_json_text(
            schemas.load(
                ROLE_SCHEMA_FILES["gen"]
            )
        ),
    )

    gen_ok, gen_raw = _role_call(
        executor,
        idir,
        "gen",
        gen_prompt,
    )

    gen_validation = _validate_role_raw(
        gen_raw,
        schemas,
        ROLE_SCHEMA_FILES["gen"],
        "GEN_OUTPUT_INVALID",
    )

    store.write_validation(
        iteration,
        "gen-validation",
        gen_validation.to_dict(),
    )

    if gen_validation.parsed is not None:
        store.write_parsed(
            iteration,
            "gen",
            gen_validation.parsed,
        )

    if not gen_ok or not gen_validation.passed:
        final = {
            "run_id": run_id,
            "execution_status": "INCOMPLETE",
            "final_decision": "REJECT",
            "failure_codes": (
                ["GEN_PROVIDER_EXECUTION_FAILED"]
                if not gen_ok
                else gen_validation.failure_codes
            ),
            "completed_roles": ["gen"],
        }
        store.write_top_level("final.json", final)
        print(_json_text(final))
        return 2

    gen_proposal = gen_validation.parsed
    assert gen_proposal is not None

    critique_input = project_critique_input(
        fixture,
        gen_proposal,
    )

    critique_prompt = _render(
        (
            b6_root
            / "prompts"
            / "critique.md"
        ).read_text(encoding="utf-8"),
        CRITIQUE_INPUT_JSON=_json_text(
            critique_input
        ),
        CRITIQUE_OUTPUT_SCHEMA_JSON=_json_text(
            schemas.load(
                ROLE_SCHEMA_FILES["critique"]
            )
        ),
    )

    critique_ok, critique_raw = _role_call(
        executor,
        idir,
        "critique",
        critique_prompt,
    )

    critique_validation = _validate_role_raw(
        critique_raw,
        schemas,
        ROLE_SCHEMA_FILES["critique"],
        "CRITIQUE_OUTPUT_INVALID",
    )

    store.write_validation(
        iteration,
        "critique-validation",
        critique_validation.to_dict(),
    )

    if critique_validation.parsed is not None:
        store.write_parsed(
            iteration,
            "critique",
            critique_validation.parsed,
        )

    # Eval is deliberately independent from Critique.
    eval_input = project_eval_input(
        fixture,
        gen_proposal,
        rubric_text,
    )

    eval_prompt = _render(
        (
            b6_root
            / "prompts"
            / "eval.md"
        ).read_text(encoding="utf-8"),
        EVAL_INPUT_JSON=_json_text(eval_input),
        EVAL_SCHEMA_JSON=_json_text(
            schemas.load(
                ROLE_SCHEMA_FILES["eval"]
            )
        ),
    )

    eval_ok, eval_raw = _role_call(
        executor,
        idir,
        "eval",
        eval_prompt,
    )

    eval_validation = _validate_role_raw(
        eval_raw,
        schemas,
        ROLE_SCHEMA_FILES["eval"],
        "EVAL_OUTPUT_INVALID",
    )

    store.write_validation(
        iteration,
        "eval-validation",
        eval_validation.to_dict(),
    )

    if eval_validation.parsed is not None:
        store.write_parsed(
            iteration,
            "eval",
            eval_validation.parsed,
        )

    gate_evidence = _proposal_only_gate_evidence(
        gen_validation,
        critique_validation,
        eval_validation,
    )

    store.write_top_level(
        "gate-evidence.json",
        gate_evidence,
    )

    validation = evaluate_b6_validation(
        f"{run_id}-validation",
        gate_evidence,
    )

    store.write_validation(
        iteration,
        "b6-validation",
        validation.to_dict(),
    )

    if validation.parsed is not None:
        store.write_top_level(
            "validation.json",
            validation.parsed,
        )

    critique_output = (
        critique_validation.parsed
        if critique_validation.parsed is not None
        else {}
    )

    eval_output = (
        eval_validation.parsed
        if eval_validation.parsed is not None
        else {}
    )

    decision = decide_b6_pipeline(
        critique_output,
        eval_output,
        validation,
        rubric,
    )

    store.write_validation(
        iteration,
        "b6-final-decision",
        decision.to_dict(),
    )

    summary = _decision_summary(decision)

    issues = (
        critique_output.get("issues", [])
        if isinstance(critique_output, dict)
        else []
    )

    criteria = (
        eval_output.get("criteria", {})
        if isinstance(eval_output, dict)
        else {}
    )

    final = {
        "run_id": run_id,
        "execution_status": "COMPLETE",
        "final_decision": summary.get(
            "decision",
            decision.status,
        ),
        "failure_codes": decision.failure_codes,
        "role_execution": {
            "gen": "PASS" if gen_ok else "PROVIDER_FAIL",
            "critique": (
                "PASS"
                if critique_ok
                else "PROVIDER_FAIL"
            ),
            "eval": (
                "PASS"
                if eval_ok
                else "PROVIDER_FAIL"
            ),
        },
        "role_schema_results": {
            "gen": gen_validation.status,
            "critique": critique_validation.status,
            "eval": eval_validation.status,
        },
        "critique_issue_count": (
            len(issues)
            if isinstance(issues, list)
            else None
        ),
        "eval_scores": {
            axis: (
                criteria.get(axis, {}).get("score")
                if isinstance(
                    criteria.get(axis),
                    dict,
                )
                else None
            )
            for axis in EVAL_NUMERIC_CRITERIA
        },
        "eval_total": summary.get("eval_total"),
        "evidence_sufficiency":
            summary.get(
                "evidence_sufficiency_status"
            ),
        "validation_status":
            summary.get("validation_status"),
        "critique_blockers":
            summary.get("critique_blockers", []),
        "code_materialization": False,
    }

    runner_failures: list[str] = []

    if not critique_ok:
        runner_failures.append(
            "CRITIQUE_PROVIDER_EXECUTION_FAILED"
        )

    if not eval_ok:
        runner_failures.append(
            "EVAL_PROVIDER_EXECUTION_FAILED"
        )

    if runner_failures:
        final["runner_failure_codes"] = (
            runner_failures
        )
        final["execution_status"] = "INCOMPLETE"

    store.write_top_level(
        "final.json",
        final,
    )

    print(_json_text(final))

    # A deterministic REJECT caused by frozen B-6 gates is still a
    # completed canonical run. Provider execution failure means the
    # pipeline itself did not complete successfully.
    return 2 if runner_failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "B-6 canonical live refactoring "
            "pipeline runner"
        )
    )

    parser.add_argument(
        "--harness-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )

    parser.add_argument(
        "--fixture",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--rubric",
        type=Path,
    )

    parser.add_argument(
        "--run-id",
    )

    parser.add_argument(
        "--claude",
        default=os.environ.get(
            "A5_CLAUDE_BIN",
            "claude",
        ),
    )

    parser.add_argument(
        "--model",
        default=os.environ.get(
            "A5_CLAUDE_MODEL"
        ),
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if shutil.which(args.claude) is None:
        print(
            f"Claude CLI not found: {args.claude}",
            file=os.sys.stderr,
        )
        return 127

    return run_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
