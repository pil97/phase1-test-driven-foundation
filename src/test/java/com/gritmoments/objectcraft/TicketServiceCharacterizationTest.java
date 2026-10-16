package com.gritmoments.objectcraft;

import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

class TicketServiceCharacterizationTest {

    @Test
    void reservesTicketWhenUserTicketAndPaymentAreValid() {
        TicketRepository ticketRepo = mock(TicketRepository.class);
        UserRepository userRepo = mock(UserRepository.class);
        PaymentApi paymentApi = mock(PaymentApi.class);

        long userId = 1L;
        long ticketId = 10L;
        String paymentInfo = "card-token";
        int price = 12_000;

        User user = new User();
        Ticket ticket = new Ticket(false, null, price);

        when(userRepo.findById(userId)).thenReturn(user);
        when(ticketRepo.findById(ticketId)).thenReturn(ticket);
        when(paymentApi.charge(paymentInfo, price)).thenReturn(true);

        TicketService service =
                new TicketService(ticketRepo, userRepo, paymentApi);

        boolean result =
                service.reserveTicket(userId, ticketId, paymentInfo);

        assertThat(result).isTrue();
        assertThat(ticket.isReserved()).isTrue();
        assertThat(readUserId(ticket)).isEqualTo(userId);

        verify(paymentApi).charge(paymentInfo, price);
        verify(ticketRepo).save(ticket);
    }

    @Test
    void rejectsReservationWhenUserDoesNotExist() {
        TicketRepository ticketRepo = mock(TicketRepository.class);
        UserRepository userRepo = mock(UserRepository.class);
        PaymentApi paymentApi = mock(PaymentApi.class);

        long userId = 1L;
        long ticketId = 10L;
        String paymentInfo = "card-token";

        when(userRepo.findById(userId)).thenReturn(null);

        TicketService service =
                new TicketService(ticketRepo, userRepo, paymentApi);

        assertThatThrownBy(
                () -> service.reserveTicket(userId, ticketId, paymentInfo)
        ).isInstanceOf(UserNotFoundException.class);

        verifyNoInteractions(paymentApi);
        verify(ticketRepo, never()).save(any(Ticket.class));
    }

    @Test
    void rejectsReservationWhenTicketIsAlreadyReserved() {
        TicketRepository ticketRepo = mock(TicketRepository.class);
        UserRepository userRepo = mock(UserRepository.class);
        PaymentApi paymentApi = mock(PaymentApi.class);

        long userId = 1L;
        long ticketId = 10L;
        String paymentInfo = "card-token";
        int price = 12_000;

        User user = new User();
        Ticket ticket = new Ticket(true, null, price);

        when(userRepo.findById(userId)).thenReturn(user);
        when(ticketRepo.findById(ticketId)).thenReturn(ticket);

        TicketService service =
                new TicketService(ticketRepo, userRepo, paymentApi);

        assertThatThrownBy(
                () -> service.reserveTicket(userId, ticketId, paymentInfo)
        ).isInstanceOf(TicketAlreadyReservedException.class);

        verifyNoInteractions(paymentApi);
        verify(ticketRepo, never()).save(any(Ticket.class));
    }

    @Test
    void leavesTicketUnreservedWhenPaymentFails() {
        TicketRepository ticketRepo = mock(TicketRepository.class);
        UserRepository userRepo = mock(UserRepository.class);
        PaymentApi paymentApi = mock(PaymentApi.class);

        long userId = 1L;
        long ticketId = 10L;
        String paymentInfo = "card-token";
        int price = 12_000;

        User user = new User();
        Ticket ticket = new Ticket(false, null, price);

        when(userRepo.findById(userId)).thenReturn(user);
        when(ticketRepo.findById(ticketId)).thenReturn(ticket);
        when(paymentApi.charge(paymentInfo, price)).thenReturn(false);

        TicketService service =
                new TicketService(ticketRepo, userRepo, paymentApi);

        assertThatThrownBy(
                () -> service.reserveTicket(userId, ticketId, paymentInfo)
        ).isInstanceOf(PaymentFailedException.class);

        verify(paymentApi).charge(paymentInfo, price);
        verify(ticketRepo, never()).save(any(Ticket.class));

        assertThat(ticket.isReserved()).isFalse();
        assertThat(readUserId(ticket)).isNull();
    }

    /*
     * Characterization-test-only observer.
     *
     * Ticket intentionally has no public userId getter in the original code.
     * Do not change production code merely to make this state observable
     * from the test.
     */
    private static Long readUserId(Ticket ticket) {
        try {
            Field userId = Ticket.class.getDeclaredField("userId");
            userId.setAccessible(true);
            return (Long) userId.get(ticket);
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("Could not observe Ticket.userId", e);
        }
    }
}
