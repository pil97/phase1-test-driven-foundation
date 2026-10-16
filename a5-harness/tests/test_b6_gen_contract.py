from __future__ import annotations

import json
import unittest
from pathlib import Path

from a5_harness.b6 import GENERATOR_INPUT_FIELDS, project_generator_input
from a5_harness.core import SchemaRegistry
from a5_harness.live_runner import _render


ROOT = Path(__file__).resolve().parents[1]

FIXTURE = json.loads(
    (
        ROOT
        / "b6"
        / "fixtures"
        / "ticket-reservation-refactoring-v0.json"
    ).read_text(encoding="utf-8")
)

PROMPT_TEMPLATE = (
    ROOT
    / "b6"
    / "prompts"
    / "gen.md"
).read_text(encoding="utf-8")

B6_SCHEMAS = SchemaRegistry(ROOT / "b6" / "schemas")


def json_text(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def valid_gen_output() -> dict:
    evidence_reference = FIXTURE["code_evidence"][0]["evidence_reference"]

    return {
        "schema_version": "0.1",
        "generation_id": "gen-example-1",
        "diagnoses": [
            {
                "id": "D1",
                "issue": "Reservation orchestration contains multiple observable responsibilities.",
                "specific_reason": (
                    "The supplied baseline evidence shows one method performing "
                    "lookup, validation, payment handling, state mutation, and persistence."
                ),
                "evidence_references": [
                    evidence_reference
                ],
            }
        ],
        "proposed_changes": [
            {
                "id": "C1",
                "description": (
                    "Make the smallest production change justified by D1 "
                    "without expanding beyond the approved target."
                ),
                "addresses_diagnosis_ids": [
                    "D1"
                ],
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                ],
                "justification": (
                    "The change is limited to the diagnosed responsibility boundary "
                    "and does not introduce speculative infrastructure."
                ),
                "behavior_preservation": (
                    "Keep B1_VALID_RESERVATION through B4_PAYMENT_FAILURE "
                    "observable outcomes unchanged."
                ),
            }
        ],
        "affected_scope": {
            "files": [
                "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                "src/main/java/com/gritmoments/objectcraft/Ticket.java",
            ],
            "symbols": [
                "TicketService.reserveTicket(long,long,String)",
                "Ticket",
            ],
            "scope_reason": (
                "These are the primary target symbols identified by the canonical fixture."
            ),
        },
        "risks": [
            {
                "id": "R1",
                "description": (
                    "Changing responsibility placement could alter reservation ordering "
                    "or payment-failure state behavior."
                ),
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                ],
                "mitigation": (
                    "Preserve the characterization-test-observed ordering and outcomes."
                ),
            }
        ],
        "validation_plan": [
            {
                "id": "V1",
                "check": (
                    "Run the existing characterization tests and confirm all four "
                    "preserved behavior cases remain unchanged."
                ),
                "validates_behavior_ids": [
                    "B1_VALID_RESERVATION",
                    "B2_MISSING_USER",
                    "B3_ALREADY_RESERVED",
                    "B4_PAYMENT_FAILURE",
                ],
                "validates_change_ids": [
                    "C1"
                ],
            }
        ],
    }


class B6GenContractTest(unittest.TestCase):
    def test_generator_projection_exposes_only_approved_fields(self) -> None:
        projection = project_generator_input(FIXTURE)

        self.assertEqual(
            set(GENERATOR_INPUT_FIELDS),
            set(projection),
        )
        self.assertEqual(
            FIXTURE["requirement"],
            projection["requirement"],
        )

        self.assertNotIn("manual_reference", projection)
        self.assertNotIn("test_evidence", projection)

    def test_rendered_gen_prompt_does_not_leak_manual_solution_markers(self) -> None:
        projection = project_generator_input(FIXTURE)

        rendered = _render(
            PROMPT_TEMPLATE,
            GEN_INPUT_JSON=json_text(projection),
            GEN_OUTPUT_SCHEMA_JSON=json_text(
                B6_SCHEMAS.load("refactoring-gen.schema.json")
            ),
        )

        manual_reference = FIXTURE["manual_reference"]

        manual_only_markers = [
            "manual_reference",
            manual_reference["end_commit"],
            "validateReservable",
            "reserveFor",
        ]

        serialized_projection = json_text(projection)

        projection_leaks = [
            marker
            for marker in manual_only_markers
            if marker in serialized_projection
        ]
        prompt_leaks = [
            marker
            for marker in manual_only_markers
            if marker in rendered
        ]

        self.assertEqual([], projection_leaks)
        self.assertEqual([], prompt_leaks)

    def test_valid_gen_output_passes_schema(self) -> None:
        errors = B6_SCHEMAS.errors(
            "refactoring-gen.schema.json",
            valid_gen_output(),
        )

        self.assertEqual([], errors)

    def test_gen_output_without_evidence_references_fails_schema(self) -> None:
        invalid = valid_gen_output()
        del invalid["diagnoses"][0]["evidence_references"]

        errors = B6_SCHEMAS.errors(
            "refactoring-gen.schema.json",
            invalid,
        )

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "evidence_references" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
