// Monte Carlo GBM pricer with antithetic variates and optional control variate
#pragma once

#include <cstdint>
#include <vector>
#include <random>

namespace quant::mc {

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
};

struct McResult {
    double price;      // estimated price
    double std_error;  // standard error of the estimate
};

// Price European call via terminal payoff; uses SoA-like streaming for cache friendliness.
McResult price_european_call(const McParams& p);

struct GreeksResult {
    double delta;
    double delta_se;
    double vega;
    double vega_se;
    double gamma;
    double gamma_se;
};

// Monte Carlo Greeks under GBM:
// - Delta, Vega: pathwise estimators
// - Gamma: Likelihood Ratio Method (LRM)
GreeksResult greeks_european_call(const McParams& p);

} // namespace quant::mc


