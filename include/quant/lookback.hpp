/// Lookback option Monte Carlo (fixed/floating strike) with optional bridge
#pragma once

#include <cstdint>
#include "quant/barrier.hpp"

namespace quant::lookback {

enum class Type { FixedStrike, FloatingStrike };

struct McParams {
    double spot;
    double strike;         // used for fixed-strike
    double rate;
    double dividend;
    double vol;
    double time;
    std::uint64_t num_paths;
    std::uint64_t seed;
    int num_steps;         // discretization steps
    bool antithetic{true};
    bool use_bridge{true};
    ::quant::OptionType opt; // call/put
    Type type{Type::FixedStrike};
};

struct McStatistic {
    double value;
    double std_error;
    double ci_low;
    double ci_high;
};

McStatistic price_mc(const McParams& p);

}


