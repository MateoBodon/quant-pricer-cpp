/// Heston model: analytic European call and QE Monte Carlo
#pragma once

#include <cstdint>

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

struct McResult { double price; double std_error; };

struct McParams {
    MarketParams mkt;
    Params h;
    std::uint64_t num_paths;
    std::uint64_t seed;
    int num_steps; // QE time steps
    bool antithetic{true};
};

// Andersen QE Monte Carlo pricing of European call
McResult call_qe_mc(const McParams& p);

}


