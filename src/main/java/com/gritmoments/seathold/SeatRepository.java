package com.gritmoments.seathold;

public interface SeatRepository {

    Seat findById(String seatId);

    void save(Seat seat);
}
