/// Analytic Black–Scholes European option pricing and Greeks
#pragma once

#include <cmath>

namespace quant::bs {

/// Standard normal PDF.
///
/// \param x input real value
/// \return \f$\varphi(x) = \frac{1}{\sqrt{2\pi}} e^{-x^2/2}\f$.
inline double normal_pdf(double x) {
    static constexpr double INV_SQRT_2PI = 0.39894228040143267794; // 1/sqrt(2*pi)
    return INV_SQRT_2PI * std::exp(-0.5 * x * x);
}

/// Standard normal CDF (via erfc for tail stability).
///
/// \param x input real value
/// \return \f$\Phi(x) = \int_{-\infty}^x \varphi(t)\,dt\f$.
inline double normal_cdf(double x) {
    return 0.5 * std::erfc(-x / std::sqrt(2.0));
}

/// Black–Scholes input parameters.
///
/// Convenience aggregate used by inline overloads.
/// All values are expressed in spot units and year fractions.
struct Params {
    double spot;    // S
    double strike;  // K
    double rate;    // r (risk-free rate)
    double dividend;// q (continuous dividend yield)
    double vol;     // sigma
    double time;    // T (years)
};

/// Helper: d1.
///
/// \param S spot price
/// \param K strike
/// \param r risk-free rate (cont.)
/// \param q dividend yield (cont.)
/// \param sigma volatility (per annum)
/// \param T time to expiry (years)
inline double d1(double S, double K, double r, double q, double sigma, double T) {
    const double vol_sqrt_t = sigma * std::sqrt(T);
    return (std::log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / vol_sqrt_t;
}

/// Helper: d2 = d1 - sigma * sqrt(T).
///
/// \param d1_value the value of d1
/// \param sigma volatility (per annum)
/// \param T time to expiry (years)
inline double d2(double d1_value, double sigma, double T) {
    return d1_value - sigma * std::sqrt(T);
}

/// Price a European call option under Black–Scholes (present value).
/**
 * \param S spot price
 * \param K strike
 * \param r risk-free rate (cont.)
 * \param q dividend yield (cont.)
 * \param sigma volatility (per annum)
 * \param T time to expiry (years)
 * \return call option price
 */
double call_price(double S, double K, double r, double q, double sigma, double T);

/// Price a European put option under Black–Scholes (present value).
/**
 * \param S spot price
 * \param K strike
 * \param r risk-free rate (cont.)
 * \param q dividend yield (cont.)
 * \param sigma volatility (per annum)
 * \param T time to expiry (years)
 * \return put option price
 */
double put_price(double S, double K, double r, double q, double sigma, double T);

inline double call_price(const Params& p) {
    return call_price(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
}

inline double put_price(const Params& p) {
    return put_price(p.spot, p.strike, p.rate, p.dividend, p.vol, p.time);
}

/// Greeks (per 1.0 change in inputs; vega per 1.0 vol unit).
/// All Greeks returned are present-value sensitivities.
double delta_call(double S, double K, double r, double q, double sigma, double T);
double delta_put(double S, double K, double r, double q, double sigma, double T);
double gamma(double S, double K, double r, double q, double sigma, double T);
double vega(double S, double K, double r, double q, double sigma, double T);
double theta_call(double S, double K, double r, double q, double sigma, double T);
double theta_put(double S, double K, double r, double q, double sigma, double T);
double rho_call(double S, double K, double r, double q, double sigma, double T);
double rho_put(double S, double K, double r, double q, double sigma, double T);

/// Implied volatility from price using a robust bracketed solver.
/// Returns NaN if no solution is found within [1e-6, 5.0].
double implied_vol_call(double S, double K, double r, double q, double T, double price);
double implied_vol_put(double S, double K, double r, double q, double T, double price);

} // namespace quant::bs


