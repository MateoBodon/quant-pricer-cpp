#include "quant/mc.hpp"
#include <cmath>
#include <algorithm>
#include <pcg_random.hpp>
#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

namespace quant::mc {

// Inverse normal CDF (Acklam's approximation)
static inline double inverse_normal_cdf(double p) {
    // Protect bounds
    if (p <= 0.0) return -INFINITY;
    if (p >= 1.0) return INFINITY;
    // Coefficients
    static const double a1 = -3.969683028665376e+01;
    static const double a2 =  2.209460984245205e+02;
    static const double a3 = -2.759285104469687e+02;
    static const double a4 =  1.383577518672690e+02;
    static const double a5 = -3.066479806614716e+01;
    static const double a6 =  2.506628277459239e+00;

    static const double b1 = -5.447609879822406e+01;
    static const double b2 =  1.615858368580409e+02;
    static const double b3 = -1.556989798598866e+02;
    static const double b4 =  6.680131188771972e+01;
    static const double b5 = -1.328068155288572e+01;

    static const double c1 = -7.784894002430293e-03;
    static const double c2 = -3.223964580411365e-01;
    static const double c3 = -2.400758277161838e+00;
    static const double c4 = -2.549732539343734e+00;
    static const double c5 =  4.374664141464968e+00;
    static const double c6 =  2.938163982698783e+00;

    static const double d1 =  7.784695709041462e-03;
    static const double d2 =  3.224671290700398e-01;
    static const double d3 =  2.445134137142996e+00;
    static const double d4 =  3.754408661907416e+00;

    // Define break-points.
    const double plow  = 0.02425;
    const double phigh = 1 - plow;
    double q, r, x;
    if (p < plow) {
        q = std::sqrt(-2.0 * std::log(p));
        x = (((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
            ((((d1*q + d2)*q + d3)*q + d4)*q + 1.0);
    } else if (p <= phigh) {
        q = p - 0.5;
        r = q * q;
        x = (((((a1*r + a2)*r + a3)*r + a4)*r + a5)*r + a6) * q /
            (((((b1*r + b2)*r + b3)*r + b4)*r + b5)*r + 1.0);
    } else {
        q = std::sqrt(-2.0 * std::log(1.0 - p));
        x = -(((((c1*q + c2)*q + c3)*q + c4)*q + c5)*q + c6) /
              ((((d1*q + d2)*q + d3)*q + d4)*q + 1.0);
    }
    // One step Halley refinement
    double e = 0.5 * std::erfc(-x / std::sqrt(2.0)) - p;
    double u = e * std::sqrt(2.0 * M_PI) * std::exp(0.5 * x * x);
    x = x - u / (1.0 + 0.5 * x * u);
    return x;
}

McResult price_european_call(const McParams& p) {
    const double S0 = p.spot;
    const double K  = p.strike;
    const double r  = p.rate;
    const double q  = p.dividend;
    const double s  = p.vol;
    const double T  = p.time;
    const std::uint64_t N = p.num_paths;
    const bool use_antithetic = p.antithetic;
    const bool use_cv = p.control_variate;

    const double df_r = std::exp(-r * T);
    const double drift = (r - q - 0.5 * s * s) * T;
    const double volt = s * std::sqrt(T);

    double sum = 0.0;
    double sumsq = 0.0;

    // Control variate: discounted S_T has expectation S0 * exp(-q T)
    const double cv_expectation = S0 * std::exp(-q * T);

#ifdef QUANT_HAS_OPENMP
    #pragma omp parallel
    {
        pcg64 rng_local(p.seed + static_cast<unsigned long long>(1 + omp_get_thread_num()));
        std::normal_distribution<double> normal(0.0, 1.0);
        double local_sum = 0.0;
        double local_sumsq = 0.0;
        #pragma omp for nowait
        for (std::int64_t i = 0; i < static_cast<std::int64_t>(N); ++i) {
            double z;
            if (p.sampler == McParams::Sampler::Pseudorandom) {
                z = normal(rng_local);
            } else {
                // van der Corput (base 2) in (0,1) -> inverse normal
                auto vdc = [](std::uint64_t n) {
                    double x = 0.0, f = 0.5; while (n) { x += f * (n & 1ULL); n >>= 1; f *= 0.5; } return x; };
                // Map iteration index and thread id to sequence value
                std::uint64_t idx = static_cast<std::uint64_t>(i) + 1ULL + static_cast<std::uint64_t>(omp_get_thread_num()) * N;
                double u = std::max(1e-12, std::min(1.0 - 1e-12, vdc(idx)));
                z = inverse_normal_cdf(u);
            }
            const double ST1 = S0 * std::exp(drift + volt * z);
            const double payoff1 = std::max(0.0, ST1 - K);
            double sample = df_r * payoff1;
            if (use_antithetic) {
                const double ST2 = S0 * std::exp(drift - volt * z);
                const double payoff2 = std::max(0.0, ST2 - K);
                const double disc_payoff2 = df_r * payoff2;
                sample = 0.5 * (sample + disc_payoff2);
                if (use_cv) {
                    const double cv_obs = 0.5 * (ST1 + ST2) * df_r;
                    sample += (cv_expectation - cv_obs);
                }
            } else if (use_cv) {
                const double cv_obs = ST1 * df_r;
                sample += (cv_expectation - cv_obs);
            }
            local_sum += sample;
            local_sumsq += sample * sample;
        }
        #pragma omp atomic
        sum += local_sum;
        #pragma omp atomic
        sumsq += local_sumsq;
    }
#else
    {
        pcg64 rng(p.seed);
        std::normal_distribution<double> normal(0.0, 1.0);
        for (std::uint64_t i = 0; i < N; ++i) {
            double z;
            if (p.sampler == McParams::Sampler::Pseudorandom) {
                z = normal(rng);
            } else {
                auto vdc = [](std::uint64_t n) {
                    double x = 0.0, f = 0.5; while (n) { x += f * (n & 1ULL); n >>= 1; f *= 0.5; } return x; };
                double u = std::max(1e-12, std::min(1.0 - 1e-12, vdc(i + 1ULL)));
                z = inverse_normal_cdf(u);
            }
            const double ST1 = S0 * std::exp(drift + volt * z);
            const double payoff1 = std::max(0.0, ST1 - K);
            double sample = df_r * payoff1;
            if (use_antithetic) {
                const double ST2 = S0 * std::exp(drift - volt * z);
                const double payoff2 = std::max(0.0, ST2 - K);
                const double disc_payoff2 = df_r * payoff2;
                sample = 0.5 * (sample + disc_payoff2);
                if (use_cv) {
                    const double cv_obs = 0.5 * (ST1 + ST2) * df_r;
                    sample += (cv_expectation - cv_obs);
                }
            } else if (use_cv) {
                const double cv_obs = ST1 * df_r;
                sample += (cv_expectation - cv_obs);
            }
            sum += sample;
            sumsq += sample * sample;
        }
    }
#endif

    const double n_eff = static_cast<double>(N);
    const double mean = sum / n_eff;
    const double var = std::max(0.0, (sumsq / n_eff) - mean * mean);
    const double se = std::sqrt(var / n_eff);
    return {mean, se};
}

GreeksResult greeks_european_call(const McParams& p) {
    const double S0 = p.spot;
    const double K  = p.strike;
    const double r  = p.rate;
    const double q  = p.dividend;
    const double s  = p.vol;
    const double T  = p.time;
    const std::uint64_t N = p.num_paths;
    const bool use_antithetic = p.antithetic;

    const double df_r = std::exp(-r * T);
    const double drift = (r - q - 0.5 * s * s) * T;
    const double volt = s * std::sqrt(T);

    double sum_delta = 0.0, sumsq_delta = 0.0;
    double sum_vega  = 0.0, sumsq_vega  = 0.0;
    double sum_gamma = 0.0, sumsq_gamma = 0.0;

    // Helpers available to both OpenMP and non-OpenMP paths
    auto pathwise = [&](double ST) -> std::pair<double,double> {
        if (ST <= K) {
            return {0.0, 0.0};
        }
        const double z_hat = (std::log(ST / S0) - drift) / volt;
        const double dST_dS0 = ST / S0;
        const double dST_dsigma = ST * (-s * T + std::sqrt(T) * z_hat);
        const double delta = df_r * dST_dS0;
        const double vega  = df_r * dST_dsigma;
        return {delta, vega};
    };

    auto weight = [&](double zval) {
        return ((zval * zval) - 1.0 - s * std::sqrt(T) * zval) / (S0 * S0 * s * s * T);
    };

#ifdef QUANT_HAS_OPENMP
    #pragma omp parallel
    {
        pcg64 rng_local(p.seed + static_cast<unsigned long long>(1 + omp_get_thread_num()));
        std::normal_distribution<double> normal(0.0, 1.0);
        double local_delta = 0.0, local_deltasq = 0.0;
        double local_vega  = 0.0, local_vegasq  = 0.0;
        double local_gamma = 0.0, local_gammasq = 0.0;
        #pragma omp for nowait
        for (std::int64_t i = 0; i < static_cast<std::int64_t>(N); ++i) {
            const double z = normal(rng_local);
            const double ST1 = S0 * std::exp(drift + volt * z);
            const double ST2 = use_antithetic ? S0 * std::exp(drift - volt * z) : ST1;
        double delta_samp, vega_samp;
        if (use_antithetic) {
                auto pv1 = pathwise(ST1);
                auto pv2 = pathwise(ST2);
                auto d1 = pv1.first; auto v1 = pv1.second;
                auto d2 = pv2.first; auto v2 = pv2.second;
                delta_samp = 0.5 * (d1 + d2);
                vega_samp  = 0.5 * (v1 + v2);
        } else {
                auto pv1 = pathwise(ST1);
                delta_samp = pv1.first;
                vega_samp  = pv1.second;
        }
            const double payoff1 = std::max(0.0, ST1 - K);
            const double term1 = df_r * payoff1 * weight(z);
            double gamma_samp = term1;
            if (use_antithetic) {
                const double payoff2 = std::max(0.0, ST2 - K);
                const double term2 = df_r * payoff2 * weight(-z);
                gamma_samp = 0.5 * (term1 + term2);
            }

            local_delta += delta_samp; local_deltasq += delta_samp * delta_samp;
            local_vega  += vega_samp;  local_vegasq  += vega_samp  * vega_samp;
            local_gamma += gamma_samp; local_gammasq += gamma_samp * gamma_samp;
        }
        #pragma omp atomic
        sum_delta += local_delta;
        #pragma omp atomic
        sumsq_delta += local_deltasq;
        #pragma omp atomic
        sum_vega += local_vega;
        #pragma omp atomic
        sumsq_vega += local_vegasq;
        #pragma omp atomic
        sum_gamma += local_gamma;
        #pragma omp atomic
        sumsq_gamma += local_gammasq;
    }
#else
    {
        pcg64 rng(p.seed);
        std::normal_distribution<double> normal(0.0, 1.0);
        for (std::uint64_t i = 0; i < N; ++i) {
            const double z = normal(rng);
            const double ST1 = S0 * std::exp(drift + volt * z);
            const double ST2 = use_antithetic ? S0 * std::exp(drift - volt * z) : ST1;
            double delta_samp, vega_samp;
            if (use_antithetic) {
                auto pv1 = pathwise(ST1);
                auto pv2 = pathwise(ST2);
                auto d1 = pv1.first; auto v1 = pv1.second;
                auto d2 = pv2.first; auto v2 = pv2.second;
                delta_samp = 0.5 * (d1 + d2);
                vega_samp  = 0.5 * (v1 + v2);
            } else {
                auto pv1 = pathwise(ST1);
                delta_samp = pv1.first;
                vega_samp  = pv1.second;
            }
            const double payoff1 = std::max(0.0, ST1 - K);
            const double term1 = df_r * payoff1 * weight(z);
            double gamma_samp = term1;
            if (use_antithetic) {
                const double payoff2 = std::max(0.0, ST2 - K);
                const double term2 = df_r * payoff2 * weight(-z);
                gamma_samp = 0.5 * (term1 + term2);
            }

            sum_delta += delta_samp; sumsq_delta += delta_samp * delta_samp;
            sum_vega  += vega_samp;  sumsq_vega  += vega_samp  * vega_samp;
            sum_gamma += gamma_samp; sumsq_gamma += gamma_samp * gamma_samp;
        }
    }
#endif

    const double n = static_cast<double>(N);
    auto finalize = [&](double s, double ss) {
        double m = s / n; double v = std::max(0.0, (ss / n) - m * m); return std::pair<double,double>{m, std::sqrt(v / n)}; };
    auto [delta, delta_se] = finalize(sum_delta, sumsq_delta);
    auto [vega,  vega_se ] = finalize(sum_vega,  sumsq_vega);
    auto [gamma, gamma_se] = finalize(sum_gamma, sumsq_gamma);
    return {delta, delta_se, vega, vega_se, gamma, gamma_se};
}

} // namespace quant::mc


