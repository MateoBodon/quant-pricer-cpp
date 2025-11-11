#include "quant/multi.hpp"
#include <algorithm>
#include <cmath>
#include <random>
#include <stdexcept>
#include <vector>

#include "quant/stats.hpp"

#include <pcg_random.hpp>

namespace quant::multi {

namespace {

std::vector<double> cholesky_lower(const std::vector<double>& corr, std::size_t n) {
    std::vector<double> L(corr);
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double sum = L[i * n + j];
            for (std::size_t k = 0; k < j; ++k) {
                sum -= L[i * n + k] * L[j * n + k];
            }
            if (i == j) {
                L[i * n + j] = (sum > 0.0) ? std::sqrt(sum) : 0.0;
            } else {
                L[i * n + j] = (L[j * n + j] > 0.0) ? (sum / L[j * n + j]) : 0.0;
            }
        }
        for (std::size_t j = i + 1; j < n; ++j) {
            L[i * n + j] = 0.0;
        }
    }
    return L;
}

double payoff_european_call(double strike, double basket) { return std::max(0.0, basket - strike); }

} // namespace

McStat basket_european_call_mc(const BasketMcParams& p) {
    const std::size_t n = p.spots.size();
    if (n == 0 || p.vols.size() != n || p.dividends.size() != n || p.weights.size() != n) {
        throw std::invalid_argument("BasketMcParams: dimension mismatch");
    }
    if (p.corr.size() != n * n) {
        throw std::invalid_argument("BasketMcParams: corr size mismatch");
    }

    auto L = cholesky_lower(p.corr, n);
    pcg64 rng(p.seed ? p.seed : 0xCAFEBABEULL);
    std::normal_distribution<double> normal(0.0, 1.0);

    const double dt = p.time;
    const double sqrt_dt = std::sqrt(dt);
    const double disc = std::exp(-p.rate * p.time);

    quant::stats::Welford acc;
    std::vector<double> z(n), y(n);

    for (std::uint64_t path = 0; path < p.num_paths; ++path) {
        for (std::size_t k = 0; k < n; ++k) {
            z[k] = normal(rng);
        }
        for (std::size_t irow = 0; irow < n; ++irow) {
            double v = 0.0;
            for (std::size_t k = 0; k <= irow; ++k) {
                v += L[irow * n + k] * z[k];
            }
            y[irow] = v;
        }

        double basket = 0.0;
        for (std::size_t k = 0; k < n; ++k) {
            const double drift = (p.rate - p.dividends[k] - 0.5 * p.vols[k] * p.vols[k]) * dt;
            const double S = p.spots[k] * std::exp(drift + p.vols[k] * sqrt_dt * y[k]);
            basket += p.weights[k] * S;
        }
        double sample = disc * payoff_european_call(p.strike, basket);

        if (p.antithetic) {
            double basket_anti = 0.0;
            for (std::size_t k = 0; k < n; ++k) {
                const double drift = (p.rate - p.dividends[k] - 0.5 * p.vols[k] * p.vols[k]) * dt;
                const double S_anti = p.spots[k] * std::exp(drift - p.vols[k] * sqrt_dt * y[k]);
                basket_anti += p.weights[k] * S_anti;
            }
            const double anti_sample = disc * payoff_european_call(p.strike, basket_anti);
            sample = 0.5 * (sample + anti_sample);
        }

        acc.add(sample);
    }

    const double variance = acc.variance();
    const double se =
        (acc.count > 0) ? std::sqrt(std::max(0.0, variance / static_cast<double>(acc.count))) : 0.0;
    return {acc.mean, se};
}

McStat merton_call_mc(const MertonParams& p) {
    pcg64 rng(p.seed ? p.seed : 0xDEADC0DEULL);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::poisson_distribution<unsigned> pois(p.lambda * p.time);

    const double disc = std::exp(-p.rate * p.time);
    const double sqrt_t = std::sqrt(p.time);
    const double jump_drift = p.lambda * (std::exp(p.muJ + 0.5 * p.sigmaJ * p.sigmaJ) - 1.0);
    const double drift = (p.rate - p.dividend - 0.5 * p.vol * p.vol - jump_drift) * p.time;

    quant::stats::Welford acc;
    std::vector<double> jumps;

    for (std::uint64_t path = 0; path < p.num_paths; ++path) {
        const unsigned N = pois(rng);
        jumps.resize(N);
        double jump_sum = 0.0;
        for (unsigned j = 0; j < N; ++j) {
            const double z = normal(rng);
            const double J = p.muJ + p.sigmaJ * z;
            jumps[j] = J;
            jump_sum += J;
        }

        const double z_diff = normal(rng);
        const double diff = p.vol * sqrt_t * z_diff;
        const double ST = p.spot * std::exp(drift + diff + jump_sum);
        const double payoff = std::max(0.0, ST - p.strike);
        double sample = disc * payoff;

        if (p.antithetic) {
            const double diff_anti = -diff;
            const double ST_anti = p.spot * std::exp(drift + diff_anti + jump_sum);
            const double payoff_anti = std::max(0.0, ST_anti - p.strike);
            sample = 0.5 * (sample + disc * payoff_anti);
        }

        acc.add(sample);
    }

    const double variance = acc.variance();
    const double se =
        (acc.count > 0) ? std::sqrt(std::max(0.0, variance / static_cast<double>(acc.count))) : 0.0;
    return {acc.mean, se};
}

} // namespace quant::multi
