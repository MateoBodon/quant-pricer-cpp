/// Digital option pricing (cash-or-nothing and asset-or-nothing)
#pragma once

namespace quant::digital {

enum class Type { CashOrNothing, AssetOrNothing };

struct Params {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    bool call; // true for call, false for put (pays if S_T > K for call, < K for put)
};

// Analytic Black–Scholes formulas for digitals
double price_bs(const Params& p, Type type);

}


