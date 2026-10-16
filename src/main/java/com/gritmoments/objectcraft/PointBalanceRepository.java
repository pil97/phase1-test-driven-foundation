package com.gritmoments.objectcraft;

public interface PointBalanceRepository {

    int findBalance(String pointAccountId);

    void deduct(String pointAccountId, int amount);
}
