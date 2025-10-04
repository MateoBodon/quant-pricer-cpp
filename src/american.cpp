#include "quant/american.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <random>
#include <stdexcept>
#include <vector>

#include <pcg_random.hpp>

#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

using quant::OptionType;

namespace quant::american {
namespace {

struct SpaceGrid {
    std::vector<double> x;
    std::vector<double> S;
};

struct OperatorWorkspace {
    std::vector<double> lower;
    std::vector<double> diag;
    std::vector<double> upper;
    std::vector<double> rhs;
};

double stretch_map(double xi, double xi0, double stretch) {
    if (stretch <= 0.0) {
        return xi;
    }
    const double eps = 1e-10;
    xi0 = std::clamp(xi0, eps, 1.0 - eps);
    if (xi <= xi0) {
        double ratio = xi / xi0;
        return xi0 * std::tanh(stretch * ratio) / std::tanh(stretch);
    }
    double ratio = (1.0 - xi) / (1.0 - xi0);
    return 1.0 - (1.0 - xi0) * std::tanh(stretch * ratio) / std::tanh(stretch);
}

SpaceGrid build_space_grid(const PsorParams& params) {
    if (params.grid.num_space < 3) {
        throw std::invalid_argument("PSOR grid requires at least 3 spatial nodes");
    }
    SpaceGrid grid;
    grid.x.resize(params.grid.num_space);
    grid.S.resize(params.grid.num_space);

    if (!params.log_space) {
        const double S_lower = 0.0;
        const double S_upper = std::max(params.base.spot * params.grid.s_max_mult,
                                        params.base.strike * params.grid.s_max_mult);
        if (S_upper <= 0.0) {
            throw std::invalid_argument("Invalid S_max for American grid");
        }
        const double xi0 = std::clamp((params.base.strike - S_lower) / (S_upper - S_lower), 0.0, 1.0);
        for (int i = 0; i < params.grid.num_space; ++i) {
            double xi = (params.grid.num_space == 1) ? 0.0
                                                    : static_cast<double>(i) / static_cast<double>(params.grid.num_space - 1);
            double mapped = stretch_map(xi, xi0, params.stretch);
            double S_val = S_lower + (S_upper - S_lower) * mapped;
            grid.x[i] = S_val;
            grid.S[i] = S_val;
        }
    } else {
        const double S_lower = std::max(1e-8, params.base.spot / params.grid.s_max_mult);
        const double S_upper = params.base.spot * params.grid.s_max_mult;
        if (S_upper <= S_lower) {
            throw std::invalid_argument("Invalid log-space bounds for American grid");
        }
        const double x_min = std::log(S_lower);
        const double x_max = std::log(S_upper);
        const double xi0 = std::clamp((std::log(params.base.strike) - x_min) / (x_max - x_min), 0.0, 1.0);
        for (int i = 0; i < params.grid.num_space; ++i) {
            double xi = (params.grid.num_space == 1) ? 0.0
                                                    : static_cast<double>(i) / static_cast<double>(params.grid.num_space - 1);
            double mapped = stretch_map(xi, xi0, params.stretch);
            double x_val = x_min + (x_max - x_min) * mapped;
            grid.x[i] = x_val;
            grid.S[i] = std::exp(x_val);
        }
    }
    return grid;
}

double intrinsic_value(OptionType type, double strike, double S) {
    if (type == OptionType::Call) {
        return std::max(0.0, S - strike);
    }
    return std::max(0.0, strike - S);
}

void build_system(const PsorParams& params,
                  const SpaceGrid& grid,
                  const std::vector<double>& V_curr,
                  double dt,
                  double theta,
                  double tau_next,
                  OperatorWorkspace& op) {
    const int M = params.grid.num_space;
    op.lower.assign(std::max(0, M - 1), 0.0);
    op.diag.assign(M, 0.0);
    op.upper.assign(std::max(0, M - 1), 0.0);
    op.rhs.assign(M, 0.0);

    const double sigma = params.base.vol;
    const double sigma2 = sigma * sigma;
    const double r = params.base.rate;
    const double q = params.base.dividend;

    auto payoff_bc = [&](bool lower) {
        const double S_val = lower ? grid.S.front() : grid.S.back();
        const double df_r = std::exp(-r * tau_next);
        const double df_q = std::exp(-q * tau_next);
        if (params.base.type == OptionType::Call) {
            if (lower) {
                return 0.0;
            }
            return S_val * df_q - params.base.strike * df_r;
        }
        if (lower) {
            return params.base.strike * df_r - S_val * df_q;
        }
        return 0.0;
    };

    const double lower_bc = payoff_bc(true);
    const double upper_bc = payoff_bc(false);

    op.diag[0] = 1.0;
    op.rhs[0] = lower_bc;
    if (M > 1) {
        op.upper[0] = 0.0;
    }

    for (int i = 1; i < M - 1; ++i) {
        const double h_minus = grid.x[i] - grid.x[i - 1];
        const double h_plus = grid.x[i + 1] - grid.x[i];
        if (h_minus <= 0.0 || h_plus <= 0.0) {
            throw std::runtime_error("Non-increasing spatial grid encountered in PSOR");
        }
        const double denom = h_minus + h_plus;

        double a_i, b_i, c_i;
        if (!params.log_space) {
            const double S_i = grid.S[i];
            a_i = 0.5 * sigma2 * S_i * S_i;
            b_i = (r - q) * S_i;
            c_i = -r;
        } else {
            a_i = 0.5 * sigma2;
            b_i = (r - q - 0.5 * sigma2);
            c_i = -r;
        }

        const double diff_im1 = 2.0 * a_i / (h_minus * denom);
        const double diff_ip1 = 2.0 * a_i / (h_plus * denom);
        const double diff_i = -diff_im1 - diff_ip1;

        const double conv_im1 = -b_i * h_plus / (h_minus * denom);
        const double conv_ip1 = b_i * h_minus / (h_plus * denom);
        const double conv_i = -conv_im1 - conv_ip1 + c_i;

        const double L_im1 = diff_im1 + conv_im1;
        const double L_i = diff_i + conv_i;
        const double L_ip1 = diff_ip1 + conv_ip1;

        op.lower[i - 1] = -theta * dt * L_im1;
        op.diag[i] = 1.0 - theta * dt * L_i;
        op.upper[i] = -theta * dt * L_ip1;

        op.rhs[i] = V_curr[i] + (1.0 - theta) * dt *
            (L_im1 * V_curr[i - 1] + L_i * V_curr[i] + L_ip1 * V_curr[i + 1]);
    }

    if (M > 1) {
        if (params.upper_boundary == quant::pde::PdeParams::UpperBoundary::Dirichlet || !params.log_space) {
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = 0.0;
            op.rhs[M - 1] = upper_bc;
        } else {
            const double dx = grid.x[M - 1] - grid.x[M - 2];
            double dVdS = (params.base.type == OptionType::Call) ? std::exp(-q * tau_next) : 0.0;
            double dUdx = grid.S.back() * dVdS;
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = -1.0;
            op.rhs[M - 1] = dx * dUdx;
        }
    }
}

double interpolate_price(const std::vector<double>& S,
                         const std::vector<double>& V,
                         double S0) {
    const std::size_t M = S.size();
    if (M == 0) {
        return 0.0;
    }
    if (S0 <= S.front()) {
        return V.front();
    }
    if (S0 >= S.back()) {
        return V.back();
    }
    auto it = std::upper_bound(S.begin(), S.end(), S0);
    std::size_t idx = static_cast<std::size_t>(std::distance(S.begin(), it));
    if (idx == 0) {
        return V.front();
    }
    double S_lo = S[idx - 1];
    double S_hi = S[idx];
    double V_lo = V[idx - 1];
    double V_hi = V[idx];
    double w = (S0 - S_lo) / (S_hi - S_lo);
    return V_lo + w * (V_hi - V_lo);
}

std::array<double, 4> polynomial_features(double x) {
    double x2 = x * x;
    return {1.0, x, x2, x2 * x};
}

struct NormalEquations {
    double ata[4][4]{};
    double atb[4]{};

    void add(const std::array<double, 4>& phi, double y) {
        for (int i = 0; i < 4; ++i) {
            atb[i] += phi[i] * y;
            for (int j = i; j < 4; ++j) {
                ata[i][j] += phi[i] * phi[j];
            }
        }
    }

    void symmetrize() {
        for (int i = 0; i < 4; ++i) {
            for (int j = 0; j < i; ++j) {
                ata[i][j] = ata[j][i];
            }
        }
    }
};

std::array<double, 4> solve_normal_equations(NormalEquations eq) {
    eq.symmetrize();
    double a[4][5];
    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 4; ++j) {
            a[i][j] = eq.ata[i][j];
        }
        a[i][4] = eq.atb[i];
    }
    for (int i = 0; i < 4; ++i) {
        int pivot = i;
        double max_val = std::abs(a[i][i]);
        for (int r = i + 1; r < 4; ++r) {
            double val = std::abs(a[r][i]);
            if (val > max_val) {
                max_val = val;
                pivot = r;
            }
        }
        if (max_val < 1e-12) {
            return {0.0, 0.0, 0.0, 0.0};
        }
        if (pivot != i) {
            for (int c = i; c < 5; ++c) {
                std::swap(a[i][c], a[pivot][c]);
            }
        }
        double pivot_inv = 1.0 / a[i][i];
        for (int c = i; c < 5; ++c) {
            a[i][c] *= pivot_inv;
        }
        for (int r = 0; r < 4; ++r) {
            if (r == i) continue;
            double factor = a[r][i];
            for (int c = i; c < 5; ++c) {
                a[r][c] -= factor * a[i][c];
            }
        }
    }
    std::array<double, 4> beta{};
    for (int i = 0; i < 4; ++i) {
        beta[i] = a[i][4];
    }
    return beta;
}

} // namespace

double price_binomial_crr(const Params& p, int steps) {
    if (steps <= 0) {
        throw std::invalid_argument("Binomial steps must be positive");
    }
    const double dt = p.time / static_cast<double>(steps);
    const double up = std::exp(p.vol * std::sqrt(dt));
    const double down = 1.0 / up;
    const double disc = std::exp(-p.rate * dt);
    const double growth = std::exp((p.rate - p.dividend) * dt);
    const double prob = (growth - down) / (up - down);
    if (prob < 0.0 || prob > 1.0) {
        throw std::runtime_error("Arbitrage detected in binomial parameters");
    }
    std::vector<double> prices(static_cast<std::size_t>(steps) + 1);
    for (int i = 0; i <= steps; ++i) {
        double ST = p.spot * std::pow(up, steps - i) * std::pow(down, i);
        prices[i] = intrinsic_value(p.type, p.strike, ST);
    }
    for (int step = steps - 1; step >= 0; --step) {
        for (int i = 0; i <= step; ++i) {
            double cont = disc * (prob * prices[i] + (1.0 - prob) * prices[i + 1]);
            double S_t = p.spot * std::pow(up, step - i) * std::pow(down, i);
            double exer = intrinsic_value(p.type, p.strike, S_t);
            prices[i] = std::max(cont, exer);
        }
    }
    return prices[0];
}

PsorResult price_psor(const PsorParams& params) {
    if (params.grid.num_time <= 0 || params.base.time <= 0.0) {
        throw std::invalid_argument("PSOR grid requires positive time steps and maturity");
    }
    if (params.omega <= 0.0 || params.omega >= 2.0) {
        throw std::invalid_argument("PSOR omega must be in (0, 2)");
    }
    SpaceGrid grid = build_space_grid(params);
    const int M = params.grid.num_space;
    std::vector<double> V(M);
    std::vector<double> intrinsic(M);
    for (int i = 0; i < M; ++i) {
        intrinsic[i] = intrinsic_value(params.base.type, params.base.strike, grid.S[i]);
        V[i] = intrinsic[i];
    }

    OperatorWorkspace op;
    const int N = params.grid.num_time;
    const double dt = params.base.time / static_cast<double>(N);
    const int rannacher_steps = params.use_rannacher ? std::min(2, N) : 0;

    int total_iters = 0;
    double final_residual = 0.0;

    for (int step = 0; step < N; ++step) {
        const double theta = (step < rannacher_steps) ? 1.0 : 0.5;
        const double tau_next = params.base.time - static_cast<double>(step + 1) * dt;
        build_system(params, grid, V, dt, theta, tau_next, op);

        std::vector<double> next = V;
        next.front() = op.rhs.front();
        next.back() = op.rhs.back();

        double residual = 0.0;
        for (int iter = 0; iter < params.max_iterations; ++iter) {
            residual = 0.0;
            const std::vector<double> prev = next;
            for (int i = 1; i < M - 1; ++i) {
                const double diag = op.diag[i];
                const double rhs = op.rhs[i];
                const double lower = op.lower[i - 1];
                const double upper = op.upper[i];
                double estimate = (rhs - lower * next[i - 1] - upper * prev[i + 1]) / diag;
                double new_val = (1.0 - params.omega) * next[i] + params.omega * estimate;
                if (new_val < intrinsic[i]) {
                    new_val = intrinsic[i];
                }
                residual = std::max(residual, std::abs(new_val - next[i]));
                next[i] = new_val;
            }
            if (residual < params.tolerance) {
                total_iters += (iter + 1);
                break;
            }
            if (iter == params.max_iterations - 1) {
                total_iters += params.max_iterations;
            }
        }
        final_residual = residual;
        V = std::move(next);
    }

    double price = interpolate_price(grid.S, V, params.base.spot);
    return PsorResult{price, total_iters, final_residual};
}

LsmcResult price_lsmc(const LsmcParams& params) {
    if (params.num_paths == 0 || params.num_steps <= 0) {
        throw std::invalid_argument("LSMC requires positive paths and time steps");
    }
    const double dt = params.base.time / static_cast<double>(params.num_steps);
    const double mu = params.base.rate - params.base.dividend;
    const double disc = std::exp(-params.base.rate * dt);
    const double drift = (mu - 0.5 * params.base.vol * params.base.vol) * dt;
    const double vol_step = params.base.vol * std::sqrt(dt);

    const std::size_t steps = static_cast<std::size_t>(params.num_steps);
    const std::size_t base_paths = static_cast<std::size_t>(params.num_paths);
    const bool use_antithetic = params.antithetic;
    const std::size_t path_count = use_antithetic ? base_paths * 2 : base_paths;

    std::vector<std::vector<double>> spots(steps + 1, std::vector<double>(path_count));
    spots[0].assign(path_count, params.base.spot);

    pcg64 rng(params.seed);
    std::normal_distribution<double> normal(0.0, 1.0);

    for (std::size_t t = 1; t <= steps; ++t) {
        auto& prev = spots[t - 1];
        auto& curr = spots[t];
        if (!use_antithetic) {
            for (std::size_t i = 0; i < path_count; ++i) {
                double z = normal(rng);
                curr[i] = prev[i] * std::exp(drift + vol_step * z);
            }
        } else {
            for (std::size_t pair = 0; pair < base_paths; ++pair) {
                std::size_t idx = 2 * pair;
                double z = normal(rng);
                curr[idx] = prev[idx] * std::exp(drift + vol_step * z);
                curr[idx + 1] = prev[idx + 1] * std::exp(drift - vol_step * z);
            }
        }
    }

    std::vector<double> cashflow(path_count);
    std::vector<bool> exercised(path_count, false);

    for (std::size_t i = 0; i < path_count; ++i) {
        cashflow[i] = intrinsic_value(params.base.type, params.base.strike, spots[steps][i]);
    }

    std::vector<double> S_itm;
    std::vector<double> y_itm;
    S_itm.reserve(path_count);
    y_itm.reserve(path_count);

    for (int t = static_cast<int>(steps) - 1; t >= 1; --t) {
        auto& spot_t = spots[static_cast<std::size_t>(t)];
        for (std::size_t i = 0; i < path_count; ++i) {
            cashflow[i] *= disc;
        }
        S_itm.clear();
        y_itm.clear();
        for (std::size_t i = 0; i < path_count; ++i) {
            if (exercised[i]) {
                continue;
            }
            double intrinsic = intrinsic_value(params.base.type, params.base.strike, spot_t[i]);
            if (intrinsic > 0.0) {
                S_itm.push_back(spot_t[i] / params.base.strike - 1.0);
                y_itm.push_back(cashflow[i]);
            }
        }
        std::array<double,4> beta{0.0, 0.0, 0.0, 0.0};
        if (S_itm.size() >= 5) {
            NormalEquations eq;
            for (std::size_t i = 0; i < S_itm.size(); ++i) {
                eq.add(polynomial_features(S_itm[i]), y_itm[i]);
            }
            beta = solve_normal_equations(eq);
        }
        for (std::size_t i = 0; i < path_count; ++i) {
            if (exercised[i]) {
                continue;
            }
            double intrinsic = intrinsic_value(params.base.type, params.base.strike, spot_t[i]);
            if (intrinsic <= 0.0) {
                continue;
            }
            double x = spot_t[i] / params.base.strike - 1.0;
            double cont = beta[0] + beta[1] * x + beta[2] * x * x + beta[3] * x * x * x;
            if (cont <= intrinsic) {
                cashflow[i] = intrinsic;
                exercised[i] = true;
            }
        }
    }

    double sum = 0.0;
    double sumsq = 0.0;
    for (std::size_t i = 0; i < path_count; ++i) {
        double pv = disc * cashflow[i];
        sum += pv;
        sumsq += pv * pv;
    }
    double mean = sum / static_cast<double>(path_count);
    double variance = (sumsq / static_cast<double>(path_count)) - mean * mean;
    variance = std::max(0.0, variance);
    double se = std::sqrt(variance / static_cast<double>(path_count));
    return LsmcResult{mean, se};
}

} // namespace quant::american
