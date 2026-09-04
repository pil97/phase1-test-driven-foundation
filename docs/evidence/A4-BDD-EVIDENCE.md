# A-4 — BDD / Acceptance Evidence

> Historical execution summary based on the completed A-4 work.
> This is not a reconstructed raw terminal log.

## Scope

A-4 translated the Seat HOLD requirements into executable BDD acceptance scenarios using Cucumber.

The acceptance layer consisted of:

- `seat_hold.feature`
- `RunCucumberTest.java`
- `SeatHoldStepDefinitions.java`
- `InMemorySeatRepository.java`

## Acceptance scenarios

The Feature covered four core Seat HOLD behaviors:

1. AVAILABLE seat -> HOLD succeeds.
2. Active HELD seat -> re-HOLD is rejected.
3. Expired HELD seat -> re-HOLD is allowed.
4. Exact boundary `now == expiresAt` -> re-HOLD is allowed.

## BDD RED

After defining the Feature, the acceptance test initially reached an Undefined Step state.

This RED state demonstrated that the business scenario existed before the corresponding Step Definition implementation was complete.

## Acceptance GREEN

The missing Step Definitions and in-memory repository support were then implemented.

After implementation, the Cucumber acceptance scenarios passed against the Seat HOLD domain.

## AI implementation experiment

A separate AI-generated production-code candidate was evaluated against the acceptance contract.

The AI candidate performed its own review and reported:

`SELF_EVALUATION=NO`

The experiment also exposed an A-3 API compatibility failure even though part of the requested behavior could appear semantically reasonable in isolation.

This showed that implementation correctness depended on more than one evaluation boundary.

## Frozen acceptance contract

The completed Feature and acceptance tests were treated as the frozen executable contract while candidate implementation behavior was evaluated.

The final acceptance state passed together with the existing A-3 tests.

## Main conclusion

The experiment demonstrated that the evaluation scopes were different:

- self-evaluation examined the implementation from the candidate's own perspective
- acceptance tests checked externally visible requirement behavior
- existing A-3 tests also protected previously established API and domain compatibility

Passing one scope therefore did not automatically prove correctness in the others.

## Final state

Final packaging regression confirmed the complete Gradle test suite remained successful and the authoritative A-3/A-4 baseline remained byte-identical.
