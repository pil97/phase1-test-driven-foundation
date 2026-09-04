from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from a5_harness.core import ValidationResult, validate_decision
from a5_harness.live_runner import _render
from a5_harness.rubric import (
    EXPECTED_AXES,
    load_rubric,
    render_eval_rubric,
)


ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = ROOT / "rubrics" / "test-quality-v0.yaml"


def candidate_validation() -> ValidationResult:
    return ValidationResult(
        "PASS",
        [],
        [],
        parsed={"candidate_set_id": "rubric-test"},
    )


def eval_validation(
    scores: tuple[int, int, int, int],
) -> ValidationResult:
    parsed = {}

    for axis, score in zip(EXPECTED_AXES, scores):
        parsed[axis] = {
            "score": score,
            "rationale": f"{axis} rationale",
        }

    return ValidationResult(
        "PASS",
        [],
        [],
        parsed=parsed,
    )


class RubricAuthorityTests(unittest.TestCase):

    # RUBRIC-1
    def test_rubric_1_yaml_parse_success(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        self.assertEqual(
            "test-quality-v0",
            rubric.rubric_id,
        )

    # RUBRIC-2
    def test_rubric_2_exactly_four_axes(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        self.assertEqual(
            EXPECTED_AXES,
            rubric.axis_names,
        )

    # RUBRIC-3
    def test_rubric_3_each_axis_score_range_is_1_to_5(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        for axis in rubric.axes.values():
            self.assertEqual(1, axis.score_min)
            self.assertEqual(5, axis.score_max)

    # RUBRIC-4
    def test_rubric_4_each_axis_weight_is_1(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        self.assertEqual(
            {
                "coverage": 1,
                "unambiguity": 1,
                "independence": 1,
                "executability": 1,
            },
            rubric.weights,
        )

    # RUBRIC-5
    def test_rubric_5_thresholds_are_approved_values(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        self.assertEqual(16, rubric.min_total)
        self.assertEqual(3, rubric.min_axis)

    # RUBRIC-6
    def test_rubric_6_eval_prompt_uses_yaml_axes_and_anchors(self) -> None:
        rubric = load_rubric(RUBRIC_PATH)

        template = (
            ROOT / "prompts" / "eval.md"
        ).read_text(encoding="utf-8")

        rendered = _render(
            template,
            RUBRIC_TEXT=render_eval_rubric(rubric),
            FIXTURE_JSON="{}",
            CANDIDATE_JSON="{}",
            EVAL_SCHEMA_JSON="{}",
        )

        self.assertNotIn(
            "{{RUBRIC_TEXT}}",
            rendered,
        )

        for name, axis in rubric.axes.items():
            self.assertIn(name, rendered)

            self.assertIn(
                f"weight: {axis.weight}",
                rendered,
            )

            self.assertIn(
                f"score range: "
                f"{axis.score_min}..{axis.score_max}",
                rendered,
            )

            for score in (1, 3, 5):
                self.assertIn(
                    axis.anchors[score],
                    rendered,
                )

    # RUBRIC-7
    def test_rubric_7_decision_uses_yaml_threshold_weight_and_min_axis(
        self,
    ) -> None:
        canonical = yaml.safe_load(
            RUBRIC_PATH.read_text(encoding="utf-8")
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rubric.yaml"

            # A. min_total authority:
            # 4+4+4+4=16 normally passes.
            # Change YAML threshold to 17 -> must fail.
            changed = copy.deepcopy(canonical)
            changed["decision"]["min_total"] = 17

            path.write_text(
                yaml.safe_dump(
                    changed,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )

            rubric = load_rubric(path)

            decision = validate_decision(
                candidate_validation(),
                eval_validation((4, 4, 4, 4)),
                rubric,
            )

            self.assertIn(
                "EVAL_TOTAL_BELOW_MIN",
                decision.failure_codes,
            )

            # B. min_axis authority:
            # All axes are 4.
            # Change YAML min_axis to 5 -> must fail.
            changed = copy.deepcopy(canonical)
            changed["decision"]["min_axis"] = 5

            path.write_text(
                yaml.safe_dump(
                    changed,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )

            rubric = load_rubric(path)

            decision = validate_decision(
                candidate_validation(),
                eval_validation((4, 4, 4, 4)),
                rubric,
            )

            self.assertIn(
                "EVAL_AXIS_BELOW_MIN",
                decision.failure_codes,
            )

            # C. weight authority:
            # Raise min_total to 17.
            # With equal weights, 4+4+4+4=16 -> fail.
            # Then change coverage weight to 2:
            # 8+4+4+4=20 -> pass.
            changed = copy.deepcopy(canonical)
            changed["decision"]["min_total"] = 17
            changed["axes"]["coverage"]["weight"] = 2

            path.write_text(
                yaml.safe_dump(
                    changed,
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )

            rubric = load_rubric(path)

            decision = validate_decision(
                candidate_validation(),
                eval_validation((4, 4, 4, 4)),
                rubric,
            )

            self.assertTrue(decision.passed)

            summary = next(
                item
                for item in decision.details
                if item["code"] == "EVAL_SCORE_SUMMARY"
            )

            self.assertEqual(
                2,
                summary["weights"]["coverage"],
            )

            self.assertEqual(
                20,
                summary["computed_total"],
            )


if __name__ == "__main__":
    unittest.main()
