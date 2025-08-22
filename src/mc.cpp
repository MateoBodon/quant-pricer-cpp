#include "quant/mc.hpp"
#include <cmath>
#include <algorithm>
#include <pcg_random.hpp>

namespace quant::mc {

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

    pcg64 rng(p.seed);
    std::normal_distribution<double> normal(0.0, 1.0);

    double sum = 0.0;
    double sumsq = 0.0;

    // Control variate: discounted S_T has expectation S0 * exp(-q T)
    const double cv_expectation = S0 * std::exp(-q * T);

    for (std::uint64_t i = 0; i < N; ++i) {
        const double z = normal(rng);
        const double ST1 = S0 * std::exp(drift + volt * z);
        const double payoff1 = std::max(0.0, ST1 - K);
        double sample = df_r * payoff1;

        if (use_antithetic) {
            const double ST2 = S0 * std::exp(drift - volt * z);
            const double payoff2 = std::max(0.0, ST2 - K);
            const double disc_payoff2 = df_r * payoff2;
            // Average antithetic pair
            sample = 0.5 * (sample + disc_payoff2);
            if (use_cv) {
                const double cv_obs = 0.5 * (ST1 + ST2) * df_r; // discounted average S_T
                sample += (cv_expectation - cv_obs);            // apply control variate
            }
        } else if (use_cv) {
            const double cv_obs = ST1 * df_r;
            sample += (cv_expectation - cv_obs);
        }

        sum += sample;
        sumsq += sample * sample;
    }

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

    pcg64 rng(p.seed);
    std::normal_distribution<double> normal(0.0, 1.0);

    double sum_delta = 0.0, sumsq_delta = 0.0;
    double sum_vega  = 0.0, sumsq_vega  = 0.0;
    double sum_gamma = 0.0, sumsq_gamma = 0.0;

    for (std::uint64_t i = 0; i < N; ++i) {
        const double z = normal(rng);
        const double ST1 = S0 * std::exp(drift + volt * z);
        const double ST2 = use_antithetic ? S0 * std::exp(drift - volt * z) : ST1;

        // Pathwise delta and vega using z inferred from ST to handle antithetic correctly
        auto pathwise = [&](double ST) {
            if (ST <= K) {
                return std::pair<double,double>{0.0, 0.0};
            }
            // Reconstruct the z that produced this ST
            const double z_hat = (std::log(ST / S0) - drift) / volt;
            const double dST_dS0 = ST / S0; // dST/dS0
            const double dST_dsigma = ST * (-s * T + std::sqrt(T) * z_hat);
            const double dPayoff_dS0 = dST_dS0;
            const double dPayoff_dsigma = dST_dsigma;
            const double delta = df_r * dPayoff_dS0;
            const double vega  = df_r * dPayoff_dsigma;
            return std::pair<double,double>{delta, vega};
        };

        double delta_samp, vega_samp;
        if (use_antithetic) {
            auto [d1, v1] = pathwise(ST1);
            auto [d2, v2] = pathwise(ST2);
            delta_samp = 0.5 * (d1 + d2);
            vega_samp  = 0.5 * (v1 + v2);
        } else {
            auto [d1, v1] = pathwise(ST1);
            delta_samp = d1;
            vega_samp  = v1;
        }

        // LRM gamma estimator with correct second derivative weight and antithetic averaging
        const auto weight = [&](double zval) {
            return ( (zval * zval) - 1.0 - s * std::sqrt(T) * zval ) / (S0 * S0 * s * s * T);
        };
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

    const double n = static_cast<double>(N);
    auto finalize = [&](double s, double ss) {
        double m = s / n; double v = std::max(0.0, (ss / n) - m * m); return std::pair<double,double>{m, std::sqrt(v / n)}; };
    auto [delta, delta_se] = finalize(sum_delta, sumsq_delta);
    auto [vega,  vega_se ] = finalize(sum_vega,  sumsq_vega);
    auto [gamma, gamma_se] = finalize(sum_gamma, sumsq_gamma);
    return {delta, delta_se, vega, vega_se, gamma, gamma_se};
}

} // namespace quant::mc


