# A-5 Requirement → Test Harness v0

이 디렉터리에는 Phase 1-1 A-5의 deterministic core와 A-5-3 live-role connection layer가 들어 있습니다.

Phase 0의 Harness v0는 수동으로 운용한 Harness였습니다. A-5에서는 이를 실행 가능한 구조로 확장하면서 AI role execution, deterministic validation, semantic Eval, 최종 decision/lifecycle 책임을 분리했습니다.

## Authority와 책임

Harness의 authority 흐름:

```text
Requirement Fixture
→ JSON Schemas
→ Deterministic Candidate Validator
→ YAML Semantic Rubric
→ Deterministic Decision
→ Runner Lifecycle
```

Canonical semantic scoring authority:

    rubrics/test-quality-v0.yaml

Live runner와 deterministic offline runner는 동일한 YAML rubric을 로드합니다. Rubric weight와 decision threshold를 각 runner에 별도로 hard-code하지 않습니다.

Claude는 Gen, Critique, Independent Eval, Refine의 role executor일 뿐입니다. 최종 PASS/REJECT 판단 권한은 갖지 않습니다.

## Deterministic core

Core가 검증하는 흐름:

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

설계 경계:

- `src/a5_harness/core.py`에는 Seat HOLD의 business meaning을 hard-code하지 않습니다.
- 필수 requirement ID, candidate kind, boundary marker는 fixture에서 가져옵니다.
- Boundary normalization은 formatting whitespace/case 차이만 제거합니다.
- Semantic error는 의도적으로 deterministic candidate gate를 통과할 수 있습니다.
- Rubric weight, score range, anchor, `min_total = 16`, `min_axis = 3`은 `rubrics/test-quality-v0.yaml`에서 가져옵니다.
- `MAX_ITERATIONS = 3`은 rubric authority가 아니라 runner lifecycle configuration입니다.
- Role-output failure는 `MAX_ITERATIONS_EXHAUSTED`와 구분합니다.
- Raw role output은 parse/schema validation 전에 저장합니다.

전체 semantic evaluation이 deterministic한 것은 아닙니다. Deterministic validator는 기계적으로 검사 가능한 계약을 확인하고, Independent AI Eval은 YAML Rubric을 기준으로 의미 품질을 평가합니다. 최종 score 계산, threshold 적용, PASS/REJECT 및 lifecycle은 deterministic Runner가 담당합니다.

## Schema, Rubric, Validator의 책임

- JSON Schema: required field, type, object shape, serialization constraint에 대한 구조 계약
- YAML Rubric: coverage, unambiguity, independence, executability, weight, score range, anchor, `min_total`, `min_axis`에 대한 semantic quality contract
- Deterministic Validator: fixture/candidate에서 기계적으로 강제 가능한 검사와 YAML-weighted score 계산, threshold 적용, 최종 PASS/REJECT

Eval prompt는 rubric의 별도 복사본을 유지하지 않습니다. `live_runner.py`가 `rubrics/test-quality-v0.yaml`을 로드하고 axis name, weight, score range, anchor를 Eval prompt에 렌더링하며, 동일하게 로드된 Rubric object를 deterministic decision에도 전달합니다. `cli.py` 역시 deterministic offline replay에서 같은 YAML rubric을 사용합니다.

Frozen self-test PASS는 테스트에 인코딩된 계약 범위가 유지됨을 보장하며, 그 밖의 모든 semantic correctness를 자동으로 증명하지는 않습니다.

## A-5-3 Live role runner

Prompt 파일:

```text
prompts/gen.md
prompts/critique.md
prompts/eval.md
prompts/refine.md
```

Runner는 role마다 fresh non-interactive Claude Code process 하나를 사용합니다.

```text
claude -p ... --output-format text --max-turns 1 --safe-mode --tools "" --disallowedTools "mcp__*"
```

`--continue` 또는 `--resume`은 사용하지 않습니다. 목적은 Gen/Critique/Eval이 conversational state를 공유하지 않게 하는 것입니다. Eval prompt에는 Critique output이나 이전 iteration score를 전달하지 않습니다.

### Positive Live run

`a5-harness/`에서 실행:

```bash
PYTHONPATH=src python3 -m a5_harness.live_runner \
  --fixture fixtures/seat-hold-v0.json \
  --mode positive
```

### Semantic-negative Live run

Initial candidate는 schema-valid하고 traceable하지만 exact-boundary business semantics를 의도적으로 반대로 구성합니다. Deterministic gate는 이 semantic error만으로 candidate를 거절하면 안 됩니다. Critique/Eval이 initial PASS를 막아야 합니다.

```bash
PYTHONPATH=src python3 -m a5_harness.live_runner \
  --fixture fixtures/seat-hold-v0.json \
  --mode semantic-negative \
  --initial-candidate fixtures/seat-hold-semantic-wrong-v0.json
```

Semantic-wrong initial candidate가 semantic evaluation과 decision gate를 통과하면 runner는 `SEMANTIC_FALSE_ACCEPT`를 기록하고 REJECT를 반환합니다. 기대 결과를 만들기 위해 Eval score를 수동으로 변경하지 않습니다.

### Model/provider evidence

Runner는 `manifest.json`에 Claude Code CLI version을 기록합니다. `--model` 또는 `A5_CLAUDE_MODEL`로 model이 명시적으로 제공되면 이를 기록합니다. 그렇지 않으면 model은 `UNKNOWN`으로 기록하며 runner가 추측하지 않습니다.

## Raw-first evidence

각 Live role invocation은 parsing 전에 input prompt와 raw stdout을 저장합니다. Parsed JSON은 해당 role contract가 통과한 뒤에만 materialize합니다.

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

Refine iteration에서는 추가로 `refine.prompt.txt`, `refine.raw.txt`, `refine.json`, `refine-validation.json`을 보존합니다.

## Python

권장 임시 환경:

```bash
python3 -m venv /tmp/phase1-a5-venv
/tmp/phase1-a5-venv/bin/python -m pip install -r requirements.txt
```

## Self-tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

A-5-3은 runner-support test를 추가했습니다. A-5-3A는 YAML parsing, axis/range/weight/threshold contract, Eval prompt rendering, YAML threshold 또는 weight 변경이 deterministic decision에 실제 영향을 주는지 검증하는 YAML rubric authority test를 추가했습니다. 이 suite는 network/AI 없이 실행됩니다.

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

## 여전히 범위에서 제외되는 항목

- generated Java source application
- generated Cucumber Feature application
- production code changes
- existing A-3/A-4 test changes
- Gradle integration into the harness itself
- git add / commit / push / PR / merge
