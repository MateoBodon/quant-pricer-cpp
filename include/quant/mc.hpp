/// Monte Carlo GBM pricer with antithetic variates and optional control variate
#pragma once

#include <cstdint>
#include <vector>
#include <random>
#include <optional>
#include "quant/term_structures.hpp"

namespace quant::mc {

/// Monte Carlo parameters for European option pricing.
///
/// Configure the simulation engine, variance reduction, and RNG sampler.
struct McParams {
    double spot;      // S0
    double strike;    // K
    double rate;      // r
    double dividend;  // q
    double vol;       // sigma
    double time;      // T
    std::uint64_t num_paths; // number of primary paths (antithetic doubles effective)
    std::uint64_t seed;      // RNG seed
    bool antithetic{true};
    bool control_variate{true}; // control variate on discounted S_T vs E[S_T]
    enum class Qmc { None, Sobol, SobolScrambled };
    enum class Bridge { None, BrownianBridge };
    Qmc qmc{Qmc::None};
    Bridge bridge{Bridge::None};
    int num_steps{1};
    // Optional piecewise-constant schedules; when set, override scalar rate/div/vol
    std::optional<quant::PiecewiseConstant> rate_schedule{};
    std::optional<quant::PiecewiseConstant> dividend_schedule{};
    std::optional<quant::PiecewiseConstant> vol_schedule{};
};

/// Summary of a Monte Carlo estimator (mean, standard error, 95% CI)
struct McStatistic {
    double value;       // sample mean
    double std_error;   // standard error of the estimate
    double ci_low;      // 95% confidence interval lower bound
    double ci_high;     // 95% confidence interval upper bound
};

/// Monte Carlo pricing result
struct McResult {
    McStatistic estimate;  // price estimate and uncertainty
};

/// Price European call via terminal payoff; uses streaming for cache friendliness.
///
/// Uses GBM analytic terminal distribution, optional antithetic and control variates.
/// Supports Sobol quasi Monte Carlo sequences (with optional scramble) and Brownian
/// bridge ordering when `num_steps > 1`.
McResult price_european_call(const McParams& p);

/// Monte Carlo Greeks result (mean/SE/CI per estimator).
struct GreeksResult {
    McStatistic delta;      // pathwise
    McStatistic vega;       // pathwise
    McStatistic gamma_lrm;  // likelihood-ratio
    McStatistic gamma_mixed;// mixed (pathwise × LR)
    McStatistic theta;      // finite-difference in time with common RNG
};

/// Monte Carlo Greeks under GBM.
/// - Delta, Vega: pathwise estimators
/// - Gamma: exposes both pure LRM and the lower-variance mixed estimator
/// - Theta: finite-difference in time using common random numbers
GreeksResult greeks_european_call(const McParams& p);

} // namespace quant::mc
