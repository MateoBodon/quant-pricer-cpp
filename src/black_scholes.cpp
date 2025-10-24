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

namespace {
double price_call_with_sigma(double S, double K, double r, double q, double sigma, double T) {
    return call_price(S, K, r, q, sigma, T);
}
double price_put_with_sigma(double S, double K, double r, double q, double sigma, double T) {
    return put_price(S, K, r, q, sigma, T);
}
}

static double implied_vol_bracketed(double S, double K, double r, double q, double T, double target,
                                    bool is_call) {
    if (T <= 0.0 || S <= 0.0 || K <= 0.0) return std::numeric_limits<double>::quiet_NaN();
    const double df_r = std::exp(-r * T);
    const double df_q = std::exp(-q * T);
    const double forward = S * df_q / df_r;
    const double intrinsic = is_call ? std::max(0.0, S * df_q - K * df_r)
                                     : std::max(0.0, K * df_r - S * df_q);
    if (target < intrinsic - 1e-14) return std::numeric_limits<double>::quiet_NaN();

    double lo = 1e-6, hi = 5.0;
    auto price_at = [&](double sigma) {
        return is_call ? price_call_with_sigma(S, K, r, q, sigma, T)
                       : price_put_with_sigma(S, K, r, q, sigma, T);
    };

    double f_lo = price_at(lo) - target;
    double f_hi = price_at(hi) - target;
    if (f_lo > 0.0) return lo; // essentially zero vol
    int iters = 0;
    while (f_hi < 0.0 && hi < 10.0 && iters < 20) {
        hi *= 1.5;
        f_hi = price_at(hi) - target;
        ++iters;
    }
    if (f_hi < 0.0) return std::numeric_limits<double>::quiet_NaN();

    // Brent's method (simple implementation)
    double a = lo, b = hi, c = hi;
    double fa = f_lo, fb = f_hi, fc = f_hi;
    double d = 0.0, e = 0.0;
    for (int iter = 0; iter < 100; ++iter) {
        if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0)) { c = a; fc = fa; d = e = b - a; }
        if (std::abs(fc) < std::abs(fb)) { a = b; b = c; c = a; fa = fb; fb = fc; fc = fa; }
        const double tol1 = 2.0 * std::numeric_limits<double>::epsilon() * std::abs(b) + 1e-12;
        const double xm = 0.5 * (c - b);
        if (std::abs(xm) <= tol1 || fb == 0.0) return b;
        if (std::abs(e) >= tol1 && std::abs(fa) > std::abs(fb)) {
            double s = fb / fa;
            double p, qv;
            if (a == c) { p = 2.0 * xm * s; qv = 1.0 - s; }
            else {
                double q2 = fa / fc; double r2 = fb / fc;
                p = s * (2.0 * xm * q2 * (q2 - r2) - (b - a) * (r2 - 1.0));
                qv = (q2 - 1.0) * (r2 - 1.0) * (s - 1.0);
            }
            if (p > 0) qv = -qv; p = std::abs(p);
            double min1 = 3.0 * xm * qv - std::abs(tol1 * qv);
            double min2 = std::abs(e * qv);
            if (2.0 * p < (min1 < min2 ? min1 : min2)) { e = d; d = p / qv; }
            else { d = xm; e = d; }
        } else { d = xm; e = d; }
        a = b; fa = fb;
        if (std::abs(d) > tol1) b += d; else b += (xm > 0 ? +tol1 : -tol1);
        fb = price_at(b) - target;
    }
    return b;
}

double implied_vol_call(double S, double K, double r, double q, double T, double price) {
    return implied_vol_bracketed(S, K, r, q, T, price, true);
}

double implied_vol_put(double S, double K, double r, double q, double T, double price) {
    return implied_vol_bracketed(S, K, r, q, T, price, false);
}

} // namespace quant::bs


