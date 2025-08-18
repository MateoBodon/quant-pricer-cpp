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

} // namespace quant::mc


