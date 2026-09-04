# Phase 1-1 Test-Driven Foundation

## Purpose

This learning project progresses through three connected stages:

```text
TDD
→ BDD / Acceptance
→ Requirement-to-Test Harness
```

The goal is to make requirements executable, expose boundary defects early, and separate AI-generated suggestions from deterministic validation and decision authority.

## Environment

- Java
- Gradle Wrapper
- JUnit
- AssertJ
- Mockito
- Cucumber
- Python
- jsonschema
- PyYAML

Claude Code can be used as an optional Live AI role executor for the A-5 Harness. It is not the Harness authority and does not own the final PASS/REJECT decision.

## A-3 — TDD / Seat HOLD

A-3 applies TDD to a small Seat HOLD domain with explicit time-boundary behavior.

Core requirements:

1. AVAILABLE seat -> HOLD succeeds.
2. Active HELD seat (`now < expiresAt`) -> re-HOLD is rejected.
3. Expired HELD seat -> re-HOLD is allowed.
4. Exact boundary (`now == expiresAt`) -> treated as expired, so re-HOLD is allowed.

`SeatHoldServiceTest` also verifies the repository interaction flow:

`lookup -> HOLD -> save`

An intentional comparison defect was introduced during the exercise, and the exact equality test detected the broken boundary semantics before the correct implementation was restored.

## A-4 — BDD / Acceptance

A-4 translates the same domain requirements into executable Cucumber acceptance scenarios.

The acceptance layer contains:

- Gherkin Feature
- Step Definitions
- Cucumber runner
- in-memory repository test double

The exercise moved from an Undefined Step RED state to Acceptance GREEN after the missing executable steps were implemented.

A separate AI implementation candidate was also evaluated. Its self-evaluation, the frozen acceptance contract, and the existing A-3 tests demonstrated that different evaluation scopes can detect different classes of failure.

## A-5 — Requirement → Test Harness

A-5 builds a deterministic Harness around AI-assisted test candidate generation.

```text
Requirement Fixture
→ Gen
→ Deterministic Candidate Gate
→ Critique
→ Independent Eval
→ Deterministic Decision
→ PASS or Refine
```

The Harness uses:

- JSON Schema for structural contracts
- YAML Rubric for semantic scoring authority
- Gen for initial test candidates
- Critique for issue discovery without final scoring authority
- Independent Eval for rubric scoring
- Refine after a rejected iteration
- deterministic code for the final PASS/REJECT decision

Canonical rubric:

[`a5-harness/rubrics/test-quality-v0.yaml`](a5-harness/rubrics/test-quality-v0.yaml)

Rubric axes:

- coverage
- unambiguity
- independence
- executability

Decision contract:

- `min_total = 16`
- `min_axis = 3`
- `MAX_ITERATIONS = 3`

`min_total` and `min_axis` come from the YAML rubric. `MAX_ITERATIONS` is runner lifecycle configuration.

## How to Run

### Java tests

```bash
JAVA_HOME=$(/usr/libexec/java_home -v 25) \
./gradlew clean test
```

### Python Harness tests

Create a temporary environment and install the pinned Harness dependencies:

```bash
python3 -m venv /tmp/phase1-a5-venv
/tmp/phase1-a5-venv/bin/python -m pip install -r a5-harness/requirements.txt
```

Run the deterministic test suite:

```bash
PYTHONPATH=a5-harness/src \
/tmp/phase1-a5-venv/bin/python -m unittest discover \
  -s a5-harness/tests \
  -v
```

The final validated suite contains 26 Python tests.

### Live AI execution

Live A-5 role execution is separate from deterministic offline reproduction.

Live execution requires a compatible Claude Code installation plus provider authentication/environment availability. The final decision still remains deterministic Harness logic.

## Evidence

- [A-3 TDD Evidence](docs/evidence/A3-TDD-EVIDENCE.md)
- [A-4 BDD / Acceptance Evidence](docs/evidence/A4-BDD-EVIDENCE.md)
- [A-5 Harness Evidence](docs/evidence/A5-HARNESS-EVIDENCE.md)

Public A-5 evidence contains only the final selected Live runs and sanitized offline replay summaries.

Intermediate authentication/debug/failure runs and original offline manifests containing local absolute paths remain local-only.

## Scope / Exclusions

- This is a focused learning project, not a production ticketing application.
- Spring and database infrastructure are intentionally out of scope here.
- Generated Java or Cucumber output is not automatically applied to the source tree.
- AI role output is not treated as final decision authority.
- Detailed learning notes, reasoning changes, and reflection are maintained separately in Notion.

The GitHub repository is intended to contain code, reproducibility instructions, and selected execution evidence rather than the full learning diary.
