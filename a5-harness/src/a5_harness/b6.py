from __future__ import annotations

from copy import deepcopy
from typing import Any

from a5_harness.core import ValidationResult


GENERATOR_INPUT_FIELDS = (
    "schema_version",
    "fixture_id",
    "baseline",
    "requirement",
    "target_scope",
    "context_scope",
    "current_code_evidence",
    "preserved_behavior",
    "allowed_scope",
    "forbidden_scope",
    "evaluation_criteria",
)


def project_generator_input(fixture: dict[str, Any]) -> dict[str, Any]:
    """Return only the canonical B-6 fields that Gen is allowed to observe."""

    source_fields = {
        "schema_version": "schema_version",
        "fixture_id": "fixture_id",
        "baseline": "baseline",
        "requirement": "requirement",
        "target_scope": "target_scope",
        "context_scope": "context_scope",
        "current_code_evidence": "code_evidence",
        "preserved_behavior": "preserved_behaviors",
        "allowed_scope": "allowed_scope",
        "forbidden_scope": "forbidden_scope",
        "evaluation_criteria": "evaluation_criteria",
    }

    missing = [
        source
        for source in source_fields.values()
        if source not in fixture
    ]
    if missing:
        raise ValueError(
            "fixture missing generator projection field(s): "
            + ", ".join(sorted(missing))
        )

    return {
        target: deepcopy(fixture[source])
        for target, source in source_fields.items()
    }


CRITIQUE_INPUT_FIELDS = (
    "requirement",
    "actual_code_evidence",
    "gen_proposal",
    "allowed_scope",
    "forbidden_scope",
    "preserved_behavior",
)


def project_critique_input(
    fixture: dict[str, Any],
    gen_proposal: dict[str, Any],
) -> dict[str, Any]:
    """Return only the canonical B-6 fields that Critique is allowed to observe."""

    source_fields = {
        "requirement": "requirement",
        "actual_code_evidence": "code_evidence",
        "allowed_scope": "allowed_scope",
        "forbidden_scope": "forbidden_scope",
        "preserved_behavior": "preserved_behaviors",
    }

    missing = [
        source
        for source in source_fields.values()
        if source not in fixture
    ]
    if missing:
        raise ValueError(
            "fixture missing critique projection field(s): "
            + ", ".join(sorted(missing))
        )

    return {
        "requirement": deepcopy(fixture["requirement"]),
        "actual_code_evidence": deepcopy(fixture["code_evidence"]),
        "gen_proposal": deepcopy(gen_proposal),
        "allowed_scope": deepcopy(fixture["allowed_scope"]),
        "forbidden_scope": deepcopy(fixture["forbidden_scope"]),
        "preserved_behavior": deepcopy(fixture["preserved_behaviors"]),
    }

EVAL_NUMERIC_CRITERIA = (
    "DIAGNOSIS_ACCURACY",
    "CHANGE_MINIMALITY",
    "BEHAVIOR_PRESERVATION_RISK",
    "TESTABILITY_IMPROVEMENT",
)


EVAL_INPUT_FIELDS = (
    "requirement",
    "actual_code_evidence",
    "gen_proposal",
    "preserved_behavior",
    "allowed_scope",
    "forbidden_scope",
    "evaluation_rubric",
)


def project_eval_input(
    fixture: dict[str, Any],
    gen_proposal: dict[str, Any],
    evaluation_rubric: str,
) -> dict[str, Any]:
    """Return only the canonical B-6 fields that Eval is allowed to observe."""

    source_fields = {
        "requirement": "requirement",
        "actual_code_evidence": "code_evidence",
        "preserved_behavior": "preserved_behaviors",
        "allowed_scope": "allowed_scope",
        "forbidden_scope": "forbidden_scope",
    }

    missing = [
        source
        for source in source_fields.values()
        if source not in fixture
    ]
    if missing:
        raise ValueError(
            "fixture missing eval projection field(s): "
            + ", ".join(sorted(missing))
        )

    if not isinstance(gen_proposal, dict):
        raise ValueError("gen_proposal must be a mapping")

    if not isinstance(evaluation_rubric, str) or not evaluation_rubric.strip():
        raise ValueError("evaluation_rubric must be a non-empty string")

    return {
        "requirement": deepcopy(fixture["requirement"]),
        "actual_code_evidence": deepcopy(fixture["code_evidence"]),
        "gen_proposal": deepcopy(gen_proposal),
        "preserved_behavior": deepcopy(fixture["preserved_behaviors"]),
        "allowed_scope": deepcopy(fixture["allowed_scope"]),
        "forbidden_scope": deepcopy(fixture["forbidden_scope"]),
        "evaluation_rubric": evaluation_rubric.strip(),
    }

B6_VALIDATE_GATES = (
    "SCHEMA_CHECK",
    "TEST_GATE",
    "BUILD_COMPILE_GATE",
    "CHARACTERIZATION_REGRESSION_GATE",
    "ALLOWED_DIFF_SCOPE_GATE",
    "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE",
    "UNSUPPORTED_GENERIC_CLAIM_GATE",
    "EVIDENCE_REFERENCE_GATE",
)

B6_FULLY_AUTOMATED_GATES = (
    "SCHEMA_CHECK",
    "TEST_GATE",
    "BUILD_COMPILE_GATE",
    "CHARACTERIZATION_REGRESSION_GATE",
    "ALLOWED_DIFF_SCOPE_GATE",
)

B6_PARTIALLY_AUTOMATED_GATES = (
    "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE",
    "UNSUPPORTED_GENERIC_CLAIM_GATE",
    "EVIDENCE_REFERENCE_GATE",
)


def _b6_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _b6_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _b6_dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _evaluate_b6_gate(
    gate_name: str,
    evidence: dict[str, Any],
) -> tuple[str, list[str], list[str], list[str]]:
    failure_codes: list[str] = []
    failure_reasons: list[str] = []
    evidence_references: list[str] = []

    if gate_name == "SCHEMA_CHECK":
        role_results = evidence.get("role_results")
        evidence_references = _b6_strings(
            evidence.get("evidence_references")
        )

        required_roles = ("gen", "critique", "eval")
        roles_pass = (
            isinstance(role_results, dict)
            and all(
                role_results.get(role) == "PASS"
                for role in required_roles
            )
        )

        if not roles_pass or not evidence_references:
            failure_codes.append("B6_SCHEMA_INVALID")
            failure_reasons.append(
                "Gen, Critique, and Eval schema results must all PASS "
                "with schema evidence references."
            )

    elif gate_name in {
        "TEST_GATE",
        "BUILD_COMPILE_GATE",
        "CHARACTERIZATION_REGRESSION_GATE",
    }:
        code_by_gate = {
            "TEST_GATE": "B6_TEST_FAILED",
            "BUILD_COMPILE_GATE": "B6_BUILD_FAILED",
            "CHARACTERIZATION_REGRESSION_GATE":
                "B6_CHARACTERIZATION_REGRESSION",
        }

        command = _b6_text(evidence.get("command"))
        evidence_reference = _b6_text(
            evidence.get("evidence_reference")
        )

        if evidence_reference:
            evidence_references.append(evidence_reference)

        passed = (
            command
            and evidence.get("exit_code") == 0
            and evidence.get("status") == "PASS"
            and evidence_reference
        )

        if not passed:
            failure_codes.append(code_by_gate[gate_name])
            failure_reasons.append(
                f"{gate_name} requires command, exit_code=0, "
                "status=PASS, and an evidence reference."
            )

    elif gate_name == "ALLOWED_DIFF_SCOPE_GATE":
        changed_files = _b6_strings(
            evidence.get("changed_files")
        )
        approved_files = set(
            _b6_strings(evidence.get("approved_files"))
        )
        evidence_reference = _b6_text(
            evidence.get("evidence_reference")
        )

        if evidence_reference:
            evidence_references.append(evidence_reference)

        valid_expansions: set[str] = set()

        expansions = evidence.get("approved_expansions", [])
        if isinstance(expansions, list):
            for expansion in expansions:
                if not isinstance(expansion, dict):
                    continue

                file_name = _b6_text(expansion.get("file"))
                justification = _b6_text(
                    expansion.get("justification")
                )
                expansion_evidence = _b6_text(
                    expansion.get("evidence_reference")
                )

                if expansion_evidence:
                    evidence_references.append(expansion_evidence)

                if (
                    file_name
                    and expansion.get("approved") is True
                    and justification
                    and expansion_evidence
                ):
                    valid_expansions.add(file_name)

        violations = [
            file_name
            for file_name in changed_files
            if file_name not in approved_files
            and file_name not in valid_expansions
        ]

        if violations or not evidence_reference:
            failure_codes.append("B6_DIFF_SCOPE_VIOLATION")

            if violations:
                failure_reasons.append(
                    "Unapproved changed file(s): "
                    + ", ".join(violations)
                )

            if not evidence_reference:
                failure_reasons.append(
                    "Diff-scope evidence reference is required."
                )

    elif gate_name == "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE":
        evidence_reference = _b6_text(
            evidence.get("evidence_reference")
        )

        if evidence_reference:
            evidence_references.append(evidence_reference)

        changes = evidence.get("changes", [])
        invalid_changes: list[str] = []

        if not isinstance(changes, list):
            changes = []
            invalid_changes.append("changes")

        for index, change in enumerate(changes):
            if not isinstance(change, dict):
                invalid_changes.append(f"change[{index}]")
                continue

            if change.get("detected") is not True:
                continue

            justification = _b6_text(
                change.get("justification")
            )
            change_evidence = _b6_text(
                change.get("evidence_reference")
            )

            if change_evidence:
                evidence_references.append(change_evidence)

            if (
                change.get("approved") is not True
                or not justification
                or not change_evidence
            ):
                invalid_changes.append(
                    _b6_text(change.get("change"))
                    or f"change[{index}]"
                )

        if invalid_changes or not evidence_reference:
            failure_codes.append(
                "B6_UNAPPROVED_PUBLIC_CONTRACT_CHANGE"
            )

            if invalid_changes:
                failure_reasons.append(
                    "Detected public contract change lacks explicit "
                    "approval, justification, or evidence: "
                    + ", ".join(invalid_changes)
                )

            if not evidence_reference:
                failure_reasons.append(
                    "Public-contract evidence reference is required."
                )

    elif gate_name == "UNSUPPORTED_GENERIC_CLAIM_GATE":
        claims = evidence.get("claims", [])
        unsupported: list[str] = []

        if not isinstance(claims, list):
            claims = []
            unsupported.append("claims")

        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                unsupported.append(f"claim[{index}]")
                continue

            claim_text = _b6_text(claim.get("claim"))
            refs = _b6_strings(
                claim.get("evidence_references")
            )
            evidence_references.extend(refs)

            if (
                not claim_text
                or not refs
                or claim.get("support_status") != "SUPPORTED"
            ):
                unsupported.append(
                    claim_text or f"claim[{index}]"
                )

        if unsupported:
            failure_codes.append(
                "B6_UNSUPPORTED_GENERIC_CLAIM"
            )
            failure_reasons.append(
                "Claim(s) lack evidence-backed semantic support: "
                + ", ".join(unsupported)
            )

    elif gate_name == "EVIDENCE_REFERENCE_GATE":
        references = evidence.get("references", [])

        invalid_references: list[str] = []
        insufficient_references: list[str] = []

        if not isinstance(references, list) or not references:
            invalid_references.append("references")
            references = []

        for index, reference in enumerate(references):
            if not isinstance(reference, dict):
                invalid_references.append(
                    f"reference[{index}]"
                )
                continue

            ref = _b6_text(reference.get("reference"))

            if ref:
                evidence_references.append(ref)

            if not ref or reference.get("exists") is not True:
                invalid_references.append(
                    ref or f"reference[{index}]"
                )
                continue

            if (
                reference.get("semantic_sufficiency")
                != "SUFFICIENT"
            ):
                insufficient_references.append(ref)

        if invalid_references:
            failure_codes.append(
                "B6_EVIDENCE_REFERENCE_INVALID"
            )
            failure_reasons.append(
                "Evidence reference(s) failed structural existence "
                "checking: "
                + ", ".join(invalid_references)
            )

        if insufficient_references:
            failure_codes.append(
                "B6_EVIDENCE_INSUFFICIENT"
            )
            failure_reasons.append(
                "Evidence reference(s) exist structurally but were "
                "semantically insufficient: "
                + ", ".join(insufficient_references)
            )

    else:
        raise ValueError(
            f"unsupported B-6 validation gate: {gate_name}"
        )

    status = "PASS" if not failure_codes else "FAIL"

    return (
        status,
        _b6_dedupe(failure_codes),
        failure_reasons,
        _b6_dedupe(evidence_references),
    )


def evaluate_b6_validation(
    validation_id: str,
    gate_evidence: dict[str, Any],
) -> ValidationResult:
    """Evaluate the frozen eight B-6 validation gates deterministically."""

    if not _b6_text(validation_id):
        raise ValueError("validation_id must be a non-empty string")

    if not isinstance(gate_evidence, dict):
        raise ValueError("gate_evidence must be a mapping")

    gates: list[dict[str, Any]] = []
    aggregate_failure_codes: list[str] = []

    for gate_name in B6_VALIDATE_GATES:
        evidence = gate_evidence.get(gate_name, {})

        if not isinstance(evidence, dict):
            evidence = {}

        (
            status,
            failure_codes,
            failure_reasons,
            evidence_references,
        ) = _evaluate_b6_gate(
            gate_name,
            evidence,
        )

        gates.append(
            {
                "gate_name": gate_name,
                "status": status,
                "failure_codes": failure_codes,
                "failure_reasons": failure_reasons,
                "evidence_references": evidence_references,
            }
        )

        aggregate_failure_codes.extend(failure_codes)

    failed_gates = [
        gate["gate_name"]
        for gate in gates
        if gate["status"] == "FAIL"
    ]

    final_validation_status = (
        "PASS" if not failed_gates else "FAIL"
    )

    output = {
        "validation_id": validation_id,
        "gates": gates,
        "final_validation_status": final_validation_status,
    }

    return ValidationResult(
        "PASS"
        if final_validation_status == "PASS"
        else "REJECT",
        _b6_dedupe(aggregate_failure_codes),
        [
            {
                "code": "B6_VALIDATION_SUMMARY",
                "final_validation_status":
                    final_validation_status,
                "failed_gates": failed_gates,
            }
        ],
        parsed=output,
    )


def decide_b6_pipeline(
    critique_output: dict[str, Any],
    eval_output: dict[str, Any],
    validation: ValidationResult,
    rubric: Any,
) -> ValidationResult:
    """Return the final deterministic B-6 PASS/REJECT decision."""

    failure_codes: list[str] = []

    validation_status = "FAIL"

    if isinstance(validation.parsed, dict):
        validation_status = validation.parsed.get(
            "final_validation_status",
            "FAIL",
        )

    if not validation.passed or validation_status != "PASS":
        if validation.failure_codes:
            failure_codes.extend(validation.failure_codes)
        else:
            failure_codes.append("B6_SCHEMA_INVALID")

    evidence_sufficiency_status = "INSUFFICIENT"

    if isinstance(eval_output, dict):
        sufficiency = eval_output.get(
            "evidence_sufficiency",
            {},
        )
        if isinstance(sufficiency, dict):
            evidence_sufficiency_status = sufficiency.get(
                "status",
                "INSUFFICIENT",
            )

    if evidence_sufficiency_status != "SUFFICIENT":
        failure_codes.append("B6_EVIDENCE_INSUFFICIENT")

    eval_total: int | None = None
    eval_axis_status: dict[str, str] = {}
    eval_shape_valid = True
    scores: dict[str, int] = {}

    criteria = (
        eval_output.get("criteria")
        if isinstance(eval_output, dict)
        else None
    )

    if not isinstance(criteria, dict):
        eval_shape_valid = False
    else:
        for axis_name in rubric.axis_names:
            criterion = criteria.get(axis_name)

            if not isinstance(criterion, dict):
                eval_shape_valid = False
                continue

            score = criterion.get("score")

            if (
                not isinstance(score, int)
                or isinstance(score, bool)
            ):
                eval_shape_valid = False
                continue

            scores[axis_name] = score

    if not eval_shape_valid or len(scores) != len(
        rubric.axis_names
    ):
        failure_codes.append("B6_SCHEMA_INVALID")
    else:
        eval_total = sum(
            scores[axis_name]
            * rubric.axes[axis_name].weight
            for axis_name in rubric.axis_names
        )

        eval_axis_status = {
            axis_name: (
                "PASS"
                if scores[axis_name] >= rubric.min_axis
                else "FAIL"
            )
            for axis_name in rubric.axis_names
        }

        if eval_total < rubric.min_total:
            failure_codes.append("EVAL_TOTAL_BELOW_MIN")

        if any(
            status == "FAIL"
            for status in eval_axis_status.values()
        ):
            failure_codes.append("EVAL_AXIS_BELOW_MIN")

    critique_blockers: list[str] = []

    issues = (
        critique_output.get("issues")
        if isinstance(critique_output, dict)
        else None
    )

    if not isinstance(issues, list):
        failure_codes.append("B6_SCHEMA_INVALID")
    else:
        for index, issue in enumerate(issues):
            if not isinstance(issue, dict):
                failure_codes.append("B6_SCHEMA_INVALID")
                continue

            if issue.get("decision") in {
                "REJECT",
                "REVISE",
            }:
                critique_blockers.append(
                    _b6_text(issue.get("id"))
                    or f"issue[{index}]"
                )

    if critique_blockers:
        failure_codes.append("B6_CRITIQUE_BLOCKER")

    failure_codes = _b6_dedupe(failure_codes)
    decision = "PASS" if not failure_codes else "REJECT"

    return ValidationResult(
        decision,
        failure_codes,
        [
            {
                "code": "B6_FINAL_DECISION",
                "decision": decision,
                "eval_total": eval_total,
                "eval_axis_status": eval_axis_status,
                "evidence_sufficiency_status":
                    evidence_sufficiency_status,
                "critique_blockers": critique_blockers,
                "validation_status": validation_status,
            }
        ],
    )

