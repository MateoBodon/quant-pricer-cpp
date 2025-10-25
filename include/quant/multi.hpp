/// Multi-asset MC pricing: basket and jump-diffusion
#pragma once

#include <cstdint>
#include <vector>

namespace quant::multi {

struct BasketMcParams {
    std::vector<double> spots;     // S0 per asset
    std::vector<double> vols;      // sigma per asset
    std::vector<double> dividends; // q per asset
    std::vector<double> weights;   // basket weights (sum to 1 typical)
    std::vector<double> corr;      // row-major NxN correlation matrix
    double rate;                   // risk-free rate
    double strike;                 // K
    double time;                   // T
    std::uint64_t num_paths;       // paths
    std::uint64_t seed;            // RNG seed
    bool antithetic{true};
};

struct McStat { double value; double std_error; };

McStat basket_european_call_mc(const BasketMcParams& p);

struct MertonParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    double lambda;    // jump intensity
    double muJ;       // mean of log jump size
    double sigmaJ;    // std of log jump size
    std::uint64_t num_paths;
    std::uint64_t seed;
    bool antithetic{true};
};

McStat merton_call_mc(const MertonParams& p);

}


