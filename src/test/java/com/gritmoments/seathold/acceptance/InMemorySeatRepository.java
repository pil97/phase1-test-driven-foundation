package com.gritmoments.seathold.acceptance;

import com.gritmoments.seathold.Seat;
import com.gritmoments.seathold.SeatRepository;

import java.util.HashMap;
import java.util.Map;

class InMemorySeatRepository implements SeatRepository {

    private final Map<String, Seat> seats = new HashMap<>();

    void put(String seatId, Seat seat) {
        seats.put(seatId, seat);
    }

    @Override
    public Seat findById(String seatId) {
        return seats.get(seatId);
    }

    @Override
    public void save(Seat seat) {
        // 같은 Seat 인스턴스를 저장하므로 이번 실습에서는 추가 작업이 필요하지 않다.
    }
}
