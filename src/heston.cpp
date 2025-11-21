#include "quant/heston.hpp"
#include "quant/black_scholes.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <complex>
#include <limits>
#include <numbers>
#include <random>
#include <vector>

namespace quant::heston {

// Heston analytic via characteristic function and Gauss-Laguerre quadrature
namespace {

struct GL32 {
    static constexpr int N = 32;
};

// 32-point Gauss–Laguerre nodes (x) and weights (w) for ∫_0^∞ w(x) f(x) dx
static const double kGL32_x[32] = {
    0.044489365833267285, 0.23452610951961964, 0.5768846293018867, 1.072448753817818,
    1.7224087764446454,  2.5283367064257942,  3.492213273021994,  4.616456769749767,
    5.903958504174244,   7.358126733186241,   8.982940924212595,  10.783018632539973,
    12.763697986742725,  14.931139755522558,  17.292454336715313, 19.855860940336054,
    22.630889013196775,  25.628636022459247,  28.862101816323474, 32.346629153964734,
    36.10049480575197,   40.14571977153944,   44.50920799575494,  49.22439498730864,
    54.33372133339691,   59.89250916213402,   65.97537728793505,  72.68762809066271,
    80.18744697791352,   88.7353404178924,    98.82954286828397,  111.7513980979377};
static const double kGL32_w[32] = {
    0.10921834195241631,   0.21044310793883672,  0.23521322966983194,  0.1959033359728629,
    0.12998378628606097,   0.07057862386571173,   0.03176091250917226,   0.011918214834837557,
    0.003738816294611212,  0.0009808033066148732, 0.00021486491880134604, 3.9203419679876094e-05,
    5.934541612868126e-06,  7.416404578666935e-07,  7.604567879120183e-08,  6.350602226625271e-09,
    4.2813829710405056e-10, 2.305899491891127e-11,  9.79937928872617e-13,  3.237801657729003e-14,
    8.171823443420105e-16,  1.5421338333936845e-17, 2.119792290163458e-19,  2.054429673787832e-21,
    1.3469825866373068e-23, 5.661294130396917e-26,  1.4185605454629279e-28, 1.91337549445389e-31,
    1.1922487600980343e-34, 2.6715112192398583e-38, 1.3386169421063085e-42, 4.5105361938984096e-48};

inline std::complex<double> iunit() { return std::complex<double>(0.0, 1.0); }

inline std::complex<double> heston_phi(std::complex<double> u, double S0, double r, double q, double T,
                                       const Params& h) {
    using cd = std::complex<double>;
    const cd i = iunit();
    const cd iu = i * u;
    const double kappa = h.kappa;
    const double theta = h.theta;
    const double sigma = h.sigma;
    const double rho = h.rho;
    const double v0 = h.v0;

    const cd d = std::sqrt(std::pow(rho * sigma * iu - kappa, 2.0) + sigma * sigma * (iu + u * u));
    const cd g = (kappa - rho * sigma * iu - d) / (kappa - rho * sigma * iu + d);
    const cd C = iu * (std::log(S0) + (r - q) * T) + (kappa * theta) / (sigma * sigma) *
                                               ((kappa - rho * sigma * iu - d) * T -
                                                2.0 * std::log((1.0 - g * std::exp(-d * T)) / (1.0 - g)));
    const cd D = ((kappa - rho * sigma * iu - d) / (sigma * sigma)) *
                 ((1.0 - std::exp(-d * T)) / (1.0 - g * std::exp(-d * T)));
    return std::exp(C + D * v0);
}

inline double P_j(int j, double lnK, const MarketParams& mkt, const Params& h) {
    // Carr–Madan style integrals via Laguerre: ∫ Re( e^{-iu lnK} φ_j(u) / (i u) ) du
    const double S0 = mkt.spot;
    const double r = mkt.rate;
    const double q = mkt.dividend;
    const double T = mkt.time;
    const std::complex<double> i = iunit();
    const std::complex<double> denom_base = i; // for 1/(i u)

    // φ1 uses shift u - i with normalization φ(-i)
    std::complex<double> phi_minus_i = heston_phi(std::complex<double>(0.0, -1.0), S0, r, q, T, h);
    double sum = 0.0;
    for (int k = 0; k < 32; ++k) {
        const double x = kGL32_x[k];
        const double w = kGL32_w[k];
        if (w == 0.0)
            continue;
        const double u = x; // Laguerre transforms ∫_0^∞ f(u) e^{-u} du ≈ Σ w_k f(x_k)
        std::complex<double> phi;
        if (j == 1) {
            phi = heston_phi(std::complex<double>(u, -1.0), S0, r, q, T, h) / phi_minus_i;
        } else {
            phi = heston_phi(std::complex<double>(u, 0.0), S0, r, q, T, h);
        }
        const std::complex<double> integrand = std::exp(-i * u * lnK) * phi / (denom_base * u);
        // Transform ∫ f(u) du into Laguerre form ∫ e^{-x} [e^{x} f(x)] dx
        sum += w * std::exp(x) * std::real(integrand);
    }
    return 0.5 + (sum / std::numbers::pi);
}

} // namespace

double call_analytic(const MarketParams& mkt, const Params& h) {
    const double lnK = std::log(mkt.strike);
    const double P1 = P_j(1, lnK, mkt, h);
    const double P2 = P_j(2, lnK, mkt, h);
    const double df_r = std::exp(-mkt.rate * mkt.time);
    const double df_q = std::exp(-mkt.dividend * mkt.time);
    const double intrinsic = std::max(0.0, mkt.spot * df_q - mkt.strike * df_r);
    double price = mkt.spot * df_q * P1 - mkt.strike * df_r * P2;
    if (price < intrinsic) {
        price = intrinsic;
    }
    return price;
}

std::complex<double> characteristic_function(double u, const MarketParams& mkt, const Params& h) {
    return heston_phi(std::complex<double>(u, 0.0), mkt.spot, mkt.rate, mkt.dividend, mkt.time, h);
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
                d.z_var[static_cast<std::size_t>(s)] =
                    quant::rng::normal(master_seed, path_id, step_id, 0U, 0U);
                d.z_perp[static_cast<std::size_t>(s)] =
                    quant::rng::normal(master_seed, path_id, step_id, 1U, 0U);
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
                s2 = v * sigma2 * exp_kdt * one_minus_exp / kappa +
                     theta * sigma2 * one_minus_exp * one_minus_exp / (2.0 * kappa);
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

            // Approximate ∫_t^{t+Δ} v_s ds using the CIR expectation so the asset drift uses a
            // consistent average variance even when κΔ is not tiny.
            double int_v;
            if (kappa_small) {
                int_v = v * dt; // κ → 0 reduces to Euler
            } else {
                int_v = theta * dt + (v - theta) * one_minus_exp / kappa;
            }
            const double v_bar = std::max(int_v / dt, 0.0);
            const double sqrt_v_bar_dt = std::sqrt(std::max(v_bar * dt, 0.0));

            // Andersen QE: σ ∫ sqrt(v) dW1 ≈ dv - κ(θ - \bar v)Δt couples asset and variance.
            const double dv = v_next - v;
            const double cross = dv - kappa * (theta - v_bar) * dt;
            const double correlated = (sigma > 1e-12) ? (rho / sigma) * cross : 0.0;
            const double diffusion = sqrt_one_minus_rho2 * sqrt_v_bar_dt * z_perp;

            logS += (p.mkt.rate - p.mkt.dividend) * dt - 0.5 * v_bar * dt + correlated + diffusion;
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
    const double se = (acc.count > 1) ? std::sqrt(acc.variance() / static_cast<double>(acc.count)) : 0.0;
    return McResult{price, se};
}

} // namespace quant::heston
