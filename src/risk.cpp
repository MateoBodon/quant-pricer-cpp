#include "quant/risk.hpp"
#include "quant/math.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace quant::risk {

VarEs var_cvar_from_pnl(const std::vector<double>& pnl, double alpha) {
    if (pnl.empty()) return {0.0, 0.0};
    std::vector<double> sorted = pnl;
    std::sort(sorted.begin(), sorted.end());
    const std::size_t idx = static_cast<std::size_t>(std::floor((1.0 - alpha) * sorted.size()));
    const double var = -sorted[idx];
    double es_sum = 0.0;
    for (std::size_t i = 0; i <= idx; ++i) es_sum += -sorted[i];
    const double cvar = es_sum / static_cast<double>(idx + 1);
    return {var, cvar};
}

VarEs var_cvar_gbm(double spot,
                   double mu,
                   double sigma,
                   double horizon_years,
                   double position,
                   unsigned long num_sims,
                   unsigned long seed,
                   double alpha) {
    pcg64 rng(seed ? seed : 0xDEADBEEF);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<double> pnl;
    pnl.reserve(num_sims);
    const double drift = (mu - 0.5 * sigma * sigma) * horizon_years;
    const double vol = sigma * std::sqrt(horizon_years);
    for (unsigned long i = 0; i < num_sims; ++i) {
        double z = normal(rng);
        double S1 = spot * std::exp(drift + vol * z);
        double pl = position * (S1 - spot);
        pnl.push_back(pl);
    }
    return var_cvar_from_pnl(pnl, alpha);
}

VarEs var_cvar_portfolio(const std::vector<double>& mu,
                         const std::vector<double>& sigma,
                         const std::vector<double>& corr,
                         const std::vector<double>& weights,
                         double horizon_years,
                         unsigned long num_sims,
                         unsigned long seed,
                         double alpha) {
    const std::size_t N = mu.size();
    if (sigma.size() != N || weights.size() != N) return {0.0, 0.0};
    if (corr.size() != N * N) return {0.0, 0.0};
    // Cholesky of corr
    std::vector<double> L(corr);
    for (std::size_t i = 0; i < N; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double sum = L[i*N + j];
            for (std::size_t k = 0; k < j; ++k) sum -= L[i*N + k] * L[j*N + k];
            if (i == j) {
                L[i*N + j] = (sum > 0.0) ? std::sqrt(sum) : 0.0;
            } else {
                L[i*N + j] = (L[j*N + j] > 0.0) ? (sum / L[j*N + j]) : 0.0;
            }
        }
        for (std::size_t j = i + 1; j < N; ++j) L[i*N + j] = 0.0;
    }

    pcg64 rng(seed ? seed : 0xBADDCAFE);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<double> pnl; pnl.reserve(num_sims);
    for (unsigned long s = 0; s < num_sims; ++s) {
        std::vector<double> z(N);
        for (std::size_t i = 0; i < N; ++i) z[i] = normal(rng);
        // correlate: y = L * z
        std::vector<double> y(N, 0.0);
        for (std::size_t i = 0; i < N; ++i) {
            for (std::size_t k = 0; k <= i; ++k) y[i] += L[i*N + k] * z[k];
        }
        double pl = 0.0;
        for (std::size_t i = 0; i < N; ++i) {
            double drift = mu[i] * horizon_years;
            double diff = sigma[i] * std::sqrt(horizon_years) * y[i];
            pl += weights[i] * (drift + diff);
        }
        pnl.push_back(pl);
    }
    return var_cvar_from_pnl(pnl, alpha);
}

} // namespace quant::risk


