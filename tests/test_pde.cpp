#include <gtest/gtest.h>
#include "quant/pde.hpp"
#include "quant/black_scholes.hpp"
#include <cmath>

using namespace quant;

TEST(PDE, PriceMatchesBS_Call) {
    pde::PdeParams pp{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.03,
        .dividend = 0.00,
        .vol = 0.2,
        .time = 1.0,
        .type = pde::OptionType::Call,
        .grid = pde::GridSpec{201, 200, 4.0}
    };
    auto res = pde::price_crank_nicolson(pp);
    double bs_price = bs::call_price(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    EXPECT_NEAR(res.price, bs_price, 1e-2);
}

TEST(PDE, PriceMatchesBS_Put) {
    pde::PdeParams pp{
        .spot = 80.0,
        .strike = 100.0,
        .rate = 0.01,
        .dividend = 0.00,
        .vol = 0.25,
        .time = 0.5,
        .type = pde::OptionType::Put,
        .grid = pde::GridSpec{201, 200, 4.0}
    };
    auto res = pde::price_crank_nicolson(pp);
    double bs_price = bs::put_price(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    EXPECT_NEAR(res.price, bs_price, 1.5e-2);
}

TEST(PDE, Convergence) {
    pde::PdeParams base{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.02,
        .dividend = 0.00,
        .vol = 0.2,
        .time = 1.0,
        .type = pde::OptionType::Call,
        .grid = pde::GridSpec{0, 0, 4.0}
    };

    double bs_price = bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    auto err = [&](int M, int N) {
        auto pp = base; pp.grid = pde::GridSpec{M, N, 4.0};
        auto res = pde::price_crank_nicolson(pp);
        return std::abs(res.price - bs_price);
    };

    double e1 = err(101, 100);
    double e2 = err(201, 200);
    double e3 = err(401, 400);
    EXPECT_GT(e1, e2);
    EXPECT_GT(e2, e3);
}

TEST(PDE, GreeksCloseToBS) {
    pde::PdeParams pp{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.02,
        .dividend = 0.01,
        .vol = 0.2,
        .time = 1.0,
        .type = pde::OptionType::Call,
        .grid = pde::GridSpec{321, 320, 4.0, 2.5},
        .log_space = true,
        .upper_boundary = pde::PdeParams::UpperBoundary::Neumann,
        .compute_theta = true
    };

    auto res = pde::price_crank_nicolson(pp);
    double bs_delta = bs::delta_call(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    double bs_gamma = bs::gamma(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);

    EXPECT_NEAR(res.delta, bs_delta, std::abs(bs_delta) * 0.02);
    EXPECT_NEAR(res.gamma, bs_gamma, std::abs(bs_gamma) * 0.02);
    ASSERT_TRUE(res.theta.has_value());
}


