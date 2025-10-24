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

// Price barrier option via CN in log-space.
// Returns present value only (price).
double price_barrier_crank_nicolson(const BarrierPdeParams& params,
                                    ::quant::OptionType opt);

struct BarrierPdeGreeksResult {
    double price;
    double delta;
    double gamma;
};

// Price + Greeks (Δ, Γ) via three-point interpolation around spot.
BarrierPdeGreeksResult price_barrier_crank_nicolson_greeks(const BarrierPdeParams& params,
                                                           ::quant::OptionType opt);

} // namespace quant::pde
