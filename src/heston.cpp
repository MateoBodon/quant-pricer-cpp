#include "quant/heston.hpp"
#include "quant/black_scholes.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <complex>
#include <limits>
#include <random>
#include <vector>

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

std::complex<double> characteristic_function(double u,
                                             const MarketParams& mkt,
                                             const Params& h) {
    return heston_phi(u, mkt.spot, mkt.rate, mkt.dividend, mkt.time, h);
}

double implied_vol_call(const MarketParams& mkt, const Params& h) {
    const double price = call_analytic(mkt, h);
    return quant::bs::implied_vol_call(mkt.spot, mkt.strike, mkt.rate, mkt.dividend, mkt.time, price);
}

McResult call_qe_mc(const McParams& p) {
    using quant::stats::Welford;

    if (p.num_paths == 0) {
        return McResult{0.0, 0.0};
    }

    const int steps = std::max(1, p.num_steps);
    if (p.mkt.time <= 0.0) {
        const double payoff0 = std::max(0.0, p.mkt.spot - p.mkt.strike);
        return McResult{payoff0, 0.0};
    }

    const double dt = p.mkt.time / static_cast<double>(steps);
    const double sqrt_dt = std::sqrt(dt);
    const double df = std::exp(-p.mkt.rate * p.mkt.time);
    const double rho = std::clamp(p.h.rho, -0.999, 0.999);
    const double one_minus_rho2 = std::max(1.0 - rho * rho, 0.0);
    const double sqrt_one_minus_rho2 = std::sqrt(one_minus_rho2);
    const double psi_threshold = 1.5;
    const double kappa = p.h.kappa;
    const double theta = std::max(p.h.theta, 0.0);
    const double sigma = std::max(p.h.sigma, 0.0);
    const double sigma2 = sigma * sigma;
    const bool use_counter = (p.rng == quant::rng::Mode::Counter);
    const bool use_qe = (p.scheme == McParams::Scheme::QE);
    const bool kappa_small = std::abs(kappa) <= 1e-12;
    const double exp_kdt = std::exp(-kappa * dt);
    const double one_minus_exp = -std::expm1(-kappa * dt);
    const std::uint64_t master_seed = p.seed ? p.seed : 0xFACEFEEDULL;
    constexpr double kUniformEps = std::numeric_limits<double>::epsilon();

    struct Draws {
        std::vector<double> z_var;
        std::vector<double> z_perp;
        std::vector<double> u;
    };

    pcg64 prng(master_seed);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::uniform_real_distribution<double> uniform_dist(0.0, 1.0);

    auto generate_draws = [&](std::uint64_t path_id) {
        Draws d;
        d.z_var.resize(static_cast<std::size_t>(steps));
        d.z_perp.resize(static_cast<std::size_t>(steps));
        d.u.resize(static_cast<std::size_t>(steps));
        if (use_counter) {
            for (int s = 0; s < steps; ++s) {
                const std::uint32_t step_id = static_cast<std::uint32_t>(s);
                d.z_var[static_cast<std::size_t>(s)] = quant::rng::normal(master_seed, path_id, step_id, 0U, 0U);
                d.z_perp[static_cast<std::size_t>(s)] = quant::rng::normal(master_seed, path_id, step_id, 1U, 0U);
                d.u[static_cast<std::size_t>(s)] = quant::rng::uniform(master_seed, path_id, step_id, 2U, 0U);
            }
        } else {
            for (int s = 0; s < steps; ++s) {
                d.z_var[static_cast<std::size_t>(s)] = normal(prng);
                d.z_perp[static_cast<std::size_t>(s)] = normal(prng);
                const double u_draw = uniform_dist(prng);
                d.u[static_cast<std::size_t>(s)] = std::clamp(u_draw, kUniformEps, 1.0 - kUniformEps);
            }
        }
        return d;
    };

    auto make_antithetic = [kUniformEps](const Draws& base) {
        Draws anti = base;
        for (std::size_t i = 0; i < anti.z_var.size(); ++i) {
            anti.z_var[i] = -base.z_var[i];
            anti.z_perp[i] = -base.z_perp[i];
            anti.u[i] = std::clamp(1.0 - base.u[i], kUniformEps, 1.0 - kUniformEps);
        }
        return anti;
    };

    auto evolve_path = [&](const Draws& draws) {
        double logS = std::log(p.mkt.spot);
        double v = std::max(0.0, p.h.v0);
        for (int s = 0; s < steps; ++s) {
            const std::size_t idx = static_cast<std::size_t>(s);
            const double z_var = draws.z_var[idx];
            const double z_perp = draws.z_perp[idx];
            const double u = draws.u[idx];

            if (!use_qe) {
                const double sqrt_v = std::sqrt(std::max(v, 0.0));
                const double dW_var = sqrt_dt * z_var;
                const double dW_perp = sqrt_dt * z_perp;
                double v_next = v + kappa * (theta - v) * dt + sigma * sqrt_v * dW_var;
                v_next = std::max(v_next, 0.0);
                const double z_star = rho * dW_var + sqrt_one_minus_rho2 * dW_perp;
                logS += (p.mkt.rate - p.mkt.dividend - 0.5 * v) * dt + sqrt_v * z_star;
                v = v_next;
                continue;
            }

            double m = theta + (v - theta) * exp_kdt;
            m = std::max(m, 0.0);
            double s2;
            if (kappa_small) {
                s2 = sigma2 * v * dt;
            } else if (sigma == 0.0) {
                s2 = 0.0;
            } else {
                s2 = v * sigma2 * exp_kdt * one_minus_exp / kappa
                     + theta * sigma2 * one_minus_exp * one_minus_exp / (2.0 * kappa);
            }
            s2 = std::max(s2, 0.0);

            const double m_safe = std::max(m, 1e-12);
            double psi = (m_safe > 0.0) ? s2 / (m_safe * m_safe) : psi_threshold + 1.0;

            double v_next = m_safe;
            if (psi < 1e-12) {
                v_next = m_safe;
            } else if (psi <= psi_threshold) {
                const double two_over_psi = 2.0 / psi;
                const double inside = std::max(0.0, two_over_psi - 1.0);
                const double b2 = two_over_psi - 1.0 + std::sqrt(std::max(0.0, two_over_psi * inside));
                const double b = std::sqrt(std::max(b2, 0.0));
                const double a = m_safe / (1.0 + b2);
                v_next = a * (b + z_var) * (b + z_var);
            } else {
                const double p_branch = (psi - 1.0) / (psi + 1.0);
                const double beta = (1.0 - p_branch) / m_safe;
                if (u <= p_branch) {
                    v_next = 0.0;
                } else {
                    v_next = -std::log((1.0 - p_branch) / (1.0 - u)) / beta;
                }
            }
            v_next = std::max(v_next, 0.0);
            const double v_avg = std::max(0.0, 0.5 * (v + v_next));
            const double sqrt_v_avg_dt = std::sqrt(v_avg * dt);
            const double cross = v_next - v - kappa * (theta - v_avg) * dt;
            const double correlated = (sigma > 1e-12) ? (rho / sigma) * cross : 0.0;
            const double diffusion = sqrt_one_minus_rho2 * sqrt_v_avg_dt * z_perp;
            logS += (p.mkt.rate - p.mkt.dividend) * dt - 0.5 * v_avg * dt + correlated + diffusion;
            v = v_next;
        }

        const double payoff = std::max(0.0, std::exp(logS) - p.mkt.strike);
        return df * payoff;
    };

    Welford acc;
    for (std::uint64_t path = 0; path < p.num_paths; ++path) {
        Draws base = generate_draws(path);
        double sample = evolve_path(base);
        if (p.antithetic) {
            Draws anti = make_antithetic(base);
            const double anti_sample = evolve_path(anti);
            sample = 0.5 * (sample + anti_sample);
        }
        acc.add(sample);
    }

    const double price = acc.mean;
    const double se = (acc.count > 1)
                          ? std::sqrt(acc.variance() / static_cast<double>(acc.count))
                          : 0.0;
    return McResult{price, se};
}

} // namespace quant::heston
