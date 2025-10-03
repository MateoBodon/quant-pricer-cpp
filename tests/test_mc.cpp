#include <array>
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
    EXPECT_NEAR(res.estimate.value, bs_price, 3.0 * res.estimate.std_error);
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

    EXPECT_LT(res_anti.estimate.std_error, naive.estimate.std_error);
    EXPECT_LT(res_cv.estimate.std_error, naive.estimate.std_error);
    EXPECT_LT(res_both.estimate.std_error, res_anti.estimate.std_error);
    EXPECT_LT(res_both.estimate.std_error, res_cv.estimate.std_error);
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
    EXPECT_NEAR(g.delta.value, dc, 3.0 * g.delta.std_error);
    EXPECT_NEAR(g.vega.value,  vg, 3.0 * g.vega.std_error);
    EXPECT_NEAR(g.gamma_lrm.value, gm, 3.0 * g.gamma_lrm.std_error);
}

TEST(MonteCarlo, GreeksAcrossMoneynessAndAntithetic) {
    mc::McParams base{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.025,
        .dividend = 0.01,
        .vol = 0.22,
        .time = 1.0,
        .num_paths = 500000,
        .seed = 246813579ULL,
        .antithetic = true,
        .control_variate = false
    };

    struct Scenario {
        const char* name;
        double spot;
        double strike;
        bool antithetic;
    };

    const std::array<Scenario, 3> scenarios{{
        {"ATM", 100.0, 100.0, true},
        {"ITM", 125.0, 100.0, false},
        {"OTM", 85.0, 100.0, true},
    }};

    constexpr double kSigmaFactor = 4.0;

    for (const auto& sc : scenarios) {
        SCOPED_TRACE(sc.name);
        auto params = base;
        params.spot = sc.spot;
        params.strike = sc.strike;
        params.antithetic = sc.antithetic;
        auto g = mc::greeks_european_call(params);
        const double delta_ref = bs::delta_call(params.spot, params.strike, params.rate, params.dividend, params.vol, params.time);
        const double vega_ref = bs::vega(params.spot, params.strike, params.rate, params.dividend, params.vol, params.time);
        const double gamma_ref = bs::gamma(params.spot, params.strike, params.rate, params.dividend, params.vol, params.time);

        EXPECT_NEAR(g.delta.value, delta_ref, kSigmaFactor * g.delta.std_error);
        EXPECT_NEAR(g.vega.value, vega_ref, kSigmaFactor * g.vega.std_error);
        EXPECT_NEAR(g.gamma_lrm.value, gamma_ref, kSigmaFactor * g.gamma_lrm.std_error);
        EXPECT_NEAR(g.gamma_mixed.value, gamma_ref, kSigmaFactor * g.gamma_mixed.std_error);
    }
}

TEST(MonteCarlo, GammaMixedVarianceLowerThanLR) {
    mc::McParams params{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.03,
        .dividend = 0.005,
        .vol = 0.2,
        .time = 1.0,
        .num_paths = 800000,
        .seed = 424242ULL,
        .antithetic = true,
        .control_variate = false
    };

    const auto g = mc::greeks_european_call(params);
    EXPECT_GT(g.gamma_lrm.std_error, 0.0);
    EXPECT_GT(g.gamma_mixed.std_error, 0.0);
    EXPECT_LT(g.gamma_mixed.std_error, g.gamma_lrm.std_error);
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
    base.num_steps = 64;
    auto prng = base;
    prng.qmc = mc::McParams::Qmc::None;
    auto r1 = mc::price_european_call(prng);
    auto qmc  = base;
    qmc.qmc = mc::McParams::Qmc::Sobol;
    qmc.bridge = mc::McParams::Bridge::BrownianBridge;
    auto r2 = mc::price_european_call(qmc);
    double bs_price = bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    double e1 = std::abs(r1.estimate.value - bs_price);
    double e2 = std::abs(r2.estimate.value - bs_price);
    // QMC should typically reduce absolute error
    EXPECT_LT(e2, e1 * 0.95);
}
