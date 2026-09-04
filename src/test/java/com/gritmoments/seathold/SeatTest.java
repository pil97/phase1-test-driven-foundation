package com.gritmoments.seathold;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.assertj.core.api.Assertions.assertThatCode;

class SeatTest {

    @Test
    void availableSeatBecomesHeldWhenHeld() {
        Instant now = Instant.parse("2026-08-31T10:00:00Z");
        Seat seat = new Seat(SeatStatus.AVAILABLE);

        seat.hold(now);

        assertThat(seat.getStatus()).isEqualTo(SeatStatus.HELD);
    }

    @Test
    void heldSeatRejectsAnotherHoldBeforeExpiration() {
        Instant now = Instant.parse("2026-08-31T10:00:00Z");
        Instant expiresAt = Instant.parse("2026-08-31T10:00:01Z");
        Seat seat = new Seat(SeatStatus.HELD, expiresAt);

        assertThatThrownBy(() -> seat.hold(now))
                .isInstanceOf(IllegalStateException.class);
    }


    @Test
    void expiredHeldSeatCanBeHeldAgain() {
        Instant expiresAt = Instant.parse("2026-08-31T10:00:00Z");
        Instant now = Instant.parse("2026-08-31T10:00:01Z");
        Seat seat = new Seat(SeatStatus.HELD, expiresAt);

        assertThatCode(() -> seat.hold(now))
                .doesNotThrowAnyException();

        assertThat(seat.getStatus()).isEqualTo(SeatStatus.HELD);
    }


    @Test
    void heldSeatCanBeHeldAgainExactlyAtExpirationTime() {
        Instant expiresAt = Instant.parse("2026-08-31T10:00:00Z");
        Instant now = Instant.parse("2026-08-31T10:00:00Z");
        Seat seat = new Seat(SeatStatus.HELD, expiresAt);

        assertThatCode(() -> seat.hold(now))
                .doesNotThrowAnyException();

        assertThat(seat.getStatus()).isEqualTo(SeatStatus.HELD);
    }

}
