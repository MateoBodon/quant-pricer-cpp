#include "quant/asian.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>

namespace quant::asian {

static inline double geometric_closed_form_call(double S, double K, double r, double q, double sigma, double T) {
    // Kemna–Vorst geometric Asian call under GBM
    const double rho = std::sqrt(1.0/3.0);
    const double sigma_g = sigma * rho;
    const double r_g = 0.5 * (r - q) + q; // drift adjustment for geometric average
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    const double mu_g = (r - q - 0.5 * sigma * sigma) * 0.5 * T + 0.5 * sigma * sigma * (1.0/6.0) * T;
    const double d1 = (std::log(S / K) + mu_g + 0.5 * sigma_g * sigma_g * T) / (sigma_g * std::sqrt(T));
    const double d2 = d1 - sigma_g * std::sqrt(T);
    return df_q * S * std::erfc(-d1 / std::sqrt(2.0)) * 0.5 - df_r * K * std::erfc(-d2 / std::sqrt(2.0)) * 0.5;
}

asian::McStatistic price_mc(const McParams& p) {
    using quant::stats::Welford;
    Welford acc;
    if (p.num_paths == 0 || p.num_steps <= 0) {
        return {0.0, 0.0, 0.0, 0.0};
    }
    const double dt = p.time / static_cast<double>(p.num_steps);
    const double df_r = std::exp(-p.rate * p.time);
    const double drift_dt = (p.rate - p.dividend - 0.5 * p.vol * p.vol) * dt;
    const double vol_sdt = p.vol * std::sqrt(dt);

    const bool fixed_strike = (p.payoff == Payoff::FixedStrike);
    const bool use_cv = p.use_geometric_cv && (p.avg == Average::Arithmetic) && fixed_strike;
    const double geo_cf = use_cv ? geometric_closed_form_call(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time) : 0.0;

    pcg64 rng(p.seed ? p.seed : 0xC0FFEEULL);
    std::normal_distribution<double> normal(0.0, 1.0);

    for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        double S = p.spot;
        double sum = 0.0;
        double log_sum = 0.0;
        for (int t = 0; t < p.num_steps; ++t) {
            const double z = normal(rng);
            S = S * std::exp(drift_dt + vol_sdt * z);
            sum += S;
            log_sum += std::log(S);
        }
        const double arith = sum / static_cast<double>(p.num_steps);
        const double geom = std::exp(log_sum / static_cast<double>(p.num_steps));

        double payoff = 0.0;
        if (fixed_strike) {
            payoff = std::max(0.0, arith - p.strike);
        } else {
            payoff = std::max(0.0, p.spot - arith);
        }
        double sample = df_r * payoff;
        if (use_cv) {
            const double geo_payoff = std::max(0.0, geom - p.strike);
            const double geo_disc = df_r * geo_payoff;
            sample += (geo_cf - geo_disc);
        }
        acc.add(sample);
    }

    const double var = acc.variance();
    const double se = std::sqrt(var / static_cast<double>(acc.count));
    const double half = quant::math::kZ95 * se;
    const double mean = acc.mean;
    return {mean, se, mean - half, mean + half};
}

} // namespace quant::asian


