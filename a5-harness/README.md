# A-5 Requirement → Test Harness v0

This directory contains the Phase 1-1 A-5 deterministic core plus the A-5-3
live-role connection layer.

## Authority and responsibility

The Harness authority is:

```text
Requirement Fixture
→ JSON Schemas
→ Deterministic Candidate Validator
→ YAML Semantic Rubric
→ Deterministic Decision
→ Runner Lifecycle
```

The canonical semantic scoring authority is:

    rubrics/test-quality-v0.yaml

The live runner and deterministic offline runner both load this same YAML rubric.
Rubric weights and decision thresholds are not separately hard-coded in those runners.

Claude is only a role executor for Gen, Critique, Independent Eval, and Refine.
It never owns the final PASS/REJECT decision.

## Deterministic core

The core validates:

```text
Requirement Fixture
→ Candidate raw text
→ JSON parse
→ Candidate JSON Schema
→ deterministic candidate validation
→ Eval raw text
→ JSON parse / Eval Schema
→ deterministic score decision
→ PASS / REJECT evidence
```

Design boundaries:

- No Seat HOLD business meaning is hard-coded into `src/a5_harness/core.py`.
- Required requirement IDs, candidate kinds, and boundary markers come from the fixture.
- Boundary normalization only removes formatting whitespace/case differences.
- Semantic errors can intentionally pass the deterministic candidate gate.
- Rubric weights, score ranges, anchors, `min_total = 16`, and `min_axis = 3` come from `rubrics/test-quality-v0.yaml`.
- `MAX_ITERATIONS = 3` is runner lifecycle configuration, not rubric authority.
- Role-output failures are distinct from `MAX_ITERATIONS_EXHAUSTED`.
- Raw role output is stored before parse/schema validation.

## Schema, Rubric, and Validator responsibilities

- JSON Schema: structural contract for required fields, types, object shape, and serialization constraints.
- YAML Rubric: semantic quality contract for coverage, unambiguity, independence, executability, weights, score ranges, anchors, `min_total`, and `min_axis`.
- Deterministic Validator: mechanically enforceable fixture/candidate checks plus YAML-weighted score calculation, threshold enforcement, and final PASS/REJECT.

The Eval prompt does not maintain an independent copy of the rubric. `live_runner.py` loads `rubrics/test-quality-v0.yaml`, renders its axis names, weights, score ranges, and anchors into the Eval prompt, and passes the same loaded Rubric object to the deterministic decision. `cli.py` uses the same YAML rubric for deterministic offline replay.

## A-5-3 live role runner

Prompt files:

```text
prompts/gen.md
prompts/critique.md
prompts/eval.md
prompts/refine.md
```

The runner uses one fresh non-interactive Claude Code process per role:

```text
claude -p ... --output-format text --max-turns 1 --safe-mode --tools "" --disallowedTools "mcp__*"
```

It never uses `--continue` or `--resume`. The goal is to prevent Gen/Critique/Eval
from sharing conversational state. The Eval prompt receives neither Critique output
nor previous iteration scores.

### Positive live run

From `a5-harness/`:

```bash
PYTHONPATH=src python3 -m a5_harness.live_runner \
  --fixture fixtures/seat-hold-v0.json \
  --mode positive
```

### Semantic-negative live run

The initial candidate is schema-valid and traceable but intentionally reverses the
exact-boundary business semantics. The deterministic gate should not reject it for
that semantic error alone. Critique/Eval must prevent an initial PASS.

```bash
PYTHONPATH=src python3 -m a5_harness.live_runner \
  --fixture fixtures/seat-hold-v0.json \
  --mode semantic-negative \
  --initial-candidate fixtures/seat-hold-semantic-wrong-v0.json
```

If the semantic-wrong initial candidate crosses the semantic evaluation and decision
gates, the runner records `SEMANTIC_FALSE_ACCEPT` and returns REJECT. It never changes
Eval scores by hand to manufacture the expected result.

### Model/provider evidence

The runner records Claude Code CLI version in `manifest.json`. If a model is explicitly
supplied through `--model` or `A5_CLAUDE_MODEL`, it is recorded. Otherwise the model is
recorded as `UNKNOWN`; the runner does not guess.

## Raw-first evidence

Each live role invocation stores its input prompt and raw stdout before parsing.
Parsed JSON is materialized only after the relevant role contract passes.

```text
runs/<run-id>/
├── input.json
├── manifest.json
├── iteration-01/
│   ├── candidate.prompt.txt       # Gen only
│   ├── candidate.raw.txt
│   ├── candidate.json
│   ├── candidate-validation.json
│   ├── critique.prompt.txt
│   ├── critique.raw.txt
│   ├── critique.json
│   ├── eval.prompt.txt
│   ├── eval.raw.txt
│   ├── eval.json
│   ├── decision-validation.json
│   └── ...
└── final.json
```

Refine iterations additionally preserve `refine.prompt.txt`, `refine.raw.txt`,
`refine.json`, and `refine-validation.json`.

## Python

Recommended temporary environment:

```bash
python3 -m venv /tmp/phase1-a5-venv
/tmp/phase1-a5-venv/bin/python -m pip install -r requirements.txt
```

## Self-tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

A-5-3 adds runner-support tests. A-5-3A adds YAML rubric authority tests covering YAML parsing, axis/range/weight/threshold contracts, Eval prompt rendering, and proof that changing YAML thresholds or weights changes the deterministic decision. The suite remains network/AI-free.

## Failure taxonomy

Candidate / fixture:

- `FIXTURE_SCHEMA_FAILED`
- `FIXTURE_DUPLICATE_REQUIREMENT_ID`
- `FIXTURE_BOUNDARY_UNKNOWN_REQUIREMENT`
- `CANDIDATE_JSON_PARSE_FAILED`
- `CANDIDATE_SCHEMA_FAILED`
- `WHITESPACE_ONLY_FIELD`
- `DUPLICATE_CANDIDATE_ID`
- `MISSING_REQUIRED_CANDIDATE_KIND`
- `MISSING_REQUIREMENT_COVERAGE`
- `MISSING_REQUIRED_BOUNDARY`
- `VAGUE_ONLY_EXPECTATION`

Role output:

- `GEN_OUTPUT_INVALID`
- `CRITIQUE_OUTPUT_INVALID`
- `EVAL_OUTPUT_INVALID`
- `REFINE_OUTPUT_INVALID`

Provider execution:

- `GEN_PROVIDER_EXECUTION_FAILED`
- `CRITIQUE_PROVIDER_EXECUTION_FAILED`
- `EVAL_PROVIDER_EXECUTION_FAILED`
- `REFINE_PROVIDER_EXECUTION_FAILED`

Decision / lifecycle:

- `EVAL_TOTAL_BELOW_MIN`
- `EVAL_AXIS_BELOW_MIN`
- `ITERATION_OUT_OF_RANGE`
- `MAX_ITERATIONS_EXHAUSTED`
- `SEMANTIC_FALSE_ACCEPT` (A-5-3 experiment finding)

## Still out of scope

- generated Java source application
- generated Cucumber Feature application
- production code changes
- existing A-3/A-4 test changes
- Gradle integration into the harness itself
- git add / commit / push / PR / merge
