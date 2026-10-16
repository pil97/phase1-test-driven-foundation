package com.gritmoments.objectcraft;

public interface PaymentApi {

    boolean charge(String paymentInfo, int price);
}
