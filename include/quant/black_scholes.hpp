// Analytic Black–Scholes European option pricing and Greeks
#pragma once

#include <cmath>

namespace quant::bs {

// Standard normal PDF and CDF
inline double normal_pdf(double x) {
    static constexpr double INV_SQRT_2PI = 0.39894228040143267794; // 1/sqrt(2*pi)
    return INV_SQRT_2PI * std::exp(-0.5 * x * x);
}

inline double normal_cdf(double x) {
    // 0.5 * erfc(-x / sqrt(2)) is numerically stable in tails
    return 0.5 * std::erfc(-x / std::sqrt(2.0));
}

struct Params {
    double spot;    // S
    double strike;  // K
    double rate;    // r (risk-free rate)
    double dividend;// q (continuous dividend yield)
    double vol;     // sigma
    double time;    // T (years)
};

// Helper: d1 and d2
inline double d1(double S, double K, double r, double q, double sigma, double T) {
    const double vol_sqrt_t = sigma * std::sqrt(T);
    return (std::log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / vol_sqrt_t;
}

inline double d2(double d1_value, double sigma, double T) {
    return d1_value - sigma * std::sqrt(T);
}

// Prices
double call_price(double S, double K, double r, double q, double sigma, double T);
double put_price(double S, double K, double r, double q, double sigma, double T);

inline double call_price(const Params& p) {
    return call_price(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
}

inline double put_price(const Params& p) {
    return put_price(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
}

// Greeks (per 1.0 change in inputs; vega is per 1.0 vol unit)
double delta_call(double S, double K, double r, double q, double sigma, double T);
double delta_put(double S, double K, double r, double q, double sigma, double T);
double gamma(double S, double K, double r, double q, double sigma, double T);
double vega(double S, double K, double r, double q, double sigma, double T);
double theta_call(double S, double K, double r, double q, double sigma, double T);
double theta_put(double S, double K, double r, double q, double sigma, double T);
double rho_call(double S, double K, double r, double q, double sigma, double T);
double rho_put(double S, double K, double r, double q, double sigma, double T);

} // namespace quant::bs


