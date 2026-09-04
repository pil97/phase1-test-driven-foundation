# A-5 — Requirement → Test Harness Evidence

## Purpose

A-5 built a Requirement-to-Test Harness that separates AI role execution from deterministic validation and final decision authority.

## Architecture

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

`MAX_ITERATIONS = 3` is runner lifecycle configuration.

The AI provider may execute Gen, Critique, Independent Eval, and Refine roles, but it does not own the final PASS/REJECT decision.

## Contracts and authority

### JSON Schema

JSON Schemas define structural contracts for requirement fixtures, generated candidates, critique output, and Eval output.

### YAML Rubric

The canonical semantic scoring authority is:

[`a5-harness/rubrics/test-quality-v0.yaml`](../../a5-harness/rubrics/test-quality-v0.yaml)

Rubric axes:

- coverage
- unambiguity
- independence
- executability

Each axis uses:

- weight = 1
- score range = 1..5
- anchors at 1 / 3 / 5

Decision thresholds:

- `min_total = 16`
- `min_axis = 3`

The same YAML rubric is loaded into both the Eval prompt and deterministic decision path.

```text
test-quality-v0.yaml
        ↓
   load_rubric()
     ├─→ Eval Prompt
     ├─→ Live Decision
     └─→ Offline Decision
```

## Positive Live Run

Public evidence:

[`a5-3-live-positive-critfix-20260903T061132Z`](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/)

Independent Eval scores:

- coverage = 5
- unambiguity = 4
- independence = 5
- executability = 4

Computed total:

`5 + 4 + 5 + 4 = 18`

Result:

- iteration = 1
- failure codes = none
- status = PASS

Key files:

- [final.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/final.json)
- [decision-validation.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/iteration-01/decision-validation.json)
- [eval.json](a5/live-runs/a5-3-live-positive-critfix-20260903T061132Z/iteration-01/eval.json)

## Semantic-Negative → Refine Run

Public evidence:

[`a5-3-semantic-negative-evalfix-20260903T070700Z`](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/)

The initial candidate was structurally valid and traceable, so the deterministic candidate gate passed it.

However, it intentionally reversed the exact-boundary meaning for `now == expiresAt`.

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

Key iteration-1 evidence:

- [candidate-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/candidate-validation.json)
- [eval.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/eval.json)
- [decision-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-01/decision-validation.json)

### Iteration 2 — Refine

Refine corrected the exact-boundary semantics.

Independent Eval scores:

- coverage = 5
- unambiguity = 4
- independence = 5
- executability = 4

Computed total:

`5 + 4 + 5 + 4 = 18`

Result:

- iteration = 2
- status = PASS

Key iteration-2 evidence:

- [refine.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/refine.json)
- [eval.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/eval.json)
- [decision-validation.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/iteration-02/decision-validation.json)
- [final.json](a5/live-runs/a5-3-semantic-negative-evalfix-20260903T070700Z/final.json)

## A-5-3A Offline Replay

The final A-5-3 results were replayed without making new Live AI calls after YAML rubric authority was introduced.

### Positive replay

- scores = 5 / 4 / 5 / 4
- computed total = 18
- status = PASS

Public sanitized evidence:

- [manifest.public.json](a5/offline-positive/manifest.public.json)
- [decision-validation.json](a5/offline-positive/decision-validation.json)
- [final.json](a5/offline-positive/final.json)
- [sanitization notice](a5/offline-positive/README.md)

### Semantic-negative replay

- scores = 1 / 4 / 5 / 4
- computed total = 14
- `EVAL_TOTAL_BELOW_MIN`
- `EVAL_AXIS_BELOW_MIN`
- status = REJECT

Public sanitized evidence:

- [manifest.public.json](a5/offline-semantic-negative/manifest.public.json)
- [decision-validation.json](a5/offline-semantic-negative/decision-validation.json)
- [final.json](a5/offline-semantic-negative/final.json)
- [sanitization notice](a5/offline-semantic-negative/README.md)

The public offline manifests are explicitly sanitized copies. Original execution evidence is retained locally.

## Deterministic self-tests

A-5-3A added rubric-authority tests that verify:

- YAML parsing
- exact four-axis contract
- score ranges
- weights
- decision thresholds
- Eval prompt rendering from YAML
- runtime proof that changing YAML thresholds or weights changes the deterministic decision

Final Python regression:

`26/26 PASS`

Fresh temporary environment reproduction also passed all 26 tests.

## Public / local evidence policy

Public repository evidence includes:

- final positive Live run
- final semantic-negative / Refine Live run
- sanitized offline replay evidence

Local-only evidence includes intermediate authentication, debugging, and failure runs, plus original offline replay manifests containing local absolute paths.

The local-only runs are not required to reproduce or understand the final accepted Harness behavior.
