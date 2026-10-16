from __future__ import annotations

import copy
import unittest
from pathlib import Path

from a5_harness.b6 import (
    B6_FULLY_AUTOMATED_GATES,
    B6_PARTIALLY_AUTOMATED_GATES,
    B6_VALIDATE_GATES,
    EVAL_NUMERIC_CRITERIA,
    decide_b6_pipeline,
    evaluate_b6_validation,
)
from a5_harness.core import SchemaRegistry
from a5_harness.rubric import load_rubric


ROOT = Path(__file__).resolve().parents[1]

RUBRIC_PATH = (
    ROOT
    / "b6"
    / "rubrics"
    / "refactoring-quality-v0.yaml"
)

B6_SCHEMAS = SchemaRegistry(ROOT / "b6" / "schemas")

TICKET_SERVICE = (
    "src/main/java/com/gritmoments/objectcraft/"
    "TicketService.java"
)
TICKET = (
    "src/main/java/com/gritmoments/objectcraft/"
    "Ticket.java"
)


def rubric():
    return load_rubric(
        RUBRIC_PATH,
        expected_axes=EVAL_NUMERIC_CRITERIA,
    )


def passing_gate_evidence() -> dict:
    return {
        "SCHEMA_CHECK": {
            "role_results": {
                "gen": "PASS",
                "critique": "PASS",
                "eval": "PASS",
            },
            "evidence_references": [
                "refactoring-gen.schema.json",
                "refactoring-critique.schema.json",
                "refactoring-eval.schema.json",
            ],
        },
        "TEST_GATE": {
            "command": "recorded-full-test-command",
            "exit_code": 0,
            "status": "PASS",
            "evidence_reference": "test-gate-evidence",
        },
        "BUILD_COMPILE_GATE": {
            "command": "recorded-build-command",
            "exit_code": 0,
            "status": "PASS",
            "evidence_reference": "build-gate-evidence",
        },
        "CHARACTERIZATION_REGRESSION_GATE": {
            "command": "recorded-characterization-command",
            "exit_code": 0,
            "status": "PASS",
            "evidence_reference":
                "characterization-gate-evidence",
        },
        "ALLOWED_DIFF_SCOPE_GATE": {
            "changed_files": [
                TICKET_SERVICE,
                TICKET,
            ],
            "approved_files": [
                TICKET_SERVICE,
                TICKET,
            ],
            "approved_expansions": [],
            "evidence_reference": "diff-scope-evidence",
        },
        "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE": {
            "changes": [],
            "evidence_reference":
                "public-contract-diff-evidence",
        },
        "UNSUPPORTED_GENERIC_CLAIM_GATE": {
            "claims": [
                {
                    "claim": "testability improved",
                    "evidence_references": [
                        "C1",
                        "V1",
                    ],
                    "support_status": "SUPPORTED",
                }
            ],
        },
        "EVIDENCE_REFERENCE_GATE": {
            "references": [
                {
                    "reference":
                        "TicketService.reserveTicket",
                    "exists": True,
                    "semantic_sufficiency":
                        "SUFFICIENT",
                },
                {
                    "reference":
                        "B1_VALID_RESERVATION",
                    "exists": True,
                    "semantic_sufficiency":
                        "SUFFICIENT",
                },
                {
                    "reference": "C1",
                    "exists": True,
                    "semantic_sufficiency":
                        "SUFFICIENT",
                },
            ],
        },
    }


def eval_output(
    scores: tuple[int, int, int, int] = (4, 4, 4, 4),
    evidence_status: str = "SUFFICIENT",
) -> dict:
    return {
        "criteria": {
            axis: {
                "score": score,
            }
            for axis, score in zip(
                EVAL_NUMERIC_CRITERIA,
                scores,
                strict=True,
            )
        },
        "evidence_sufficiency": {
            "status": evidence_status,
        },
    }


def clean_critique() -> dict:
    return {
        "schema_version": "0.1",
        "review_id": "critique-clean",
        "issues": [],
    }


class B6ValidationDecisionTests(unittest.TestCase):
    def test_frozen_gate_partition_is_exact(self):
        self.assertEqual(
            (
                "SCHEMA_CHECK",
                "TEST_GATE",
                "BUILD_COMPILE_GATE",
                "CHARACTERIZATION_REGRESSION_GATE",
                "ALLOWED_DIFF_SCOPE_GATE",
                "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE",
                "UNSUPPORTED_GENERIC_CLAIM_GATE",
                "EVIDENCE_REFERENCE_GATE",
            ),
            B6_VALIDATE_GATES,
        )

        self.assertEqual(
            B6_VALIDATE_GATES[:5],
            B6_FULLY_AUTOMATED_GATES,
        )
        self.assertEqual(
            B6_VALIDATE_GATES[5:],
            B6_PARTIALLY_AUTOMATED_GATES,
        )

    def test_positive_validation_and_final_decision_pass(self):
        validation = evaluate_b6_validation(
            "validation-positive",
            passing_gate_evidence(),
        )

        self.assertTrue(validation.passed)
        self.assertEqual(
            "PASS",
            validation.parsed["final_validation_status"],
        )
        self.assertEqual(
            8,
            len(validation.parsed["gates"]),
        )
        self.assertEqual(
            [],
            B6_SCHEMAS.errors(
                "refactoring-validation.schema.json",
                validation.parsed,
            ),
        )

        decision = decide_b6_pipeline(
            clean_critique(),
            eval_output(),
            validation,
            rubric(),
        )

        self.assertTrue(decision.passed)
        self.assertEqual([], decision.failure_codes)

        summary = decision.details[0]

        self.assertEqual("PASS", summary["decision"])
        self.assertEqual(16, summary["eval_total"])
        self.assertEqual(
            "SUFFICIENT",
            summary["evidence_sufficiency_status"],
        )
        self.assertEqual([], summary["critique_blockers"])
        self.assertEqual(
            "PASS",
            summary["validation_status"],
        )

    def test_low_total_and_low_axis_reject(self):
        validation = evaluate_b6_validation(
            "validation-score-negative",
            passing_gate_evidence(),
        )

        low_total = decide_b6_pipeline(
            clean_critique(),
            eval_output((3, 3, 3, 3)),
            validation,
            rubric(),
        )

        self.assertFalse(low_total.passed)
        self.assertIn(
            "EVAL_TOTAL_BELOW_MIN",
            low_total.failure_codes,
        )

        low_axis = decide_b6_pipeline(
            clean_critique(),
            eval_output((5, 5, 5, 2)),
            validation,
            rubric(),
        )

        self.assertFalse(low_axis.passed)
        self.assertNotIn(
            "EVAL_TOTAL_BELOW_MIN",
            low_axis.failure_codes,
        )
        self.assertIn(
            "EVAL_AXIS_BELOW_MIN",
            low_axis.failure_codes,
        )

    def test_high_score_insufficient_evidence_rejects(self):
        validation = evaluate_b6_validation(
            "validation-evidence-negative",
            passing_gate_evidence(),
        )

        decision = decide_b6_pipeline(
            clean_critique(),
            eval_output(
                (5, 5, 5, 5),
                "INSUFFICIENT",
            ),
            validation,
            rubric(),
        )

        self.assertFalse(decision.passed)
        self.assertIn(
            "B6_EVIDENCE_INSUFFICIENT",
            decision.failure_codes,
        )
        self.assertNotIn(
            "EVAL_TOTAL_BELOW_MIN",
            decision.failure_codes,
        )
        self.assertNotIn(
            "EVAL_AXIS_BELOW_MIN",
            decision.failure_codes,
        )

    def test_validation_failure_overrides_high_score(self):
        evidence = passing_gate_evidence()
        evidence[
            "CHARACTERIZATION_REGRESSION_GATE"
        ]["exit_code"] = 1
        evidence[
            "CHARACTERIZATION_REGRESSION_GATE"
        ]["status"] = "FAIL"

        validation = evaluate_b6_validation(
            "validation-regression-negative",
            evidence,
        )

        self.assertFalse(validation.passed)
        self.assertIn(
            "B6_CHARACTERIZATION_REGRESSION",
            validation.failure_codes,
        )

        decision = decide_b6_pipeline(
            clean_critique(),
            eval_output((5, 5, 5, 5)),
            validation,
            rubric(),
        )

        self.assertFalse(decision.passed)
        self.assertIn(
            "B6_CHARACTERIZATION_REGRESSION",
            decision.failure_codes,
        )

    def test_unresolved_critique_issue_is_blocker(self):
        validation = evaluate_b6_validation(
            "validation-critique-negative",
            passing_gate_evidence(),
        )

        critique = clean_critique()
        critique["issues"] = [
            {
                "id": "I1",
                "decision": "REVISE",
            }
        ]

        decision = decide_b6_pipeline(
            critique,
            eval_output((5, 5, 5, 5)),
            validation,
            rubric(),
        )

        self.assertFalse(decision.passed)
        self.assertIn(
            "B6_CRITIQUE_BLOCKER",
            decision.failure_codes,
        )
        self.assertEqual(
            ["I1"],
            decision.details[0]["critique_blockers"],
        )

    def test_approved_scope_expansion_is_not_automatic_failure(
        self,
    ):
        evidence = passing_gate_evidence()

        expansion_file = (
            "src/main/java/com/gritmoments/objectcraft/"
            "ReservationPolicy.java"
        )

        evidence[
            "ALLOWED_DIFF_SCOPE_GATE"
        ]["changed_files"].append(expansion_file)

        evidence[
            "ALLOWED_DIFF_SCOPE_GATE"
        ]["approved_expansions"] = [
            {
                "file": expansion_file,
                "approved": True,
                "justification":
                    "Observed code requires this target.",
                "evidence_reference":
                    "scope-expansion-approval",
            }
        ]

        approved = evaluate_b6_validation(
            "validation-approved-expansion",
            evidence,
        )

        self.assertTrue(approved.passed)

        evidence[
            "ALLOWED_DIFF_SCOPE_GATE"
        ]["approved_expansions"][0]["approved"] = False

        rejected = evaluate_b6_validation(
            "validation-unapproved-expansion",
            evidence,
        )

        self.assertFalse(rejected.passed)
        self.assertIn(
            "B6_DIFF_SCOPE_VIOLATION",
            rejected.failure_codes,
        )

    def test_public_contract_change_requires_approval_not_absence(
        self,
    ):
        evidence = passing_gate_evidence()

        evidence[
            "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE"
        ]["changes"] = [
            {
                "change":
                    "Ticket public method signature",
                "detected": True,
                "approved": True,
                "justification":
                    "Explicitly approved observed requirement.",
                "evidence_reference":
                    "public-contract-approval",
            }
        ]

        approved = evaluate_b6_validation(
            "validation-approved-public-change",
            evidence,
        )

        self.assertTrue(approved.passed)

        evidence[
            "UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE"
        ]["changes"][0]["approved"] = False

        rejected = evaluate_b6_validation(
            "validation-unapproved-public-change",
            evidence,
        )

        self.assertFalse(rejected.passed)
        self.assertIn(
            "B6_UNAPPROVED_PUBLIC_CONTRACT_CHANGE",
            rejected.failure_codes,
        )

    def test_generic_claim_uses_evidence_and_semantic_status(
        self,
    ):
        evidence = passing_gate_evidence()

        supported = evaluate_b6_validation(
            "validation-supported-claim",
            evidence,
        )
        self.assertTrue(supported.passed)

        evidence = copy.deepcopy(evidence)
        claim = evidence[
            "UNSUPPORTED_GENERIC_CLAIM_GATE"
        ]["claims"][0]
        claim["support_status"] = "UNSUPPORTED"

        rejected = evaluate_b6_validation(
            "validation-unsupported-claim",
            evidence,
        )

        self.assertFalse(rejected.passed)
        self.assertIn(
            "B6_UNSUPPORTED_GENERIC_CLAIM",
            rejected.failure_codes,
        )

    def test_evidence_reference_structural_and_semantic_boundaries(
        self,
    ):
        structural = passing_gate_evidence()
        structural[
            "EVIDENCE_REFERENCE_GATE"
        ]["references"][0]["exists"] = False

        structural_result = evaluate_b6_validation(
            "validation-structural-evidence-negative",
            structural,
        )

        self.assertIn(
            "B6_EVIDENCE_REFERENCE_INVALID",
            structural_result.failure_codes,
        )

        semantic = passing_gate_evidence()
        semantic[
            "EVIDENCE_REFERENCE_GATE"
        ]["references"][0][
            "semantic_sufficiency"
        ] = "INSUFFICIENT"

        semantic_result = evaluate_b6_validation(
            "validation-semantic-evidence-negative",
            semantic,
        )

        self.assertIn(
            "B6_EVIDENCE_INSUFFICIENT",
            semantic_result.failure_codes,
        )


if __name__ == "__main__":
    unittest.main()
