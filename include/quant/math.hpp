/// Common mathematical utilities shared across engines
#pragma once

#include <cmath>
#include <limits>
#include <numbers>

namespace quant::math {

/// 95% two-sided normal quantile used for confidence intervals
inline constexpr double kZ95 = 1.95996398454005423552;

/// Inverse standard normal CDF (Acklam/Moro style, high accuracy)
/// p in (0,1). Returns +/- infinity at the bounds.
inline double inverse_normal_cdf(double p) {
    if (p <= 0.0)
        return -INFINITY;
    if (p >= 1.0)
        return INFINITY;

    // Coefficients from Peter J. Acklam's approximation
    static const double a1 = -3.969683028665376e+01;
    static const double a2 = 2.209460984245205e+02;
    static const double a3 = -2.759285104469687e+02;
    static const double a4 = 1.383577518672690e+02;
    static const double a5 = -3.066479806614716e+01;
    static const double a6 = 2.506628277459239e+00;

    static const double b1 = -5.447609879822406e+01;
    static const double b2 = 1.615858368580409e+02;
    static const double b3 = -1.556989798598866e+02;
    static const double b4 = 6.680131188771972e+01;
    static const double b5 = -1.328068155288572e+01;

    static const double c1 = -7.784894002430293e-03;
    static const double c2 = -3.223964580411365e-01;
    static const double c3 = -2.400758277161838e+00;
    static const double c4 = -2.549732539343734e+00;
    static const double c5 = 4.374664141464968e+00;
    static const double c6 = 2.938163982698783e+00;

    static const double d1 = 7.784695709041462e-03;
    static const double d2 = 3.224671290700398e-01;
    static const double d3 = 2.445134137142996e+00;
    static const double d4 = 3.754408661907416e+00;

    const double plow = 0.02425;
    const double phigh = 1.0 - plow;
    double q, r, x;
    if (p < plow) {
        q = std::sqrt(-2.0 * std::log(p));
        x = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    } else if (p <= phigh) {
        q = p - 0.5;
        r = q * q;
        x = (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
            (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0);
    } else {
        q = std::sqrt(-2.0 * std::log(1.0 - p));
        x = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    }

    // One Halley refinement
    double e = 0.5 * std::erfc(-x / std::sqrt(2.0)) - p;
    double u = e * std::sqrt(2.0 * std::numbers::pi) * std::exp(0.5 * x * x);
    x = x - u / (1.0 + 0.5 * x * u);
    return x;
}

} // namespace quant::math
