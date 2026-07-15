/// Vectorized vanilla-option portfolio valuation and deterministic stress P&L.
#pragma once

#include <cstddef>
#include <vector>

namespace quant::portfolio {

enum class OptionType : int { Put = -1, Call = 1 };

struct VanillaPosition {
    OptionType type;
    double quantity;
    double spot;
    double strike;
    double rate;
    double dividend;
    double volatility;
    double time;
};

struct PositionRisk {
    double price;
    double value;
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
};

struct PortfolioTotals {
    double value{};
    double delta{};
    double gamma{};
    double vega{};
    double theta{};
    double rho{};
};

struct RiskResult {
    std::vector<PositionRisk> positions;
    PortfolioTotals totals;
};

struct MarketShock {
    double spot_return;
    double volatility_shift;
    double rate_shift;
    double dividend_shift;
    double time_elapsed;
};

struct ScenarioResult {
    std::size_t scenario_count{};
    std::size_t position_count{};
    double base_portfolio_value{};
    std::vector<double> portfolio_pnl;
    // Scenario-major (scenario_count, position_count); empty in aggregate-only mode.
    std::vector<double> position_pnl;
};

/// Validate and value a non-empty portfolio. Throws std::invalid_argument on
/// non-finite or economically invalid inputs.
RiskResult price_risk(const std::vector<VanillaPosition>& positions);

/// Exact-reprice each position under each shock. When include_position_pnl is
/// false, the potentially large scenario-by-position matrix is not allocated.
ScenarioResult scenario_pnl(const std::vector<VanillaPosition>& positions,
                            const std::vector<MarketShock>& shocks, bool include_position_pnl = false);

} // namespace quant::portfolio
