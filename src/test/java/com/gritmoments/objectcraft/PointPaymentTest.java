package com.gritmoments.objectcraft;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class PointPaymentTest {

    @Test
    void deductsPointsWhenBalanceIsExactlyEnough() {
        PointBalanceRepository pointBalanceRepository =
                mock(PointBalanceRepository.class);

        PointPayment payment =
                new PointPayment(pointBalanceRepository);

        String pointAccountId = "point-account";
        int price = 12_000;

        when(pointBalanceRepository.findBalance(pointAccountId))
                .thenReturn(price);

        boolean result =
                payment.charge(pointAccountId, price);

        assertThat(result).isTrue();

        verify(pointBalanceRepository)
                .deduct(pointAccountId, price);
    }

    @Test
    void returnsFalseWithoutDeductingWhenBalanceIsInsufficient() {
        PointBalanceRepository pointBalanceRepository =
                mock(PointBalanceRepository.class);

        PointPayment payment =
                new PointPayment(pointBalanceRepository);

        String pointAccountId = "point-account";
        int price = 12_000;

        when(pointBalanceRepository.findBalance(pointAccountId))
                .thenReturn(price - 1);

        boolean result =
                payment.charge(pointAccountId, price);

        assertThat(result).isFalse();

        verify(pointBalanceRepository, never())
                .deduct(anyString(), anyInt());
    }
}
