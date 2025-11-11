#include "quant/bs_barrier.hpp"

#include "quant/black_scholes.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace quant::bs {

namespace {

struct RrContext {
    double S;
    double K;
    double B;
    double r;
    double q;
    double sigma;
    double T;
    double disc_r;
    double disc_q;
    double sigma_sqrt_T;
    double mu;
    double mu_sigma;
    double lambda;
    double rebate;

    RrContext(double S_, double K_, double B_, double r_, double q_, double sigma_, double T_, double rebate_)
        : S(S_), K(K_), B(B_), r(r_), q(q_), sigma(sigma_), T(T_), disc_r(std::exp(-r_ * T_)),
          disc_q(std::exp(-q_ * T_)), sigma_sqrt_T(sigma_ * std::sqrt(T_)),
          mu((r_ - q_ - 0.5 * sigma_ * sigma_) / (sigma_ * sigma_)), mu_sigma((1.0 + mu) * sigma_sqrt_T),
          lambda(std::sqrt(mu * mu + 2.0 * (r_ - q_) / (sigma_ * sigma_))), rebate(rebate_) {}

    static double cdf(double x) { return normal_cdf(x); }

    double A(double phi) const {
        const double x1 = std::log(S / K) / sigma_sqrt_T + mu_sigma;
        const double N1 = cdf(phi * x1);
        const double N2 = cdf(phi * (x1 - sigma_sqrt_T));
        return phi * (S * disc_q * N1 - K * disc_r * N2);
    }

    double Bf(double phi) const {
        const double x2 = std::log(S / B) / sigma_sqrt_T + mu_sigma;
        const double N1 = cdf(phi * x2);
        const double N2 = cdf(phi * (x2 - sigma_sqrt_T));
        return phi * (S * disc_q * N1 - K * disc_r * N2);
    }

    double pow_safe(double base, double exponent, double weight) const {
        if (weight == 0.0) {
            return 0.0;
        }
        return std::pow(base, exponent) * weight;
    }

    double C(double eta, double phi) const {
        const double HS = B / S;
        const double pow0 = std::pow(HS, 2.0 * mu);
        const double pow1 = pow0 * HS * HS;
        const double y1 = std::log(B * HS / K) / sigma_sqrt_T + mu_sigma;
        const double N1 = cdf(eta * y1);
        const double N2 = cdf(eta * (y1 - sigma_sqrt_T));
        const double term1 = pow_safe(HS, 2.0 * (mu + 1.0), S * disc_q * N1);
        const double term2 = pow_safe(HS, 2.0 * mu, K * disc_r * N2);
        return phi * (term1 - term2);
    }

    double D(double eta, double phi) const {
        const double HS = B / S;
        const double pow0 = std::pow(HS, 2.0 * mu);
        const double pow1 = pow0 * HS * HS;
        const double y2 = std::log(B / S) / sigma_sqrt_T + mu_sigma;
        const double N1 = cdf(eta * y2);
        const double N2 = cdf(eta * (y2 - sigma_sqrt_T));
        const double term1 = pow_safe(HS, 2.0 * (mu + 1.0), S * disc_q * N1);
        const double term2 = pow_safe(HS, 2.0 * mu, K * disc_r * N2);
        return phi * (term1 - term2);
    }

    double E(double eta) const {
        if (rebate <= 0.0) {
            return 0.0;
        }
        const double HS_pow = std::pow(B / S, 2.0 * mu);
        const double x2 = std::log(S / B) / sigma_sqrt_T + mu_sigma;
        const double y2 = std::log(B / S) / sigma_sqrt_T + mu_sigma;
        const double N1 = cdf(eta * (x2 - sigma_sqrt_T));
        const double N2 = cdf(eta * (y2 - sigma_sqrt_T));
        const double adj = (N2 == 0.0) ? 0.0 : HS_pow * N2;
        return rebate * disc_r * (N1 - adj);
    }

    double F(double eta) const {
        if (rebate <= 0.0) {
            return 0.0;
        }
        const double HS = B / S;
        const double pow_plus = std::pow(HS, mu + lambda);
        const double pow_minus = std::pow(HS, mu - lambda);
        const double z = std::log(B / S) / sigma_sqrt_T + lambda * sigma_sqrt_T;
        const double N1 = cdf(eta * z);
        const double N2 = cdf(eta * (z - 2.0 * lambda * sigma_sqrt_T));
        const double term1 = (N1 == 0.0) ? 0.0 : pow_plus * N1;
        const double term2 = (N2 == 0.0) ? 0.0 : pow_minus * N2;
        return rebate * (term1 + term2);
    }
};

bool barrier_triggered(const BarrierSpec& spec, double S) {
    switch (spec.type) {
    case BarrierType::DownOut:
    case BarrierType::DownIn:
        return S <= spec.B;
    case BarrierType::UpOut:
    case BarrierType::UpIn:
        return S >= spec.B;
    }
    return false;
}

} // namespace

double reiner_rubinstein_price(OptionType opt, const BarrierSpec& barrier, double S, double K, double r,
                               double q, double sigma, double T) {
    if (S <= 0.0 || K <= 0.0 || barrier.B <= 0.0) {
        throw std::invalid_argument("Positive S, K, and barrier required");
    }
    if (sigma <= 0.0 || T <= 0.0) {
        // Degenerate: revert to intrinsic values respecting barrier.
        const bool call = (opt == OptionType::Call);
        const double intrinsic = call ? std::max(0.0, S - K) : std::max(0.0, K - S);
        const bool triggered_now = barrier_triggered(barrier, S);
        switch (barrier.type) {
        case BarrierType::DownOut:
        case BarrierType::UpOut:
            return triggered_now ? barrier.rebate : intrinsic;
        case BarrierType::DownIn:
        case BarrierType::UpIn:
            return triggered_now ? intrinsic : barrier.rebate;
        }
    }

    const bool triggered = barrier_triggered(barrier, S);

    switch (barrier.type) {
    case BarrierType::DownOut:
    case BarrierType::UpOut:
        if (triggered) {
            return barrier.rebate;
        }
        break;
    case BarrierType::DownIn:
    case BarrierType::UpIn:
        if (triggered) {
            return (opt == OptionType::Call) ? call_price(S, K, r, q, sigma, T)
                                             : put_price(S, K, r, q, sigma, T);
        }
        break;
    }

    const RrContext ctx(S, K, barrier.B, r, q, sigma, T, barrier.rebate);
    const bool call = (opt == OptionType::Call);

    switch (opt) {
    case OptionType::Call:
        switch (barrier.type) {
        case BarrierType::DownIn:
            if (K >= barrier.B)
                return ctx.C(1.0, 1.0) + ctx.E(1.0);
            return ctx.A(1.0) - ctx.Bf(1.0) + ctx.D(1.0, 1.0) + ctx.E(1.0);
        case BarrierType::UpIn:
            if (K >= barrier.B)
                return ctx.A(1.0) + ctx.E(-1.0);
            return ctx.Bf(1.0) - ctx.C(-1.0, 1.0) + ctx.D(-1.0, 1.0) + ctx.E(-1.0);
        case BarrierType::DownOut:
            if (K >= barrier.B)
                return ctx.A(1.0) - ctx.C(1.0, 1.0) + ctx.F(1.0);
            return ctx.Bf(1.0) - ctx.D(1.0, 1.0) + ctx.F(1.0);
        case BarrierType::UpOut:
            if (K >= barrier.B)
                return ctx.F(-1.0);
            return ctx.A(1.0) - ctx.Bf(1.0) + ctx.C(-1.0, 1.0) - ctx.D(-1.0, 1.0) + ctx.F(-1.0);
        }
        break;
    case OptionType::Put:
        switch (barrier.type) {
        case BarrierType::DownIn:
            if (K >= barrier.B)
                return ctx.Bf(-1.0) - ctx.C(1.0, -1.0) + ctx.D(1.0, -1.0) + ctx.E(1.0);
            return ctx.A(-1.0) + ctx.E(1.0);
        case BarrierType::UpIn:
            if (K >= barrier.B)
                return ctx.A(-1.0) - ctx.Bf(-1.0) + ctx.D(-1.0, -1.0) + ctx.E(-1.0);
            return ctx.C(-1.0, -1.0) + ctx.E(-1.0);
        case BarrierType::DownOut:
            if (K >= barrier.B)
                return ctx.A(-1.0) - ctx.Bf(-1.0) + ctx.C(1.0, -1.0) - ctx.D(1.0, -1.0) + ctx.F(1.0);
            return ctx.F(1.0);
        case BarrierType::UpOut:
            if (K >= barrier.B)
                return ctx.Bf(-1.0) - ctx.D(-1.0, -1.0) + ctx.F(-1.0);
            return ctx.A(-1.0) - ctx.C(-1.0, -1.0) + ctx.F(-1.0);
        }
        break;
    }

    throw std::logic_error("Unsupported barrier configuration");
}

} // namespace quant::bs
