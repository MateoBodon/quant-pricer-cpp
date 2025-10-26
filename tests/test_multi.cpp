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

// Note: Merton jump-diffusion monotonic comparisons depend on parameterization;
// variance effects can dominate mean effects, so we skip strict monotonic tests here.
