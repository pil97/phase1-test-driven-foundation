from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .rubric import Rubric, load_rubric

MAX_ITERATIONS = 3

# These are language-level vague-only assertions, not domain/business rules.
# Matching is intentionally narrow: an assertion must normalize to one of these
# phrases to hard-fail. Concrete assertions that merely contain a vague phrase
# are left to semantic Critique/Eval.
VAGUE_ONLY_PHRASES = {
    "적절히 처리",
    "적절히 처리된다",
    "정상적으로 처리",
    "정상적으로 처리된다",
    "올바르게 처리",
    "올바르게 처리된다",
    "문제없이 처리",
    "문제없이 처리된다",
    "정상 동작한다",
    "expected behavior",
    "works correctly",
    "behaves correctly",
    "handled properly",
    "works as expected",
}


@dataclass(frozen=True)
class HarnessConfig:
    # Lifecycle configuration only.
    # Rubric scores, weights, and thresholds come from YAML.
    max_iterations: int = MAX_ITERATIONS


@dataclass
class ValidationResult:
    status: str
    failure_codes: list[str]
    details: list[dict[str, Any]]
    parsed: dict[str, Any] | None = None

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, Any]:
        result = {
            "status": self.status,
            "failure_codes": self.failure_codes,
            "details": self.details,
        }
        if self.parsed is not None:
            result["parsed"] = self.parsed
        return result


class SchemaRegistry:
    def __init__(self, schema_dir: Path | None = None) -> None:
        if schema_dir is None:
            schema_dir = Path(__file__).resolve().parents[2] / "schemas"
        self.schema_dir = schema_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, filename: str) -> dict[str, Any]:
        if filename not in self._cache:
            with (self.schema_dir / filename).open("r", encoding="utf-8") as f:
                self._cache[filename] = json.load(f)
        return self._cache[filename]

    def errors(self, filename: str, data: Any) -> list[str]:
        validator = Draft202012Validator(self.load(filename))
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        rendered: list[str] = []
        for error in errors:
            path = ".".join(str(p) for p in error.absolute_path) or "$"
            rendered.append(f"{path}: {error.message}")
        return rendered


SCHEMAS = SchemaRegistry()


def _parse_json(raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        return None, str(exc)
    if not isinstance(parsed, dict):
        return None, "top-level JSON value must be an object"
    return parsed, None


def validate_fixture(fixture: dict[str, Any]) -> ValidationResult:
    errors = SCHEMAS.errors("requirement-fixture.schema.json", fixture)
    if errors:
        return ValidationResult(
            "REJECT",
            ["FIXTURE_SCHEMA_FAILED"],
            [{"code": "FIXTURE_SCHEMA_FAILED", "errors": errors}],
        )

    requirement_ids = [item["id"] for item in fixture["requirements"]]
    if len(requirement_ids) != len(set(requirement_ids)):
        return ValidationResult(
            "REJECT",
            ["FIXTURE_DUPLICATE_REQUIREMENT_ID"],
            [{"code": "FIXTURE_DUPLICATE_REQUIREMENT_ID"}],
        )

    requirement_id_set = set(requirement_ids)
    unknown_boundary_ids = sorted(
        {
            item["requirement_id"]
            for item in fixture["required_boundaries"]
            if item["requirement_id"] not in requirement_id_set
        }
    )
    if unknown_boundary_ids:
        return ValidationResult(
            "REJECT",
            ["FIXTURE_BOUNDARY_UNKNOWN_REQUIREMENT"],
            [
                {
                    "code": "FIXTURE_BOUNDARY_UNKNOWN_REQUIREMENT",
                    "requirement_ids": unknown_boundary_ids,
                }
            ],
        )

    return ValidationResult("PASS", [], [], parsed=fixture)


def _normalize_boundary(value: str) -> str:
    # v0 deliberately performs formatting normalization only.
    # It does not parse or infer business semantics.
    return re.sub(r"\s+", "", value).casefold()


def _normalize_assertion(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"[.!?。！？]+$", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _all_candidates(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    return [*candidate.get("unit_tests", []), *candidate.get("gherkin_scenarios", [])]


def _assertion_values(candidate: dict[str, Any]) -> Iterable[tuple[str, str, str]]:
    for item in candidate.get("unit_tests", []):
        for value in item.get("expected", []):
            yield item.get("candidate_id", ""), "expected", value
    for item in candidate.get("gherkin_scenarios", []):
        for value in item.get("then", []):
            yield item.get("candidate_id", ""), "then", value


def _check_whitespace_only(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for item in candidate.get("unit_tests", []):
        cid = item.get("candidate_id", "")
        for field in ("name", "action"):
            value = item.get(field)
            if isinstance(value, str) and not value.strip():
                failures.append({"candidate_id": cid, "field": field})
        for field in ("setup", "expected"):
            for index, value in enumerate(item.get(field, [])):
                if isinstance(value, str) and not value.strip():
                    failures.append({"candidate_id": cid, "field": field, "index": index})
        for index, boundary in enumerate(item.get("boundary_conditions", [])):
            for field in ("condition", "expected"):
                value = boundary.get(field)
                if isinstance(value, str) and not value.strip():
                    failures.append(
                        {
                            "candidate_id": cid,
                            "field": f"boundary_conditions[{index}].{field}",
                        }
                    )

    for item in candidate.get("gherkin_scenarios", []):
        cid = item.get("candidate_id", "")
        value = item.get("name")
        if isinstance(value, str) and not value.strip():
            failures.append({"candidate_id": cid, "field": "name"})
        for field in ("given", "when", "then"):
            for index, value in enumerate(item.get(field, [])):
                if isinstance(value, str) and not value.strip():
                    failures.append({"candidate_id": cid, "field": field, "index": index})
        for index, boundary in enumerate(item.get("boundary_conditions", [])):
            for field in ("condition", "expected"):
                value = boundary.get(field)
                if isinstance(value, str) and not value.strip():
                    failures.append(
                        {
                            "candidate_id": cid,
                            "field": f"boundary_conditions[{index}].{field}",
                        }
                    )
    return failures


def _missing_requirement_coverage(
    fixture: dict[str, Any], candidate: dict[str, Any]
) -> list[dict[str, Any]]:
    expected = {item["id"] for item in fixture["requirements"]}
    required_kinds = set(fixture["required_candidate_kinds"])
    kind_items = {
        "unit": candidate.get("unit_tests", []),
        "gherkin": candidate.get("gherkin_scenarios", []),
    }
    failures: list[dict[str, Any]] = []
    for kind in sorted(required_kinds):
        seen = {
            rid
            for item in kind_items.get(kind, [])
            for rid in item.get("requirement_ids", [])
        }
        missing = sorted(expected - seen)
        if missing:
            failures.append({"kind": kind, "missing_requirement_ids": missing})
    return failures


def _missing_required_kinds(
    fixture: dict[str, Any], candidate: dict[str, Any]
) -> list[str]:
    available = set()
    if candidate.get("unit_tests"):
        available.add("unit")
    if candidate.get("gherkin_scenarios"):
        available.add("gherkin")
    return sorted(set(fixture["required_candidate_kinds"]) - available)


def _missing_required_boundaries(
    fixture: dict[str, Any], candidate: dict[str, Any]
) -> list[dict[str, str]]:
    kind_items = {
        "unit": candidate.get("unit_tests", []),
        "gherkin": candidate.get("gherkin_scenarios", []),
    }
    failures: list[dict[str, str]] = []
    for required in fixture["required_boundaries"]:
        required_id = required["requirement_id"]
        required_condition = _normalize_boundary(required["condition"])
        for kind in fixture["required_candidate_kinds"]:
            found = False
            for item in kind_items.get(kind, []):
                if required_id not in item.get("requirement_ids", []):
                    continue
                conditions = {
                    _normalize_boundary(boundary["condition"])
                    for boundary in item.get("boundary_conditions", [])
                }
                if required_condition in conditions:
                    found = True
                    break
            if not found:
                failures.append(
                    {
                        "kind": kind,
                        "requirement_id": required_id,
                        "condition": required["condition"],
                    }
                )
    return failures


def _duplicate_candidate_ids(candidate: dict[str, Any]) -> list[str]:
    ids = [item.get("candidate_id") for item in _all_candidates(candidate)]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for cid in ids:
        if cid in seen:
            duplicates.add(cid)
        seen.add(cid)
    return sorted(duplicates)


def _vague_only_assertions(candidate: dict[str, Any]) -> list[dict[str, str]]:
    normalized_forbidden = {_normalize_assertion(value) for value in VAGUE_ONLY_PHRASES}
    failures: list[dict[str, str]] = []
    for candidate_id, field, value in _assertion_values(candidate):
        if _normalize_assertion(value) in normalized_forbidden:
            failures.append(
                {
                    "candidate_id": candidate_id,
                    "field": field,
                    "assertion": value,
                }
            )
    return failures


def validate_candidate_data(
    fixture: dict[str, Any], candidate: dict[str, Any]
) -> ValidationResult:
    fixture_result = validate_fixture(fixture)
    if not fixture_result.passed:
        return fixture_result

    schema_errors = SCHEMAS.errors("test-candidate.schema.json", candidate)
    if schema_errors:
        return ValidationResult(
            "REJECT",
            ["CANDIDATE_SCHEMA_FAILED"],
            [{"code": "CANDIDATE_SCHEMA_FAILED", "errors": schema_errors}],
            parsed=candidate,
        )

    failure_codes: list[str] = []
    details: list[dict[str, Any]] = []

    whitespace = _check_whitespace_only(candidate)
    if whitespace:
        failure_codes.append("WHITESPACE_ONLY_FIELD")
        details.append({"code": "WHITESPACE_ONLY_FIELD", "fields": whitespace})

    duplicates = _duplicate_candidate_ids(candidate)
    if duplicates:
        failure_codes.append("DUPLICATE_CANDIDATE_ID")
        details.append({"code": "DUPLICATE_CANDIDATE_ID", "candidate_ids": duplicates})

    missing_kinds = _missing_required_kinds(fixture, candidate)
    if missing_kinds:
        failure_codes.append("MISSING_REQUIRED_CANDIDATE_KIND")
        details.append({"code": "MISSING_REQUIRED_CANDIDATE_KIND", "kinds": missing_kinds})

    missing_coverage = _missing_requirement_coverage(fixture, candidate)
    if missing_coverage:
        failure_codes.append("MISSING_REQUIREMENT_COVERAGE")
        details.append({"code": "MISSING_REQUIREMENT_COVERAGE", "missing": missing_coverage})

    missing_boundaries = _missing_required_boundaries(fixture, candidate)
    if missing_boundaries:
        failure_codes.append("MISSING_REQUIRED_BOUNDARY")
        details.append({"code": "MISSING_REQUIRED_BOUNDARY", "missing": missing_boundaries})

    vague = _vague_only_assertions(candidate)
    if vague:
        failure_codes.append("VAGUE_ONLY_EXPECTATION")
        details.append({"code": "VAGUE_ONLY_EXPECTATION", "assertions": vague})

    status = "PASS" if not failure_codes else "REJECT"
    return ValidationResult(status, failure_codes, details, parsed=candidate)


def validate_candidate_raw(fixture: dict[str, Any], raw_text: str) -> ValidationResult:
    parsed, parse_error = _parse_json(raw_text)
    if parse_error is not None:
        return ValidationResult(
            "REJECT",
            ["CANDIDATE_JSON_PARSE_FAILED"],
            [{"code": "CANDIDATE_JSON_PARSE_FAILED", "error": parse_error}],
        )
    assert parsed is not None
    return validate_candidate_data(fixture, parsed)



def validate_candidate_role_raw(
    fixture: dict[str, Any], raw_text: str, role: str
) -> ValidationResult:
    """Validate Gen/Refine output while preserving role-output taxonomy.

    Structural output-contract failures are role failures. A structurally valid
    candidate that fails deterministic quality gates keeps the candidate failure
    codes so it can be refined.
    """
    if role not in {"gen", "refine"}:
        raise ValueError("candidate-producing role must be 'gen' or 'refine'")

    result = validate_candidate_raw(fixture, raw_text)
    structural_codes = {"CANDIDATE_JSON_PARSE_FAILED", "CANDIDATE_SCHEMA_FAILED"}
    if any(code in structural_codes for code in result.failure_codes):
        role_code = "GEN_OUTPUT_INVALID" if role == "gen" else "REFINE_OUTPUT_INVALID"
        return ValidationResult(
            "REJECT",
            [role_code],
            [
                {
                    "code": role_code,
                    "underlying_failure_codes": result.failure_codes,
                    "underlying_details": result.details,
                }
            ],
        )
    return result

def _validate_role_raw(raw_text: str, schema_filename: str, failure_code: str) -> ValidationResult:
    parsed, parse_error = _parse_json(raw_text)
    if parse_error is not None:
        return ValidationResult(
            "REJECT",
            [failure_code],
            [{"code": failure_code, "stage": "parse", "error": parse_error}],
        )
    assert parsed is not None
    errors = SCHEMAS.errors(schema_filename, parsed)
    if errors:
        return ValidationResult(
            "REJECT",
            [failure_code],
            [{"code": failure_code, "stage": "schema", "errors": errors}],
            parsed=parsed,
        )
    return ValidationResult("PASS", [], [], parsed=parsed)


def validate_critique_raw(raw_text: str) -> ValidationResult:
    return _validate_role_raw(raw_text, "critique.schema.json", "CRITIQUE_OUTPUT_INVALID")


def validate_eval_raw(raw_text: str) -> ValidationResult:
    return _validate_role_raw(raw_text, "eval.schema.json", "EVAL_OUTPUT_INVALID")


def validate_decision(
    candidate_validation: ValidationResult,
    eval_validation: ValidationResult,
    rubric: Rubric | None = None,
) -> ValidationResult:
    failure_codes: list[str] = []
    details: list[dict[str, Any]] = []

    # Canonical scoring authority is the YAML rubric.
    if rubric is None:
        rubric = load_rubric()

    if not candidate_validation.passed:
        failure_codes.extend(candidate_validation.failure_codes)
        details.append(
            {
                "code": "CANDIDATE_GATE_FAILED",
                "candidate_failure_codes": candidate_validation.failure_codes,
            }
        )

    if not eval_validation.passed or eval_validation.parsed is None:
        if "EVAL_OUTPUT_INVALID" not in failure_codes:
            failure_codes.append("EVAL_OUTPUT_INVALID")
        details.append({"code": "EVAL_OUTPUT_INVALID"})
        return ValidationResult(
            "REJECT",
            _dedupe(failure_codes),
            details,
        )

    scores = {
        axis: int(eval_validation.parsed[axis]["score"])
        for axis in rubric.axis_names
    }

    weighted_scores = {
        axis: scores[axis] * rubric.axes[axis].weight
        for axis in rubric.axis_names
    }

    total = sum(weighted_scores.values())

    if total < rubric.min_total:
        failure_codes.append("EVAL_TOTAL_BELOW_MIN")
        details.append(
            {
                "code": "EVAL_TOTAL_BELOW_MIN",
                "actual": total,
                "minimum": rubric.min_total,
            }
        )

    below_axes = {
        axis: score
        for axis, score in scores.items()
        if score < rubric.min_axis
    }

    if below_axes:
        failure_codes.append("EVAL_AXIS_BELOW_MIN")
        details.append(
            {
                "code": "EVAL_AXIS_BELOW_MIN",
                "actual": below_axes,
                "minimum": rubric.min_axis,
            }
        )

    details.append(
        {
            "code": "EVAL_SCORE_SUMMARY",
            "rubric_id": rubric.rubric_id,
            "scores": scores,
            "weights": rubric.weights,
            "weighted_scores": weighted_scores,
            "computed_total": total,
            "reported_total_ignored": (
                eval_validation.parsed.get("reported_total")
            ),
        }
    )

    return ValidationResult(
        "PASS" if not failure_codes else "REJECT",
        _dedupe(failure_codes),
        details,
    )


def finalize_iteration(
    iteration: int,
    decision: ValidationResult,
    role_output_failure: str | None = None,
    config: HarnessConfig = HarnessConfig(),
) -> ValidationResult:
    if iteration < 1 or iteration > config.max_iterations:
        return ValidationResult(
            "REJECT",
            ["ITERATION_OUT_OF_RANGE"],
            [
                {
                    "code": "ITERATION_OUT_OF_RANGE",
                    "iteration": iteration,
                    "max_iterations": config.max_iterations,
                }
            ],
        )

    if role_output_failure is not None:
        # Role-output contract failures remain distinct from lifecycle exhaustion.
        return ValidationResult(
            "REJECT",
            [role_output_failure],
            [{"code": role_output_failure, "iteration": iteration}],
        )

    if decision.passed:
        return ValidationResult(
            "PASS",
            [],
            [{"code": "FINAL_PASS", "iteration": iteration}],
        )

    if iteration == config.max_iterations:
        return ValidationResult(
            "REJECT",
            _dedupe([*decision.failure_codes, "MAX_ITERATIONS_EXHAUSTED"]),
            [
                *decision.details,
                {
                    "code": "MAX_ITERATIONS_EXHAUSTED",
                    "iteration": iteration,
                    "max_iterations": config.max_iterations,
                },
            ],
        )

    return ValidationResult(
        "REJECT",
        decision.failure_codes,
        [
            *decision.details,
            {
                "code": "REFINE_REQUIRED",
                "iteration": iteration,
                "next_iteration": iteration + 1,
            },
        ],
    )


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
