#include <gtest/gtest.h>
#include <vector>
#include "quant/term_structures.hpp"

TEST(Sanity, TrueIsTrue) {
    EXPECT_TRUE(true);
}

TEST(PiecewiseConstant, RightClosedIntervals) {
    quant::PiecewiseConstant pc{
        .times = {0.25, 0.50, 1.00},
        .values = {1.0, 2.0, 3.0}
    };

    // t <= first knot uses first value
    EXPECT_DOUBLE_EQ(pc.value(0.00), 1.0);
    EXPECT_DOUBLE_EQ(pc.value(0.25), 1.0); // right-closed at 0.25

    // (0.25, 0.50] -> 2.0
    EXPECT_DOUBLE_EQ(pc.value(0.30), 2.0);
    EXPECT_DOUBLE_EQ(pc.value(0.50), 2.0);

    // (0.50, 1.00] -> 3.0
    EXPECT_DOUBLE_EQ(pc.value(0.51), 3.0);
    EXPECT_DOUBLE_EQ(pc.value(1.00), 3.0);

    // Beyond last knot -> last value
    EXPECT_DOUBLE_EQ(pc.value(2.00), 3.0);
}
