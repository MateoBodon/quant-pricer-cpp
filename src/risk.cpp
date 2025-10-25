#include "quant/risk.hpp"
#include "quant/math.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>
#include <vector>

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

namespace {
static inline double chi2_cdf_complement(double x, double k) {
    // Complementary CDF for chi-square using regularized gamma Q(k/2, x/2)
    // Use a simple series/incomplete gamma approximation sufficient for small k
    // For k=1 or 2, we can use closed-forms via error/exponential functions.
    if (k == 1.0) {
        // Chi-square(1) ~ Z^2, P[Z^2 >= x] = 2*(1 - Phi(sqrt(x)))
        const double z = std::sqrt(std::max(0.0, x));
        const double tail = 1.0 - 0.5 * std::erfc(-z / std::sqrt(2.0));
        return 2.0 * (1.0 - tail);
    }
    if (k == 2.0) {
        // Chi-square(2) ~ Exp(1/2), tail = exp(-x/2)
        return std::exp(-0.5 * x);
    }
    // Fallback: simple upper incomplete gamma approximation (not tight but serviceable)
    const double s = 0.5 * k;
    const double t = 0.5 * x;
    // Regularized upper gamma Q(s, t) ~ e^{-t} * sum_{n=0}^{s-1} t^n / n! when s integer
    int s_int = static_cast<int>(std::round(s));
    if (std::abs(s - s_int) < 1e-9 && s_int > 0 && s_int <= 10) {
        double sum = 0.0;
        double term = 1.0;
        for (int n = 0; n < s_int; ++n) {
            if (n > 0) term *= t / n;
            sum += term;
        }
        return std::exp(-t) * sum;
    }
    // As a last resort, clamp
    return std::exp(-0.5 * x);
}
}

BacktestStats kupiec_christoffersen(const std::vector<int>& exceptions, double alpha) {
    BacktestStats out{};
    out.alpha = alpha;
    const unsigned long T = static_cast<unsigned long>(exceptions.size());
    out.T = T;
    unsigned long N = 0;
    for (int e : exceptions) if (e) ++N;
    out.N = N;
    const double pi = static_cast<double>(N) / std::max(1UL, T);
    // Kupiec POF LR = -2 log( ((1-alpha)^{T-N} alpha^N) / ((1-pi)^{T-N} pi^N) )
    const double term1 = (T - N) * (std::log(1.0 - alpha) - std::log(std::max(1e-12, 1.0 - pi)));
    const double term2 = N * (std::log(std::max(1e-12, alpha)) - std::log(std::max(1e-12, pi)));
    out.lr_pof = -2.0 * (term1 + term2);
    out.p_pof = chi2_cdf_complement(out.lr_pof, 1.0);

    // Christoffersen independence: build transition counts
    unsigned long n00 = 0, n01 = 0, n10 = 0, n11 = 0;
    for (unsigned long t = 1; t < T; ++t) {
        int a = exceptions[t - 1] ? 1 : 0;
        int b = exceptions[t] ? 1 : 0;
        if (a == 0 && b == 0) ++n00;
        else if (a == 0 && b == 1) ++n01;
        else if (a == 1 && b == 0) ++n10;
        else ++n11;
    }
    const double pi0 = (n00 + n01) ? static_cast<double>(n01) / static_cast<double>(n00 + n01) : 0.0;
    const double pi1 = (n10 + n11) ? static_cast<double>(n11) / static_cast<double>(n10 + n11) : 0.0;
    const double pi_bar = (n01 + n11) ? static_cast<double>(n01 + n11) / static_cast<double>(n00 + n01 + n10 + n11) : 0.0;
    auto safe_log = [](double x){ return std::log(std::max(1e-12, x)); };
    const double ll_ind = (n00 + n01) * safe_log(1.0 - pi0) + n01 * safe_log(pi0)
                        + (n10 + n11) * safe_log(1.0 - pi1) + n11 * safe_log(pi1);
    const double ll_null = (n00 + n01 + n10 + n11) * safe_log(1.0 - pi_bar) + (n01 + n11) * safe_log(pi_bar);
    out.lr_ind = -2.0 * (ll_null - ll_ind);
    out.p_ind = chi2_cdf_complement(out.lr_ind, 1.0);

    out.lr_cc = out.lr_pof + out.lr_ind;
    out.p_cc = chi2_cdf_complement(out.lr_cc, 2.0);
    return out;
}

quant::risk::VarEs var_cvar_t(double mu,
                 double sigma,
                 double nu,
                 double horizon_years,
                 double position,
                 unsigned long num_sims,
                 unsigned long seed,
                 double alpha) {
    pcg64 rng(seed ? seed : 0xABCD1234);
    std::student_t_distribution<double> tdist(nu);
    std::vector<double> pnl; pnl.reserve(num_sims);
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


