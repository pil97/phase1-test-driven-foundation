package com.gritmoments.objectcraft;

public interface TicketRepository {

    Ticket findById(long ticketId);

    void save(Ticket ticket);
}
