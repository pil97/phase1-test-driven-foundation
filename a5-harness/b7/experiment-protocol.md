# B-7 Prompt / Design Constraint A/B 비교 실험 Protocol

## 1. 목적

이 실험은 동일한 티켓 예약 baseline에 대해
두 가지 AI 리팩터링 조건을 적용하고 결과를 비교한다.

핵심 질문은 다음과 같다.

> 동일한 요구사항에서 설계 제약을 거의 주지 않은 경우와,
> 문제 정의 및 설계 제약을 명시한 경우가
> 설계 결정, 책임 배치, abstraction 수, 변경 범위,
> behavior-preservation 위험, testability,
> 이후 Point Payment 변경비용에 어떤 차이를 만드는가?

이 실험은 특정 prompting 방식이 항상 더 우수하다는
일반 법칙을 증명하는 것이 아니다.

최종 결론은 이 Protocol에서 정의한
두 canonical execution에서 실제로 관찰된 차이로 제한한다.

---

## 2. 동결 Baseline

```text
B7_BASELINE=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
```

이 commit은 B-5 manual refactoring이 시작되기 전의 원본 구현이며,
TicketService characterization safety net은 이미 존재하는 상태다.

B-5 manual refactoring은 이 baseline 이후에 시작된다.

다음 항목은 비교 reference로만 사용한다.

- B-5 manual refactoring 결과
- B-6 proposal/result
- 이후 Point Payment 구현

이 항목들은 AI execution input으로 제공하지 않는다.

---

## 3. 공통 초기 요구사항

Prompt A와 Prompt B에는 다음 요구사항을 동일하게 제공한다.

```text
제공된 티켓 예약 구현의 설계를 개선하도록 리팩터링하라.

현재 관찰 가능한 티켓 예약 동작은 변경하지 않는다.

리팩터링을 실제 코드에 구현하고,
기존 test/build safety net을 이용해 결과를 검증하라.
```

초기 리팩터링 실험에는 Point Payment 요구사항을 포함하지 않는다.

---

## 4. 공통 Source Context

Prompt A와 Prompt B는 모두 다음 commit에서 추출한
동일한 repository snapshot을 입력으로 사용한다.

```text
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
```

snapshot에는 해당 commit에 존재하는 production source와 test가 포함된다.

여기에는 TicketServiceCharacterizationTest도 포함된다.

AI에는 다음 내용을 제공하지 않는다.

- 이후 B-5 manual refactoring commit
- B-5 manual 최종 구현
- Point Payment 구현
- Point Payment test
- B-6 canonical proposal
- B-6 critique
- B-6 evaluation
- B-6 manual-vs-AI comparison
- 다른 A/B condition에서 생성된 결과

---

## 5. Prompt A — 낮은 Constraint 조건

Prompt A 원문은 다음으로 동결한다.

```text
제공된 티켓 예약 구현의 설계를 개선하도록 리팩터링하라.

현재 관찰 가능한 티켓 예약 동작은 변경하지 않는다.

리팩터링을 실제 코드에 구현하고,
기존 test/build safety net을 이용해 결과를 검증하라.
```

Prompt A는 설계 결정을 상당 부분 AI에게 위임하는 조건이다.

다음을 미리 지정하지 않는다.

- 특정 architecture
- 특정 target class
- 특정 target method
- 책임 이동 방향
- setter 제거
- payment abstraction
- extension point
- design pattern
- 미래 Point Payment 구조

---

## 6. Prompt B — 명시적 Constraint 조건

Prompt B 원문은 다음으로 동결한다.

```text
제공된 티켓 예약 구현의 설계를 개선하도록 리팩터링하라.

현재 관찰 가능한 티켓 예약 동작은 변경하지 않는다.

코드를 변경하기 전에 다음을 수행하라.

1. 현재 코드에서 실제로 관찰되는 설계 문제 또는 책임 문제를
   구체적인 code evidence를 근거로 정의하라.

2. 현재 responsibility boundary를 확인하고,
   책임 이동이 필요하다고 판단한다면 그 이유를 설명하라.

3. 현재 characterization safety net이 포착하고 있는
   기존 observable behavior를 보존하라.

4. 현재 requirement와 현재 code evidence로
   정당화되는 변경만 수행하라.

5. 아직 존재하지 않는 미래 requirement만을 위해
   abstraction, layer, pattern, extension point,
   architecture를 추가하지 마라.

6. 구체적인 근거가 없다면
   기존 public contract 변경을 최소화하라.

7. 설계를 판단할 때 testability를 고려하라.

8. affected scope, 주요 risk,
   그리고 결과를 어떻게 validation할 것인지 설명하라.

특정 architecture나 정답 구조를 미리 가정하지 마라.

그 후 현재 evidence로 정당화되는
가장 작은 범위의 리팩터링을 구현하고,
기존 test/build safety net으로 결과를 검증하라.
```

Prompt B에도 B-5 manual solution은 제공하지 않는다.

특히 다음을 지시하지 않는다.

- 특정 Ticket method 생성
- 특정 validation 이동
- 특정 setter 제거
- 특정 payment interface 생성
- selector / strategy / factory / port 도입

---

## 7. A/B의 유일한 의도적 차이

실험에서 의도적으로 다르게 두는 것은 다음뿐이다.

```text
Prompt A
=
동일한 현재 requirement
+
낮은 design constraint

Prompt B
=
동일한 현재 requirement
+
명시적 problem/design constraint
```

그 외 통제 가능한 변수는 동일하게 유지한다.

---

## 8. Provider / Model 정책

두 canonical condition은 동일한 provider를 사용한다.

```text
PROVIDER=claude-code-cli
```

canonical execution 전에 다음 값을 확인하고 기록한다.

1. 실제 Claude executable
2. 정확한 Claude CLI version
3. 명시적으로 사용할 model
4. 실제 execution mechanism

Prompt A와 Prompt B는 반드시 다음을 동일하게 사용한다.

- 동일 Claude executable
- 동일 Claude CLI version
- 동일 explicit model argument
- 동일 execution mechanism

A/B 사이에 provider, CLI version, model이 다르면
canonical comparison을 시작하지 않는다.

model은 UNKNOWN 상태로 두지 않는다.

각 condition은 fresh provider process에서 실행한다.

A와 B 사이에 --continue 또는 --resume context를 공유하지 않는다.

---

## 9. Canonical Run 횟수

```text
PROMPT_A_CANONICAL_RUN_COUNT=1
PROMPT_B_CANONICAL_RUN_COUNT=1
```

결과가 마음에 들지 않는다는 이유로 재실행하지 않는다.

명확한 infrastructure/provider failure가 발생하면
해당 evidence를 보존한다.

더 좋은 결과를 얻기 위한 sample-shopping 목적으로 rerun하지 않는다.

---

## 10. 실행 Isolation 전략

Prompt A와 Prompt B는 exact frozen baseline에서
git archive로 추출한 독립 snapshot을 사용한다.

개념적으로 다음과 같다.

```text
baseline commit
        |
        +---- isolated snapshot A
        |
        +---- isolated snapshot B
```

각 snapshot은 다음 조건을 만족해야 한다.

- 동일 baseline의 tracked file을 포함
- 동일 commit에서 시작
- 서로 production 수정 상태를 공유하지 않음
- .git history를 포함하지 않음
- 이후 B-5/B-6 commit을 repository history를 통해 확인할 수 없음
- 다른 condition의 output을 입력으로 받지 않음

현재 main working branch를
A/B의 mutable execution workspace로 사용하지 않는다.

---

## 11. 초기 결과 측정 지표

### 객관적 / 기계적으로 측정 가능한 항목

각 A/B initial result에서 다음을 기록한다.

- 변경된 production file 수
- 새 production file 수
- 변경된 class 수
- 새 class 수
- 변경된 method 수
- 새 method 수
- interface 수 변화
- public contract 변화
- diff 추가 line 수
- diff 삭제 line 수
- 변경된 test file 수
- 새 test file 수
- package/layer spread
- build 결과
- test 결과
- characterization regression 결과

### Semantic Review 항목

각 결과에서 다음을 검토한다.

- 변경 후 TicketService의 responsibility
- 변경 후 Ticket의 responsibility
- payment 관련 abstraction 수
- 새 extension point
- future-oriented abstraction
- behavior-preservation 전략
- design decision의 근거
- affected scope의 정당성
- testability 영향

기계적 metric과 semantic judgment를 혼합하지 않는다.

---

## 12. 동결된 Point Payment 후속 요구사항

초기 Prompt A와 Prompt B 결과가 각각 동결된 이후,
양쪽 condition에 다음과 같은 동일한 후속 requirement를 제공한다.

```text
티켓 결제 수단으로 포인트 결제를 지원하라.

포인트 결제 시 지정된 포인트 계정의 잔액이
티켓 가격 이상이면 결제는 성공한다.

결제가 성공하면 해당 포인트 잔액에서
티켓 가격과 정확히 동일한 금액을 차감한다.

포인트 잔액이 부족하면 결제는 실패하며,
포인트는 차감되지 않아야 한다.

기존에 보존된 티켓 예약 동작을 변경하지 않으면서
이 기능을 현재 티켓 예약 흐름에 통합하라.
```

이 requirement는 behavior만 규정한다.

다음을 미리 알려주지 않는다.

- class 이름
- interface 이름
- repository 이름
- 구현 pattern
- selector
- factory
- strategy
- port
- package 구조

---

## 13. Point Payment Reference 격리

과거 B-5 Point Payment 구현은 comparison-only evidence로 사용한다.

해당 구현의 이름과 source 구조를 AI input으로 제공하지 않는다.

B-5 Point Payment reference 구현은
A/B execution artifact가 필요한 수준까지 모두 동결된 이후에만
comparison을 위해 확인한다.

---

## 14. Point Payment 변경비용 측정 지표

동일한 Point Payment 후속 requirement를 적용한 뒤 다음을 측정한다.

### 객관적 / 기계적으로 측정 가능한 항목

- 다시 수정된 기존 production file 수
- 새 production file 수
- 다시 수정된 기존 class 수
- 새 class 수
- 새 interface 수
- 변경된 method 수
- 추가된 method 수
- public contract 변화 수
- diff 추가 line 수
- diff 삭제 line 수
- 변경된 test file 수
- 새 test file 수
- package/layer spread

### Semantic Review 항목

- payment abstraction 증가량
- TicketService 수정 필요 여부
- Ticket 수정 필요 여부
- 기존 설계를 우회하는 코드 필요 여부
- 기존 abstraction이 실제 변경비용을 줄였는지
- 기존 abstraction이 오히려 unused/duplicate structure를 만들었는지

---

## 15. Overengineering 측정 기준

class 또는 pattern 이름만 보고 overengineering을 판정하지 않는다.

최소 다음을 검토한다.

- 현재 requirement로 정당화되지 않는 abstraction
- duplicate interface
- duplicate payment abstraction
- future-only extension point
- 불필요한 strategy/factory/selector 구조
- 불필요한 architecture layer
- 현재 responsibility와 관계없는 package/layer spread
- abstraction justification과 실제 current pressure의 관계

모든 semantic judgment는 다음을 함께 고려한다.

```text
현재 requirement
+
실제 code pressure
+
추가된 abstraction
+
명시되거나 추론 가능한 justification
```

---

## 16. Behavior Preservation

두 initial condition은 동일한 characterization behavior를 기준으로 한다.

단순히 test suite가 PASS했다는 사실만으로 비교를 끝내지 않는다.

다음도 함께 기록한다.

- 어떤 behavior-preservation risk가 존재했는가
- 해당 risk를 제어하기 위해 어떤 design decision을 사용했는가
- public behavior가 변경되었는가
- 기존 characterization coverage가 계속 유효한가
- 새 test가 단순 evidence 추가인지 contract 변화까지 만들었는가

---

## 17. Solution Leakage 차단 규칙

```text
B5_MANUAL_SOLUTION_EXPOSED_TO_A=NO
B5_MANUAL_SOLUTION_EXPOSED_TO_B=NO

B6_SOLUTION_EXPOSED_TO_A=NO
B6_SOLUTION_EXPOSED_TO_B=NO

B5_POINT_PAYMENT_SOLUTION_EXPOSED_TO_A=NO
B5_POINT_PAYMENT_SOLUTION_EXPOSED_TO_B=NO
```

Prompt A와 Prompt B는 각 단계에서 다음만 확인할 수 있다.

- frozen baseline snapshot
- 현재 experiment stage에 제공된 requirement

다른 solution reference는 입력으로 제공하지 않는다.

---

## 18. 인과 해석의 한계

이 실험은 condition별 canonical execution을 1회씩 사용한다.

따라서 최종적으로 주장할 수 있는 범위는 다음과 같다.

```text
이 두 canonical execution에서 관찰된 차이
```

다음과 같은 일반 법칙은 이 실험으로 증명하지 않는다.

```text
Prompt B는 항상 Prompt A보다 우수하다.
```

또는 그 밖의 universal prompt-performance claim을 하지 않는다.

---

## 19. B-6 Artifact 보호

B-7 작업에서는 이미 동결된 B-6 artifact를 수정하지 않는다.

최소 다음을 포함한다.

```text
a5-harness/b6/
a5-harness/runs/b6-*
B-6 prompts
B-6 schemas
B-6 rubric
B-6 runner
B-6 comparison evidence
```

B-7 artifact는 별도의 다음 영역에 둔다.

```text
a5-harness/b7/
```

---

## 20. 문서 언어 정책

B-7의 문서성 artifact는 한국어를 canonical 언어로 사용한다.

자연어 section heading, 설명, 판단, risk, validation,
comparison narrative는 한국어로 작성한다.

다만 다음 기술 식별자는 필요한 경우 영어를 유지한다.

- 코드
- 명령어
- 경로
- class / method / interface 이름
- schema key
- machine-readable key/value
- commit hash
- provider/model 식별자
- 실험 식별자로 사용되는 Prompt A / Prompt B 등

기존 B-7 문서에 영어 자연어 본문이 존재하면
후속 작업 전에 의미와 evidence를 변경하지 않는 범위에서
한국어 canonical 문서로 수정한다.

새 문서는 처음부터 한국어로 작성한다.

---

## 21. WORK-1 동결 값

```text
B7_BASELINE=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1

PROMPT_A_FROZEN=YES
PROMPT_B_FROZEN=YES

COMMON_REQUIREMENT_FROZEN=YES
COMMON_SOURCE_CONTEXT_FROZEN=YES

POINT_PAYMENT_REQUIREMENT_FROZEN=YES

PROMPT_A_CANONICAL_RUN_COUNT=1
PROMPT_B_CANONICAL_RUN_COUNT=1

PROVIDER=claude-code-cli

PROVIDER_MODEL_POLICY=
A/B는 동일 executable + 동일 CLI version + 동일 explicit model 사용

INITIAL_METRICS_FROZEN=YES
CHANGE_COST_METRICS_FROZEN=YES
OVERENGINEERING_METRICS_FROZEN=YES

ISOLATION_STRATEGY=
공유 .git history가 없는 독립적인 git-archive baseline snapshot 사용

DOCUMENT_LANGUAGE_POLICY=
KOREAN_CANONICAL

B5_MANUAL_SOLUTION_EXPOSED_TO_A=NO
B5_MANUAL_SOLUTION_EXPOSED_TO_B=NO
B5_POINT_PAYMENT_SOLUTION_EXPOSED=NO

AI_EXECUTED=NO
PRODUCTION_MODIFIED=NO
```
