# B-7 Prompt A/B 최종 비교

## 1. 목적과 실험 질문

B-7은 동일한 티켓 예약 baseline에서 서로 다른 Prompt constraint가 AI 리팩터링 결과의 구조와 변경 범위에 어떤 차이를 만드는지 비교했다.

핵심 질문은 다음과 같다.

> Problem Definition과 Design Constraints의 명시 정도가 AI output scope를 실제로 통제하는가? 그리고 initial minimality와 이후 Point Payment 변경비용은 같은 방향으로 움직이는가?

이 문서는 WORK-2의 initial A/B evidence와 WORK-3의 Point Payment change-cost evidence를 함께 해석하는 B-7 최종 비교 artifact다.

---

## 2. Protocol 요약

동결 baseline:

```text
B7_BASELINE=
8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
```

실험 조건:

```text
Prompt A
→ 낮은 design constraint

Prompt B
→ 명시적 problem/design constraint
→ evidence 기반
→ 최소 변경
→ future-only abstraction 금지
→ public contract 최소화
```

두 condition 모두 동일한 frozen baseline과 source context를 사용했고, Point Payment 요구사항은 initial execution input에서 제외했다.

Canonical run count:

```ini
PROMPT_A_CANONICAL_RUN_COUNT=1
PROMPT_B_CANONICAL_RUN_COUNT=1
```

Provider/model 정책은 A/B 사이에 동일 executable, 동일 CLI version, 동일 explicit model을 사용하는 것으로 동결했다.

이 실험의 해석 범위는 다음으로 제한한다.

```text
이 두 canonical executions에서 관찰된 결과
```

통계적 또는 보편적 prompt 우월성을 주장하지 않는다.

---

## 3. Initial A/B 비교

### 3.1 Objective metrics

| metric | Prompt A | Prompt B |
|---|---:|---:|
| changed production files | 2 | 2 |
| new production files | 0 | 0 |
| changed classes | 2 | 2 |
| new classes | 0 | 0 |
| new methods | 4 | 1 |
| removed methods | 2 | 2 |
| public contract added | 2 | 1 |
| public contract removed | 2 | 2 |
| diff added lines | 24 | 6 |
| diff deleted lines | 19 | 7 |

두 결과 모두 public setter를 제거하고 Ticket으로 state transition 책임을 이동했으며 기존 Characterization behavior를 보존했다.

### 3.2 설계 차이

Prompt A initial은 다음 decomposition을 만들었다.

```text
Ticket.ensureReservable()
Ticket.reserveFor(...)

TicketService.ensureUserExists(...)
TicketService.charge(...)
```

Prompt B initial은 다음과 같이 더 작은 command surface를 만들었다.

```text
Ticket.reserve(...)
```

Prompt A는 Ticket 책임 이동 외에도 service 내부 orchestration을 추가로 분해했다.

Prompt B는 state-transition 캡슐화에 직접 필요한 변경에 더 가까운 범위를 선택했다.

### 3.3 Initial observation

이 두 canonical executions의 initial 결과에서는 Prompt B가 다음 항목에서 더 작았다.

```text
new methods
new public contract
diff surface
```

따라서 initial minimality만 놓고 보면 Prompt B가 우세했다.

다만 이것은 최종 quality winner 판정이 아니다.

---

## 4. Point Payment change-cost 비교

동일한 frozen Point Payment 후속 requirement를 각 initial result에 적용했다.

### 4.1 Objective metrics

| metric | Prompt A | Prompt B |
|---|---:|---:|
| existing production files remodified | 1 | 1 |
| new production files | 3 | 4 |
| existing classes remodified | 1 | 1 |
| new classes | 2 | 3 |
| new interfaces | 1 | 1 |
| methods changed | 1 | 1 |
| methods added | 8 | 8 |
| methods removed | 0 | 0 |
| public contract changes | 11 | 12 |
| diff added lines | 254 | 289 |
| diff deleted lines | 1 | 8 |
| changed existing test files | 0 | 0 |
| new test files | 2 | 2 |
| package/layer spread | 1 | 1 |

이 두 canonical executions에서는 Prompt A-derived design이 Point Payment 추가 시 다음 surface에서 더 작았다.

```text
new production files
new classes
public contract changes
diff added/deleted lines
```

반면 기존 production file/class 재수정 수, method changed/added 수, test surface, package/layer spread는 동일했다.

---

## 5. Behavior equivalence

양쪽 모두 다음 validation을 통과했다.

| validation | Prompt A | Prompt B |
|---|---|---|
| Point Payment targeted test | PASS | PASS |
| full test | PASS | PASS |
| build | PASS | PASS |
| Characterization Test | PASS | PASS |
| 기존 Characterization Test 수정 | NO | NO |

따라서 최종 비교의 중심은 correctness 우열이 아니다.

비교 대상은 다음이다.

```text
change surface
public contract
existing abstraction reuse
service decomposition
follow-up change cost
```

---

## 6. Problem Definition / Design Constraints의 효과

Prompt A는 design constraint가 적었기 때문에 validation 분리, state transition 분리, service helper 분리, public contract 확장 범위와 service decomposition 정도를 AI가 더 많이 결정했다.

실제 initial 결과에서도 Prompt A는 Prompt B보다 더 넓은 decomposition과 더 큰 change surface를 만들었다.

Prompt B는 evidence 기반, 최소 변경, future-only abstraction 금지, public contract 최소화 조건을 명시적으로 제공했다.

실제 initial 결과에서는 Prompt B가 더 적은 new method, 더 작은 public surface, 더 작은 diff를 만들었다.

따라서 이 두 canonical executions에서는:

```text
PROMPT_CONSTRAINT_EFFECT=
OBSERVED_IN_ACTUAL_CODE_STRUCTURE_AND_INITIAL_CHANGE_SURFACE
```

라고 해석할 수 있다.

즉 Problem Definition과 Design Constraints의 차이가 실제 코드 구조와 initial scope 차이로 나타났다.

다만 이 결과를 "더 constrained한 prompt가 항상 더 좋다"는 일반 법칙으로 확대하지 않는다.

---

## 7. Initial minimality vs future change-cost

이번 B-7의 핵심 결과는 initial minimality와 follow-up change-cost가 같은 방향으로 움직이지 않았다는 점이다.

```text
Initial refactoring
→ Prompt B가 더 minimal

Point Payment follow-up
→ Prompt A-derived design이 더 작은 추가 change surface
```

Prompt A initial의 broader decomposition 중 다음 구조는 Point Payment 단계에서 실제로 재사용됐다.

```text
TicketService.ensureUserExists(...)
TicketService.charge(...)
Ticket.ensureReservable()
Ticket.reserveFor(...)
```

WORK-3 frozen interpretation:

```ini
PROMPT_A_EXISTING_ABSTRACTION_EFFECT=
CHANGE_COST_REDUCTION_CONTRIBUTION

PROMPT_B_EXISTING_ABSTRACTION_EFFECT=
PARTIAL_CHANGE_COST_REDUCTION_CONTRIBUTION
```

Prompt B의 `Ticket.reserve(...)` abstraction도 재사용됐지만, service orchestration 측면에서는 follow-up 단계에서 추가 decomposition이 필요했다.

따라서 이 canonical case에서는 다음 두 등식이 성립하지 않았다.

```text
initial diff가 더 작다
=
future change cost도 항상 더 작다
```

```text
initial diff가 더 크다
=
자동으로 과설계다
```

이는 "minimal initial surface"와 "potentially reusable decomposition" 사이의 trade-off를 보여준다.

---

## 8. Responsibility 비교

양쪽 모두 reservation state transition 책임을 Ticket으로 이동시켜 기존 setter 기반 mutation을 제거했다.

차이는 책임 이동의 범위에 있었다.

Prompt A는 domain state transition과 함께 service orchestration도 더 세분화했다.

Prompt B는 domain state transition encapsulation에 집중하고 service orchestration은 initial 단계에서 대부분 유지했다.

Point Payment 단계에서는 Prompt A의 일부 service/domain decomposition이 그대로 재사용됐고, Prompt B는 service orchestration decomposition을 추가했다.

따라서 broader responsibility decomposition 자체를 무조건 waste 또는 무조건 future-proofing으로 판정할 수 없다.

이번 case에서는 일부 decomposition이 실제 후속 변경에서 reuse benefit을 제공했다는 수준으로만 기록한다.

---

## 9. Overengineering 해석

Initial 결과:

```text
Prompt A
→ architecture-level overengineering evidence 없음
→ broader-than-minimum refactoring scope 관찰

Prompt B
→ overengineering evidence 없음
```

Point Payment 결과:

```ini
PROMPT_A_OVERENGINEERING_OBSERVATION=
NO_CLEAR_OVERENGINEERING_IN_CURRENT_CHANGE

PROMPT_B_OVERENGINEERING_OBSERVATION=
NO_ARCHITECTURAL_OVERENGINEERING_WITH_EXTRA_PUBLIC_EXCEPTION_SURFACE
```

Prompt A의 broader initial decomposition은 initial requirement만 보면 최소 범위보다 넓었지만, Point Payment change에서 일부가 실제 재사용됐다.

Prompt B는 follow-up에서도 architecture-level abstraction explosion을 만들지 않았지만 `InsufficientPointBalanceException`이라는 추가 public exception surface가 생겼다. Frozen requirement는 별도 exception type을 요구하지 않았다.

따라서 다음과 같은 이분법은 사용하지 않는다.

```text
Prompt A = 과설계
Prompt B = 적정설계
```

Overengineering은 class/pattern 수만으로 판정할 수 없고, 현재 requirement와 실제 change evidence를 함께 봐야 한다.

---

## 10. Testability

Initial 단계에서 양쪽 모두 Ticket invariant를 domain object로 이동시켜 구조적으로 직접적인 domain behavior 검증이 가능한 형태를 만들었다.

Prompt A는 `ensureReservable()`을 별도 public method로 노출했고, Prompt B는 `reserve(...)` command 안에서 invariant와 state transition을 함께 다루었다.

그러나 WORK-2에서는 새 test coverage 증가가 없었다.

따라서 다음 둘을 구분한다.

```text
design testability
actual test coverage
```

Point Payment 단계에서는 양쪽 모두 새 Point Payment test를 추가했고 targeted/full/build/Characterization validation을 통과했다.

---

## 11. Public contract

Initial public contract addition:

```text
Prompt A = 2
Prompt B = 1
```

Point Payment public contract changes:

```text
Prompt A = 11
Prompt B = 12
```

Prompt B의 follow-up 결과에는 `InsufficientPointBalanceException`이라는 추가 public exception surface가 포함됐다.

차이는 크지 않지만 frozen requirement가 별도 public exception type을 요구한 것은 아니므로 final comparison에서 관찰 항목으로 유지한다.

---

## 12. Payment abstraction

양쪽 모두:

```ini
PAYMENT_ABSTRACTION_DELTA=2
```

이며 다음 production abstraction을 추가했다.

```text
PointAccount
PointAccountRepository
```

양쪽 모두 다음 architecture-level abstraction을 추가하지 않았다.

```text
PaymentPort
PaymentSelector
Strategy
Factory
Adapter
```

따라서 Point Payment 단계에서 architecture-level abstraction explosion은 관찰되지 않았다.

Prompt A의 method-level functional indirection은 named payment abstraction으로 계산하지 않는다.

---

## 13. B-7이 보여준 것

이 두 canonical executions에서 다음을 관찰했다.

1. Prompt constraint 차이는 actual code structure 차이로 나타났다.
2. explicit design constraints는 initial refactoring scope를 줄이는 방향과 일치하는 결과를 만들었다.
3. initial minimality와 later change-cost는 동일 방향이 아니었다.
4. Prompt A의 broader initial decomposition 중 일부는 Point Payment change에서 실제 재사용됐다.
5. overengineering은 abstraction/class count만으로 판정할 수 없었다.
6. 동일한 correctness 수준을 달성해도 design surface와 follow-up change cost는 달라질 수 있었다.
7. Problem Definition과 Design Constraints는 AI가 맡게 되는 설계 결정의 범위를 통제하는 데 실제 영향을 줄 수 있다는 evidence가 관찰됐다.

---

## 14. B-7이 보여주지 못한 것

이 실험은 다음을 입증하지 않는다.

```text
Prompt B가 일반적으로 항상 더 우수하다.

Prompt A가 future change에 항상 더 강하다.

특정 prompt 스타일이 통계적으로 우월하다.

모든 backend domain에서 동일한 결과가 나온다.

모든 후속 requirement에서 동일한 change-cost pattern이 나온다.

broader decomposition을 미리 만드는 것이 일반적으로 더 좋은 전략이다.

항상 최소 변경을 선택하는 것이 일반적으로 더 좋은 전략이다.
```

---

## 15. 한계

다음 한계가 있다.

```text
각 condition은 canonical execution 1회

모델 stochasticity 존재

Prompt A/B 실행 순서 완전 randomization 없음

하나의 작은 Ticket reservation domain만 사용

하나의 follow-up requirement만 사용

provider/model은 동일하지만 output variability를 완전히 제거하지 못함
```

따라서 결론은 반드시 이 두 canonical executions에서 관찰된 결과로 제한한다.

---

## 16. 최종 결론

Initial refactoring에서는 Prompt B가 더 constrained하고 minimal한 결과를 만들었다.

```text
Prompt B
→ fewer new methods
→ smaller new public surface
→ smaller initial diff
```

하지만 동일한 Point Payment follow-up에서는 Prompt A-derived design이 더 작은 추가 change surface를 보였다.

```text
Prompt A-derived design
→ fewer new production files
→ fewer new classes
→ fewer public contract changes
→ smaller added/deleted diff surface
```

따라서 B-7의 최종 해석은 Prompt A 또는 Prompt B의 단순 승패가 아니다.

이 두 canonical executions에서는 명시적인 Problem Definition과 Design Constraints가 AI output의 initial scope를 실제로 통제했다. 동시에 initial minimality와 future change-cost 사이에는 trade-off가 관찰됐다.

즉:

```text
Problem Definition과 Design Constraints는 중요하다.

하지만
"항상 최소 변경"
자체가 모든 future change에 최적이라는 뜻은 아니다.

또한
"초기 구조가 더 많다"
자체가 과설계를 의미하지도 않는다.
```

실제 설계 평가는 현재 requirement에 대한 정당성뿐 아니라 이후 변경에서 그 구조가 실제로 재사용되는지까지 evidence로 확인해야 한다.

B-7은 이 원칙을 하나의 통제된 canonical comparison에서 코드와 change-cost evidence로 확인했다.
