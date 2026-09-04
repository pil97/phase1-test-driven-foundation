package com.gritmoments.seathold.acceptance;

import com.gritmoments.seathold.Seat;
import com.gritmoments.seathold.SeatHoldService;
import com.gritmoments.seathold.SeatStatus;
import io.cucumber.java.ko.그리고;
import io.cucumber.java.ko.그러면;
import io.cucumber.java.ko.만일;
import io.cucumber.java.ko.조건;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;

public class SeatHoldStepDefinitions {

    private static final String SEAT_ID = "seat-1";

    private InMemorySeatRepository repository;
    private SeatHoldService service;
    private Instant now;
    private Throwable holdFailure;

    @조건("AVAILABLE 상태의 좌석이 준비되어 있다")
    public void availableSeatIsPrepared() {
        now = Instant.parse("2026-08-31T10:00:00Z");

        prepareSeat(new Seat(SeatStatus.AVAILABLE));
    }

    @조건("아직 만료되지 않은 HELD 상태의 좌석이 준비되어 있다")
    public void activeHeldSeatIsPrepared() {
        now = Instant.parse("2026-08-31T10:00:00Z");
        Instant expiresAt = Instant.parse("2026-08-31T10:00:01Z");

        prepareSeat(new Seat(SeatStatus.HELD, expiresAt));
    }

    @조건("만료 시점이 지난 HELD 상태의 좌석이 준비되어 있다")
    public void expiredHeldSeatIsPrepared() {
        Instant expiresAt = Instant.parse("2026-08-31T10:00:00Z");
        now = Instant.parse("2026-08-31T10:00:01Z");

        prepareSeat(new Seat(SeatStatus.HELD, expiresAt));
    }

    @조건("현재 시각이 정확히 만료 시각인 HELD 상태의 좌석이 준비되어 있다")
    public void heldSeatAtExactExpirationIsPrepared() {
        Instant expiresAt = Instant.parse("2026-08-31T10:00:00Z");
        now = Instant.parse("2026-08-31T10:00:00Z");

        prepareSeat(new Seat(SeatStatus.HELD, expiresAt));
    }

    @만일("사용자가 그 좌석에 HOLD를 요청한다")
    @만일("사용자가 그 좌석에 새로운 HOLD를 요청한다")
    public void userRequestsHold() {
        try {
            service.hold(SEAT_ID, now);
            holdFailure = null;
        } catch (Throwable throwable) {
            holdFailure = throwable;
        }
    }

    @그러면("HOLD 요청이 성공한다")
    public void holdRequestSucceeds() {
        assertThat(holdFailure).isNull();
    }

    @그러면("HOLD 요청이 거절된다")
    public void holdRequestIsRejected() {
        assertThat(holdFailure)
                .isInstanceOf(IllegalStateException.class);
    }

    @그리고("좌석 상태는 HELD다")
    @그리고("좌석 상태는 HELD로 유지된다")
    public void seatStatusIsHeld() {
        Seat seat = repository.findById(SEAT_ID);

        assertThat(seat.getStatus())
                .isEqualTo(SeatStatus.HELD);
    }

    private void prepareSeat(Seat seat) {
        repository = new InMemorySeatRepository();
        repository.put(SEAT_ID, seat);
        service = new SeatHoldService(repository);
        holdFailure = null;
    }
}
