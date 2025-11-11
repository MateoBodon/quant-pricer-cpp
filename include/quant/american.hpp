#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

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
    double ridge_lambda{0.0};
    double itm_moneyness_eps{0.0};
    std::size_t min_itm{32};
};

struct LsmcDiagnostics {
    std::vector<std::size_t> itm_counts;        // number of truly ITM paths per exercise date
    std::vector<std::size_t> regression_counts; // number of samples entering regression per date
    std::vector<double> condition_numbers;      // condition number of normal equations matrix per date
};

struct LsmcResult {
    double price;
    double std_error;
    LsmcDiagnostics diagnostics{};
};

LsmcResult price_lsmc(const LsmcParams& params);

struct Greeks {
    double delta;
    double gamma;
};

// Compute Greeks via bump-and-reprice around spot using PSOR as pricer.
// rel_bump is a small relative bump (e.g., 1e-3)
Greeks greeks_psor_bump(PsorParams params, double rel_bump);

} // namespace quant::american
