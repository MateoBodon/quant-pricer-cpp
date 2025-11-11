/// Reiner–Rubinstein closed-form barrier option pricer
#pragma once

#include "quant/barrier.hpp"

namespace quant::bs {

double reiner_rubinstein_price(OptionType opt, const BarrierSpec& barrier, double S, double K, double r,
                               double q, double sigma, double T);

}
