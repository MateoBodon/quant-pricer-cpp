#include "quant/portfolio.hpp"

#include "quant/black_scholes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace quant::portfolio {
namespace {

void validate_position(const VanillaPosition& position) {
    const bool finite = std::isfinite(position.quantity) && std::isfinite(position.spot) &&
                        std::isfinite(position.strike) && std::isfinite(position.rate) &&
                        std::isfinite(position.dividend) && std::isfinite(position.volatility) &&
                        std::isfinite(position.time);
    if (!finite) {
        throw std::invalid_argument("portfolio position contains a non-finite value");
    }
    if (position.type != OptionType::Call && position.type != OptionType::Put) {
        throw std::invalid_argument("portfolio option type must be Call or Put");
    }
    if (position.spot <= 0.0 || position.strike <= 0.0 || position.volatility < 0.0 || position.time < 0.0) {
        throw std::invalid_argument(
            "portfolio position requires positive spot/strike and non-negative vol/time");
    }
}

double option_price(const VanillaPosition& position) {
    if (position.type == OptionType::Call) {
        return quant::bs::call_price(position.spot, position.strike, position.rate, position.dividend,
                                     position.volatility, position.time);
    }
    return quant::bs::put_price(position.spot, position.strike, position.rate, position.dividend,
                                position.volatility, position.time);
}

PositionRisk position_risk(const VanillaPosition& position) {
    const bool call = position.type == OptionType::Call;
    double price;
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
    if (position.time <= 0.0 || position.volatility <= 0.0) {
        // Preserve the scalar library's explicit expiry/deterministic conventions.
        price = option_price(position);
        delta = call ? quant::bs::delta_call(position.spot, position.strike, position.rate, position.dividend,
                                             position.volatility, position.time)
                     : quant::bs::delta_put(position.spot, position.strike, position.rate, position.dividend,
                                            position.volatility, position.time);
        gamma = quant::bs::gamma(position.spot, position.strike, position.rate, position.dividend,
                                 position.volatility, position.time);
        vega = quant::bs::vega(position.spot, position.strike, position.rate, position.dividend,
                               position.volatility, position.time);
        theta = call ? quant::bs::theta_call(position.spot, position.strike, position.rate, position.dividend,
                                             position.volatility, position.time)
                     : quant::bs::theta_put(position.spot, position.strike, position.rate, position.dividend,
                                            position.volatility, position.time);
        rho = call ? quant::bs::rho_call(position.spot, position.strike, position.rate, position.dividend,
                                         position.volatility, position.time)
                   : quant::bs::rho_put(position.spot, position.strike, position.rate, position.dividend,
                                        position.volatility, position.time);
    } else {
        // Fused analytic path: every price/Greek shares one d1/d2 and discount calculation.
        const double sqrt_time = std::sqrt(position.time);
        const double d1 =
            (std::log(position.spot / position.strike) +
             (position.rate - position.dividend + 0.5 * position.volatility * position.volatility) *
                 position.time) /
            (position.volatility * sqrt_time);
        const double d2 = d1 - position.volatility * sqrt_time;
        const double discount_rate = std::exp(-position.rate * position.time);
        const double discount_dividend = std::exp(-position.dividend * position.time);
        const double density = quant::bs::normal_pdf(d1);
        const double carry_theta =
            -(position.spot * discount_dividend * density * position.volatility) / (2.0 * sqrt_time);
        gamma = discount_dividend * density / (position.spot * position.volatility * sqrt_time);
        vega = position.spot * discount_dividend * density * sqrt_time;
        if (call) {
            const double cdf_d1 = quant::bs::normal_cdf(d1);
            const double cdf_d2 = quant::bs::normal_cdf(d2);
            price = position.spot * discount_dividend * cdf_d1 - position.strike * discount_rate * cdf_d2;
            delta = discount_dividend * cdf_d1;
            theta = carry_theta + position.dividend * position.spot * discount_dividend * cdf_d1 -
                    position.rate * position.strike * discount_rate * cdf_d2;
            rho = position.strike * position.time * discount_rate * cdf_d2;
        } else {
            const double cdf_minus_d1 = quant::bs::normal_cdf(-d1);
            const double cdf_minus_d2 = quant::bs::normal_cdf(-d2);
            price = position.strike * discount_rate * cdf_minus_d2 -
                    position.spot * discount_dividend * cdf_minus_d1;
            delta = -discount_dividend * cdf_minus_d1;
            theta = carry_theta - position.dividend * position.spot * discount_dividend * cdf_minus_d1 +
                    position.rate * position.strike * discount_rate * cdf_minus_d2;
            rho = -position.strike * position.time * discount_rate * cdf_minus_d2;
        }
    }
    const double quantity = position.quantity;
    return PositionRisk{price,           quantity * price, quantity * delta, quantity * gamma,
                        quantity * vega, quantity * theta, quantity * rho};
}

void validate_shock(const MarketShock& shock) {
    const bool finite = std::isfinite(shock.spot_return) && std::isfinite(shock.volatility_shift) &&
                        std::isfinite(shock.rate_shift) && std::isfinite(shock.dividend_shift) &&
                        std::isfinite(shock.time_elapsed);
    if (!finite) {
        throw std::invalid_argument("portfolio shock contains a non-finite value");
    }
    if (shock.spot_return <= -1.0 || shock.time_elapsed < 0.0) {
        throw std::invalid_argument(
            "portfolio shock requires spot_return > -1 and non-negative time_elapsed");
    }
}

} // namespace

RiskResult price_risk(const std::vector<VanillaPosition>& positions) {
    if (positions.empty()) {
        throw std::invalid_argument("portfolio positions must be non-empty");
    }
    RiskResult result;
    result.positions.reserve(positions.size());
    for (const auto& position : positions) {
        validate_position(position);
        const auto risk = position_risk(position);
        result.positions.push_back(risk);
        result.totals.value += risk.value;
        result.totals.delta += risk.delta;
        result.totals.gamma += risk.gamma;
        result.totals.vega += risk.vega;
        result.totals.theta += risk.theta;
        result.totals.rho += risk.rho;
    }
    return result;
}

ScenarioResult scenario_pnl(const std::vector<VanillaPosition>& positions,
                            const std::vector<MarketShock>& shocks, bool include_position_pnl) {
    if (positions.empty() || shocks.empty()) {
        throw std::invalid_argument("portfolio positions and shocks must be non-empty");
    }
    for (const auto& position : positions) {
        validate_position(position);
    }
    for (const auto& shock : shocks) {
        validate_shock(shock);
        for (const auto& position : positions) {
            if (position.volatility + shock.volatility_shift < 0.0) {
                throw std::invalid_argument("portfolio shock produces negative volatility");
            }
        }
    }

    const std::size_t scenario_count = shocks.size();
    const std::size_t position_count = positions.size();
    if (include_position_pnl && scenario_count > std::vector<double>().max_size() / position_count) {
        throw std::overflow_error("portfolio scenario detail matrix is too large");
    }

    std::vector<double> base_values;
    base_values.reserve(position_count);
    double base_portfolio_value = 0.0;
    for (const auto& position : positions) {
        const double value = position.quantity * option_price(position);
        base_values.push_back(value);
        base_portfolio_value += value;
    }

    ScenarioResult result;
    result.scenario_count = scenario_count;
    result.position_count = position_count;
    result.base_portfolio_value = base_portfolio_value;
    result.portfolio_pnl.resize(scenario_count);
    if (include_position_pnl) {
        result.position_pnl.resize(scenario_count * position_count);
    }

    for (std::size_t scenario_index = 0; scenario_index < scenario_count; ++scenario_index) {
        const auto& shock = shocks[scenario_index];
        const bool identity_shock = shock.spot_return == 0.0 && shock.volatility_shift == 0.0 &&
                                    shock.rate_shift == 0.0 && shock.dividend_shift == 0.0 &&
                                    shock.time_elapsed == 0.0;
        if (identity_shock) {
            result.portfolio_pnl[scenario_index] = 0.0;
            if (include_position_pnl) {
                std::fill_n(result.position_pnl.data() + scenario_index * position_count, position_count,
                            0.0);
            }
            continue;
        }
        double total_pnl = 0.0;
        for (std::size_t position_index = 0; position_index < position_count; ++position_index) {
            auto shocked = positions[position_index];
            shocked.spot *= 1.0 + shock.spot_return;
            shocked.volatility += shock.volatility_shift;
            shocked.rate += shock.rate_shift;
            shocked.dividend += shock.dividend_shift;
            shocked.time = std::max(0.0, shocked.time - shock.time_elapsed);
            const double pnl = shocked.quantity * option_price(shocked) - base_values[position_index];
            total_pnl += pnl;
            if (include_position_pnl) {
                result.position_pnl[scenario_index * position_count + position_index] = pnl;
            }
        }
        result.portfolio_pnl[scenario_index] = total_pnl;
    }
    return result;
}

} // namespace quant::portfolio
