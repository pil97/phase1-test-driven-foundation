package com.gritmoments.objectcraft;

public class Ticket {

    private boolean reserved;
    private Long userId;
    private int price;

    public Ticket(boolean reserved, Long userId, int price) {
        this.reserved = reserved;
        this.userId = userId;
        this.price = price;
    }

    public boolean isReserved() {
        return reserved;
    }

    public int getPrice() {
        return price;
    }

    public void reserveFor(long userId) {
        this.reserved = true;
        this.userId = userId;
    }

    public void setReserved(boolean reserved) {
        this.reserved = reserved;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }
}
