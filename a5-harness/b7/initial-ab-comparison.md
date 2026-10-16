# B-7 WORK-2 Initial Prompt A/B Comparison

## 1. 문서 목적

이 문서는 B-7 WORK-2에서 동결한 Prompt A와 Prompt B를 동일 baseline과 동일 실행 조건에서 각각 정확히 1회 실행한 뒤, Point Payment 적용 전 initial design 결과를 비교한 정적 evidence artifact다.

이번 문서는 **initial canonical A/B에서 관찰된 차이**까지만 기록한다.

아직 WORK-3 Point Payment change-cost experiment가 남아 있으므로, 이 문서만으로 Prompt A 또는 Prompt B의 최종 우열을 확정하지 않는다.

---

## 2. 실험 조건

```ini
B7_BASELINE=8cfcd6c1a6de43b6f2ce7a2acc031fee5ebed4f1
START_HEAD=4e54529c11354642dcdae92450f4fc72365a3813

CLAUDE_EXECUTABLE=/Users/apple/.local/bin/claude
CLAUDE_CLI_VERSION=2.1.301 (Claude Code)
CLAUDE_EXPLICIT_MODEL=opus
EXECUTION_MECHANISM=fresh claude -p process per condition; explicit --model; no --continue/--resume; no shared conversation

PROMPT_A_CANONICAL_RUN_COUNT=1
PROMPT_B_CANONICAL_RUN_COUNT=1

A_B_BASELINE_IDENTICAL=YES
ISOLATION_GUARD=PASS

DOCUMENT_CANONICAL_LANGUAGE=KOREAN
```

Prompt A와 Prompt B는 모두 frozen baseline의 독립 `git archive` snapshot에서 실행했다.

Prompt B 실행 시 Prompt A workspace와 pristine reference는 읽을 수 없도록 추가 격리했다.

---

## 3. Canonical 실행 결과

| 항목 | Prompt A | Prompt B |
|---|---|---|
| provider exit | `0` | `0` |
| Characterization Test | `PASS` | `PASS` |
| full test | `PASS` | `PASS` |
| build | `PASS` | `PASS` |
| Characterization Test 수정 | `NO` | `NO` |
| canonical run count | `1` | `1` |
| initial workspace 보존 | `YES` | `YES` |

두 condition 모두 기존 Characterization Test를 수정하지 않고 통과했다.

따라서 이번 initial comparison에서 behavior preservation evidence는 동일한 safety net을 기준으로 비교할 수 있다.

---

## 4. Objective Initial Metrics

| metric | Prompt A | Prompt B |
|---|---:|---:|
| changed production files | 2 | 2 |
| new production files | 0 | 0 |
| deleted production files | 0 | 0 |
| changed classes | 2 | 2 |
| new classes | 0 | 0 |
| removed classes | 0 | 0 |
| changed methods | 1 | 1 |
| new methods | 4 | 1 |
| removed methods | 2 | 2 |
| interface count delta | 0 | 0 |
| public contract added | 2 | 1 |
| public contract removed | 2 | 2 |
| changed test files | 0 | 0 |
| new test files | 0 | 0 |
| package/layer spread | 1 | 1 |
| diff added lines | 24 | 6 |
| diff deleted lines | 19 | 7 |

### Prompt A의 새 method

```text
Ticket.ensureReservable()
Ticket.reserveFor(long)
TicketService.charge(String,int)
TicketService.ensureUserExists(long)
```

제거:

```text
Ticket.setReserved(boolean)
Ticket.setUserId(Long)
```

### Prompt B의 새 method

```text
Ticket.reserve(long)
```

제거:

```text
Ticket.setReserved(boolean)
Ticket.setUserId(Long)
```

두 condition 모두 새 interface, 새 class, 새 package/layer를 만들지 않았다.

---

## 5. TicketService Responsibility

### Prompt A

Prompt A는 `TicketService.reserveTicket(...)`를 orchestration 단계가 보이도록 더 분해했다.

```text
ensureUserExists
→ ticket lookup
→ ticket.ensureReservable
→ charge
→ ticket.reserveFor
→ save
```

사용자 존재 확인과 payment failure 처리를 각각 private method인 `ensureUserExists(...)`, `charge(...)`로 추출했다.

이 변경은 서비스 내부 흐름의 가독성을 높이지만, initial requirement의 핵심 책임 이동인 Ticket state transition 이외의 서비스 내부 구조도 함께 변경했다.

### Prompt B

Prompt B는 기존 서비스 orchestration을 거의 그대로 유지했다.

```text
user lookup/check
→ ticket lookup/check
→ payment
→ ticket.reserve
→ save
```

서비스가 담당하던 `setReserved(true)`와 `setUserId(userId)` 두 상태 변경만 `Ticket.reserve(userId)`로 이동했다.

따라서 `TicketService`의 기존 orchestration 책임은 유지하면서, Ticket state transition 책임만 도메인 객체로 옮겼다.

### 관찰

두 condition 모두 `TicketService`를 orchestration boundary로 유지했다.

차이는 Prompt A가 서비스 내부 구현까지 추가로 분해했고, Prompt B는 상태 전이 책임 이동에 필요한 최소 변경에 가까운 범위를 선택했다는 점이다.

---

## 6. Ticket Responsibility

### Baseline

Baseline의 `Ticket`은 다음 public setter를 노출했다.

```text
setReserved(boolean)
setUserId(Long)
```

그 결과 `reserved`와 `userId`를 서로 독립적으로 변경할 수 있었다.

### Prompt A

Prompt A는 다음을 추가했다.

```text
ensureReservable()
reserveFor(long)
```

`reserveFor(...)`는 내부에서 `ensureReservable()`을 다시 호출한 뒤 `reserved=true`와 `userId` 설정을 함께 수행한다.

따라서 Ticket이 예약 가능 여부 검증과 상태 전이를 스스로 보호하도록 책임이 이동했다.

또한 `price`를 `final`로 변경했다.

### Prompt B

Prompt B는 하나의 command method만 추가했다.

```text
reserve(long)
```

이 method가 이미 예약됐는지 검사하고, `reserved=true`와 `userId` 설정을 한 번에 수행한다.

서비스에는 payment 이전 rejection 순서를 보존하기 위한 `ticket.isReserved()` 사전 확인이 남아 있다.

### 관찰

두 condition 모두 잘못된 setter 조합을 제거하고 Ticket이 예약 상태 전이를 캡슐화하도록 개선했다.

Prompt A는 예약 가능 검증을 별도 public method로도 노출했고, Prompt B는 검증과 state transition을 하나의 `reserve(...)` command 안에 묶었다.

---

## 7. Payment 관련 Abstraction

Baseline, Prompt A, Prompt B 모두 production payment boundary는 다음 하나다.

```text
PaymentApi
```

새 payment interface, strategy, factory, selector, layer는 추가되지 않았다.

Prompt A의 `TicketService.charge(...)`는 기존 `PaymentApi.charge(...)` 호출과 `PaymentFailedException` 처리를 감싼 private helper다.

따라서 interface/layer 수준의 새로운 payment abstraction으로 계산하지 않는다.

Prompt B는 기존 payment 코드를 그대로 유지했다.

---

## 8. Public Contract 변화

### Prompt A

추가:

```text
Ticket.ensureReservable()
Ticket.reserveFor(long)
```

제거:

```text
Ticket.setReserved(boolean)
Ticket.setUserId(Long)
```

### Prompt B

추가:

```text
Ticket.reserve(long)
```

제거:

```text
Ticket.setReserved(boolean)
Ticket.setUserId(Long)
```

두 condition 모두 setter 제거로 public contract를 변경했다.

Prompt B는 새 public surface를 하나 추가했고, Prompt A는 두 개 추가했다.

현재 repository 내부 evidence에서는 제거된 setter 사용처가 `TicketService`뿐이지만, repository 외부 caller가 존재한다면 두 결과 모두 compile compatibility risk가 있다.

---

## 9. Behavior-Preservation 전략

Characterization Test가 고정한 주요 observable behavior는 다음과 같다.

```text
정상 예약 성공
존재하지 않는 사용자 거부
이미 예약된 Ticket 거부
이미 예약된 경우 payment 미호출
payment 실패 시 save 미호출
payment 실패 시 Ticket 상태 미변경
성공 시 reserved/userId 변경
```

Prompt A와 Prompt B 모두 Characterization Test 파일을 수정하지 않았고 해당 test를 통과했다.

또한 두 결과 모두:

```text
UserNotFoundException
TicketAlreadyReservedException
PaymentFailedException
true 반환
Ticket.userId field 이름
Ticket 생성자
Ticket.isReserved()
Ticket.getPrice()
```

를 유지했다.

Ticket lookup 결과가 `null`일 때 기존과 동일하게 NPE가 발생하는 경로도 변경하지 않았다.

---

## 10. Design Decision 근거

### Prompt A

Prompt A는 Ticket이 자기 예약 규칙을 보유해야 한다는 판단을 중심으로 리팩터링했다.

추가로 서비스 method를 작은 단계로 분해해 읽기 쉬운 orchestration을 만들었다.

AI justification은 다음에 집중했다.

```text
예약 규칙을 Ticket으로 이동
setter 제거
중복 예약 방지
service orchestration 가독성
기존 호출 순서와 예외 시점 유지
```

### Prompt B

Prompt B는 변경 전에 실제 code evidence를 명시적으로 분석했다.

주요 근거는 다음이었다.

```text
reserved와 userId는 함께 바뀌어야 함
public setter가 invalid state를 허용함
setter 사용처는 TicketService 하나뿐임
이미 예약된 경우 payment 이전에 거부해야 함
미래 requirement를 위한 구조는 추가하지 않음
```

이 근거를 바탕으로 `Ticket.reserve(userId)` 하나에 상태 전이와 도메인 guard를 묶고, 서비스의 기존 orchestration은 유지했다.

---

## 11. Affected Scope 정당성

두 condition의 물리적 scope는 동일하다.

```text
changed production files=2
changed classes=2
package/layer spread=1
new class=0
new interface=0
```

그러나 변경 강도는 다르다.

Prompt A:

```text
new methods=4
public contract added=2
diff=+24/-19
```

Prompt B:

```text
new methods=1
public contract added=1
diff=+6/-7
```

Prompt A의 핵심 Ticket 책임 이동은 현재 code pressure로 정당화된다.

다만 `TicketService.ensureUserExists(...)`, `TicketService.charge(...)`, `price final` 변경까지 같은 canonical run에 포함한 것은 핵심 state-transition 문제 해결보다 넓은 scope다.

Prompt B는 Ticket state-transition 캡슐화에 직접 필요한 변경을 중심으로 scope를 제한했다.

---

## 12. Testability 영향

두 결과 모두 예약 규칙을 `Ticket` 내부로 이동했기 때문에, 이후 mock 없이 Ticket 자체의 예약 규칙을 단위 테스트할 수 있는 구조가 됐다.

Prompt A는 `ensureReservable()`을 public으로 분리해 guard 자체를 직접 호출할 수도 있다.

Prompt B는 `reserve(...)`라는 하나의 command를 통해 invariant와 state transition을 함께 테스트하게 된다.

이번 WORK에서는 두 condition 모두 새 test를 추가하지 않았다.

따라서 testability 개선 가능성은 구조적 관찰이며, 새 test coverage 증가를 의미하지 않는다.

---

## 13. Overengineering Review

### Prompt A

다음 architecture-level overengineering evidence는 발견되지 않았다.

```text
새 interface 없음
duplicate payment abstraction 없음
strategy/factory/selector 없음
새 architecture layer 없음
새 package spread 없음
future-only extension point 없음
```

따라서 Prompt A를 **architecture overengineering**으로 판정하지 않는다.

다만 initial requirement와 code pressure에 비해 다음 추가 scope가 관찰된다.

```text
TicketService.ensureUserExists(...) private extraction
TicketService.charge(...) private extraction
Ticket.price final 변경
Ticket.ensureReservable() 별도 public contract 추가
```

특히 service는 payment 전에 `ticket.ensureReservable()`을 호출하고, 이후 `ticket.reserveFor(...)`도 내부에서 다시 `ensureReservable()`을 호출한다.

이 이중 guard는 behavior preservation에는 문제가 없지만, 현재 single-threaded characterization evidence만 놓고 보면 Prompt B보다 더 많은 decomposition과 public surface를 만든다.

따라서 Prompt A의 observation은 다음과 같이 기록한다.

```ini
PROMPT_A_OVERENGINEERING_OBSERVATION=
NO_ARCHITECTURAL_OVERENGINEERING;
BROADER_THAN_MINIMUM_REFACTORING_SCOPE_OBSERVED
```

### Prompt B

Prompt B는 새 abstraction/layer/interface를 추가하지 않았고, state-transition 책임 이동에 필요한 public command 하나만 추가했다.

서비스의 기존 payment/user orchestration도 유지했다.

현재 initial requirement와 current code evidence 기준으로 future-only abstraction 또는 불필요한 architecture expansion은 관찰되지 않았다.

```ini
PROMPT_B_OVERENGINEERING_OBSERVATION=
NO_OVERENGINEERING_EVIDENCE_OBSERVED
```

이 observation은 WORK-2 initial design만 대상으로 한다.

---

## 14. Initial Canonical A/B에서 관찰된 차이

두 condition은 동일하게 다음 핵심 방향을 선택했다.

```text
public setter 제거
Ticket으로 예약 state transition 이동
기존 characterization behavior 보존
새 interface/layer 추가 없음
```

차이는 변경 범위와 public surface에 있다.

Prompt A는:

```text
Ticket 도메인 책임 이동
+
service 내부 method extraction
+
price immutability 강화
+
별도 public guard
```

까지 수행했다.

Prompt B는:

```text
Ticket.reserve(long)
```

를 중심으로 상태 전이 캡슐화에 필요한 범위만 변경했다.

따라서 **initial design 결과만 놓고 보면 Prompt B가 Prompt A보다 더 작은 diff와 더 작은 새 public surface를 만들었다**는 객관적 차이는 기록할 수 있다.

그러나 이것은 최종 quality winner 판정이 아니다.

---

## 15. 아직 결론 내릴 수 없는 것

WORK-2만으로 다음을 확정하지 않는다.

```text
Prompt B가 최종적으로 더 좋은 prompt다
Prompt A가 최종적으로 더 나쁜 prompt다
Prompt B가 미래 변경에 항상 더 강하다
Prompt A의 추가 decomposition이 실제 change cost를 증가시킨다
```

B-7의 핵심 후속 단계는 동일한 Point Payment requirement를 A/B initial result 각각에 적용해 change cost를 비교하는 것이다.

따라서 최종 Prompt A/B 품질 판단은 WORK-3 evidence 이후에 수행한다.

---

## 16. WORK-3 시작점

WORK-2 종료 시 다음 initial workspace를 그대로 보존한다.

```text
Prompt A initial result
= a5-harness/runs/b7/work-2/20261016-220540/prompt-a-initial

Prompt B initial result
= a5-harness/runs/b7/work-2/20261016-220540/prompt-b-initial
```

WORK-3에서는 이 두 workspace를 직접 덮어쓰지 않는다.

각각 별도 Point Payment experiment copy를 만든 뒤 동일한 frozen Point Payment requirement를 적용해야 한다.

---

## 17. WORK-2 현재 판정

```ini
PROMPT_A_CANONICAL_RUN_COUNT=1
PROMPT_B_CANONICAL_RUN_COUNT=1

PROMPT_A_PROVIDER_EXIT=0
PROMPT_B_PROVIDER_EXIT=0

PROMPT_A_CHARACTERIZATION_RESULT=PASS
PROMPT_B_CHARACTERIZATION_RESULT=PASS

PROMPT_A_TEST_RESULT=PASS
PROMPT_B_TEST_RESULT=PASS

PROMPT_A_BUILD_RESULT=PASS
PROMPT_B_BUILD_RESULT=PASS

PROMPT_A_INITIAL_WORKSPACE_PRESERVED=YES
PROMPT_B_INITIAL_WORKSPACE_PRESERVED=YES

A_B_BASELINE_IDENTICAL=YES
ISOLATION_GUARD=PASS

B5_MANUAL_SOLUTION_EXPOSED_TO_A=NO
B5_MANUAL_SOLUTION_EXPOSED_TO_B=NO
B6_SOLUTION_EXPOSED_TO_A=NO
B6_SOLUTION_EXPOSED_TO_B=NO

MAIN_PRODUCTION_MODIFIED=NO
B6_FROZEN_ARTIFACT_MODIFIED=NO
PROTOCOL_MODIFIED=NO

DOCUMENT_CANONICAL_LANGUAGE=KOREAN
PUSH=NO
```

정적 comparison artifact를 repository에 반영하고 final validation/commit을 완료한 뒤 WORK-2 종료보고를 확정한다.
