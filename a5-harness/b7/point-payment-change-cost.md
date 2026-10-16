# B-7 WORK-3 Point Payment Change-Cost 비교

## 1. 실험 목적

이 문서는 B-7 WORK-3에서 수행한 Prompt A와 Prompt B의 Point Payment change-cost 실험 결과를 정리한 한국어 canonical artifact다.

비교 대상은 다음 두 delta로 제한한다.

```text
Prompt A initial
→ Prompt A Point Payment

Prompt B initial
→ Prompt B Point Payment
```

baseline부터 Point Payment 결과까지의 전체 diff는 이번 change-cost metric에 포함하지 않는다.

이번 문서는 동일한 Point Payment requirement를 각 initial design에 독립적으로 적용했을 때 실제로 발생한 변경 surface, public contract surface, 신규 abstraction, 기존 파일 재수정, service orchestration 재사용 정도를 비교한다.

최종적인 Prompt A/B의 일반적 우열은 여기서 확정하지 않는다. WORK-4에서 initial-result evidence와 이번 change-cost evidence를 함께 비교한 뒤 해석한다.

---

## 2. 비교 조건

두 canonical condition은 다음 기준을 동일하게 유지했다.

```text
CLAUDE_EXECUTABLE=/Users/apple/.local/bin/claude
CLAUDE_CLI_VERSION=2.1.301 (Claude Code)
CLAUDE_EXPLICIT_MODEL=opus

ALLOWED_TOOLS=
Read Write Edit Bash Glob Grep

PROMPT_TRANSPORT=STDIN
```

두 condition 모두 fresh process로 실행했으며 `--continue`, `--resume`, shared conversation은 사용하지 않았다.

Prompt A valid canonical run count와 Prompt B valid canonical run count는 각각 정확히 1회다.

```ini
PROMPT_A_VALID_CANONICAL_RUN_COUNT=1
PROMPT_B_VALID_CANONICAL_RUN_COUNT=1
```

Prompt B 실행 시 Prompt A initial/result/evidence는 execution input으로 노출하지 않았다.

```ini
PROMPT_A_RESULT_EXPOSED_TO_B=NO
```

source-level diff에서는 다음 generated artifact를 동일하게 제외했다.

```text
.gradle/
build/
out/
target/
compiled class
test report
jar
__pycache__/
IDE metadata
.DS_Store
```

---

## 3. 동일 Point Payment requirement

두 condition에는 다음 frozen requirement를 동일하게 사용했다.

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

frozen requirement SHA256:

```text
487b86d437c7ad9ebd0fde73d9cd2223b7e0253e820c9b8e7dfae053988b9996
```

solution hint, class/interface 이름 힌트, B-5 Point Payment 구현, 다른 condition의 Point Payment 결과는 입력으로 제공하지 않았다.

---

## 4. Prompt A canonical result

Prompt A valid canonical run:

```text
b7-work3-prompt-a-replacement-20261016T135646Z
```

Prompt A initial → Point Payment 결과에서 실제 source change는 다음과 같다.

```text
A  src/main/java/com/gritmoments/objectcraft/PointAccount.java
A  src/main/java/com/gritmoments/objectcraft/PointAccountNotFoundException.java
A  src/main/java/com/gritmoments/objectcraft/PointAccountRepository.java
M  src/main/java/com/gritmoments/objectcraft/TicketService.java

A  src/test/java/com/gritmoments/objectcraft/PointAccountTest.java
A  src/test/java/com/gritmoments/objectcraft/TicketServicePointPaymentTest.java
```

핵심 결과:

```ini
PROMPT_A_EXISTING_PRODUCTION_FILES_REMODIFIED=1
PROMPT_A_NEW_PRODUCTION_FILES=3
PROMPT_A_EXISTING_CLASSES_REMODIFIED=1
PROMPT_A_NEW_CLASSES=2
PROMPT_A_NEW_INTERFACES=1
PROMPT_A_METHODS_CHANGED=1
PROMPT_A_METHODS_ADDED=8
PROMPT_A_METHODS_REMOVED=0
PROMPT_A_PUBLIC_CONTRACT_CHANGES=11
PROMPT_A_DIFF_ADDED=254
PROMPT_A_DIFF_DELETED=1
PROMPT_A_TEST_FILES_CHANGED=0
PROMPT_A_NEW_TEST_FILES=2
PROMPT_A_PACKAGE_LAYER_SPREAD=1
```

new production type:

```text
PointAccount                         public class
PointAccountNotFoundException        public exception class
PointAccountRepository               public interface
```

기존 production type 중 다시 수정된 것은 `TicketService` 하나다.

`Ticket`은 Point Payment change에서 다시 수정되지 않았다.

---

## 5. Prompt B canonical result

Prompt B valid canonical run:

```text
b7-work3-prompt-b-20261016T142029Z
```

Prompt B initial → Point Payment 결과에서 실제 source change는 다음과 같다.

```text
A  src/main/java/com/gritmoments/objectcraft/InsufficientPointBalanceException.java
A  src/main/java/com/gritmoments/objectcraft/PointAccount.java
A  src/main/java/com/gritmoments/objectcraft/PointAccountNotFoundException.java
A  src/main/java/com/gritmoments/objectcraft/PointAccountRepository.java
M  src/main/java/com/gritmoments/objectcraft/TicketService.java

A  src/test/java/com/gritmoments/objectcraft/PointAccountTest.java
A  src/test/java/com/gritmoments/objectcraft/TicketServicePointPaymentTest.java
```

핵심 결과:

```ini
PROMPT_B_EXISTING_PRODUCTION_FILES_REMODIFIED=1
PROMPT_B_NEW_PRODUCTION_FILES=4
PROMPT_B_EXISTING_CLASSES_REMODIFIED=1
PROMPT_B_NEW_CLASSES=3
PROMPT_B_NEW_INTERFACES=1
PROMPT_B_METHODS_CHANGED=1
PROMPT_B_METHODS_ADDED=8
PROMPT_B_METHODS_REMOVED=0
PROMPT_B_PUBLIC_CONTRACT_CHANGES=12
PROMPT_B_DIFF_ADDED=289
PROMPT_B_DIFF_DELETED=8
PROMPT_B_TEST_FILES_CHANGED=0
PROMPT_B_NEW_TEST_FILES=2
PROMPT_B_PACKAGE_LAYER_SPREAD=1
```

new production type:

```text
InsufficientPointBalanceException    public exception class
PointAccount                         public class
PointAccountNotFoundException        public exception class
PointAccountRepository               public interface
```

기존 production type 중 다시 수정된 것은 `TicketService` 하나다.

`Ticket`은 Point Payment change에서 다시 수정되지 않았다.

---

## 6. Objective change-cost comparison

| metric | Prompt A | Prompt B |
| --- | ---: | ---: |
| 기존 production 파일 재수정 | 1 | 1 |
| 신규 production 파일 | 3 | 4 |
| 기존 class 재수정 | 1 | 1 |
| 신규 class | 2 | 3 |
| 신규 interface | 1 | 1 |
| 변경된 method | 1 | 1 |
| 추가된 method | 8 | 8 |
| 삭제된 method | 0 | 0 |
| public contract 변화 | 11 | 12 |
| diff added lines | 254 | 289 |
| diff deleted lines | 1 | 8 |
| 변경된 기존 test file | 0 | 0 |
| 신규 test file | 2 | 2 |
| package/layer spread | 1 | 1 |

이 두 canonical executions에서는 Prompt A-derived initial design이 Point Payment change에서 더 작은 신규 production file 수, 신규 class 수, public contract surface, added/deleted diff surface를 보였다.

다만 두 condition 모두 동일한 수의 기존 production file과 기존 class를 다시 수정했고, method changed/added 수와 test surface, package spread는 동일했다.

---

## 7. TicketService/Ticket 재수정 비교

### Prompt A

```ini
PROMPT_A_TICKET_SERVICE_REMODIFIED=YES
PROMPT_A_TICKET_REMODIFIED=NO
```

`TicketService`에는 다음 change가 발생했다.

```text
PointAccountRepository dependency 추가
4-argument constructor 추가
기존 3-argument constructor를 새 constructor로 delegate
reserveTicketWithPoints(...) 추가
reserve(..., IntConsumer payment) 추가
payWithPoints(...) 추가
```

기존 card path는 기존 `charge(...)` helper를 재사용했다.

기존 domain flow:

```text
ensureUserExists(...)
Ticket.ensureReservable()
payment
Ticket.reserveFor(...)
```

도 Point Payment change에서 재사용됐다.

### Prompt B

```ini
PROMPT_B_TICKET_SERVICE_REMODIFIED=YES
PROMPT_B_TICKET_REMODIFIED=NO
```

`TicketService`에는 다음 change가 발생했다.

```text
PointAccountRepository dependency 추가
4-argument constructor 추가
기존 3-argument constructor를 새 constructor로 delegate
reserveTicketWithPoints(...) 추가
findReservableTicket(...) 추가
completeReservation(...) 추가
PointAccount lookup / validation / deduction / save 추가
```

기존 `reserveTicket(...)`도 새 helper 구조를 사용하도록 재구성됐다.

기존 domain command인 `Ticket.reserve(...)`는 그대로 재사용됐다.

양쪽 모두 Point Payment requirement를 수용하기 위해 `Ticket` 자체를 다시 수정할 필요는 없었다.

---

## 8. Payment abstraction 비교

named non-exception payment-related structure는 양쪽 동일하다.

Prompt A:

```text
PointAccount                   class
PointAccountRepository         interface
```

Prompt B:

```text
PointAccount                   class
PointAccountRepository         interface
```

따라서:

```ini
PROMPT_A_PAYMENT_ABSTRACTION_DELTA=2
PROMPT_B_PAYMENT_ABSTRACTION_DELTA=2
```

payment-related exception delta는 다음과 같다.

```ini
PROMPT_A_PAYMENT_RELATED_EXCEPTION_DELTA=1
PROMPT_B_PAYMENT_RELATED_EXCEPTION_DELTA=2
```

Prompt A:

```text
PointAccountNotFoundException
```

Prompt B:

```text
InsufficientPointBalanceException
PointAccountNotFoundException
```

양쪽 모두 `PaymentPort`, `PaymentSelector`, Strategy, Factory, Adapter, 별도 payment-specific service는 만들지 않았다.

Prompt A의 `reserve(..., IntConsumer payment)`는 method-level functional indirection이지만 새 named payment abstraction은 아니므로 `PAYMENT_ABSTRACTION_DELTA`에는 포함하지 않는다.

---

## 9. Existing abstraction effect

### Prompt A

frozen observation:

```ini
PROMPT_A_EXISTING_ABSTRACTION_EFFECT=
CHANGE_COST_REDUCTION_CONTRIBUTION
```

기존 `TicketService.ensureUserExists(...)`, `TicketService.charge(...)`, `Ticket.ensureReservable()`, `Ticket.reserveFor(...)`가 Point Payment change에서 실제로 재사용됐다.

특히 card path는 기존 `charge(...)`를 그대로 사용했고, 기존 reservation ordering을 새 private `reserve(..., IntConsumer payment)` 안에서 재조합할 수 있었다.

Point Payment change에서 `Ticket` 재수정도 필요하지 않았다.

따라서 Prompt A initial의 service/domain decomposition은 이번 canonical change에서 실제 change-cost 감소에 기여한 evidence가 있다.

### Prompt B

frozen observation:

```ini
PROMPT_B_EXISTING_ABSTRACTION_EFFECT=
PARTIAL_CHANGE_COST_REDUCTION_CONTRIBUTION
```

기존 `Ticket.reserve(...)`는 Point Payment change에서도 그대로 재사용됐으며 `Ticket` 재수정이 필요하지 않았다.

반면 service orchestration에서는 Point Payment 통합 과정에서 새 `findReservableTicket(...)`과 `completeReservation(...)` decomposition이 추가됐다.

따라서 Prompt B initial abstraction은 domain state-transition 측면에서는 change-cost 감소에 기여했지만, service orchestration 측면에서는 추가 decomposition이 필요했다.

이 관찰은 이번 두 canonical executions에 한정하며 일반 법칙으로 확대하지 않는다.

---

## 10. Overengineering review

### Prompt A

frozen observation:

```ini
PROMPT_A_OVERENGINEERING_OBSERVATION=
NO_CLEAR_OVERENGINEERING_IN_CURRENT_CHANGE
```

`PointAccount`와 `PointAccountRepository`는 실제 Point Payment 구현에서 사용됐다.

Strategy, Factory, Selector, PaymentPort, Adapter 같은 future-only structure는 추가되지 않았다.

`reserve(..., IntConsumer payment)`는 새로운 indirection이지만 card와 point 두 실제 payment path에서 사용되므로 unused abstraction으로 보지 않는다.

따라서 현재 requirement 기준으로 명확한 overengineering evidence는 확인되지 않았다.

### Prompt B

frozen observation:

```ini
PROMPT_B_OVERENGINEERING_OBSERVATION=
NO_ARCHITECTURAL_OVERENGINEERING_WITH_EXTRA_PUBLIC_EXCEPTION_SURFACE
```

`PointAccount`, `PointAccountRepository`, `findReservableTicket(...)`, `completeReservation(...)`은 실제 code path에서 사용된다.

future-only Strategy, Factory, Selector, PaymentPort, Adapter는 추가되지 않았다.

다만 `InsufficientPointBalanceException`은 frozen requirement가 반드시 별도 public exception type으로 표현하라고 요구한 것은 아니다.

따라서 Prompt B에는 추가 public exception surface가 생겼다는 observation을 남긴다.

이 사실만으로 Prompt B 전체를 overengineering이라고 판정하지 않는다.

---

## 11. Behavior / test / build equivalence

양쪽 모두 동일한 validation 수준을 통과했다.

| validation | Prompt A | Prompt B |
| --- | --- | --- |
| Point Payment targeted test | PASS | PASS |
| full test | PASS | PASS |
| build | PASS | PASS |
| Characterization Test | PASS | PASS |
| 기존 Characterization Test 수정 | NO | NO |

Point Payment test evidence는 양쪽 모두 다음 behavior를 검증했다.

```text
충분한 잔액
→ 결제 성공
→ 티켓 가격과 정확히 동일한 금액 차감

잔액 부족
→ 결제 실패
→ 잔액 미차감

기존 reservation behavior 유지
```

따라서 이 실험에서 양쪽 모두 requirement correctness와 기존 reservation safety net을 통과했다.

change-cost comparison의 차이는 correctness 성공/실패가 아니라 변경 surface, public contract surface, exception surface, service orchestration 재사용, existing abstraction 재사용에서 관찰한다.

---

## 12. 관찰된 차이

이 두 canonical executions에서 확인된 객관적 차이는 다음과 같다.

Prompt A와 Prompt B 모두:

```text
기존 production file 1개 재수정
기존 class 1개 재수정
new interface 1개
method changed 1개
method added 8개
기존 test file 변경 0개
new test file 2개
package/layer spread 1
TicketService 재수정 YES
Ticket 재수정 NO
Payment abstraction delta 2
```

였다.

Prompt A는 Prompt B보다:

```text
new production file        3 vs 4
new class                  2 vs 3
public contract change    11 vs 12
diff added lines         254 vs 289
diff deleted lines         1 vs 8
payment-related exception  1 vs 2
```

의 더 작은 surface를 보였다.

Prompt A의 기존 service/domain decomposition은 이번 Point Payment change에서 직접 재사용됐다.

Prompt B의 `Ticket.reserve(...)` domain abstraction도 재사용됐지만 service orchestration에서는 새 decomposition이 추가됐다.

양쪽 모두 existing design을 버리는 bypass는 필요하지 않았다.

```ini
PROMPT_A_DESIGN_BYPASS_REQUIRED=NO
PROMPT_B_DESIGN_BYPASS_REQUIRED=NO
```

---

## 13. 해석 한계

이번 결과는 정확히 다음 두 canonical executions의 관찰이다.

```text
Prompt A initial
→ Prompt A Point Payment

Prompt B initial
→ Prompt B Point Payment
```

따라서 다음과 같은 일반적 결론은 이 문서에서 확정하지 않는다.

```text
Prompt A가 일반적으로 더 우수하다.

Prompt B explicit constraint 방식이 실패했다.

Prompt A가 모든 미래 변경에 더 강하다.

Prompt B가 항상 change cost가 높다.
```

현재 허용되는 해석은 다음 수준까지다.

```text
이 두 canonical executions에서는
Prompt A-derived initial design이
Point Payment change에서 더 작은 production/public/diff surface를 보였다.

Prompt A의 기존 decomposition은 이번 change에서 직접 재사용됐다.

Prompt B의 domain abstraction은 재사용됐지만,
service orchestration에서는 추가 decomposition이 필요했다.
```

최종 Prompt A/B 품질 해석은 WORK-4에서 WORK-2 initial-result evidence와 WORK-3 change-cost evidence를 함께 비교한 뒤 수행한다.

---

## 14. WORK-4로 넘길 frozen evidence

WORK-4에는 다음 objective metric을 frozen evidence로 넘긴다.

```ini
PROMPT_A_EXISTING_PRODUCTION_FILES_REMODIFIED=1
PROMPT_B_EXISTING_PRODUCTION_FILES_REMODIFIED=1

PROMPT_A_NEW_PRODUCTION_FILES=3
PROMPT_B_NEW_PRODUCTION_FILES=4

PROMPT_A_EXISTING_CLASSES_REMODIFIED=1
PROMPT_B_EXISTING_CLASSES_REMODIFIED=1

PROMPT_A_NEW_CLASSES=2
PROMPT_B_NEW_CLASSES=3

PROMPT_A_NEW_INTERFACES=1
PROMPT_B_NEW_INTERFACES=1

PROMPT_A_METHODS_CHANGED=1
PROMPT_B_METHODS_CHANGED=1

PROMPT_A_METHODS_ADDED=8
PROMPT_B_METHODS_ADDED=8

PROMPT_A_METHODS_REMOVED=0
PROMPT_B_METHODS_REMOVED=0

PROMPT_A_PUBLIC_CONTRACT_CHANGES=11
PROMPT_B_PUBLIC_CONTRACT_CHANGES=12

PROMPT_A_DIFF_ADDED=254
PROMPT_A_DIFF_DELETED=1

PROMPT_B_DIFF_ADDED=289
PROMPT_B_DIFF_DELETED=8

PROMPT_A_TEST_FILES_CHANGED=0
PROMPT_B_TEST_FILES_CHANGED=0

PROMPT_A_NEW_TEST_FILES=2
PROMPT_B_NEW_TEST_FILES=2

PROMPT_A_PACKAGE_LAYER_SPREAD=1
PROMPT_B_PACKAGE_LAYER_SPREAD=1

PROMPT_A_PAYMENT_ABSTRACTION_DELTA=2
PROMPT_B_PAYMENT_ABSTRACTION_DELTA=2

PROMPT_A_PAYMENT_RELATED_EXCEPTION_DELTA=1
PROMPT_B_PAYMENT_RELATED_EXCEPTION_DELTA=2

PROMPT_A_TICKET_SERVICE_REMODIFIED=YES
PROMPT_B_TICKET_SERVICE_REMODIFIED=YES

PROMPT_A_TICKET_REMODIFIED=NO
PROMPT_B_TICKET_REMODIFIED=NO

PROMPT_A_DESIGN_BYPASS_REQUIRED=NO
PROMPT_B_DESIGN_BYPASS_REQUIRED=NO

PROMPT_A_EXISTING_ABSTRACTION_EFFECT=
CHANGE_COST_REDUCTION_CONTRIBUTION

PROMPT_B_EXISTING_ABSTRACTION_EFFECT=
PARTIAL_CHANGE_COST_REDUCTION_CONTRIBUTION

PROMPT_A_OVERENGINEERING_OBSERVATION=
NO_CLEAR_OVERENGINEERING_IN_CURRENT_CHANGE

PROMPT_B_OVERENGINEERING_OBSERVATION=
NO_ARCHITECTURAL_OVERENGINEERING_WITH_EXTRA_PUBLIC_EXCEPTION_SURFACE
```

validation evidence:

```ini
PROMPT_A_PP_TEST_RESULT=PASS
PROMPT_A_FULL_TEST_RESULT=PASS
PROMPT_A_BUILD_RESULT=PASS
PROMPT_A_CHARACTERIZATION_RESULT=PASS

PROMPT_B_PP_TEST_RESULT=PASS
PROMPT_B_FULL_TEST_RESULT=PASS
PROMPT_B_BUILD_RESULT=PASS
PROMPT_B_CHARACTERIZATION_RESULT=PASS
```

canonical run count:

```ini
PROMPT_A_VALID_CANONICAL_RUN_COUNT=1
PROMPT_B_VALID_CANONICAL_RUN_COUNT=1
```

WORK-4는 이 frozen evidence를 WORK-2 initial comparison evidence와 함께 사용해 최종 Prompt A/B interpretation을 수행한다.
