#include "quant/digital.hpp"
#include "quant/black_scholes.hpp"

#include <cmath>

namespace quant::digital {

double price_bs(const Params& p, Type type) {
    using namespace quant::bs;
    const double df_r = std::exp(-p.rate * p.time);
    const double df_q = std::exp(-p.dividend * p.time);
    if (p.time <= 0.0) {
        bool in = p.call ? (p.spot > p.strike) : (p.spot < p.strike);
        if (type == Type::CashOrNothing) return in ? 1.0 : 0.0;
        return in ? p.spot : 0.0;
    }
    if (p.vol <= 0.0) {
        const double forward = p.spot * df_q / df_r;
        bool in = p.call ? (forward > p.strike) : (forward < p.strike);
        if (type == Type::CashOrNothing) return df_r * (in ? 1.0 : 0.0);
        return df_q * (in ? p.spot : 0.0);
    }
    const double d1v = d1(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
    const double d2v = d2(d1v, p.vol, p.time);
    if (type == Type::CashOrNothing) {
        // cash-or-nothing price = df_r * N(±d2)
        return df_r * (p.call ? normal_cdf(d2v) : normal_cdf(-d2v));
    } else {
        // asset-or-nothing price = S*df_q * N(±d1)
        return p.spot * df_q * (p.call ? normal_cdf(d1v) : normal_cdf(-d1v));
    }
}

} // namespace quant::digital


