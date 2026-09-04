from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


EXPECTED_AXES = (
    "coverage",
    "unambiguity",
    "independence",
    "executability",
)

DEFAULT_RUBRIC_PATH = (
    Path(__file__).resolve().parents[2]
    / "rubrics"
    / "test-quality-v0.yaml"
)


@dataclass(frozen=True)
class AxisRubric:
    weight: int
    score_min: int
    score_max: int
    anchors: dict[int, str]
    intermediate_scores: str


@dataclass(frozen=True)
class Rubric:
    schema_version: str
    rubric_id: str
    axes: dict[str, AxisRubric]
    min_total: int
    min_axis: int
    source_path: Path

    @property
    def axis_names(self) -> tuple[str, ...]:
        return tuple(self.axes.keys())

    @property
    def weights(self) -> dict[str, int]:
        return {
            name: axis.weight
            for name, axis in self.axes.items()
        }


def _require_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _require_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def load_rubric(path: Path | None = None) -> Rubric:
    source = (path or DEFAULT_RUBRIC_PATH).resolve()

    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("rubric YAML must contain a top-level mapping")

    schema_version = _require_text(
        raw.get("schema_version"),
        "schema_version",
    )
    rubric_id = _require_text(
        raw.get("rubric_id"),
        "rubric_id",
    )

    raw_axes = raw.get("axes")
    if not isinstance(raw_axes, dict):
        raise ValueError("axes must be a mapping")

    if tuple(raw_axes.keys()) != EXPECTED_AXES:
        raise ValueError(
            "axes must be exactly and in order: "
            + ", ".join(EXPECTED_AXES)
        )

    axes: dict[str, AxisRubric] = {}

    for name in EXPECTED_AXES:
        raw_axis = raw_axes[name]
        if not isinstance(raw_axis, dict):
            raise ValueError(f"axes.{name} must be a mapping")

        weight = _require_int(
            raw_axis.get("weight"),
            f"axes.{name}.weight",
        )
        score_min = _require_int(
            raw_axis.get("score_min"),
            f"axes.{name}.score_min",
        )
        score_max = _require_int(
            raw_axis.get("score_max"),
            f"axes.{name}.score_max",
        )

        if weight <= 0:
            raise ValueError(f"axes.{name}.weight must be positive")

        if score_min != 1 or score_max != 5:
            raise ValueError(
                f"axes.{name} score range must be exactly 1..5 in v0"
            )

        raw_anchors = raw_axis.get("anchors")
        if not isinstance(raw_anchors, dict):
            raise ValueError(f"axes.{name}.anchors must be a mapping")

        anchors: dict[int, str] = {}
        for score in (1, 3, 5):
            if score not in raw_anchors:
                raise ValueError(
                    f"axes.{name}.anchors must define {score}"
                )
            anchors[score] = _require_text(
                raw_anchors[score],
                f"axes.{name}.anchors.{score}",
            )

        axes[name] = AxisRubric(
            weight=weight,
            score_min=score_min,
            score_max=score_max,
            anchors=anchors,
            intermediate_scores=_require_text(
                raw_axis.get("intermediate_scores"),
                f"axes.{name}.intermediate_scores",
            ),
        )

    decision = raw.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("decision must be a mapping")

    min_total = _require_int(
        decision.get("min_total"),
        "decision.min_total",
    )
    min_axis = _require_int(
        decision.get("min_axis"),
        "decision.min_axis",
    )

    if min_total <= 0:
        raise ValueError("decision.min_total must be positive")

    if not 1 <= min_axis <= 5:
        raise ValueError("decision.min_axis must be within 1..5")

    maximum_total = sum(
        axis.score_max * axis.weight
        for axis in axes.values()
    )
    if min_total > maximum_total:
        raise ValueError(
            "decision.min_total exceeds maximum weighted total"
        )

    return Rubric(
        schema_version=schema_version,
        rubric_id=rubric_id,
        axes=axes,
        min_total=min_total,
        min_axis=min_axis,
        source_path=source,
    )


def render_eval_rubric(rubric: Rubric) -> str:
    lines: list[str] = [
        f"Rubric ID: {rubric.rubric_id}",
        "",
    ]

    for name, axis in rubric.axes.items():
        lines.extend(
            [
                name,
                f"weight: {axis.weight}",
                f"score range: {axis.score_min}..{axis.score_max}",
                f"1: {axis.anchors[1]}",
                f"3: {axis.anchors[3]}",
                f"5: {axis.anchors[5]}",
                axis.intermediate_scores,
                "",
            ]
        )

    return "\n".join(lines).rstrip()
