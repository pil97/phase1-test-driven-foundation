# Phase 1-1 테스트 주도 기반 구축

## 목적

이 학습 프로젝트는 서로 연결된 세 단계로 진행합니다.

```text
TDD
→ BDD / Acceptance
→ Requirement-to-Test Harness
```

목표는 요구사항을 실행 가능한 형태로 만들고, 경계조건 결함을 이른 시점에 드러내며, AI가 생성한 제안과 deterministic validation 및 최종 판단 권한을 분리하는 것입니다.

## 실행 환경

- Java
- Gradle Wrapper
- JUnit
- AssertJ
- Mockito
- Cucumber
- Python
- jsonschema
- PyYAML

Claude Code는 A-5 Harness에서 선택적인 Live AI role executor로 사용할 수 있습니다. Claude Code 자체가 Harness의 authority는 아니며 최종 PASS/REJECT 판단 권한도 갖지 않습니다.

## A-3 — TDD / Seat HOLD

A-3에서는 작은 Seat HOLD 도메인에 TDD를 적용하고 시간 경계조건을 명시적으로 다뤘습니다.

핵심 요구사항:

1. AVAILABLE 좌석 → HOLD 성공
2. 유효한 HELD 좌석(`now < expiresAt`) → 재-HOLD 거절
3. 만료된 HELD 좌석 → 재-HOLD 허용
4. 정확한 경계(`now == expiresAt`) → 만료로 취급하여 재-HOLD 허용

`SeatHoldServiceTest`에서는 repository 상호작용 흐름도 검증합니다.

`lookup -> HOLD -> save`

실습 중 의도적으로 비교 연산 결함을 넣었고, 정확한 equality 경계 테스트가 잘못된 경계 semantics를 검출한 뒤 올바른 구현으로 복구했습니다.

## A-4 — BDD / Acceptance

A-4에서는 같은 도메인 요구사항을 실행 가능한 Cucumber acceptance scenario로 옮겼습니다.

Acceptance layer 구성:

- Gherkin Feature
- Step Definitions
- Cucumber runner
- in-memory repository test double

Feature만 정의한 초기에는 Undefined Step RED 상태였고, 누락된 실행 Step을 구현한 뒤 Acceptance GREEN으로 전환했습니다.

별도의 AI implementation candidate도 평가했습니다. candidate의 self-evaluation, frozen acceptance contract, 기존 A-3 테스트를 함께 비교하면서 서로 다른 evaluation scope가 서로 다른 종류의 실패를 검출할 수 있음을 확인했습니다.

## A-5 — Requirement → Test Harness

A-5에서는 AI-assisted test candidate generation을 둘러싼 Harness를 구현했습니다.

Phase 0의 Harness v0는 수동으로 운용한 Harness였고, A-5에서는 구조 계약, deterministic validator, semantic Eval, deterministic decision/lifecycle을 분리해 실행 가능한 형태로 발전시켰습니다.

```text
Requirement Fixture
→ Gen
→ Deterministic Candidate Gate
→ Critique
→ Independent Eval
→ Deterministic Decision
→ PASS or Refine
```

Harness 구성:

- JSON Schema: 구조 계약
- YAML Rubric: semantic Eval 기준
- Gen: 최초 test candidate 생성
- Critique: 최종 점수 권한 없이 문제 탐색
- Independent Eval: rubric 기준 의미 품질 평가
- Refine: REJECT된 iteration 이후 개선
- deterministic code: 최종 score 계산, threshold 적용, PASS/REJECT 및 lifecycle 판단

전체 semantic evaluation이 deterministic한 것은 아닙니다. Independent AI Eval이 의미 품질을 평가하고, deterministic Runner가 그 결과를 바탕으로 최종 score 계산, threshold, lifecycle을 담당합니다.

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

`min_total`과 `min_axis`는 YAML rubric에서 가져오며, `MAX_ITERATIONS`는 runner lifecycle configuration입니다.

Frozen test PASS는 테스트에 인코딩된 계약 범위가 유지됨을 보장할 뿐, 그 밖의 모든 의미 품질까지 자동으로 증명하지는 않습니다.

## 실행 방법

### Java 테스트

```bash
JAVA_HOME=$(/usr/libexec/java_home -v 25) \
./gradlew clean test
```

### Python Harness 테스트

임시 환경을 만들고 고정된 Harness dependency를 설치합니다.

```bash
python3 -m venv /tmp/phase1-a5-venv
/tmp/phase1-a5-venv/bin/python -m pip install -r a5-harness/requirements.txt
```

Deterministic test suite 실행:

```bash
PYTHONPATH=a5-harness/src \
/tmp/phase1-a5-venv/bin/python -m unittest discover \
  -s a5-harness/tests \
  -v
```

최종 검증된 suite는 Python 테스트 26개입니다.

### Live AI 실행

A-5 Live role execution은 deterministic offline reproduction과 분리되어 있습니다.

Live 실행에는 호환되는 Claude Code 설치와 provider authentication/environment availability가 필요합니다. Live role을 AI가 실행하더라도 최종 판단은 deterministic Harness logic이 담당합니다.

## 검증 결과

최종 제출 검증 기준:

- Python Harness tests: `26/26 PASS`
- Gradle: `BUILD SUCCESSFUL`
- A-3/A-4 authoritative baseline: `12/12 unchanged`
- 공개 파일 집합: `119 files`
- selected Live evidence와 sanitized offline evidence만 공개

## 검증 기록

- [A-3 TDD 검증 기록](docs/evidence/A3-TDD-EVIDENCE.md)
- [A-4 BDD / Acceptance 검증 기록](docs/evidence/A4-BDD-EVIDENCE.md)
- [A-5 Harness 검증 기록](docs/evidence/A5-HARNESS-EVIDENCE.md)

공개 A-5 evidence에는 최종 선택된 Live run과 sanitized offline replay summary만 포함합니다.

중간 authentication/debug/failure run과 local absolute path가 포함된 original offline manifest는 local-only로 유지합니다.

## 범위 및 제외 사항

- 이 repository는 production ticketing application이 아니라 Phase 1-1 학습 프로젝트입니다.
- Spring 및 database infrastructure는 이번 범위에서 의도적으로 제외했습니다.
- 생성된 Java 또는 Cucumber output을 source tree에 자동 적용하지 않습니다.
- AI role output을 최종 판단 authority로 취급하지 않습니다.
- 상세 학습 과정, 판단 변화, 회고는 별도로 Notion에 정리합니다.

GitHub repository에는 전체 학습 일지보다 코드, 재현 방법, 선택된 실행 evidence를 중심으로 담습니다.
