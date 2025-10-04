#pragma once

#include <cstdint>
#include <optional>

#include "quant/barrier.hpp"
#include "quant/pde.hpp"

namespace quant::american {

struct Params {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    quant::OptionType type;
};

double price_binomial_crr(const Params& p, int steps);

struct PsorParams {
    Params base;
    quant::pde::GridSpec grid;
    bool log_space{false};
    quant::pde::PdeParams::UpperBoundary upper_boundary{quant::pde::PdeParams::UpperBoundary::Dirichlet};
    double stretch{0.0};
    double omega{1.5};
    int max_iterations{10000};
    double tolerance{1e-8};
    bool use_rannacher{true};
};

struct PsorResult {
    double price;
    int total_iterations;
    double max_residual;
};

PsorResult price_psor(const PsorParams& params);

struct LsmcParams {
    Params base;
    std::uint64_t num_paths;
    std::uint64_t seed;
    int num_steps;
    bool antithetic{true};
};

struct LsmcResult {
    double price;
    double std_error;
};

LsmcResult price_lsmc(const LsmcParams& params);

} // namespace quant::american

