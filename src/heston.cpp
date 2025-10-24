#include "quant/heston.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace quant::heston {

// Minimal placeholder analytic using Black-Scholes with implied vol = sqrt(theta)
// TODO: replace with full Heston characteristic-function integral
double call_analytic(const MarketParams& mkt, const Params& h) {
    const double sigma_eff = std::sqrt(std::max(0.0, h.theta));
    // crude proxy until full implementation
    const double d1 = (std::log(mkt.spot / mkt.strike) + (mkt.rate - mkt.dividend + 0.5 * sigma_eff * sigma_eff) * mkt.time)
                      / (sigma_eff * std::sqrt(mkt.time));
    const double d2 = d1 - sigma_eff * std::sqrt(mkt.time);
    const double df_r = std::exp(-mkt.rate * mkt.time);
    const double df_q = std::exp(-mkt.dividend * mkt.time);
    const double N1 = 0.5 * std::erfc(-d1 / std::sqrt(2.0));
    const double N2 = 0.5 * std::erfc(-d2 / std::sqrt(2.0));
    return mkt.spot * df_q * N1 - mkt.strike * df_r * N2;
}

McResult call_qe_mc(const McParams& p) {
    using quant::stats::Welford;
    const double dt = p.mkt.time / static_cast<double>(p.num_steps);
    const double df = std::exp(-p.mkt.rate * p.mkt.time);
    Welford acc;
    pcg64 rng(p.seed ? p.seed : 0xFACEFEEDULL);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::uniform_real_distribution<double> uniform(0.0, 1.0);

    auto simulate_once = [&](int sign) {
        double S = p.mkt.spot;
        double v = std::max(0.0, p.h.v0);
        for (int i = 0; i < p.num_steps; ++i) {
            const double z1 = normal(rng) * sign;
            const double z2 = normal(rng) * sign;
            const double eps1 = z1;
            const double eps2 = p.h.rho * z1 + std::sqrt(std::max(0.0, 1.0 - p.h.rho * p.h.rho)) * z2;
            // Andersen QE scheme (simplified)
            const double kappa = p.h.kappa;
            const double theta = p.h.theta;
            const double sigma = p.h.sigma;
            const double m = theta + (v - theta) * std::exp(-kappa * dt);
            const double s2 = v * sigma * sigma * std::exp(-kappa * dt) * (1.0 - std::exp(-kappa * dt)) / kappa
                              + theta * sigma * sigma * 0.5 / kappa * (1.0 - std::exp(-kappa * dt)) * (1.0 - std::exp(-kappa * dt));
            const double psi = s2 / (m * m);
            double v_next;
            if (psi <= 1.5) {
                const double b2 = 2.0 / psi - 1.0 + std::sqrt(2.0 / psi) * std::sqrt(2.0 / psi - 1.0);
                const double a = m / (1.0 + b2);
                const double b = b2;
                const double u = std::min(1.0 - std::numeric_limits<double>::epsilon(), std::max(uniform(rng), std::numeric_limits<double>::min()));
                v_next = a * std::pow(1.0 + b, (u < (b / (1.0 + b)) ? 1.0 : 0.0));
            } else {
                const double pexp = (psi - 1.0) / (psi + 1.0);
                const double beta = (1.0 - pexp) / m;
                const double u = std::min(1.0 - std::numeric_limits<double>::epsilon(), std::max(uniform(rng), std::numeric_limits<double>::min()));
                v_next = (u > pexp) ? std::log((1.0 - pexp) / (1.0 - u)) / beta : 0.0;
            }
            const double z_s = eps1;
            const double drift = (p.mkt.rate - p.mkt.dividend - 0.5 * v_next) * dt;
            const double diff = std::sqrt(std::max(0.0, v_next)) * std::sqrt(dt) * z_s;
            S = S * std::exp(drift + diff);
            v = std::max(0.0, v_next);
        }
        return df * std::max(0.0, S - p.mkt.strike);
    };

    for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        double sample = simulate_once(+1);
        if (p.antithetic) sample = 0.5 * (sample + simulate_once(-1));
        acc.add(sample);
    }
    const double se = std::sqrt(acc.variance() / static_cast<double>(acc.count));
    return McResult{acc.mean, se};
}

} // namespace quant::heston


