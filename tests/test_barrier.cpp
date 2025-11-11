#include <gtest/gtest.h>

#include "quant/barrier.hpp"
#include "quant/black_scholes.hpp"
#include "quant/bs_barrier.hpp"
#include "quant/mc.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/pde_barrier.hpp"

using namespace quant;

TEST(Barrier, ReinerRubinsteinParity) {
    BarrierSpec down_out{BarrierType::DownOut, 90.0, 0.0};
    BarrierSpec down_in{BarrierType::DownIn, 90.0, 0.0};

    const double S = 100.0;
    const double K = 95.0;
    const double r = 0.02;
    const double q = 0.0;
    const double sigma = 0.20;
    const double T = 1.0;

    const double vanilla = bs::call_price(S, K, r, q, sigma, T);
    const double out_price = bs::reiner_rubinstein_price(OptionType::Call, down_out, S, K, r, q, sigma, T);
    const double in_price = bs::reiner_rubinstein_price(OptionType::Call, down_in, S, K, r, q, sigma, T);

    EXPECT_NEAR(in_price + out_price, vanilla, 1e-8);
}

TEST(Barrier, MonteCarloMatchesAnalyticWithinError) {
    BarrierSpec spec{BarrierType::DownOut, 90.0, 0.0};

    mc::McParams params{
        .spot = 100.0,
        .strike = 95.0,
        .rate = 0.02,
        .dividend = 0.0,
        .vol = 0.20,
        .time = 1.0,
        .num_paths = 120000,
        .seed = 123456789ULL,
        .antithetic = true,
        .control_variate = false,
        .qmc = mc::McParams::Qmc::None,
        .bridge = mc::McParams::Bridge::BrownianBridge,
        .num_steps = 32,
    };

    const double analytic =
        bs::reiner_rubinstein_price(OptionType::Call, spec, params.spot, params.strike, params.rate,
                                    params.dividend, params.vol, params.time);
    auto res = mc::price_barrier_option(params, params.strike, OptionType::Call, spec);
    EXPECT_LE(std::abs(res.estimate.value - analytic), 3.0 * res.estimate.std_error);
}

TEST(Barrier, PdeMatchesAnalytic) {
    BarrierSpec spec{BarrierType::UpOut, 120.0, 0.0};
    quant::pde::BarrierPdeParams params{};
    params.spot = 100.0;
    params.strike = 105.0;
    params.rate = 0.02;
    params.dividend = 0.0;
    params.vol = 0.25;
    params.time = 1.0;
    params.barrier = spec;
    params.grid = quant::pde::GridSpec{201, 200, 4.0};

    const double analytic =
        bs::reiner_rubinstein_price(OptionType::Put, spec, params.spot, params.strike, params.rate,
                                    params.dividend, params.vol, params.time);
    const double pde_price = quant::pde::price_barrier_crank_nicolson(params, OptionType::Put);
    EXPECT_NEAR(pde_price, analytic, 1e-3);
}

TEST(Barrier, PdeGreeksProduceFiniteValues) {
    BarrierSpec spec{BarrierType::UpOut, 120.0, 0.0};
    quant::pde::BarrierPdeParams params{};
    params.spot = 100.0;
    params.strike = 105.0;
    params.rate = 0.02;
    params.dividend = 0.0;
    params.vol = 0.25;
    params.time = 1.0;
    params.barrier = spec;
    params.grid = quant::pde::GridSpec{201, 200, 4.0};
    auto res = quant::pde::price_barrier_crank_nicolson_greeks(params, OptionType::Put);
    EXPECT_TRUE(std::isfinite(res.price));
    EXPECT_TRUE(std::isfinite(res.delta));
    EXPECT_TRUE(std::isfinite(res.gamma));
}
