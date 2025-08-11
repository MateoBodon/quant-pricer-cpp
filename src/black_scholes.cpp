#include <algorithm>
#include "quant/black_scholes.hpp"

namespace quant::bs {

double call_price(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        return std::max(0.0, S - K);
    }
    if (sigma <= 0.0) {
        // Deterministic forward price under r, q
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        return df_r * std::max(0.0, forward - K);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    return S * df_q * normal_cdf(d1v) - K * df_r * normal_cdf(d2v);
}

double put_price(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        return std::max(0.0, K - S);
    }
    if (sigma <= 0.0) {
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        return df_r * std::max(0.0, K - forward);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    return K * df_r * normal_cdf(-d2v) - S * df_q * normal_cdf(-d1v);
}

double delta_call(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0 || sigma <= 0.0) {
        return S > K ? 1.0 : (S < K ? 0.0 : 0.5);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    return std::exp(-q * T) * normal_cdf(d1v);
}

double delta_put(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0 || sigma <= 0.0) {
        return S < K ? -1.0 : (S > K ? 0.0 : -0.5);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    return std::exp(-q * T) * (normal_cdf(d1v) - 1.0);
}

double gamma(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    return std::exp(-q * T) * normal_pdf(d1v) / (S * sigma * std::sqrt(T));
}

double vega(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    return S * std::exp(-q * T) * normal_pdf(d1v) * std::sqrt(T);
}

double theta_call(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        // Instantaneous expiration: only intrinsic value remains; theta undefined, return 0
        return 0.0;
    }
    if (sigma <= 0.0) {
        // Deterministic case: derivative of discounted forward payoff
        // Approximate with analytical simplification: theta dominated by carry and discount
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        const double itm = forward > K ? 1.0 : 0.0;
        // d/dT [df_r * (forward-K)_+] = df_r*((r-q)S*exp((r-q)T)*itm - r*(forward-K)_+)
        const double payoff = std::max(0.0, forward - K);
        return df_r * ((r - q) * forward * itm - r * payoff);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    const double term1 = - (S * df_q * normal_pdf(d1v) * sigma) / (2.0 * std::sqrt(T));
    const double term2 = q * S * df_q * normal_cdf(d1v);
    const double term3 = - r * K * df_r * normal_cdf(d2v);
    return term1 + term2 + term3;
}

double theta_put(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        return 0.0;
    }
    if (sigma <= 0.0) {
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        const double itm = forward < K ? 1.0 : 0.0;
        const double payoff = std::max(0.0, K - forward);
        return df_r * (- (r - q) * forward * itm - r * payoff);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    const double term1 = - (S * df_q * normal_pdf(d1v) * sigma) / (2.0 * std::sqrt(T));
    const double term2 = - q * S * df_q * normal_cdf(-d1v);
    const double term3 = + r * K * df_r * normal_cdf(-d2v);
    return term1 + term2 + term3;
}

double rho_call(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        return 0.0;
    }
    if (sigma <= 0.0) {
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        const double payoff = std::max(0.0, forward - K);
        // d/dr [df_r * payoff] = -T*df_r*payoff + df_r * d(payoff)/dr
        // d(payoff)/dr = T*forward*itm, itm = 1 if forward>K
        const double itm = forward > K ? 1.0 : 0.0;
        return -T * df_r * payoff + df_r * (T * forward * itm);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    return K * T * df_r * normal_cdf(d2v);
}

double rho_put(double S, double K, double r, double q, double sigma, double T) {
    if (T <= 0.0) {
        return 0.0;
    }
    if (sigma <= 0.0) {
        const double forward = S * std::exp((r - q) * T);
        const double df_r = std::exp(-r * T);
        const double payoff = std::max(0.0, K - forward);
        const double itm = forward < K ? 1.0 : 0.0;
        return -T * df_r * payoff - df_r * (T * forward * itm);
    }
    const double d1v = d1(S, K, r, q, sigma, T);
    const double d2v = d2(d1v, sigma, T);
    const double df_r = std::exp(-r * T);
    return -K * T * df_r * normal_cdf(-d2v);
}

} // namespace quant::bs


