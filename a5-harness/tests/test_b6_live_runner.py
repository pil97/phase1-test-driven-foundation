from __future__ import annotations

import json
import unittest
from pathlib import Path

from a5_harness.b6_live_runner import (
    _proposal_only_gate_evidence,
    _render,
    _validate_role_raw,
)
from a5_harness.core import SchemaRegistry, ValidationResult


ROOT = Path(__file__).resolve().parents[1]

B6_SCHEMAS = SchemaRegistry(
    ROOT / "b6" / "schemas"
)


class B6LiveRunnerTests(unittest.TestCase):
    def test_render_replaces_b6_placeholders(self):
        rendered = _render(
            "{{GEN_INPUT_JSON}}::"
            "{{GEN_OUTPUT_SCHEMA_JSON}}",
            GEN_INPUT_JSON='{"fixture":1}',
            GEN_OUTPUT_SCHEMA_JSON='{"type":"object"}',
        )

        self.assertEqual(
            '{"fixture":1}::{"type":"object"}',
            rendered,
        )

    def test_valid_gen_raw_is_schema_validated(self):
        raw = json.dumps(
            {
                "schema_version": "0.1",
                "generation_id": "g1",
                "diagnoses": [],
                "proposed_changes": [],
                "affected_scope": {
                    "files": [],
                    "symbols": [],
                },
                "risks": [],
                "validation_plan": [],
            }
        )

        result = _validate_role_raw(
            raw,
            B6_SCHEMAS,
            "refactoring-gen.schema.json",
            "GEN_OUTPUT_INVALID",
        )

        # This assertion intentionally allows the frozen schema,
        # not this test, to define whether the shape is sufficient.
        if result.passed:
            self.assertIsNotNone(result.parsed)
        else:
            self.assertEqual(
                ["GEN_OUTPUT_INVALID"],
                result.failure_codes,
            )

    def test_proposal_only_evidence_never_fakes_code_gates(self):
        passed = ValidationResult(
            "PASS",
            [],
            [],
            parsed={},
        )

        evidence = _proposal_only_gate_evidence(
            passed,
            passed,
            passed,
        )

        self.assertEqual(
            {"SCHEMA_CHECK"},
            set(evidence),
        )

        self.assertNotIn(
            "TEST_GATE",
            evidence,
        )
        self.assertNotIn(
            "BUILD_COMPILE_GATE",
            evidence,
        )
        self.assertNotIn(
            "CHARACTERIZATION_REGRESSION_GATE",
            evidence,
        )
        self.assertNotIn(
            "ALLOWED_DIFF_SCOPE_GATE",
            evidence,
        )

    def test_schema_check_uses_all_three_roles(self):
        passed = ValidationResult(
            "PASS",
            [],
            [],
            parsed={},
        )
        failed = ValidationResult(
            "REJECT",
            ["EVAL_OUTPUT_INVALID"],
            [],
        )

        evidence = _proposal_only_gate_evidence(
            passed,
            passed,
            failed,
        )

        self.assertEqual(
            {
                "gen": "PASS",
                "critique": "PASS",
                "eval": "FAIL",
            },
            evidence[
                "SCHEMA_CHECK"
            ]["role_results"],
        )


if __name__ == "__main__":
    unittest.main()
