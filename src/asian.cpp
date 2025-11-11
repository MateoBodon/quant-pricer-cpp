#include "quant/asian.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"
#include "quant/qmc/sobol.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>
#include <vector>
#include <memory>
#include <stdexcept>

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
    if (p.qmc != Qmc::None && p.num_steps > static_cast<int>(quant::qmc::SobolSequence::kMaxSupportedDimension)) {
        throw std::invalid_argument("asian::price_mc: Sobol dimension exceeds supported maximum");
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
    std::vector<double> normals(static_cast<std::size_t>(p.num_steps));
    const bool use_qmc = p.qmc != Qmc::None;
    std::unique_ptr<quant::qmc::SobolSequence> sobol_seq;
    std::vector<double> sobol_point;
    if (use_qmc) {
        sobol_seq = std::make_unique<quant::qmc::SobolSequence>(
            static_cast<std::size_t>(p.num_steps),
            p.qmc == Qmc::SobolScrambled,
            p.seed ? p.seed : 0x9E3779B97F4A7C15ULL);
        sobol_point.resize(static_cast<std::size_t>(p.num_steps));
    }

    auto run_path = [&](const std::vector<double>& draws) {
        double S = p.spot;
        double arith_acc = 0.0;
        double log_acc = 0.0;
        for (int t = 0; t < p.num_steps; ++t) {
            const double z = draws[static_cast<std::size_t>(t)];
            S = S * std::exp(drift_dt + vol_sdt * z);
            arith_acc += S;
            log_acc += std::log(S);
        }
        const double inv_steps = 1.0 / static_cast<double>(p.num_steps);
        const double arith = arith_acc * inv_steps;
        const double geom = std::exp(log_acc * inv_steps);

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
        return sample;
    };

    std::vector<double> antithetic_draws(static_cast<std::size_t>(p.num_steps));

    for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        if (use_qmc) {
            sobol_seq->generate(i, sobol_point.data());
            for (int t = 0; t < p.num_steps; ++t) {
                const double u = std::clamp(
                    sobol_point[static_cast<std::size_t>(t)],
                    std::numeric_limits<double>::min(),
                    1.0 - std::numeric_limits<double>::epsilon());
                normals[static_cast<std::size_t>(t)] = quant::math::inverse_normal_cdf(u);
            }
        } else {
            for (int t = 0; t < p.num_steps; ++t) {
                normals[static_cast<std::size_t>(t)] = normal(rng);
            }
        }
        double sample = run_path(normals);
        if (p.antithetic) {
            for (int t = 0; t < p.num_steps; ++t) {
                antithetic_draws[static_cast<std::size_t>(t)] = -normals[static_cast<std::size_t>(t)];
            }
            const double antithetic_sample = run_path(antithetic_draws);
            sample = 0.5 * (sample + antithetic_sample);
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
