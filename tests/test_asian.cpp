#include <gtest/gtest.h>
#include "quant/asian.hpp"

using namespace quant::asian;

TEST(Asian, MC_GeometricCV_ReducesSE) {
    McParams base{100.0, 100.0, 0.03, 0.0, 0.2, 1.0, 60000, 42, 64, true, true, Payoff::FixedStrike, Average::Arithmetic};
    auto with_cv = price_mc(base);
    base.use_geometric_cv = false;
    auto no_cv = price_mc(base);
    EXPECT_LT(with_cv.std_error, no_cv.std_error);
}


