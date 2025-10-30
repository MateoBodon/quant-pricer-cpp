#include <gtest/gtest.h>
#include "quant/multi.hpp"

TEST(MultiAsset, BasketCallIncreasesWithCorrelation) {
    quant::multi::BasketMcParams p{};
    p.spots = {100.0, 100.0};
    p.vols = {0.2, 0.2};
    p.dividends = {0.0, 0.0};
    p.weights = {0.5, 0.5};
    p.corr = {1.0, 0.0, 0.0, 1.0};
    p.rate = 0.02; p.strike = 100.0; p.time = 1.0;
    p.num_paths = 60000; p.seed = 2025; p.antithetic = true;

    auto price_rho0 = quant::multi::basket_european_call_mc(p).value;
    p.corr = {1.0, 0.8, 0.8, 1.0};
    auto price_rho8 = quant::multi::basket_european_call_mc(p).value;
    EXPECT_GT(price_rho8, price_rho0);
}

TEST(MultiAsset, BasketAntitheticReducesSE) {
    quant::multi::BasketMcParams base{};
    base.spots = {100.0, 95.0, 110.0};
    base.vols = {0.18, 0.22, 0.25};
    base.dividends = {0.0, 0.0, 0.0};
    base.weights = {0.4, 0.3, 0.3};
    base.corr = {
        1.0, 0.5, 0.4,
        0.5, 1.0, 0.3,
        0.4, 0.3, 1.0
    };
    base.rate = 0.02;
    base.strike = 100.0;
    base.time = 1.0;
    base.num_paths = 120000;
    base.seed = 4242;
    base.antithetic = false;

    auto plain = quant::multi::basket_european_call_mc(base);
    base.antithetic = true;
    auto anti = quant::multi::basket_european_call_mc(base);

    EXPECT_GT(plain.std_error, 0.0);
    EXPECT_GT(anti.std_error, 0.0);
    EXPECT_LT(anti.std_error, plain.std_error);
}

TEST(MultiAsset, MertonAntitheticReducesSE) {
    quant::multi::MertonParams base{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.02,
        .dividend = 0.0,
        .vol = 0.2,
        .time = 1.0,
        .lambda = 0.75,
        .muJ = -0.1,
        .sigmaJ = 0.2,
        .num_paths = 150000,
        .seed = 1337,
        .antithetic = false
    };

    auto plain = quant::multi::merton_call_mc(base);
    base.antithetic = true;
    auto anti = quant::multi::merton_call_mc(base);

    EXPECT_GT(plain.std_error, 0.0);
    EXPECT_GT(anti.std_error, 0.0);
    EXPECT_LT(anti.std_error, plain.std_error);
}

// Note: Additional monotonicity properties in jump diffusion depend on parameterization;
// we only assert variance-reduction characteristics here.
