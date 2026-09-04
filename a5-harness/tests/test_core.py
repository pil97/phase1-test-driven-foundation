from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from a5_harness.core import (
    HarnessConfig,
    MAX_ITERATIONS,
    finalize_iteration,
    validate_candidate_raw,
    validate_candidate_role_raw,
    validate_critique_raw,
    validate_decision,
    validate_eval_raw,
)
from a5_harness.evidence import EvidenceStore

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "fixtures" / "seat-hold-v0.json").read_text(encoding="utf-8"))


def positive_candidate() -> dict:
    return {
        "schema_version": "0.1",
        "candidate_set_id": "candidate-positive",
        "unit_tests": [
            {
                "candidate_id": "UT-1",
                "kind": "unit",
                "requirement_ids": ["R1"],
                "name": "available seat hold succeeds",
                "setup": ["좌석 상태는 AVAILABLE이다."],
                "action": "좌석 HOLD를 요청한다.",
                "expected": ["HOLD 요청이 성공한다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "UT-2",
                "kind": "unit",
                "requirement_ids": ["R2"],
                "name": "active held seat rejects re-hold",
                "setup": ["좌석 상태는 HELD이고 현재 시각은 expiresAt보다 이르다."],
                "action": "재-HOLD를 요청한다.",
                "expected": ["재-HOLD 요청이 거절된다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "UT-3",
                "kind": "unit",
                "requirement_ids": ["R3"],
                "name": "expired held seat permits re-hold",
                "setup": ["좌석의 기존 HOLD가 만료된 상태다."],
                "action": "재-HOLD를 요청한다.",
                "expected": ["재-HOLD 요청이 허용된다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "UT-4",
                "kind": "unit",
                "requirement_ids": ["R4"],
                "name": "exact expiration boundary permits re-hold",
                "setup": ["좌석 상태는 HELD이다."],
                "action": "expiresAt과 같은 현재 시각에 재-HOLD를 요청한다.",
                "expected": ["재-HOLD 요청이 허용된다."],
                "boundary_conditions": [
                    {"condition": "now==expiresAt", "expected": "기존 HOLD는 만료 상태다."}
                ],
            },
        ],
        "gherkin_scenarios": [
            {
                "candidate_id": "GH-1",
                "kind": "gherkin",
                "requirement_ids": ["R1"],
                "name": "AVAILABLE 좌석 HOLD",
                "given": ["좌석이 AVAILABLE 상태이다."],
                "when": ["사용자가 HOLD를 요청한다."],
                "then": ["HOLD 요청이 성공한다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "GH-2",
                "kind": "gherkin",
                "requirement_ids": ["R2"],
                "name": "유효 HOLD 재요청 거절",
                "given": ["좌석은 HELD 상태이고 현재 시각은 expiresAt보다 이르다."],
                "when": ["사용자가 다시 HOLD를 요청한다."],
                "then": ["재-HOLD 요청이 거절된다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "GH-3",
                "kind": "gherkin",
                "requirement_ids": ["R3"],
                "name": "만료 HOLD 재요청 허용",
                "given": ["기존 HOLD가 만료된 좌석이다."],
                "when": ["사용자가 다시 HOLD를 요청한다."],
                "then": ["재-HOLD 요청이 허용된다."],
                "boundary_conditions": [],
            },
            {
                "candidate_id": "GH-4",
                "kind": "gherkin",
                "requirement_ids": ["R4"],
                "name": "정확한 만료 경계",
                "given": ["좌석이 HELD 상태이다.", "현재 시각은 expiresAt과 같다."],
                "when": ["사용자가 다시 HOLD를 요청한다."],
                "then": ["재-HOLD 요청이 허용된다."],
                "boundary_conditions": [
                    {"condition": "now == expiresAt", "expected": "기존 HOLD는 만료 상태다."}
                ],
            },
        ],
    }


def eval_payload(scores=(4, 4, 4, 4), reported_total=None) -> dict:
    result = {}
    for axis, score in zip(
        ("coverage", "unambiguity", "independence", "executability"), scores
    ):
        result[axis] = {"score": score, "rationale": f"{axis} rationale"}
    if reported_total is not None:
        result["reported_total"] = reported_total
    return result


def raw(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False)


class DeterministicCoreTests(unittest.TestCase):
    def validate_candidate(self, value: dict):
        return validate_candidate_raw(FIXTURE, raw(value))

    def test_positive_final_pass(self):
        candidate_result = self.validate_candidate(positive_candidate())
        eval_result = validate_eval_raw(raw(eval_payload()))
        decision = validate_decision(candidate_result, eval_result)
        self.assertTrue(candidate_result.passed)
        self.assertTrue(eval_result.passed)
        self.assertTrue(decision.passed)
        self.assertEqual([], decision.failure_codes)

    def test_negative_missing_requirement(self):
        value = positive_candidate()
        value["unit_tests"] = [x for x in value["unit_tests"] if "R4" not in x["requirement_ids"]]
        result = self.validate_candidate(value)
        self.assertIn("MISSING_REQUIREMENT_COVERAGE", result.failure_codes)

    def test_negative_missing_required_boundary(self):
        value = positive_candidate()
        value["unit_tests"][-1]["boundary_conditions"] = []
        result = self.validate_candidate(value)
        self.assertIn("MISSING_REQUIRED_BOUNDARY", result.failure_codes)

    def test_boundary_formatting_normalization(self):
        value = positive_candidate()
        value["unit_tests"][-1]["boundary_conditions"][0]["condition"] = "now    ==   expiresAt"
        result = self.validate_candidate(value)
        self.assertTrue(result.passed)

    def test_negative_vague_only_expected(self):
        value = positive_candidate()
        value["unit_tests"][0]["expected"] = ["정상적으로 처리된다."]
        result = self.validate_candidate(value)
        self.assertIn("VAGUE_ONLY_EXPECTATION", result.failure_codes)

    def test_concrete_assertion_containing_vague_phrase_not_hard_failed(self):
        value = positive_candidate()
        value["unit_tests"][0]["expected"] = ["정상적으로 처리되어 좌석 상태가 HELD가 된다."]
        result = self.validate_candidate(value)
        self.assertNotIn("VAGUE_ONLY_EXPECTATION", result.failure_codes)

    def test_negative_duplicate_candidate_id(self):
        value = positive_candidate()
        value["gherkin_scenarios"][0]["candidate_id"] = "UT-1"
        result = self.validate_candidate(value)
        self.assertIn("DUPLICATE_CANDIDATE_ID", result.failure_codes)

    def test_negative_eval_total_below_min(self):
        candidate_result = self.validate_candidate(positive_candidate())
        eval_result = validate_eval_raw(raw(eval_payload((3, 3, 3, 3))))
        decision = validate_decision(candidate_result, eval_result)
        self.assertIn("EVAL_TOTAL_BELOW_MIN", decision.failure_codes)

    def test_negative_eval_axis_below_min_even_if_total_passes(self):
        candidate_result = self.validate_candidate(positive_candidate())
        eval_result = validate_eval_raw(raw(eval_payload((5, 5, 5, 2))))
        decision = validate_decision(candidate_result, eval_result)
        self.assertNotIn("EVAL_TOTAL_BELOW_MIN", decision.failure_codes)
        self.assertIn("EVAL_AXIS_BELOW_MIN", decision.failure_codes)

    def test_runner_ignores_reported_total(self):
        candidate_result = self.validate_candidate(positive_candidate())
        eval_result = validate_eval_raw(raw(eval_payload((4, 4, 4, 4), reported_total=1)))
        decision = validate_decision(candidate_result, eval_result)
        self.assertTrue(decision.passed)
        summary = next(x for x in decision.details if x["code"] == "EVAL_SCORE_SUMMARY")
        self.assertEqual(16, summary["computed_total"])
        self.assertEqual(1, summary["reported_total_ignored"])

    def test_negative_malformed_candidate_json(self):
        result = validate_candidate_raw(FIXTURE, '{"schema_version":')
        self.assertEqual(["CANDIDATE_JSON_PARSE_FAILED"], result.failure_codes)

    def test_gen_and_refine_structural_output_failures_are_role_failures(self):
        malformed = '{"schema_version":'
        gen_result = validate_candidate_role_raw(FIXTURE, malformed, "gen")
        refine_result = validate_candidate_role_raw(FIXTURE, malformed, "refine")
        self.assertEqual(["GEN_OUTPUT_INVALID"], gen_result.failure_codes)
        self.assertEqual(["REFINE_OUTPUT_INVALID"], refine_result.failure_codes)
        self.assertNotIn("MAX_ITERATIONS_EXHAUSTED", gen_result.failure_codes)
        self.assertNotIn("MAX_ITERATIONS_EXHAUSTED", refine_result.failure_codes)

    def test_negative_malformed_eval_json_is_role_output_invalid(self):
        result = validate_eval_raw('{"coverage":')
        self.assertEqual(["EVAL_OUTPUT_INVALID"], result.failure_codes)

    def test_critique_contract_has_no_scores_or_final_status(self):
        valid = {
            "issues": [
                {
                    "category": "coverage",
                    "requirement_ids": ["R1"],
                    "candidate_ids": ["UT-1"],
                    "issue": "example issue",
                    "suggestion": "example suggestion",
                }
            ]
        }
        self.assertTrue(validate_critique_raw(raw(valid)).passed)
        invalid = copy.deepcopy(valid)
        invalid["total"] = 20
        result = validate_critique_raw(raw(invalid))
        self.assertEqual(["CRITIQUE_OUTPUT_INVALID"], result.failure_codes)

    def test_max_iterations_exhaustion_distinct_from_role_output_failure(self):
        candidate_result = self.validate_candidate(positive_candidate())
        eval_result = validate_eval_raw(raw(eval_payload((3, 3, 3, 3))))
        decision = validate_decision(candidate_result, eval_result)
        exhausted = finalize_iteration(MAX_ITERATIONS, decision)
        self.assertIn("MAX_ITERATIONS_EXHAUSTED", exhausted.failure_codes)
        role_invalid = finalize_iteration(1, decision, role_output_failure="EVAL_OUTPUT_INVALID")
        self.assertEqual(["EVAL_OUTPUT_INVALID"], role_invalid.failure_codes)
        self.assertNotIn("MAX_ITERATIONS_EXHAUSTED", role_invalid.failure_codes)

    def test_semantic_wrong_boundary_meaning_is_not_hardcoded_into_core(self):
        value = positive_candidate()
        value["unit_tests"][-1]["expected"] = ["재-HOLD 요청이 거절된다."]
        value["unit_tests"][-1]["boundary_conditions"][0]["expected"] = "기존 HOLD는 아직 active다."
        value["gherkin_scenarios"][-1]["then"] = ["재-HOLD 요청이 거절된다."]
        value["gherkin_scenarios"][-1]["boundary_conditions"][0]["expected"] = "기존 HOLD는 아직 active다."
        result = self.validate_candidate(value)
        self.assertTrue(result.passed)

    def test_evidence_raw_exists_when_parse_fails_but_parsed_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp))
            invalid_raw = '{"coverage":'
            store.write_raw(1, "eval", invalid_raw)
            result = validate_eval_raw(invalid_raw)
            if result.passed and result.parsed is not None:
                store.write_parsed(1, "eval", result.parsed)
            iteration_dir = Path(tmp) / "iteration-01"
            self.assertTrue((iteration_dir / "eval.raw.txt").exists())
            self.assertFalse((iteration_dir / "eval.json").exists())


if __name__ == "__main__":
    unittest.main()
