/// Asian option Monte Carlo (arithmetic/geometric) with optional geometric CV
#pragma once

#include <cstdint>

namespace quant::asian {

enum class Payoff { FixedStrike, FloatingStrike };
enum class Average { Arithmetic, Geometric };

struct McParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    std::uint64_t num_paths;
    std::uint64_t seed;
    int num_steps; // averaging steps
    bool antithetic{true};
    bool use_geometric_cv{true};
    Payoff payoff{Payoff::FixedStrike};
    Average avg{Average::Arithmetic};
};

struct McStatistic {
    double value;
    double std_error;
    double ci_low;
    double ci_high;
};

McStatistic price_mc(const McParams& p);

}


