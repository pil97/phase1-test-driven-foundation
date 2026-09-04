package com.gritmoments.seathold;

import java.time.Instant;

public class Seat {

    private SeatStatus status;
    private Instant expiresAt;

    public Seat(SeatStatus status) {
        this.status = status;
    }

    public Seat(SeatStatus status, Instant expiresAt) {
        this.status = status;
        this.expiresAt = expiresAt;
    }

    public void hold(Instant now) {
        if (status == SeatStatus.HELD && now.isBefore(expiresAt)) {
            throw new IllegalStateException();
        }

        status = SeatStatus.HELD;
    }

    public SeatStatus getStatus() {
        return status;
    }
}
