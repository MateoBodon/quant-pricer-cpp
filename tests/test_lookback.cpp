#include "quant/black_scholes.hpp"
#include "quant/lookback.hpp"
#include <gtest/gtest.h>

using namespace quant;

TEST(Lookback, FixedStrikeCallAboveEuropean) {
    lookback::McParams p{.spot = 100.0,
                         .strike = 100.0,
                         .rate = 0.02,
                         .dividend = 0.00,
                         .vol = 0.2,
                         .time = 1.0,
                         .num_paths = 120000,
                         .seed = 4242,
                         .num_steps = 64,
                         .antithetic = true,
                         .use_bridge = false,
                         .opt = OptionType::Call,
                         .type = lookback::Type::FixedStrike};
    auto res = lookback::price_mc(p);
    double euro = bs::call_price(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
    // With high paths, lookback call should exceed vanilla with margin > a few SEs
    EXPECT_GT(res.value + 3.0 * res.std_error, euro);
}
