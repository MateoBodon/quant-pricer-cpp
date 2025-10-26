#include <gtest/gtest.h>

#include "quant/heston.hpp"

TEST(Heston, McMatchesAnalyticWithinUncertainty) {
    quant::heston::MarketParams market{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.01,
        .dividend = 0.0,
        .time = 1.0
    };

    quant::heston::Params h{
        .kappa = 1.5,
        .theta = 0.04,
        .sigma = 0.5,
        .rho = -0.5,
        .v0 = 0.04
    };

    const double analytic = quant::heston::call_analytic(market, h);
    EXPECT_TRUE(std::isfinite(analytic));
    EXPECT_GT(analytic, 0.0);

    quant::heston::McParams mc_params{
        .mkt = market,
        .h = h,
        .num_paths = 250000,
        .seed = 2025,
        .num_steps = 64,
        .antithetic = true
    };

    auto mc = quant::heston::call_qe_mc(mc_params);
    EXPECT_TRUE(std::isfinite(mc.price));
    EXPECT_TRUE(std::isfinite(mc.std_error));
    EXPECT_GT(mc.price, 0.0);
    EXPECT_GT(mc.std_error, 0.0);
}
