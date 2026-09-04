# A-3 — TDD Evidence

> Historical execution summary based on the completed A-3 work.
> This is not a reconstructed raw terminal log.

## Scope

A-3 used the Seat HOLD domain to practice test-driven development around time-sensitive state transitions and a small service flow.

## Tested requirements

1. AVAILABLE seat -> HOLD succeeds.
2. HELD seat with `now < expiresAt` -> re-HOLD is rejected.
3. Expired HELD seat -> re-HOLD is allowed.
4. Exact boundary `now == expiresAt` -> treated as expired, so re-HOLD is allowed.

The time contract was therefore:

- active iff `now < expiresAt`
- expired iff `now >= expiresAt`

## Service-level test

`SeatHoldServiceTest` used a mocked `SeatRepository` to verify the service flow:

`lookup -> HOLD -> save`

This separated the domain transition rule from repository interaction.

## FIRST review lens

The tests were reviewed with the FIRST testing principles in mind, including keeping cases focused, repeatable, and independently understandable.

## Intentional defect experiment

An intentional boundary defect changed the active-HOLD comparison from the correct `isBefore` interpretation to a `!isAfter` form.

That defect incorrectly treated equality (`now == expiresAt`) as still active.

The exact equality test detected the defect, demonstrating why the boundary case needed its own test.

The defect was then removed and the correct boundary semantics restored.

## Final state

After restoration, the completed A-3 implementation passed the Gradle test suite.

Final packaging regression also confirmed:

- `BUILD SUCCESSFUL`
- the authoritative A-3/A-4 baseline files remained byte-identical.
