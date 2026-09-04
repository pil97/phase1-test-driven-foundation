# A-4 — BDD / Acceptance 검증 기록

> 이 문서는 완료된 A-4 작업을 기반으로 정리한 과거 실행 요약입니다.
> 실제 터미널 원본 로그를 재구성한 문서가 아닙니다.

## 범위

A-4에서는 Seat HOLD 요구사항을 Cucumber를 사용한 실행 가능한 BDD acceptance scenario로 변환했습니다.

Acceptance layer 구성:

- `seat_hold.feature`
- `RunCucumberTest.java`
- `SeatHoldStepDefinitions.java`
- `InMemorySeatRepository.java`

## Acceptance scenario

Feature는 네 가지 핵심 Seat HOLD 동작을 다룹니다.

1. AVAILABLE 좌석 → HOLD 성공
2. Active HELD 좌석 → 재-HOLD 거절
3. Expired HELD 좌석 → 재-HOLD 허용
4. 정확한 경계 `now == expiresAt` → 재-HOLD 허용

## BDD RED

Feature를 정의한 직후 acceptance test는 처음에 Undefined Step 상태에 도달했습니다.

이 RED 상태는 business scenario가 먼저 존재하고, 그에 대응하는 Step Definition 구현은 아직 완료되지 않았음을 보여줬습니다.

## Acceptance GREEN

이후 누락된 Step Definitions와 in-memory repository support를 구현했습니다.

구현 후 Cucumber acceptance scenario가 Seat HOLD domain을 대상으로 통과했습니다.

## AI implementation 실험

별도의 AI-generated production-code candidate를 acceptance contract에 대해 평가했습니다.

AI candidate는 자체 검토 후 다음과 같이 보고했습니다.

`SELF_EVALUATION=NO`

이 실험에서는 일부 요청 동작이 개별적으로는 의미상 타당해 보일 수 있어도 기존 A-3 API compatibility failure가 발생할 수 있음을 확인했습니다.

즉 implementation correctness는 하나의 evaluation boundary만으로 결정되지 않았습니다.

## Frozen acceptance contract

완료된 Feature와 acceptance test를 frozen executable contract로 두고 candidate implementation behavior를 평가했습니다.

최종 acceptance 상태는 기존 A-3 test와 함께 통과했습니다.

## 핵심 결론

실험을 통해 evaluation scope가 서로 다름을 확인했습니다.

- self-evaluation: candidate 자신의 관점에서 implementation을 검토
- acceptance tests: 외부에서 보이는 requirement behavior를 검증
- 기존 A-3 tests: 이전에 확립한 API 및 domain compatibility도 보호

따라서 하나의 scope를 통과했다고 해서 다른 scope의 correctness까지 자동으로 증명되지는 않습니다.

## 최종 상태

최종 packaging regression에서 전체 Gradle test suite가 계속 성공했고, authoritative A-3/A-4 baseline도 byte-identical하게 유지됨을 확인했습니다.
