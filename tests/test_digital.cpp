#include "quant/digital.hpp"
#include <gtest/gtest.h>

using namespace quant::digital;

TEST(Digital, CashOrNothing_ParityVsBS) {
    Params p{100.0, 100.0, 0.03, 0.01, 0.2, 1.0, true};
    double price_call = price_bs(p, Type::CashOrNothing);
    p.call = false;
    double price_put = price_bs(p, Type::CashOrNothing);
    double df_r = std::exp(-0.03);
    EXPECT_NEAR(price_call + price_put, df_r, 1e-10);
}

TEST(Digital, AssetOrNothing_Sanity) {
    Params p{120.0, 100.0, 0.02, 0.00, 0.25, 0.5, true};
    double price_call = price_bs(p, Type::AssetOrNothing);
    EXPECT_GT(price_call, 0.0);
}
