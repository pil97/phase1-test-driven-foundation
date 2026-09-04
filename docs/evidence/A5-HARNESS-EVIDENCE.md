# A-5 — Requirement → Test Harness 검증 기록

## 목적

A-5에서는 AI role execution과 deterministic validation, 최종 decision authority를 분리하는 Requirement-to-Test Harness를 구현했습니다.

Phase 0의 Harness v0는 수동으로 운용한 Harness였고, A-5에서는 이를 구조 계약과 실행 가능한 validation/decision 흐름으로 발전시켰습니다.

## 구조

```text
Authoritative Requirement Fixture
→ Gen
→ Deterministic Candidate Gate
→ Critique
→ Independent Eval
→ Deterministic Decision
→ PASS or Refine
→ repeat up to MAX_ITERATIONS
```

`MAX_ITERATIONS = 3`은 runner lifecycle configuration입니다.

AI provider는 Gen, Critique, Independent Eval, Refine role을 실행할 수 있지만 최종 PASS/REJECT 판단 권한은 갖지 않습니다.

전체 semantic evaluation이 deterministic한 것은 아닙니다. Independent AI Eval이 의미 품질을 평가하고, deterministic Runner가 최종 score 계산, threshold 적용, PASS/REJECT 및 lifecycle을 담당합니다.

## 계약과 authority

### JSON Schema

JSON Schema는 requirement fixture, generated candidate, critique output, Eval output의 구조 계약을 정의합니다.

### YAML Rubric

Canonical semantic scoring authority:

[`a5-harness/rubrics/test-quality-v0.yaml`](../../a5-harness/rubrics/test-quality-v0.yaml)

Rubric axes:

- coverage
- unambiguity
- independence
- executability

각 axis:

- weight = 1
- score range = 1..5
- anchors at 1 / 3 / 5

Decision thresholds:

- `min_total = 16`
- `min_axis = 3`

동일한 YAML rubric을 Eval prompt와 deterministic decision path에서 함께 로드합니다.

```text
test-quality-v0.yaml
        ↓
   load_rubric()
     ├─→ Eval Prompt
     ├─→ Live Decision
     └─→ Offline Decision
```

Deterministic validator는 기계적으로 검사 가능한 계약을 확인합니다. Frozen self-test PASS는 인코딩된 계약 범위가 유지됨을 보장할 뿐, 그 밖의 모든 semantic correctness까지 자동으로 증명하지는 않습니다.

## Positive Live Run

공개 evidence:

[`a5-3-live-positive-critfix-20260903T061132Z`](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/)

Independent Eval scores:

- coverage = 5
- unambiguity = 4
- independence = 5
- executability = 4

Computed total:

`5 + 4 + 5 + 4 = 18`

결과:

- iteration = 1
- failure codes = none
- status = PASS

주요 파일:

- [final.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/final.json)
- [decision-validation.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/iteration-01/decision-validation.json)
- [eval.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/iteration-01/eval.json)

## Semantic-Negative → Refine Run

공개 evidence:

[`a5-3-semantic-negative-evalfix-20260903T070700Z`](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/)

Initial candidate는 structurally valid하고 traceable했기 때문에 deterministic candidate gate를 통과했습니다.

하지만 `now == expiresAt`의 exact-boundary meaning을 의도적으로 반대로 구성했습니다.

### Iteration 1

Independent Eval scores:

- coverage = 1
- unambiguity = 4
- independence = 5
- executability = 4

Computed total:

`1 + 4 + 5 + 4 = 14`

Decision:

- `EVAL_TOTAL_BELOW_MIN`
- actual total = 14
- required total = 16
- `EVAL_AXIS_BELOW_MIN`
- coverage = 1
- required per-axis minimum = 3
- status = REJECT

Iteration 1 주요 evidence:

- [candidate-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/candidate-validation.json)
- [eval.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/eval.json)
- [decision-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/decision-validation.json)

### Iteration 2 — Refine

Refine가 exact-boundary semantics를 수정했습니다.

Independent Eval scores:

- coverage = 5
- unambiguity = 4
- independence = 5
- executability = 4

Computed total:

`5 + 4 + 5 + 4 = 18`

결과:

- iteration = 2
- status = PASS

Iteration 2 주요 evidence:

- [refine.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/refine.json)
- [eval.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/eval.json)
- [decision-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/decision-validation.json)
- [final.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/final.json)

## A-5-3A Offline Replay

YAML rubric authority를 도입한 뒤 새로운 Live AI call을 만들지 않고 최종 A-5-3 결과를 replay했습니다.

### Positive replay

- scores = 5 / 4 / 5 / 4
- computed total = 18
- status = PASS

공개 sanitized evidence:

- [manifest.public.json](a5/offline-positive/manifest.public.json)
- [decision-validation.json](a5/offline-positive/decision-validation.json)
- [final.json](a5/offline-positive/final.json)
- [sanitization 안내](a5/offline-positive/README.md)

### Semantic-negative replay

- scores = 1 / 4 / 5 / 4
- computed total = 14
- `EVAL_TOTAL_BELOW_MIN`
- `EVAL_AXIS_BELOW_MIN`
- status = REJECT

공개 sanitized evidence:

- [manifest.public.json](a5/offline-semantic-negative/manifest.public.json)
- [decision-validation.json](a5/offline-semantic-negative/decision-validation.json)
- [final.json](a5/offline-semantic-negative/final.json)
- [sanitization 안내](a5/offline-semantic-negative/README.md)

Public offline manifest는 명시적으로 sanitized한 copy입니다. Original execution evidence는 local에 보존합니다.

## Deterministic self-tests

A-5-3A에서는 다음 rubric-authority test를 추가했습니다.

- YAML parsing
- exact four-axis contract
- score ranges
- weights
- decision thresholds
- Eval prompt rendering from YAML
- YAML threshold 또는 weight 변경이 deterministic decision에 영향을 주는 runtime proof

최종 Python regression:

`26/26 PASS`

Fresh temporary environment reproduction에서도 26개 테스트를 모두 통과했습니다.

## Public / local evidence 정책

Public repository evidence:

- final positive Live run
- final semantic-negative / Refine Live run
- sanitized offline replay evidence

Local-only evidence:

- intermediate authentication run
- debugging run
- failure run
- local absolute path가 포함된 original offline replay manifest

Local-only run은 최종 accepted Harness behavior를 재현하거나 이해하는 데 필요하지 않습니다.
