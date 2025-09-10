#include <gtest/gtest.h>
#include "quant/mc.hpp"
#include "quant/black_scholes.hpp"

using namespace quant;

TEST(MonteCarlo, PriceCloseToBS) {
    mc::McParams mp{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.03,
        .dividend = 0.0,
        .vol = 0.2,
        .time = 1.0,
        .num_paths = 200000,
        .seed = 42,
        .antithetic = true,
        .control_variate = true
    };
    auto res = mc::price_european_call(mp);
    double bs_price = bs::call_price(mp.spot, mp.strike, mp.rate, mp.dividend, mp.vol, mp.time);
    // Allow ~3 standard errors
    EXPECT_NEAR(res.price, bs_price, 3.0 * res.std_error);
}

TEST(MonteCarlo, VarianceReductionWorks) {
    mc::McParams base{
        .spot = 100.0,
        .strike = 105.0,
        .rate = 0.03,
        .dividend = 0.01,
        .vol = 0.25,
        .time = 0.75,
        .num_paths = 100000,
        .seed = 12345,
        .antithetic = false,
        .control_variate = false
    };

    auto naive = mc::price_european_call(base);

    auto anti = base; anti.antithetic = true; auto res_anti = mc::price_european_call(anti);
    auto cv   = base; cv.control_variate = true; auto res_cv = mc::price_european_call(cv);
    auto both = base; both.antithetic = true; both.control_variate = true; auto res_both = mc::price_european_call(both);

    EXPECT_LT(res_anti.std_error, naive.std_error);
    EXPECT_LT(res_cv.std_error, naive.std_error);
    EXPECT_LT(res_both.std_error, res_anti.std_error);
    EXPECT_LT(res_both.std_error, res_cv.std_error);
}

TEST(MonteCarlo, GreeksCloseToAnalytic) {
    mc::McParams mp{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.03,
        .dividend = 0.01,
        .vol = 0.2,
        .time = 1.0,
        .num_paths = 400000,
        .seed = 987654321ULL,
        .antithetic = true,
        .control_variate = false // control variate not used for Greeks here
    };
    auto g = mc::greeks_european_call(mp);
    double dc = bs::delta_call(mp.spot, mp.strike, mp.rate, mp.dividend, mp.vol, mp.time);
    double vg = bs::vega(mp.spot, mp.strike, mp.rate, mp.dividend, mp.vol, mp.time);
    double gm = bs::gamma(mp.spot, mp.strike, mp.rate, mp.dividend, mp.vol, mp.time);
    EXPECT_NEAR(g.delta, dc, 3.0 * g.delta_se);
    EXPECT_NEAR(g.vega,  vg, 3.0 * g.vega_se);
    EXPECT_NEAR(g.gamma, gm, 3.0 * g.gamma_se);
}

TEST(MonteCarlo, QmcReducesErrorVsAnalytic) {
    // Compare absolute error vs analytic for PRNG vs QMC
    mc::McParams base{
        .spot = 100.0,
        .strike = 110.0,
        .rate = 0.02,
        .dividend = 0.00,
        .vol = 0.25,
        .time = 1.0,
        .num_paths = 120000,
        .seed = 2025,
        .antithetic = false,
        .control_variate = false
    };
    auto prng = base; prng.sampler = mc::McParams::Sampler::Pseudorandom; auto r1 = mc::price_european_call(prng);
    auto qmc  = base; qmc.sampler  = mc::McParams::Sampler::QmcVdc;        auto r2 = mc::price_european_call(qmc);
    double bs_price = bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    double e1 = std::abs(r1.price - bs_price);
    double e2 = std::abs(r2.price - bs_price);
    // QMC should typically reduce absolute error
    EXPECT_LT(e2, e1 * 0.95);
}


