from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import (
    HarnessConfig,
    SCHEMAS,
    finalize_iteration,
    validate_candidate_role_raw,
    validate_critique_raw,
    validate_decision,
    validate_eval_raw,
    validate_fixture,
)
from .evidence import EvidenceStore
from .rubric import load_rubric, render_eval_rubric


@dataclass(frozen=True)
class ClaudeExecutor:
    executable: str = "claude"
    model: str | None = None

    def version(self) -> str:
        try:
            result = subprocess.run(
                [self.executable, "--version"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError:
            return "UNKNOWN"
        value = (result.stdout or result.stderr).strip()
        return value or "UNKNOWN"

    def run(self, prompt: str) -> tuple[int, str, str]:
        # Every call starts a fresh non-interactive process. We intentionally do
        # not use --continue or --resume. --safe-mode + --tools "" minimizes local
        # project/customization/tool influence; MCP tools are also denied.
        command = [
            self.executable,
            "-p",
            prompt,
            "--output-format",
            "text",
            "--max-turns",
            "1",
            "--safe-mode",
            "--tools",
            "",
            "--disallowedTools",
            "mcp__*",
        ]
        if self.model:
            command.extend(["--model", self.model])
        try:
            result = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError as exc:
            return 127, "", str(exc)
        return result.returncode, result.stdout, result.stderr


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a top-level JSON object")
    return value


def _render(template: str, **values: str) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = [part for part in rendered.split("{{")[1:] if "}}" in part]
    if unresolved:
        names = [part.split("}}", 1)[0] for part in unresolved]
        raise ValueError(f"unresolved prompt placeholders: {names}")
    return rendered


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    _write_text(path, _json_text(value) + "\n")


def _role_call(
    executor: ClaudeExecutor,
    iteration_dir: Path,
    role: str,
    prompt: str,
) -> tuple[bool, str]:
    _write_text(iteration_dir / f"{role}.prompt.txt", prompt)
    exit_code, stdout, stderr = executor.run(prompt)
    # Raw stdout is persisted exactly as received before any parse attempt.
    _write_text(iteration_dir / f"{role}.raw.txt", stdout)
    _write_text(iteration_dir / f"{role}.stderr.txt", stderr)
    _write_json(
        iteration_dir / f"{role}.provider.json",
        {"exit_code": exit_code, "fresh_process": True},
    )
    return exit_code == 0, stdout


def _schema_text(name: str) -> str:
    return _json_text(SCHEMAS.load(name))


def _store_parsed_if_valid(store: EvidenceStore, iteration: int, role: str, validation: Any) -> None:
    if validation.passed and validation.parsed is not None:
        store.write_parsed(iteration, role, validation.parsed)


def _candidate_validation_file(store: EvidenceStore, iteration: int, validation: Any) -> None:
    store.write_validation(iteration, "candidate-validation", validation.to_dict())


def _finish(
    run_dir: Path,
    run_id: str,
    status: str,
    iteration: int,
    failure_codes: list[str],
    computed_total: int | None = None,
    finding: str | None = None,
) -> int:
    final: dict[str, Any] = {
        "run_id": run_id,
        "status": status,
        "iteration": iteration,
        "failure_codes": failure_codes,
        "computed_total": computed_total,
    }
    if finding:
        final["finding"] = finding
    _write_json(run_dir / "final.json", final)
    print(_json_text(final))
    return 0 if status == "PASS" else 1


def _score_total(decision: Any) -> int | None:
    for detail in decision.details:
        if detail.get("code") == "EVAL_SCORE_SUMMARY":
            return int(detail["computed_total"])
    return None


def _provider_failure(
    run_dir: Path, run_id: str, iteration: int, role: str
) -> int:
    return _finish(
        run_dir,
        run_id,
        "REJECT",
        iteration,
        [f"{role.upper()}_PROVIDER_EXECUTION_FAILED"],
    )


def _load_prompt(root: Path, name: str) -> str:
    return (root / "prompts" / name).read_text(encoding="utf-8")


def run_pipeline(args: argparse.Namespace) -> int:
    root = args.harness_root.resolve()
    fixture = _load_json(args.fixture)
    fixture_validation = validate_fixture(fixture)
    if not fixture_validation.passed:
        print(_json_text(fixture_validation.to_dict()))
        return 2

    config = HarnessConfig()

    rubric_path = (
        args.rubric.resolve()
        if args.rubric is not None
        else root / "rubrics" / "test-quality-v0.yaml"
    )
    rubric = load_rubric(rubric_path)
    rubric_text = render_eval_rubric(rubric)

    run_id = args.run_id or (
        f"a5-3-{args.mode}-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    run_dir = (root / "runs" / run_id).resolve()
    if run_dir.exists():
        raise SystemExit(f"run directory already exists: {run_dir}")
    store = EvidenceStore(run_dir)
    store.write_top_level("input.json", fixture)

    executor = ClaudeExecutor(executable=args.claude, model=args.model)
    store.write_top_level(
        "manifest.json",
        {
            "run_id": run_id,
            "fixture_id": fixture["fixture_id"],
            "mode": args.mode,
            "provider": "claude-code-cli",
            "provider_version": executor.version(),
            "model": args.model or "UNKNOWN",
            "fresh_context_strategy": "separate claude -p process per role; no --continue/--resume",
            "max_iterations": config.max_iterations,
            "rubric_id": rubric.rubric_id,
            "rubric_path": str(rubric.source_path),
            "rubric_weights": rubric.weights,
            "min_total": rubric.min_total,
            "min_axis": rubric.min_axis,
            "live_ai_call": True,
        },
    )

    candidate_schema = _schema_text("test-candidate.schema.json")
    critique_schema = _schema_text("critique.schema.json")
    eval_schema = _schema_text("eval.schema.json")
    fixture_text = _json_text(fixture)

    candidate: dict[str, Any] | None = None
    candidate_raw: str | None = None
    pending_feedback: dict[str, Any] | None = None

    for iteration in range(1, config.max_iterations + 1):
        idir = store.iteration_dir(iteration)

        if iteration == 1 and args.mode == "semantic-negative":
            if args.initial_candidate is None:
                raise SystemExit("--initial-candidate is required for semantic-negative mode")
            candidate_raw = args.initial_candidate.read_text(encoding="utf-8")
            store.write_raw(iteration, "candidate", candidate_raw)
            candidate_validation = validate_candidate_role_raw(fixture, candidate_raw, "gen")
        elif iteration == 1:
            gen_prompt = _render(
                _load_prompt(root, "gen.md"),
                FIXTURE_JSON=fixture_text,
                CANDIDATE_SCHEMA_JSON=candidate_schema,
            )
            ok, candidate_raw = _role_call(executor, idir, "candidate", gen_prompt)
            # Mirror Gen naming in metadata while retaining candidate.raw.txt contract.
            _write_json(idir / "candidate-role.json", {"role": "Gen"})
            if not ok:
                return _provider_failure(run_dir, run_id, iteration, "gen")
            candidate_validation = validate_candidate_role_raw(fixture, candidate_raw, "gen")
        else:
            assert candidate is not None
            assert pending_feedback is not None
            refine_prompt = _render(
                _load_prompt(root, "refine.md"),
                FIXTURE_JSON=fixture_text,
                CANDIDATE_JSON=_json_text(candidate),
                CRITIQUE_JSON=_json_text(pending_feedback.get("critique")) if pending_feedback.get("critique") is not None else "null",
                EVAL_JSON=_json_text(pending_feedback.get("eval")) if pending_feedback.get("eval") is not None else "null",
                FAILURE_JSON=_json_text(pending_feedback.get("failures", {})),
                CANDIDATE_SCHEMA_JSON=candidate_schema,
            )
            ok, refine_raw = _role_call(executor, idir, "refine", refine_prompt)
            if not ok:
                return _provider_failure(run_dir, run_id, iteration, "refine")
            refine_validation = validate_candidate_role_raw(fixture, refine_raw, "refine")
            store.write_validation(iteration, "refine-validation", refine_validation.to_dict())
            if refine_validation.parsed is not None and "REFINE_OUTPUT_INVALID" not in refine_validation.failure_codes:
                store.write_parsed(iteration, "refine", refine_validation.parsed)
            if "REFINE_OUTPUT_INVALID" in refine_validation.failure_codes:
                return _finish(run_dir, run_id, "REJECT", iteration, ["REFINE_OUTPUT_INVALID"])
            # Refine output is the candidate for this iteration; preserve both role raw and candidate evidence.
            candidate_raw = refine_raw
            store.write_raw(iteration, "candidate", candidate_raw)
            candidate_validation = refine_validation

        _candidate_validation_file(store, iteration, candidate_validation)

        # Candidate parse/schema failure is a role-output contract failure, not a semantic/quality refine cycle.
        role_invalid = [
            code for code in candidate_validation.failure_codes
            if code in {"GEN_OUTPUT_INVALID", "REFINE_OUTPUT_INVALID"}
        ]
        if role_invalid:
            return _finish(run_dir, run_id, "REJECT", iteration, role_invalid)

        if candidate_validation.parsed is None:
            return _finish(run_dir, run_id, "REJECT", iteration, ["CANDIDATE_OUTPUT_INVALID"])
        candidate = candidate_validation.parsed
        # Parsed candidate is materialized after parse/schema success, even if custom deterministic gates fail.
        store.write_parsed(iteration, "candidate", candidate)

        if not candidate_validation.passed:
            decision_stub = {
                "status": "REJECT",
                "failure_codes": candidate_validation.failure_codes,
                "details": candidate_validation.details,
            }
            store.write_validation(iteration, "decision-validation", decision_stub)
            if iteration == config.max_iterations:
                return _finish(
                    run_dir,
                    run_id,
                    "REJECT",
                    iteration,
                    [*candidate_validation.failure_codes, "MAX_ITERATIONS_EXHAUSTED"],
                )
            pending_feedback = {
                "critique": None,
                "eval": None,
                "failures": decision_stub,
            }
            continue

        critique_prompt = _render(
            _load_prompt(root, "critique.md"),
            FIXTURE_JSON=fixture_text,
            CANDIDATE_JSON=_json_text(candidate),
            CRITIQUE_SCHEMA_JSON=critique_schema,
        )
        ok, critique_raw = _role_call(executor, idir, "critique", critique_prompt)
        if not ok:
            return _provider_failure(run_dir, run_id, iteration, "critique")
        critique_validation = validate_critique_raw(critique_raw)
        store.write_validation(iteration, "critique-validation", critique_validation.to_dict())
        if critique_validation.passed and critique_validation.parsed is not None:
            store.write_parsed(iteration, "critique", critique_validation.parsed)
        if not critique_validation.passed:
            return _finish(run_dir, run_id, "REJECT", iteration, ["CRITIQUE_OUTPUT_INVALID"])

        # Fresh independent evaluator receives neither Critique nor previous scores.
        eval_prompt = _render(
            _load_prompt(root, "eval.md"),
            FIXTURE_JSON=fixture_text,
            CANDIDATE_JSON=_json_text(candidate),
            EVAL_SCHEMA_JSON=eval_schema,
            RUBRIC_TEXT=rubric_text,
        )
        ok, eval_raw = _role_call(executor, idir, "eval", eval_prompt)
        if not ok:
            return _provider_failure(run_dir, run_id, iteration, "eval")
        eval_validation = validate_eval_raw(eval_raw)
        store.write_validation(iteration, "eval-validation", eval_validation.to_dict())
        if eval_validation.passed and eval_validation.parsed is not None:
            store.write_parsed(iteration, "eval", eval_validation.parsed)
        if not eval_validation.passed:
            return _finish(run_dir, run_id, "REJECT", iteration, ["EVAL_OUTPUT_INVALID"])

        decision = validate_decision(candidate_validation, eval_validation, rubric)
        store.write_validation(iteration, "decision-validation", decision.to_dict())
        total = _score_total(decision)

        if args.mode == "semantic-negative" and iteration == 1 and decision.passed:
            return _finish(
                run_dir,
                run_id,
                "REJECT",
                iteration,
                ["SEMANTIC_FALSE_ACCEPT"],
                computed_total=total,
                finding="Semantic-wrong initial candidate crossed both semantic evaluation and deterministic decision gates.",
            )

        finalized = finalize_iteration(iteration, decision, config=config)
        store.write_validation(iteration, "iteration-finalization", finalized.to_dict())
        if finalized.passed:
            return _finish(run_dir, run_id, "PASS", iteration, [], computed_total=total)
        if "MAX_ITERATIONS_EXHAUSTED" in finalized.failure_codes:
            return _finish(
                run_dir,
                run_id,
                "REJECT",
                iteration,
                finalized.failure_codes,
                computed_total=total,
            )

        pending_feedback = {
            "critique": critique_validation.parsed,
            "eval": eval_validation.parsed,
            "failures": decision.to_dict(),
        }

    return _finish(run_dir, run_id, "REJECT", config.max_iterations, ["MAX_ITERATIONS_EXHAUSTED"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A-5-3 live Claude role runner")
    parser.add_argument("--harness-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--rubric",
        type=Path,
        help="YAML rubric authority; defaults to <harness-root>/rubrics/test-quality-v0.yaml",
    )
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--mode", choices=("positive", "semantic-negative"), required=True)
    parser.add_argument("--initial-candidate", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--claude", default=os.environ.get("A5_CLAUDE_BIN", "claude"))
    parser.add_argument("--model", default=os.environ.get("A5_CLAUDE_MODEL"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if shutil.which(args.claude) is None:
        print(f"Claude CLI not found: {args.claude}", file=sys.stderr)
        return 127
    return run_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
