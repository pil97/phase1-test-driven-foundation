package com.gritmoments.seathold;

import java.time.Instant;

public class SeatHoldService {

    private final SeatRepository repository;

    public SeatHoldService(SeatRepository repository) {
        this.repository = repository;
    }

    public Seat hold(String seatId, Instant now) {
        Seat seat = repository.findById(seatId);

        seat.hold(now);

        repository.save(seat);

        return seat;
    }
}
