#include "quant/asian.hpp"
#include <gtest/gtest.h>

using namespace quant::asian;

TEST(Asian, MC_GeometricCV_ReducesSE) {
    McParams base{100.0,
                  100.0,
                  0.03,
                  0.0,
                  0.2,
                  1.0,
                  60000,
                  42,
                  64,
                  true,
                  true,
                  Payoff::FixedStrike,
                  Average::Arithmetic};
    auto with_cv = price_mc(base);
    base.use_geometric_cv = false;
    auto no_cv = price_mc(base);
    EXPECT_LT(with_cv.std_error, no_cv.std_error);
}

TEST(Asian, AntitheticReducesSE) {
    McParams base{100.0,
                  100.0,
                  0.03,
                  0.0,
                  0.2,
                  1.0,
                  80000,
                  2025,
                  64,
                  false,
                  false,
                  Payoff::FixedStrike,
                  Average::Arithmetic};
    auto plain = price_mc(base);
    base.antithetic = true;
    auto anti = price_mc(base);
    EXPECT_GT(plain.std_error, 0.0);
    EXPECT_GT(anti.std_error, 0.0);
    EXPECT_LT(anti.std_error, plain.std_error);
}
