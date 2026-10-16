from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from a5_harness.b6 import CRITIQUE_INPUT_FIELDS, project_critique_input


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "b6" / "fixtures" / "ticket-reservation-refactoring-v0.json"
PROMPT_PATH = ROOT / "b6" / "prompts" / "critique.md"
SCHEMA_PATH = ROOT / "b6" / "schemas" / "refactoring-critique.schema.json"

MANUAL_ONLY_MARKERS = (
    "validateReservable",
    "reserveFor",
    "81140a1f681405ffbdedf946dd584b5b734e8e2d",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gen_proposal() -> dict:
    return {
        "schema_version": "0.1",
        "generation_id": "gen-test",
        "diagnoses": [
            {
                "id": "D1",
                "issue": "service mixes reservation validation and orchestration",
                "specific_reason": "baseline evidence shows multiple responsibilities",
                "evidence_references": ["TicketService.reserve"],
            }
        ],
        "proposed_changes": [
            {
                "id": "C1",
                "description": "move reservation-specific state validation toward Ticket",
                "addresses_diagnosis_ids": ["D1"],
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                ],
                "justification": "responsibility follows ticket state",
                "behavior_preservation": "existing externally observable reservation behavior remains unchanged",
            }
        ],
        "affected_scope": {
            "files": [
                "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                "src/main/java/com/gritmoments/objectcraft/TicketService.java",
            ],
            "symbols": ["Ticket", "TicketService"],
            "scope_reason": "limited to the current reservation responsibility boundary",
        },
        "risks": [
            {
                "id": "R1",
                "description": "reservation behavior could regress during responsibility movement",
                "affected_files": [
                    "src/main/java/com/gritmoments/objectcraft/Ticket.java",
                    "src/main/java/com/gritmoments/objectcraft/TicketService.java",
                ],
                "mitigation": "run characterization tests",
            }
        ],
        "validation_plan": [
            {
                "id": "V1",
                "check": "run existing characterization tests",
                "validates_behavior_ids": ["PB-1"],
                "validates_change_ids": ["C1"],
            }
        ],
    }


def valid_critique() -> dict:
    return {
        "schema_version": "0.1",
        "review_id": "critique-test",
        "issues": [
            {
                "id": "I1",
                "issue": "The proposed responsibility move is not fully justified by the cited evidence.",
                "evidence_references": [
                    {
                        "source": "actual_code_evidence",
                        "reference": "TicketService.reserve",
                    },
                    {
                        "source": "gen_proposal",
                        "reference": "C1",
                    },
                ],
                "risk": "Moving behavior without sufficient evidence may create an incorrect ownership boundary.",
                "decision": "REVISE",
                "reason": "The proposal should tie the ownership change to concrete state or behavior evidence.",
                "related_diagnosis_ids": ["D1"],
                "related_change_ids": ["C1"],
            }
        ],
    }


class B6CritiqueContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json(FIXTURE_PATH)
        cls.schema = load_json(SCHEMA_PATH)
        cls.validator = Draft202012Validator(cls.schema)

    def test_projection_contains_only_approved_fields(self):
        projected = project_critique_input(self.fixture, gen_proposal())

        self.assertEqual(CRITIQUE_INPUT_FIELDS, tuple(projected.keys()))
        self.assertNotIn("manual_reference", projected)
        self.assertNotIn("manual_comparison", projected)
        self.assertNotIn("final_pipeline_status", projected)
        self.assertNotIn("evaluation_result", projected)

    def test_projection_uses_required_authoritative_sources(self):
        projected = project_critique_input(self.fixture, gen_proposal())

        self.assertEqual(self.fixture["requirement"], projected["requirement"])
        self.assertEqual(self.fixture["code_evidence"], projected["actual_code_evidence"])
        self.assertEqual(self.fixture["allowed_scope"], projected["allowed_scope"])
        self.assertEqual(self.fixture["forbidden_scope"], projected["forbidden_scope"])
        self.assertEqual(self.fixture["preserved_behaviors"], projected["preserved_behavior"])
        self.assertEqual(gen_proposal(), projected["gen_proposal"])

    def test_projection_is_deep_copied(self):
        proposal = gen_proposal()
        projected = project_critique_input(self.fixture, proposal)

        projected["gen_proposal"]["generation_id"] = "mutated"
        self.assertEqual("gen-test", proposal["generation_id"])

        projected["requirement"]["_probe"] = "mutated"
        self.assertNotIn("_probe", self.fixture["requirement"])

    def test_missing_required_fixture_field_is_rejected(self):
        fixture = copy.deepcopy(self.fixture)
        fixture.pop("code_evidence")

        with self.assertRaisesRegex(
            ValueError,
            "fixture missing critique projection field",
        ):
            project_critique_input(fixture, gen_proposal())

    def test_manual_reference_does_not_leak_through_projection(self):
        projected = project_critique_input(self.fixture, gen_proposal())
        rendered = json.dumps(projected, ensure_ascii=False)

        self.assertNotIn('"manual_reference"', rendered)
        for marker in MANUAL_ONLY_MARKERS:
            self.assertNotIn(marker, rendered)

    def test_rendered_prompt_does_not_expose_manual_reference(self):
        projected = project_critique_input(self.fixture, gen_proposal())
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        rendered = (
            prompt
            .replace(
                "{{CRITIQUE_INPUT_JSON}}",
                json.dumps(projected, ensure_ascii=False, indent=2),
            )
            .replace(
                "{{CRITIQUE_OUTPUT_SCHEMA_JSON}}",
                json.dumps(self.schema, ensure_ascii=False, indent=2),
            )
        )

        self.assertNotIn("{{CRITIQUE_INPUT_JSON}}", rendered)
        self.assertNotIn("{{CRITIQUE_OUTPUT_SCHEMA_JSON}}", rendered)

        for marker in MANUAL_ONLY_MARKERS:
            self.assertNotIn(marker, rendered)

    def test_prompt_contains_frozen_review_rules(self):
        prompt = PROMPT_PATH.read_text(encoding="utf-8")

        required_rules = (
            "REVIEW_INDEPENDENTLY_FROM_GENERATOR",
            "REQUIRE_CODE_EVIDENCE",
            "REJECT_DUPLICATE_ABSTRACTION",
            "REJECT_SPECULATIVE_FUTURE_DESIGN",
            "REJECT_UNJUSTIFIED_SCOPE_EXPANSION",
            "CHECK_RESPONSIBILITY_AND_DEPENDENCY_BOUNDARIES",
            "CHECK_TESTABILITY_AND_EXTERNAL_COUPLING",
            "CHECK_BEHAVIOR_REGRESSION_AND_EDGE_CASES",
            "REQUIRE_CONCRETE_REJECTION_REASON",
        )

        for rule in required_rules:
            self.assertIn(rule, prompt)

    def test_prompt_does_not_hardcode_negative_fixture_answer(self):
        prompt = PROMPT_PATH.read_text(encoding="utf-8")

        self.assertNotIn("PaymentPort", prompt)
        self.assertNotIn("PaymentSelector", prompt)

    def test_schema_accepts_valid_handcrafted_critique(self):
        errors = list(self.validator.iter_errors(valid_critique()))
        self.assertEqual([], errors)

    def test_schema_rejects_missing_evidence_references(self):
        invalid = valid_critique()
        invalid["issues"][0].pop("evidence_references")

        errors = list(self.validator.iter_errors(invalid))
        self.assertTrue(errors)

    def test_schema_rejects_missing_reason(self):
        invalid = valid_critique()
        invalid["issues"][0].pop("reason")

        errors = list(self.validator.iter_errors(invalid))
        self.assertTrue(errors)

    def test_schema_rejects_final_pipeline_verdict_authority(self):
        invalid = valid_critique()
        invalid["final_status"] = "PASS"

        errors = list(self.validator.iter_errors(invalid))
        self.assertTrue(errors)

        invalid = valid_critique()
        invalid["final_score"] = 100

        errors = list(self.validator.iter_errors(invalid))
        self.assertTrue(errors)

    def test_empty_issue_list_is_valid_without_overall_verdict(self):
        value = {
            "schema_version": "0.1",
            "review_id": "critique-clean",
            "issues": [],
        }

        errors = list(self.validator.iter_errors(value))
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main()
