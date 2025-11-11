/// Heston model: analytic European call and QE Monte Carlo
#pragma once

#include <cstdint>
#include <complex>

#include "quant/rng.hpp"

namespace quant::heston {

struct Params {
    double kappa;   // mean reversion speed
    double theta;   // long-run variance
    double sigma;   // vol of vol
    double rho;     // correlation
    double v0;      // initial variance
};

struct MarketParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double time;
};

// Analytic European call via Heston characteristic function and Gauss-Laguerre
double call_analytic(const MarketParams& mkt, const Params& h);

/// Risk-neutral characteristic function φ(u) = E[e^{iu ln S_T}]
std::complex<double> characteristic_function(double u,
                                             const MarketParams& mkt,
                                             const Params& h);

/// Black–Scholes implied volatility implied by the Heston analytic call price
double implied_vol_call(const MarketParams& mkt, const Params& h);

struct McResult { double price; double std_error; };

struct McParams {
    MarketParams mkt;
    Params h;
    std::uint64_t num_paths;
    std::uint64_t seed;
    int num_steps; // QE time steps
    bool antithetic{true};
    quant::rng::Mode rng{quant::rng::Mode::Counter};
    enum class Scheme { Euler, QE };
    Scheme scheme{Scheme::QE};
};

// Andersen QE Monte Carlo pricing of European call
McResult call_qe_mc(const McParams& p);

}
