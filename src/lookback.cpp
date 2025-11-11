#include "quant/lookback.hpp"
#include "quant/math.hpp"
#include "quant/qmc/brownian_bridge.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace quant::lookback {

McStatistic price_mc(const McParams& p) {
    using quant::stats::Welford;
    if (p.num_paths == 0 || p.num_steps <= 0)
        return {0.0, 0.0, 0.0, 0.0};
    const double dt = p.time / static_cast<double>(p.num_steps);
    const double drift_dt = (p.rate - p.dividend - 0.5 * p.vol * p.vol) * dt;
    const double vol_sdt = p.vol * std::sqrt(dt);
    const double disc = std::exp(-p.rate * p.time);

    Welford acc;
    pcg64 rng(p.seed ? p.seed : 0xBADC0FFEEULL);
    std::normal_distribution<double> normal(0.0, 1.0);

    // Optional Brownian bridge for better path statistics of extrema
    std::unique_ptr<quant::qmc::BrownianBridge> bridge;
    if (p.use_bridge) {
        bridge = std::make_unique<quant::qmc::BrownianBridge>(static_cast<std::size_t>(p.num_steps), p.time);
    }

    std::vector<double> normals;
    std::vector<double> increments;
    if (bridge) {
        normals.resize(static_cast<std::size_t>(p.num_steps));
        increments.resize(static_cast<std::size_t>(p.num_steps));
    }

    for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        auto simulate_once = [&](int sign) {
            double S = p.spot;
            double S_min = S;
            double S_max = S;
            if (bridge) {
                for (int t = 0; t < p.num_steps; ++t)
                    normals[static_cast<std::size_t>(t)] = normal(rng) * sign;
                bridge->transform(normals.data(), increments.data());
                for (int t = 0; t < p.num_steps; ++t) {
                    const double dw = increments[static_cast<std::size_t>(t)]; // N(0, dt)
                    S = S * std::exp(drift_dt + p.vol * dw);
                    S_min = std::min(S_min, S);
                    S_max = std::max(S_max, S);
                }
            } else {
                for (int t = 0; t < p.num_steps; ++t) {
                    double z = normal(rng) * sign;
                    S = S * std::exp(drift_dt + vol_sdt * z);
                    S_min = std::min(S_min, S);
                    S_max = std::max(S_max, S);
                }
            }
            double payoff = 0.0;
            if (p.type == Type::FixedStrike) {
                if (p.opt == ::quant::OptionType::Call)
                    payoff = std::max(0.0, S_max - p.strike);
                else
                    payoff = std::max(0.0, p.strike - S_min);
            } else { // Floating strike
                if (p.opt == ::quant::OptionType::Call)
                    payoff = std::max(0.0, S - S_min);
                else
                    payoff = std::max(0.0, S_max - S);
            }
            return disc * payoff;
        };
        double sample = simulate_once(+1);
        if (p.antithetic)
            sample = 0.5 * (sample + simulate_once(-1));
        acc.add(sample);
    }

    const double se = std::sqrt(acc.variance() / static_cast<double>(acc.count));
    const double half = quant::math::kZ95 * se;
    return {acc.mean, se, acc.mean - half, acc.mean + half};
}

} // namespace quant::lookback
