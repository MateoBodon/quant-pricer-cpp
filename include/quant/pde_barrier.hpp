#pragma once

#include "quant/barrier.hpp"
#include "quant/pde.hpp"

namespace quant::pde {

struct BarrierPdeParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    BarrierSpec barrier;
    GridSpec grid;
    bool log_space{true};
};

double price_barrier_crank_nicolson(const BarrierPdeParams& params,
                                    ::quant::OptionType opt);

}
