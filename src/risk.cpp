#include "quant/risk.hpp"
#include "quant/math.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <random>
#include <stdexcept>
#include <vector>

namespace quant::risk {

VarEs var_cvar_from_pnl(const std::vector<double>& pnl, double alpha) {
    if (pnl.empty())
        return {0.0, 0.0};
    std::vector<double> sorted = pnl;
    std::sort(sorted.begin(), sorted.end());
    const std::size_t idx = static_cast<std::size_t>(std::floor((1.0 - alpha) * sorted.size()));
    const double var = -sorted[idx];
    double es_sum = 0.0;
    for (std::size_t i = 0; i <= idx; ++i)
        es_sum += -sorted[i];
    const double cvar = es_sum / static_cast<double>(idx + 1);
    return {var, cvar};
}

VarEs var_cvar_gbm(double spot, double mu, double sigma, double horizon_years, double position,
                   unsigned long num_sims, unsigned long seed, double alpha) {
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

VarEs var_cvar_portfolio(const std::vector<double>& mu, const std::vector<double>& sigma,
                         const std::vector<double>& corr, const std::vector<double>& weights,
                         double horizon_years, unsigned long num_sims, unsigned long seed, double alpha) {
    const std::size_t N = mu.size();
    if (sigma.size() != N || weights.size() != N)
        return {0.0, 0.0};
    if (corr.size() != N * N)
        return {0.0, 0.0};
    // Cholesky of corr
    std::vector<double> L(corr);
    for (std::size_t i = 0; i < N; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double sum = L[i * N + j];
            for (std::size_t k = 0; k < j; ++k)
                sum -= L[i * N + k] * L[j * N + k];
            if (i == j) {
                L[i * N + j] = (sum > 0.0) ? std::sqrt(sum) : 0.0;
            } else {
                L[i * N + j] = (L[j * N + j] > 0.0) ? (sum / L[j * N + j]) : 0.0;
            }
        }
        for (std::size_t j = i + 1; j < N; ++j)
            L[i * N + j] = 0.0;
    }

    pcg64 rng(seed ? seed : 0xBADDCAFE);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<double> pnl;
    pnl.reserve(num_sims);
    for (unsigned long s = 0; s < num_sims; ++s) {
        std::vector<double> z(N);
        for (std::size_t i = 0; i < N; ++i)
            z[i] = normal(rng);
        // correlate: y = L * z
        std::vector<double> y(N, 0.0);
        for (std::size_t i = 0; i < N; ++i) {
            for (std::size_t k = 0; k <= i; ++k)
                y[i] += L[i * N + k] * z[k];
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

namespace {
static inline double chi2_cdf_complement(double x, double k) {
    // Complementary CDF for chi-square.
    // For the cases we rely on (k ∈ {1,2}), closed forms exist; for any other
    // value fall back to a simple (conservative) exponential tail.
    const double z = std::sqrt(std::max(0.0, x));
    if (k == 1.0) {
        // Chi-square(1) tail = 2 * (1 - Phi(z)) = erfc(z / sqrt(2))
        return std::erfc(z / std::sqrt(2.0));
    }
    if (k == 2.0) {
        // Chi-square(2) tail = exp(-x/2)
        return std::exp(-0.5 * x);
    }
    // Fallback: ensure the result remains in (0,1] even if coarse.
    const double tail = std::exp(-0.5 * x);
    return std::clamp(tail, 0.0, 1.0);
}

double bernoulli_log_likelihood(unsigned long successes, unsigned long failures, double probability) {
    double value = 0.0;
    if (successes > 0) {
        if (probability <= 0.0)
            return -std::numeric_limits<double>::infinity();
        value += static_cast<double>(successes) * std::log(probability);
    }
    if (failures > 0) {
        if (probability >= 1.0)
            return -std::numeric_limits<double>::infinity();
        value += static_cast<double>(failures) * std::log1p(-probability);
    }
    return value;
}
} // namespace

BacktestStats kupiec_christoffersen(const std::vector<int>& exceptions, double alpha) {
    if (!std::isfinite(alpha) || alpha <= 0.0 || alpha >= 1.0)
        throw std::invalid_argument("VaR confidence alpha must be finite and in (0,1)");
    if (exceptions.empty())
        throw std::invalid_argument("VaR exception sequence must be non-empty");

    BacktestStats out{};
    out.alpha = alpha;
    const unsigned long T = static_cast<unsigned long>(exceptions.size());
    out.T = T;
    unsigned long N = 0;
    for (int e : exceptions) {
        if (e != 0 && e != 1)
            throw std::invalid_argument("VaR exception sequence values must be 0 or 1");
        if (e == 1)
            ++N;
    }
    out.N = N;
    const double pi = static_cast<double>(N) / std::max(1UL, T);
    const double expected_exception_probability = 1.0 - alpha;
    const double ll_pof_null = bernoulli_log_likelihood(N, T - N, expected_exception_probability);
    const double ll_pof_mle = bernoulli_log_likelihood(N, T - N, pi);
    out.lr_pof = std::max(0.0, 2.0 * (ll_pof_mle - ll_pof_null));
    out.p_pof = chi2_cdf_complement(out.lr_pof, 1.0);

    // Christoffersen independence: build transition counts
    unsigned long n00 = 0, n01 = 0, n10 = 0, n11 = 0;
    for (unsigned long t = 1; t < T; ++t) {
        int a = exceptions[t - 1] ? 1 : 0;
        int b = exceptions[t] ? 1 : 0;
        if (a == 0 && b == 0)
            ++n00;
        else if (a == 0 && b == 1)
            ++n01;
        else if (a == 1 && b == 0)
            ++n10;
        else
            ++n11;
    }
    const unsigned long transitions = n00 + n01 + n10 + n11;
    if (transitions == 0) {
        out.lr_ind = 0.0;
        out.p_ind = 1.0;
        out.lr_cc = out.lr_pof;
        out.p_cc = chi2_cdf_complement(out.lr_cc, 2.0);
        return out;
    }
    const double pi0 = (n00 + n01) ? static_cast<double>(n01) / static_cast<double>(n00 + n01) : 0.0;
    const double pi1 = (n10 + n11) ? static_cast<double>(n11) / static_cast<double>(n10 + n11) : 0.0;
    const double pi_bar = static_cast<double>(n01 + n11) / static_cast<double>(transitions);
    const double ll_ind = bernoulli_log_likelihood(n01, n00, pi0) + bernoulli_log_likelihood(n11, n10, pi1);
    const double ll_null = bernoulli_log_likelihood(n01 + n11, n00 + n10, pi_bar);
    out.lr_ind = std::max(0.0, 2.0 * (ll_ind - ll_null));
    out.p_ind = chi2_cdf_complement(out.lr_ind, 1.0);

    out.lr_cc = out.lr_pof + out.lr_ind;
    out.p_cc = chi2_cdf_complement(out.lr_cc, 2.0);
    return out;
}

quant::risk::VarEs var_cvar_t(double mu, double sigma, double nu, double horizon_years, double position,
                              unsigned long num_sims, unsigned long seed, double alpha) {
    if (nu <= 2.0) {
        throw std::invalid_argument("Student-t degrees of freedom must exceed 2 for finite variance");
    }
    pcg64 rng(seed ? seed : 0xABCD1234);
    std::student_t_distribution<double> tdist(nu);
    std::vector<double> pnl;
    pnl.reserve(num_sims);
    const double scale = sigma * std::sqrt(horizon_years) * std::sqrt((nu - 2.0) / nu);
    const double drift = mu * horizon_years;
    for (unsigned long i = 0; i < num_sims; ++i) {
        double z = tdist(rng);
        // Linear P&L model: drift + scaled heavy-tail shock
        double pl = position * (drift + scale * z);
        pnl.push_back(pl);
    }
    return var_cvar_from_pnl(pnl, alpha);
}

} // namespace quant::risk
