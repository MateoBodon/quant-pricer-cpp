/// Monte Carlo pricing for barrier options
#pragma once

#include "quant/barrier.hpp"
#include "quant/mc.hpp"

namespace quant::mc {

/// Price a barrier option via Monte Carlo. The control variate is disabled for
/// knock-in structures even if requested, to avoid bias from parity mismatches.
McResult price_barrier_option(const McParams& base,
                              double strike,
                              OptionType opt,
                              const BarrierSpec& barrier);

}
