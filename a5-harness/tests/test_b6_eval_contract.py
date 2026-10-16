from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from a5_harness.b6 import (
    EVAL_INPUT_FIELDS,
    EVAL_NUMERIC_CRITERIA,
    project_eval_input,
)
from a5_harness.core import SchemaRegistry
from a5_harness.live_runner import _render
from a5_harness.rubric import load_rubric, render_eval_rubric


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
    / "eval.md"
).read_text(encoding="utf-8")

RUBRIC_PATH = (
    ROOT
    / "b6"
    / "rubrics"
    / "refactoring-quality-v0.yaml"
)

B6_SCHEMAS = SchemaRegistry(ROOT / "b6" / "schemas")
EVAL_SCHEMA = B6_SCHEMAS.load("refactoring-eval.schema.json")
EVAL_VALIDATOR = Draft202012Validator(EVAL_SCHEMA)


def json_text(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def valid_gen_proposal() -> dict:
    evidence_reference = FIXTURE["code_evidence"][0]["evidence_reference"]

    return {
        "schema_version": "0.1",
        "generation_id": "gen-eval-contract-example",
        "diagnoses": [
            {
                "id": "D1",
                "issue": (
                    "Reservation orchestration contains multiple "
                    "observable responsibilities."
                ),
                "specific_reason": (
                    "The supplied code evidence shows lookup, validation, "
                    "payment, state mutation, and persistence concerns "
                    "inside the reservation flow."
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
                    "Move only the responsibility supported by the "
                    "diagnosed reservation behavior."
                ),
                "addresses_diagnosis_ids": [
                    "D1"
                ],
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                ],
                "justification": (
                    "The change is limited to the observed responsibility "
                    "boundary and does not add speculative infrastructure."
                ),
                "behavior_preservation": (
                    "Keep B1_VALID_RESERVATION through "
                    "B4_PAYMENT_FAILURE unchanged."
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
                "The proposal remains within the approved target."
            ),
        },
        "risks": [
            {
                "id": "R1",
                "description": (
                    "Responsibility movement could alter validation or "
                    "payment-failure ordering."
                ),
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                ],
                "mitigation": (
                    "Preserve the characterization-test-observed outcomes."
                ),
            }
        ],
        "validation_plan": [
            {
                "id": "V1",
                "check": (
                    "Run the frozen characterization tests."
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


def load_b6_rubric():
    return load_rubric(
        RUBRIC_PATH,
        expected_axes=EVAL_NUMERIC_CRITERIA,
    )


def rendered_rubric() -> str:
    return render_eval_rubric(load_b6_rubric())


def valid_eval_output() -> dict:
    criterion_evidence = [
        {
            "source": "actual_code_evidence",
            "reference": "TicketService.reserveTicket",
        },
        {
            "source": "gen_proposal",
            "reference": "D1/C1",
        },
    ]

    return {
        "schema_version": "0.1",
        "evaluation_id": "eval-example-1",
        "criteria": {
            name: {
                "score": 4,
                "rationale": (
                    f"{name} is supported by the supplied evidence."
                ),
                "evidence_references": copy.deepcopy(
                    criterion_evidence
                ),
            }
            for name in EVAL_NUMERIC_CRITERIA
        },
        "evidence_sufficiency": {
            "status": "SUFFICIENT",
            "rationale": (
                "The supplied code evidence, preserved behavior, "
                "scope, and proposal are sufficient for the evaluation."
            ),
            "evidence_references": [
                {
                    "source": "actual_code_evidence",
                    "reference": "TicketService.reserveTicket",
                },
                {
                    "source": "preserved_behavior",
                    "reference": "B1_VALID_RESERVATION",
                },
            ],
        },
    }


def schema_errors(value: dict) -> list:
    return sorted(
        EVAL_VALIDATOR.iter_errors(value),
        key=lambda error: [str(part) for part in error.path],
    )


class B6EvalContractTests(unittest.TestCase):

    def test_eval_rubric_has_exact_frozen_numeric_criteria(self) -> None:
        rubric = load_b6_rubric()

        self.assertEqual(
            EVAL_NUMERIC_CRITERIA,
            rubric.axis_names,
        )
        self.assertEqual(4, len(rubric.axes))
        self.assertEqual(16, rubric.min_total)
        self.assertEqual(3, rubric.min_axis)

        for axis in rubric.axes.values():
            self.assertEqual(1, axis.weight)
            self.assertEqual(1, axis.score_min)
            self.assertEqual(5, axis.score_max)

        self.assertNotIn(
            "EVIDENCE_SUFFICIENCY",
            rubric.axes,
        )

    def test_eval_projection_contains_only_allowed_fields(self) -> None:
        projection = project_eval_input(
            FIXTURE,
            valid_gen_proposal(),
            rendered_rubric(),
        )

        self.assertEqual(
            EVAL_INPUT_FIELDS,
            tuple(projection.keys()),
        )

        self.assertEqual(
            FIXTURE["requirement"],
            projection["requirement"],
        )
        self.assertEqual(
            FIXTURE["code_evidence"],
            projection["actual_code_evidence"],
        )
        self.assertEqual(
            FIXTURE["preserved_behaviors"],
            projection["preserved_behavior"],
        )
        self.assertEqual(
            FIXTURE["allowed_scope"],
            projection["allowed_scope"],
        )
        self.assertEqual(
            FIXTURE["forbidden_scope"],
            projection["forbidden_scope"],
        )

    def test_eval_projection_rejects_missing_required_fixture_evidence(self) -> None:
        fixture = copy.deepcopy(FIXTURE)
        fixture.pop("code_evidence")

        with self.assertRaises(ValueError):
            project_eval_input(
                fixture,
                valid_gen_proposal(),
                rendered_rubric(),
            )

    def test_critique_previous_eval_and_desired_status_are_not_exposed(self) -> None:
        fixture = copy.deepcopy(FIXTURE)

        sentinels = (
            "FORBIDDEN_CRITIQUE_SENTINEL",
            "FORBIDDEN_PREVIOUS_EVAL_SENTINEL",
            "FORBIDDEN_DESIRED_PASS_SENTINEL",
        )

        fixture["critique_output"] = {
            "value": sentinels[0]
        }
        fixture["previous_eval"] = {
            "value": sentinels[1]
        }
        fixture["desired_pass_status"] = sentinels[2]

        projection = project_eval_input(
            fixture,
            valid_gen_proposal(),
            rendered_rubric(),
        )
        serialized = json_text(projection)

        for sentinel in sentinels:
            self.assertNotIn(sentinel, serialized)

    def test_manual_reference_is_not_exposed_to_eval(self) -> None:
        fixture = copy.deepcopy(FIXTURE)

        manual_markers = (
            "validateReservable",
            "reserveFor",
            "81140a1f681405ffbdedf946dd584b5b734e8e2d",
        )

        fixture["manual_reference"] = {
            "markers": list(manual_markers)
        }

        projection = project_eval_input(
            fixture,
            valid_gen_proposal(),
            rendered_rubric(),
        )

        prompt = _render(
            PROMPT_TEMPLATE,
            EVAL_INPUT_JSON=json_text(projection),
            EVAL_SCHEMA_JSON=json_text(EVAL_SCHEMA),
        )

        for marker in manual_markers:
            self.assertNotIn(marker, json_text(projection))
            self.assertNotIn(marker, prompt)

    def test_eval_prompt_renders_independent_input_rubric_and_schema(self) -> None:
        projection = project_eval_input(
            FIXTURE,
            valid_gen_proposal(),
            rendered_rubric(),
        )

        prompt = _render(
            PROMPT_TEMPLATE,
            EVAL_INPUT_JSON=json_text(projection),
            EVAL_SCHEMA_JSON=json_text(EVAL_SCHEMA),
        )

        self.assertNotIn("{{EVAL_INPUT_JSON}}", prompt)
        self.assertNotIn("{{EVAL_SCHEMA_JSON}}", prompt)

        for criterion in EVAL_NUMERIC_CRITERIA:
            self.assertIn(criterion, prompt)

        self.assertIn(
            "EVIDENCE_SUFFICIENCY is not a numeric criterion",
            prompt,
        )
        self.assertIn(
            "Do not make the final pipeline PASS/REJECT decision",
            prompt,
        )

    def test_eval_schema_positive_output_passes(self) -> None:
        self.assertEqual(
            [],
            schema_errors(valid_eval_output()),
        )

    def test_eval_schema_rejects_missing_numeric_criterion(self) -> None:
        invalid = valid_eval_output()
        invalid["criteria"].pop(
            "TESTABILITY_IMPROVEMENT"
        )

        self.assertTrue(schema_errors(invalid))

    def test_eval_schema_rejects_missing_rationale(self) -> None:
        invalid = valid_eval_output()
        invalid["criteria"]["DIAGNOSIS_ACCURACY"].pop(
            "rationale"
        )

        self.assertTrue(schema_errors(invalid))

    def test_eval_schema_rejects_missing_evidence_references(self) -> None:
        invalid = valid_eval_output()
        invalid["criteria"]["CHANGE_MINIMALITY"].pop(
            "evidence_references"
        )

        self.assertTrue(schema_errors(invalid))

    def test_evidence_sufficiency_cannot_be_fifth_numeric_axis(self) -> None:
        invalid = valid_eval_output()
        invalid["criteria"]["EVIDENCE_SUFFICIENCY"] = {
            "score": 5,
            "rationale": "Incorrect fifth numeric axis.",
            "evidence_references": [
                {
                    "source": "actual_code_evidence",
                    "reference": "TicketService.reserveTicket",
                }
            ],
        }

        self.assertTrue(schema_errors(invalid))

    def test_eval_schema_rejects_final_pipeline_verdict(self) -> None:
        for field, value in (
            ("final_pipeline_status", "PASS"),
            ("final_decision", "PASS"),
            ("approved", True),
            ("deployment_status", "READY"),
        ):
            with self.subTest(field=field):
                invalid = valid_eval_output()
                invalid[field] = value
                self.assertTrue(schema_errors(invalid))


if __name__ == "__main__":
    unittest.main()
