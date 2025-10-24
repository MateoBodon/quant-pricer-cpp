#include "quant/heston.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace quant::heston {

// Heston analytic via characteristic function and Gauss-Laguerre quadrature
namespace {

struct GL32 { static constexpr int N = 32; };

// 32-point Gauss–Laguerre nodes (x) and weights (w) for ∫_0^∞ w(x) f(x) dx
static const double kGL32_x[32] = {
    0.044489365833267, 0.234526109519619, 0.576884629301886, 1.07244875381782,
    1.72240877644465, 2.52833670642579, 3.49221327302199, 4.61645676974977,
    5.90395850417424, 7.35812673318624, 8.98294092421260, 10.7830186325399,
    12.7636979867427, 14.9311397555226, 17.2924543367153, 19.8558609403361,
    22.6308890131960, 25.6286360224592, 28.8621018163235, 32.3466291539647,
    36.1004948057519, 40.1457197715394, 44.5092079957549, 49.2243949873086,
    54.3337213333969, 59.8925091621340, 65.9738932315048, 72.6764856363483,
    80.1456711922165, 88.7250222336802, 99.3663896266145, 116.498428833741
};
static const double kGL32_w[32] = {
    0.109218341952385, 0.210443107938813, 0.235213229669847, 0.195903335972881,
    0.129983786286072, 0.068212565104719, 0.028248880785091, 0.009025579689953,
    0.002169537515914, 0.000359246582804, 0.000040069955161, 2.67678014474e-06,
    9.73806705861e-08, 1.56920701086e-09, 8.00611520883e-12, 4.40455033387e-15,
    2.06776392922e-19, 4.99469948627e-25, 1.03614617085e-32, 1.42362101688e-43,
    1.30902850238e-59, 7.91001810658e-86, 2.69453204242e-130, 3.32235353348e-206,
    9.37858201788e-342, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
};

inline std::complex<double> iunit() { return std::complex<double>(0.0, 1.0); }

inline std::complex<double> heston_phi(double u,
                                       double S0,
                                       double r,
                                       double q,
                                       double T,
                                       const Params& h) {
    using cd = std::complex<double>;
    const cd i = iunit();
    const cd iu = i * u;
    const double kappa = h.kappa;
    const double theta = h.theta;
    const double sigma = h.sigma;
    const double rho   = h.rho;
    const double v0    = h.v0;

    const cd d = std::sqrt( std::pow(rho * sigma * iu - kappa, 2.0) + sigma * sigma * (iu + iu * iu) );
    const cd g = (kappa - rho * sigma * iu - d) / (kappa - rho * sigma * iu + d);
    const cd C = iu * (std::log(S0) + (r - q) * T)
                 + (kappa * theta) / (sigma * sigma)
                   * ( (kappa - rho * sigma * iu - d) * T - 2.0 * std::log( (1.0 - g * std::exp(-d * T)) / (1.0 - g) ) );
    const cd D = ((kappa - rho * sigma * iu - d) / (sigma * sigma)) * ( (1.0 - std::exp(-d * T)) / (1.0 - g * std::exp(-d * T)) );
    return std::exp(C + D * v0);
}

inline double P_j(int j, double lnK,
                  const MarketParams& mkt,
                  const Params& h) {
    // Carr–Madan style integrals via Laguerre: ∫ Re( e^{-iu lnK} φ_j(u) / (i u) ) du
    const double S0 = mkt.spot;
    const double r  = mkt.rate;
    const double q  = mkt.dividend;
    const double T  = mkt.time;
    const std::complex<double> i = iunit();
    const std::complex<double> denom_base = i; // for 1/(i u)

    // φ1 uses shift u - i with normalization φ(-i)
    std::complex<double> phi_minus_i = heston_phi(-1.0, S0, r, q, T, h);
    double sum = 0.0;
    for (int k = 0; k < 32; ++k) {
        const double x = kGL32_x[k];
        const double w = kGL32_w[k];
        if (w == 0.0) continue;
        const double u = x; // Laguerre transforms ∫_0^∞ f(u) e^{-u} du ≈ Σ w_k f(x_k)
        std::complex<double> phi;
        if (j == 1) {
            phi = heston_phi(u - 1.0, S0, r, q, T, h) / phi_minus_i;
        } else {
            phi = heston_phi(u, S0, r, q, T, h);
        }
        const std::complex<double> integrand = std::exp(-i * u * lnK) * phi / (denom_base * u);
        sum += w * std::real(integrand);
    }
    return 0.5 + (1.0 / M_PI) * sum;
}

} // namespace

double call_analytic(const MarketParams& mkt, const Params& h) {
    const double lnK = std::log(mkt.strike);
    const double P1 = P_j(1, lnK, mkt, h);
    const double P2 = P_j(2, lnK, mkt, h);
    const double df_r = std::exp(-mkt.rate * mkt.time);
    const double df_q = std::exp(-mkt.dividend * mkt.time);
    return mkt.spot * df_q * P1 - mkt.strike * df_r * P2;
}

McResult call_qe_mc(const McParams& p) {
    using quant::stats::Welford;
    const double dt = p.mkt.time / static_cast<double>(p.num_steps);
    const double df = std::exp(-p.mkt.rate * p.mkt.time);
    Welford acc;
    pcg64 rng(p.seed ? p.seed : 0xFACEFEEDULL);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::uniform_real_distribution<double> uniform(0.0, 1.0);

    auto simulate_once = [&](int sign) {
        double S = p.mkt.spot;
        double v = std::max(0.0, p.h.v0);
        for (int i = 0; i < p.num_steps; ++i) {
            const double z1 = normal(rng) * sign;
            const double z2 = normal(rng) * sign;
            const double eps1 = z1;
            const double eps2 = p.h.rho * z1 + std::sqrt(std::max(0.0, 1.0 - p.h.rho * p.h.rho)) * z2;
            // Andersen QE scheme (simplified)
            const double kappa = p.h.kappa;
            const double theta = p.h.theta;
            const double sigma = p.h.sigma;
            const double m = theta + (v - theta) * std::exp(-kappa * dt);
            const double s2 = v * sigma * sigma * std::exp(-kappa * dt) * (1.0 - std::exp(-kappa * dt)) / kappa
                              + theta * sigma * sigma * 0.5 / kappa * (1.0 - std::exp(-kappa * dt)) * (1.0 - std::exp(-kappa * dt));
            const double psi = s2 / (m * m);
            double v_next;
            if (psi <= 1.5) {
                const double b2 = 2.0 / psi - 1.0 + std::sqrt(2.0 / psi) * std::sqrt(2.0 / psi - 1.0);
                const double a = m / (1.0 + b2);
                const double b = b2;
                const double u = std::min(1.0 - std::numeric_limits<double>::epsilon(), std::max(uniform(rng), std::numeric_limits<double>::min()));
                v_next = a * std::pow(1.0 + b, (u < (b / (1.0 + b)) ? 1.0 : 0.0));
            } else {
                const double pexp = (psi - 1.0) / (psi + 1.0);
                const double beta = (1.0 - pexp) / m;
                const double u = std::min(1.0 - std::numeric_limits<double>::epsilon(), std::max(uniform(rng), std::numeric_limits<double>::min()));
                v_next = (u > pexp) ? std::log((1.0 - pexp) / (1.0 - u)) / beta : 0.0;
            }
            const double z_s = eps1;
            const double drift = (p.mkt.rate - p.mkt.dividend - 0.5 * v_next) * dt;
            const double diff = std::sqrt(std::max(0.0, v_next)) * std::sqrt(dt) * z_s;
            S = S * std::exp(drift + diff);
            v = std::max(0.0, v_next);
        }
        return df * std::max(0.0, S - p.mkt.strike);
    };

    for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        double sample = simulate_once(+1);
        if (p.antithetic) sample = 0.5 * (sample + simulate_once(-1));
        acc.add(sample);
    }
    const double se = std::sqrt(acc.variance() / static_cast<double>(acc.count));
    return McResult{acc.mean, se};
}

} // namespace quant::heston


