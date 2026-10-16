# B-6 Manual Refactoring vs AI Pipeline 최종 비교

## 1. 목적

이 문서는 B-6 종료를 위해 다음 두 결과를 비교한다.

- B-5에서 실제 수행한 Manual Refactoring
- B-6에서 실제 실행한 Canonical AI Refactoring Pipeline

두 결과는 evidence level이 다르다.

B-5에는 실제 production code, 실제 diff, 실제 characterization test 보존 evidence가 있다.

B-6에는 실제 AI proposal, Critique, Independent Eval, Validate,
Deterministic Final Decision evidence가 있다.

단 B-6에서는 AI-generated production patch를 materialize하지 않았다.

따라서 이 문서는 Manual code와 AI code의 실제 구현 비용,
실제 build 결과, 실제 regression 결과를 직접 비교하지 않는다.

---

## 2. Canonical Baseline

```text
BASELINE=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
```

이 baseline은 B-5 Characterization Test 안전망이 확보된
refactoring 시작점이다.

---

## 3. B-5 Manual Refactoring 범위

```text
MANUAL_START=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1

MANUAL_END=
81140a1f681405ffbdedf946dd584b5b734e8e2d
```

Manual Refactoring은 다음 4개 commit으로 진행됐다.

```text
4039cbcb1f2cf673112051446e1cf80ae80ef32a
refactor: extract ticket reservation state change

05505aeed7f452b97387af5b5a65e061af11dfbc
refactor: move reservation state change to Ticket

9005e02eb0b1e0663676e16f537e7f6e6b35d0e4
refactor: move ticket reservation validation to Ticket

81140a1f681405ffbdedf946dd584b5b734e8e2d
refactor: encapsulate ticket reservation state
```

실제 net production changed files:

```text
Ticket.java
TicketService.java
```

```text
MANUAL_ACTUAL_CHANGED_FILE_COUNT=2
```

실제 net diff:

```text
2 files changed
9 insertions
8 deletions
```

새 production class/interface는 추가하지 않았다.

또한 Characterization Test blob은
MANUAL_START와 MANUAL_END에서 동일했다.

```text
CHARACTERIZATION_TEST_UNCHANGED=YES
```

---

## 4. B-5 Manual 실제 설계 결과

Baseline의 TicketService는 다음을 직접 수행했다.

```text
ticket.isReserved()

ticket.setReserved(true)
ticket.setUserId(userId)
```

Manual Refactoring 이후에는 다음으로 변경됐다.

```text
ticket.validateReservable()

ticket.reserveFor(userId)
```

따라서 Ticket이 다음 두 책임을 직접 소유하게 됐다.

```text
예약 가능 여부 검증
예약 상태 전이
```

또한 다음 public mutation method가 제거됐다.

```text
setReserved(boolean)
setUserId(Long)
```

즉 Manual 결과는:

```text
validation ownership
+
state-transition ownership
```

을 모두 Ticket으로 이동시키고,
예약 상태를 외부 setter로 직접 변경하는 경로를 제거했다.

---

## 5. B-6 Canonical AI Run

Run 1:

```text
RUN_ID=
b6-canonical-20261016T101504Z

RESULT=
INCOMPLETE_PROVIDER_AUTH_FAILURE

ROOT_CAUSE=
CLAUDE_OAUTH_EXPIRED
```

Run 1은 canonical evaluation 결과로 사용하지 않는다.

Run 2:

```text
RUN_ID=
b6-canonical-postauth-20261016T102757Z

EXECUTION_STATUS=
COMPLETE

FINAL_DECISION=
REJECT
```

Run 2에서는 실제로 다음 전체 pipeline이 실행됐다.

```text
Gen
→ Critique
→ Independent Eval
→ Validate
→ Deterministic Final Decision
```

---

## 6. Actual Gen Proposal

Gen schema validation:

```text
GEN_SCHEMA_RESULT=PASS
```

실제 Gen 구조:

```text
AI_GEN_DIAGNOSIS_COUNT=2
AI_GEN_PROPOSED_CHANGE_COUNT=1
RISK_COUNT=3
VALIDATION_PLAN_COUNT=4
```

Gen이 제안한 affected production files:

```text
Ticket.java
TicketService.java
```

추가 production architecture layer는 제안하지 않았다.

---

## 7. AI Diagnosis

### D1

```text
D1_RESERVATION_STATE_TRANSITION_OWNED_BY_SERVICE
```

AI는 TicketService가 application orchestration뿐 아니라
Ticket 자신의 예약 상태 전이까지 직접 수행하고 있다고 진단했다.

AI는 repository lookup, payment 호출, persistence 같은 orchestration 자체를
문제로 보지 않았다.

문제는 Ticket의 예약 상태 변경 규칙이
TicketService에 있다는 점이라고 판단했다.

### D2

```text
D2_ANEMIC_TICKET_WITH_UNENCAPSULATED_RESERVATION_INVARIANT
```

AI는 예약 완료 시 다음 두 상태가 함께 변경되어야 한다고 진단했다.

```text
reserved=true
userId=requesting user
```

그러나 baseline에서는 이 상태가 각각 독립적인 setter로 노출돼 있었다.

따라서 AI는 Ticket이 reservation intent를 표현하는
domain operation을 가져야 한다고 판단했다.

---

## 8. AI Proposed Design

AI Gen의 실제 proposed change는 1개다.

```text
C1_INTRODUCE_TICKET_RESERVE_OPERATION
```

Ticket에 다음 operation을 추가하는 제안이다.

```text
Ticket.reserve(Long userId)
```

그리고 TicketService의:

```text
ticket.setReserved(true)
ticket.setUserId(userId)
```

를:

```text
ticket.reserve(userId)
```

로 교체하도록 제안했다.

호출 위치는 기존 state mutation과 동일하게:

```text
payment 성공 이후
→ ticket.reserve(userId)
→ ticketRepo.save(ticket)
```

순서를 유지하도록 했다.

그러나 AI는 already-reserved validation은 TicketService에 유지했다.

또한 다음 setter도 제거하지 않았다.

```text
setReserved(boolean)
setUserId(Long)
```

AI는 이를 existing public contract로 간주해 보존하는 쪽을 선택했다.

따라서 AI proposal은:

```text
state-transition ownership
```

은 Ticket으로 이동했지만,

```text
validation ownership
public setter encapsulation
```

까지는 이동시키지 않았다.

---

## 9. Manual vs AI Diagnosis 비교

### 공통점

Manual과 AI 모두 다음 문제를 동일하게 보았다.

```text
TicketService가 Ticket의 예약 상태 변경을 직접 수행한다.
```

둘 다 예약 상태 전이 책임을 Ticket으로 옮기는 방향을 선택했다.

따라서:

```text
MANUAL_AI_DIAGNOSIS_OVERLAP=YES
```

### 차이점

Manual actual design은 already-reserved validation까지
Ticket으로 이동시켰다.

AI Gen은 validation ordering과 evidence 범위를 보수적으로 해석해
validation을 TicketService에 유지했다.

Manual은 public reservation-state setter를 제거했다.

AI는 public contract 보존을 이유로 setter를 유지했다.

따라서:

```text
MANUAL_AI_DESIGN_OVERLAP=PARTIAL
```

---

## 10. Responsibility Placement 비교

| Concern | B-5 Manual actual | B-6 AI proposal |
|---|---|---|
| Application orchestration | TicketService | TicketService |
| User lookup | TicketService | TicketService |
| Payment call | TicketService | TicketService |
| Persistence | TicketService | TicketService |
| Reservation state transition | Ticket | Ticket |
| Reservation validation | Ticket | TicketService |
| Public reservation setters | 제거 | 유지 |

공통 방향은 reservation state ownership을 Ticket으로 이동하는 것이다.

차이는 encapsulation을 어디까지 수행했는가에 있다.

---

## 11. Change Minimality

### Manual actual

실제 production changed files:

```text
Ticket.java
TicketService.java
```

```text
MANUAL_ACTUAL_CHANGED_FILE_COUNT=2
```

새 production class/interface:

```text
NO
```

### AI proposal

Gen이 제안한 production affected files:

```text
Ticket.java
TicketService.java
```

새 production architecture layer는 제안하지 않았다.

그러나 validation plan V4에서는 Ticket.reserve(Long)에 대한
focused unit test 추가를 제안했다.

동시에 V2에서는 baseline 대비
Ticket.java와 TicketService.java만 변경되어야 한다고 적었다.

따라서 V4와 V2 사이에는 scope inconsistency가 존재한다.

AI production patch가 materialize되지 않았으므로
실제 AI changed-file count와 Manual actual changed-file count를
직접 비교하지 않는다.

---

## 12. Overengineering 관찰

Canonical fixture는 speculative payment abstraction을
검토 가능한 대상으로 포함했다.

그러나 Gen은 다음을 제안하지 않았다.

```text
PaymentPort
PaymentSelector
```

또한 Gen은 다음 근거로 추가 payment abstraction을 명시적으로 제외했다.

```text
두 번째 payment method 없음
증명된 variation point 없음
증명된 layering problem 없음
```

따라서:

```text
AI_PAYMENT_PORT_PROPOSED=NO
AI_PAYMENT_SELECTOR_PROPOSED=NO
SPECULATIVE_PAYMENT_ABSTRACTION_PROPOSED=NO
```

이는 overengineering 방지 rule이 실제 proposal에 영향을 준 evidence다.

---

## 13. Behavior Preservation

### Manual

B-5 Manual Refactoring은 실제 production code를 변경했다.

그러나 Characterization Test blob은
MANUAL_START와 MANUAL_END에서 동일했다.

```text
CHARACTERIZATION_TEST_UNCHANGED=YES
```

### AI

Gen은 다음 behavior를 보존 대상으로 명시했다.

```text
B1_VALID_RESERVATION
B2_MISSING_USER
B3_ALREADY_RESERVED
B4_PAYMENT_FAILURE
```

그리고 conceptual ordering을 다음과 같이 유지했다.

```text
user lookup
→ reservation check
→ payment
→ reservation state transition
→ save
```

하지만:

```text
AI_CODE_MATERIALIZED=NO
```

이므로 이는 proposal-level behavior preservation claim이다.

실제 AI implementation regression evidence는 아니다.

---

## 14. Testability 비교

AI Gen은 다음 operation에 대한 focused unit test를 제안했다.

```text
Ticket.reserve(Long)
```

Eval은 이를 실제이지만 제한적인 testability improvement로 평가했다.

그러나 Critique는 다음 두 문제를 지적했다.

1. V4의 새 test file이 affected scope / V2 diff rule과 충돌한다.
2. V4는 userId를 읽어 검증해야 하지만 evidence에는 readable userId accessor가 없다.

또한 public setters가 그대로 남아 있기 때문에
reservation invariant는 object boundary에서 완전히 enforce되지 않는다.

따라서 AI implementation이 Manual implementation보다
실제 testability가 더 좋았다고 주장하지 않는다.

---

## 15. Critique 결과

Actual Critique에는 3개의 semantic issue가 있었다.

```text
I1_V4_ADDITIVE_TEST_CONTRADICTS_DECLARED_SCOPE_AND_V2

I2_V4_ASSERTS_USERID_WITHOUT_AN_EVIDENCED_ACCESSOR

I3_D2_INVARIANT_CLAIM_OVERSTATED_GIVEN_RETAINED_SETTERS
```

이 세 issue는 실제 proposal에 대한 substantive review 결과다.

별도로 Critique output은 required field를 누락했다.

```text
related_diagnosis_ids
related_change_ids
```

따라서:

```text
CRITIQUE_CONTENT_ISSUES=3
CRITIQUE_SEMANTIC_CONTENT=EXISTS
CRITIQUE_CONTRACT_COMPLIANCE=FAIL
CRITIQUE_SCHEMA_RESULT=REJECT
```

Semantic content와 contract compliance를 서로 다른 차원으로 기록한다.

---

## 16. Independent Eval 결과

Actual Eval:

```text
DIAGNOSIS_ACCURACY=5
CHANGE_MINIMALITY=4
BEHAVIOR_PRESERVATION_RISK=5
TESTABILITY_IMPROVEMENT=3

EVAL_TOTAL=17
EVIDENCE_SUFFICIENCY=SUFFICIENT
```

Numeric threshold 자체는 충족했다.

그러나:

```text
high Eval score
!=
pipeline PASS
```

였다.

즉 Eval은 최종 권한이 아니라
pipeline decision을 구성하는 하나의 evidence source로 작동했다.

---

## 17. Validate 결과

Actual Validate:

```text
VALIDATE_RESULT=FAIL
```

Failed gates:

```text
SCHEMA_CHECK
TEST_GATE
BUILD_COMPILE_GATE
CHARACTERIZATION_REGRESSION_GATE
ALLOWED_DIFF_SCOPE_GATE
UNAPPROVED_PUBLIC_CONTRACT_CHANGE_GATE
EVIDENCE_REFERENCE_GATE
```

이 실패들은 동일한 의미가 아니다.

### 실제 runtime contract failure

```text
SCHEMA_CHECK
```

Critique output이 required schema를 충족하지 못했기 때문에
실제로 실패한 contract gate다.

### Materialized patch evidence 부재

B-6 runner는 AI-generated production patch를 materialize하지 않았다.

따라서 다음 실제 patch evidence가 존재하지 않았다.

```text
test command / exit evidence
build command / exit evidence
characterization regression evidence
actual diff-scope evidence
actual public-contract diff evidence
```

따라서:

```text
B6_TEST_FAILED
B6_BUILD_FAILED
```

를 실제 AI patch의 test failure 또는 compile failure로 해석하면 안 된다.

실제 AI production patch 자체가 존재하지 않았기 때문이다.

---

## 18. Deterministic Final Decision

Actual runtime evidence:

```text
EVAL_TOTAL=17
EVIDENCE_SUFFICIENCY=SUFFICIENT
VALIDATION_STATUS=FAIL
CRITIQUE_BLOCKERS=3

FINAL_DECISION=REJECT
```

모든 Eval axis가 threshold를 통과했더라도
Critique blockers와 hard-gate failure가 유지됐다.

Deterministic Final Decision은 이를 override하지 않고
최종 결과를 REJECT로 확정했다.

Canonical REJECT 결과는 tuning이나 AI rerun 없이 그대로 보존한다.

---

## 19. Evidence Level 차이

### B-5 Manual

```text
ACTUAL CODE
ACTUAL DIFF
ACTUAL CHARACTERIZATION TEST PRESERVATION
```

### B-6 AI

```text
ACTUAL AI PROPOSAL
ACTUAL CRITIQUE
ACTUAL EVAL
ACTUAL VALIDATE
ACTUAL DETERMINISTIC FINAL DECISION
```

그러나:

```text
AI_CODE_MATERIALIZED=NO
AI_ACTUAL_DIFF_AVAILABLE=NO
AI_ACTUAL_BUILD_EVIDENCE=NO
AI_ACTUAL_CHARACTERIZATION_EVIDENCE=NO
```

따라서:

```text
DIRECT_MANUAL_VS_AI_CODE_COST_COMPARISON=NO
```

를 유지한다.

---

## 20. B-6이 입증한 것

B-6은 다음을 입증했다.

1. Frozen canonical fixture를 이용해 B-5 manual solution 자체를 정답으로 노출하지 않고 AI refactoring proposal을 생성할 수 있었다.
2. Gen / Critique / Eval / Validate / Final Decision을 명시적인 contract로 분리할 수 있었다.
3. AI output schema compliance가 실제 runtime quality gate로 작동했다.
4. Independent Eval의 높은 score가 hard constraint를 override하지 못했다.
5. Evidence Sufficiency를 별도의 명시적 gate로 유지할 수 있었다.
6. Deterministic Final Decision이 AI self-verdict 대신 최종 권한으로 작동했다.
7. Unsupported PaymentPort / PaymentSelector abstraction을 제안하지 않는 overengineering restraint가 실제 proposal에서 확인됐다.
8. Canonical AI result가 REJECT여도 결과를 tuning하지 않고 그대로 보존할 수 있었다.

---

## 21. B-6이 입증하지 못한 것

B-6은 다음을 입증하지 못했다.

```text
실제 AI-generated production patch

실제 AI changed-file count

실제 AI compile 성공/실패

실제 AI characterization regression 성공/실패

실제 AI public-contract diff

Manual vs AI 실제 구현 비용 직접 비교

AI implementation이 Manual implementation보다 우월하거나 열등하다는 주장
```

Evidence보다 강한 주장을 새로 만들지 않는다.

---

## 22. B-5 Causal Limitation 보존

B-5에는 이미 다음 limitation이 있었다.

```text
Original baseline에 동일한 Point Payment change를
별도로 구현한 direct A/B가 없다.
```

B-6 비교에서도 이 limitation을 제거하지 않는다.

따라서 기존 실험 evidence보다 강한 causal claim을 만들지 않는다.

---

## 23. 최종 결론

B-5 Manual과 B-6 AI Proposal은 다음 중요한 설계 방향에서 일치했다.

```text
TicketService가 직접 수행하던 reservation state-transition behavior를
Ticket으로 이동한다.
```

그러나 Manual actual implementation은 더 나아가:

```text
reservation validation ownership을 Ticket으로 이동
public reservation-state setters 제거
```

까지 수행했다.

AI proposal은 더 보수적으로:

```text
state transition은 Ticket으로 이동
validation은 TicketService에 유지
public setters 유지
```

를 선택했다.

AI proposal은 Independent Eval에서 높은 점수를 받았지만,
Critique에서 3개의 substantive issue가 발견됐고
Critique schema contract도 충족하지 못했다.

또한 materialized AI patch가 없었기 때문에
실제 test/build/diff/regression evidence는 존재하지 않았다.

Deterministic pipeline의 canonical result는:

```text
FINAL_DECISION=REJECT
```

다.

이 REJECT 결과는 그대로 보존한다.

MASTER가 B-6을 PASS로 판정한다면 그 의미는:

```text
AI proposal 자체가 PASS했다
```

가 아니다.

의미는 다음과 같다.

```text
AI Refactoring Pipeline을 설계하고
Gen / Critique / Eval / Validate contract를 구현하고
Frozen canonical fixture로 실제 실행하고
runtime evidence를 보존하고
Deterministic Final Decision까지 작동시키고
결과가 REJECT여도 tuning하지 않고 보존하고
Manual reference와 비교하고
실험의 한계를 정확하게 기록했다.
```
