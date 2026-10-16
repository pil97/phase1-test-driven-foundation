from __future__ import annotations

from copy import deepcopy
from typing import Any


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
