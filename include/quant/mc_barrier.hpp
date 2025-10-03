/// Monte Carlo pricing for barrier options
#pragma once

#include "quant/barrier.hpp"
#include "quant/mc.hpp"

namespace quant::mc {

McResult price_barrier_option(const McParams& base,
                              double strike,
                              OptionType opt,
                              const BarrierSpec& barrier);

}

