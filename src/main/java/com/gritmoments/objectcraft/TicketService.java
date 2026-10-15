package com.gritmoments.objectcraft;

public class TicketService {

    private final TicketRepository ticketRepo;
    private final UserRepository userRepo;
    private final PaymentApi paymentApi;

    public TicketService(
            TicketRepository ticketRepo,
            UserRepository userRepo,
            PaymentApi paymentApi
    ) {
        this.ticketRepo = ticketRepo;
        this.userRepo = userRepo;
        this.paymentApi = paymentApi;
    }

    public boolean reserveTicket(long userId, long ticketId, String paymentInfo) {
        User user = userRepo.findById(userId);
        if (user == null) {
            throw new UserNotFoundException();
        }

        Ticket ticket = ticketRepo.findById(ticketId);
        if (ticket.isReserved()) {
            throw new TicketAlreadyReservedException();
        }

        boolean paymentSuccess =
                paymentApi.charge(paymentInfo, ticket.getPrice());

        if (!paymentSuccess) {
            throw new PaymentFailedException();
        }

        ticket.setReserved(true);
        ticket.setUserId(userId);
        ticketRepo.save(ticket);

        return true;
    }
}
