/// Monte Carlo pricing for barrier options
#pragma once

#include "quant/barrier.hpp"
#include "quant/mc.hpp"

namespace quant::mc {

McResult price_barrier_option(const McParams& base,
                              double strike,
                              OptionType opt,
                              const BarrierSpec& barrier);

/// Note: barrier MC respects McParams.control_variate to enable/disable
/// the terminal stock control variate in the path payoff.

}

