#include "quant/bs_barrier.hpp"
#include "quant/mc_barrier.hpp"
#include <gtest/gtest.h>

using quant::BarrierType;
using quant::OptionType;

TEST(BarrierMC, ConvergesWithStepsAndMatchesRRWithinSE) {
    quant::BarrierSpec spec{BarrierType::DownOut, 90.0, 0.0};
    quant::mc::McParams base{.spot = 100.0,
                             .strike = 95.0,
                             .rate = 0.02,
                             .dividend = 0.0,
                             .vol = 0.20,
                             .time = 1.0,
                             .num_paths = 100000,
                             .seed = 424242ULL,
                             .antithetic = true,
                             .control_variate = false,
                             .qmc = quant::mc::McParams::Qmc::None,
                             .bridge = quant::mc::McParams::Bridge::BrownianBridge,
                             .num_steps = 16};

    const double rr = quant::bs::reiner_rubinstein_price(OptionType::Call, spec, base.spot, base.strike,
                                                         base.rate, base.dividend, base.vol, base.time);

    // Coarse steps tolerance
    auto r16 = quant::mc::price_barrier_option(base, base.strike, OptionType::Call, spec);
    EXPECT_LE(std::abs(r16.estimate.value - rr), 5.0 * r16.estimate.std_error);

    base.num_steps = 64;
    auto r64 = quant::mc::price_barrier_option(base, base.strike, OptionType::Call, spec);
    EXPECT_LE(std::abs(r64.estimate.value - rr), 3.0 * r64.estimate.std_error);
}
