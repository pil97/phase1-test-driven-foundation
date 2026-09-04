package com.gritmoments.seathold;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class SeatHoldServiceTest {

    @Test
    void holdsAvailableSeatAndSavesIt() {
        SeatRepository repository = mock(SeatRepository.class);
        Seat seat = new Seat(SeatStatus.AVAILABLE);
        Instant now = Instant.parse("2026-08-31T10:00:00Z");

        when(repository.findById("seat-1")).thenReturn(seat);

        SeatHoldService service = new SeatHoldService(repository);

        Seat result = service.hold("seat-1", now);

        assertThat(result.getStatus()).isEqualTo(SeatStatus.HELD);
        verify(repository).save(seat);
    }
}
