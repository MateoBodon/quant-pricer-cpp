#include <gtest/gtest.h>

#include "quant/black_scholes.hpp"
#include "quant/portfolio.hpp"

#include <cmath>
#include <limits>
#include <vector>

using quant::portfolio::MarketShock;
using quant::portfolio::OptionType;
using quant::portfolio::VanillaPosition;

namespace {
VanillaPosition call(double quantity = 2.0) {
    return {OptionType::Call, quantity, 100.0, 105.0, 0.03, 0.01, 0.24, 0.75};
}

VanillaPosition put(double quantity = -1.5) {
    return {OptionType::Put, quantity, 92.0, 100.0, 0.02, 0.005, 0.31, 0.40};
}
} // namespace

TEST(PortfolioRisk, PositionAndPortfolioValuesMatchScalarAnalytics) {
    const std::vector<VanillaPosition> positions{call(), put()};
    const auto result = quant::portfolio::price_risk(positions);
    ASSERT_EQ(result.positions.size(), positions.size());

    const double call_price = quant::bs::call_price(100.0, 105.0, 0.03, 0.01, 0.24, 0.75);
    const double put_price = quant::bs::put_price(92.0, 100.0, 0.02, 0.005, 0.31, 0.40);
    EXPECT_DOUBLE_EQ(result.positions[0].price, call_price);
    EXPECT_DOUBLE_EQ(result.positions[0].value, 2.0 * call_price);
    EXPECT_DOUBLE_EQ(result.positions[1].price, put_price);
    EXPECT_DOUBLE_EQ(result.positions[1].value, -1.5 * put_price);
    EXPECT_DOUBLE_EQ(result.totals.value, result.positions[0].value + result.positions[1].value);
    EXPECT_DOUBLE_EQ(result.totals.delta, result.positions[0].delta + result.positions[1].delta);
    EXPECT_DOUBLE_EQ(result.totals.gamma, result.positions[0].gamma + result.positions[1].gamma);
    EXPECT_DOUBLE_EQ(result.totals.vega, result.positions[0].vega + result.positions[1].vega);
    EXPECT_DOUBLE_EQ(result.totals.theta, result.positions[0].theta + result.positions[1].theta);
    EXPECT_DOUBLE_EQ(result.totals.rho, result.positions[0].rho + result.positions[1].rho);
}

TEST(PortfolioRisk, ZeroShockIsExactlyZeroAndDetailSumsInOrder) {
    const std::vector<VanillaPosition> positions{call(), put(), call(-0.25)};
    const std::vector<MarketShock> shocks{{0.0, 0.0, 0.0, 0.0, 0.0},
                                          {-0.12, 0.08, 0.01, -0.002, 5.0 / 365.0}};
    const auto result = quant::portfolio::scenario_pnl(positions, shocks, true);
    ASSERT_EQ(result.portfolio_pnl.size(), 2U);
    ASSERT_EQ(result.position_pnl.size(), 6U);
    EXPECT_DOUBLE_EQ(result.portfolio_pnl[0], 0.0);
    for (std::size_t i = 0; i < positions.size(); ++i) {
        EXPECT_DOUBLE_EQ(result.position_pnl[i], 0.0);
    }
    double detail_sum = 0.0;
    for (std::size_t i = 0; i < positions.size(); ++i) {
        detail_sum += result.position_pnl[positions.size() + i];
    }
    EXPECT_DOUBLE_EQ(result.portfolio_pnl[1], detail_sum);
}

TEST(PortfolioRisk, AggregateOnlyAvoidsDetailAllocationAndIsDeterministic) {
    const std::vector<VanillaPosition> positions{call(), put()};
    const std::vector<MarketShock> shocks{{0.05, -0.02, 0.005, 0.001, 1.0 / 365.0}};
    const auto first = quant::portfolio::scenario_pnl(positions, shocks, false);
    const auto second = quant::portfolio::scenario_pnl(positions, shocks, false);
    EXPECT_TRUE(first.position_pnl.empty());
    EXPECT_EQ(first.portfolio_pnl, second.portfolio_pnl);
    EXPECT_DOUBLE_EQ(first.base_portfolio_value, second.base_portfolio_value);
}

TEST(PortfolioRisk, ExpiryUsesIntrinsicValue) {
    auto expired = call(3.0);
    expired.spot = 110.0;
    expired.strike = 100.0;
    expired.time = 0.0;
    const auto result = quant::portfolio::price_risk({expired});
    EXPECT_DOUBLE_EQ(result.positions[0].price, 10.0);
    EXPECT_DOUBLE_EQ(result.totals.value, 30.0);
}

TEST(PortfolioRisk, InvalidInputsFailClosed) {
    auto invalid = call();
    invalid.spot = 0.0;
    EXPECT_THROW(quant::portfolio::price_risk({invalid}), std::invalid_argument);
    invalid = call();
    invalid.quantity = std::numeric_limits<double>::quiet_NaN();
    EXPECT_THROW(quant::portfolio::price_risk({invalid}), std::invalid_argument);
    invalid = call();
    invalid.type = static_cast<OptionType>(0);
    EXPECT_THROW(quant::portfolio::price_risk({invalid}), std::invalid_argument);
    EXPECT_THROW(quant::portfolio::price_risk({}), std::invalid_argument);
    EXPECT_THROW(quant::portfolio::scenario_pnl({call()}, {}, false), std::invalid_argument);
    EXPECT_THROW(quant::portfolio::scenario_pnl({call()}, {{-1.0, 0.0, 0.0, 0.0, 0.0}}, false),
                 std::invalid_argument);
    EXPECT_THROW(quant::portfolio::scenario_pnl({call()}, {{0.0, -0.25, 0.0, 0.0, 0.0}}, false),
                 std::invalid_argument);
    EXPECT_THROW(quant::portfolio::scenario_pnl({call()}, {{0.0, 0.0, 0.0, 0.0, -0.01}}, false),
                 std::invalid_argument);
}
