package com.gritmoments.objectcraft;

public class PointPayment implements PaymentApi {

    private final PointBalanceRepository pointBalanceRepository;

    public PointPayment(PointBalanceRepository pointBalanceRepository) {
        this.pointBalanceRepository = pointBalanceRepository;
    }

    @Override
    public boolean charge(String paymentInfo, int price) {
        int balance =
                pointBalanceRepository.findBalance(paymentInfo);

        if (balance < price) {
            return false;
        }

        pointBalanceRepository.deduct(paymentInfo, price);
        return true;
    }
}
