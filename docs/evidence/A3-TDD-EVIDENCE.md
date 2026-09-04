# A-3 — TDD 검증 기록

> 이 문서는 완료된 A-3 작업을 기반으로 정리한 과거 실행 요약입니다.
> 실제 터미널 원본 로그를 재구성한 문서가 아닙니다.

## 범위

A-3에서는 Seat HOLD 도메인을 사용해 시간에 민감한 상태 전이와 작은 service flow를 중심으로 test-driven development를 실습했습니다.

## 테스트한 요구사항

1. AVAILABLE 좌석 → HOLD 성공
2. `now < expiresAt`인 HELD 좌석 → 재-HOLD 거절
3. 만료된 HELD 좌석 → 재-HOLD 허용
4. 정확한 경계 `now == expiresAt` → 만료로 취급하여 재-HOLD 허용

따라서 시간 계약은 다음과 같습니다.

- active iff `now < expiresAt`
- expired iff `now >= expiresAt`

## Service-level 테스트

`SeatHoldServiceTest`에서는 mocked `SeatRepository`를 사용해 service flow를 검증했습니다.

`lookup -> HOLD -> save`

이를 통해 domain transition rule과 repository interaction을 분리해 확인했습니다.

## FIRST 관점의 검토

테스트는 FIRST testing principles를 기준으로 검토했습니다. 각 case가 집중되어 있고, 반복 실행 가능하며, 서로 독립적으로 이해할 수 있는지를 확인했습니다.

## 의도적 결함 실험

경계조건 검증을 위해 active-HOLD 비교를 올바른 `isBefore` 해석에서 `!isAfter` 형태로 의도적으로 변경했습니다.

이 결함은 equality(`now == expiresAt`)를 아직 active인 것으로 잘못 처리했습니다.

정확한 equality 테스트가 이 결함을 검출했고, 경계조건을 별도 테스트로 두어야 하는 이유를 확인했습니다.

이후 결함을 제거하고 올바른 boundary semantics를 복구했습니다.

## 최종 상태

복구 후 완료된 A-3 구현은 Gradle test suite를 통과했습니다.

최종 packaging regression에서도 다음을 확인했습니다.

- `BUILD SUCCESSFUL`
- authoritative A-3/A-4 baseline files가 byte-identical하게 유지됨
