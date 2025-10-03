#include "quant/pde.hpp"

#include "quant/black_scholes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace quant::pde {

namespace {

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

struct SpaceGrid {
    std::vector<double> x; // coordinate used for differencing (S or log S)
    std::vector<double> S; // actual asset levels corresponding to x
};

SpaceGrid build_space_grid(const PdeParams& p) {
    if (p.grid.num_space < 3) {
        throw std::invalid_argument("PDE grid requires at least 3 spatial nodes");
    }
    SpaceGrid grid{};
    grid.x.resize(p.grid.num_space);
    grid.S.resize(p.grid.num_space);

    if (!p.log_space) {
        const double S_lower = 0.0;
        const double S_upper = std::max(p.spot * p.grid.s_max_mult, p.strike * p.grid.s_max_mult);
        if (S_upper <= S_lower) {
            throw std::invalid_argument("Upper bound must exceed lower bound in S-grid");
        }
        const double xi0 = std::clamp((p.strike - S_lower) / (S_upper - S_lower), 0.0, 1.0);
        for (int i = 0; i < p.grid.num_space; ++i) {
            double xi = (p.grid.num_space == 1) ? 0.0 : static_cast<double>(i) / static_cast<double>(p.grid.num_space - 1);
            double mapped = stretch_map(xi, xi0, p.grid.stretch);
            double S_val = S_lower + (S_upper - S_lower) * mapped;
            grid.x[i] = S_val;
            grid.S[i] = S_val;
        }
    } else {
        const double S_lower = std::max(1e-8, p.spot / p.grid.s_max_mult);
        const double S_upper = p.spot * p.grid.s_max_mult;
        if (S_upper <= S_lower) {
            throw std::invalid_argument("Invalid log-space bounds (check s_max_mult)");
        }
        const double x_min = std::log(S_lower);
        const double x_max = std::log(S_upper);
        const double xi0 = std::clamp((std::log(p.strike) - x_min) / (x_max - x_min), 0.0, 1.0);
        for (int i = 0; i < p.grid.num_space; ++i) {
            double xi = (p.grid.num_space == 1) ? 0.0 : static_cast<double>(i) / static_cast<double>(p.grid.num_space - 1);
            double mapped = stretch_map(xi, xi0, p.grid.stretch);
            double x_val = x_min + (x_max - x_min) * mapped;
            grid.x[i] = x_val;
            grid.S[i] = std::exp(x_val);
        }
    }
    return grid;
}

struct OperatorWorkspace {
    std::vector<double> lower;
    std::vector<double> diag;
    std::vector<double> upper;
    std::vector<double> rhs;
};

void build_system(const PdeParams& p,
                  const SpaceGrid& grid,
                  const std::vector<double>& V_curr,
                  double dt,
                  double theta,
                  double tau_next,
                  OperatorWorkspace& op) {
    const int M = p.grid.num_space;
    op.lower.assign(std::max(0, M - 1), 0.0);
    op.diag.assign(M, 0.0);
    op.upper.assign(std::max(0, M - 1), 0.0);
    op.rhs.assign(M, 0.0);

    const double sigma = p.vol;
    const double sigma2 = sigma * sigma;
    const double r = p.rate;
    const double q = p.dividend;

    auto payoff_bc = [&](bool lower) {
        const double tau = tau_next;
        if (!p.log_space) {
            const double S_val = lower ? grid.S.front() : grid.S.back();
            if (p.type == OptionType::Call) {
                if (lower) return 0.0;
                return S_val * std::exp(-q * tau) - p.strike * std::exp(-r * tau);
            } else {
                if (lower) return p.strike * std::exp(-r * tau);
                return 0.0;
            }
        } else {
            const double S_val = lower ? grid.S.front() : grid.S.back();
            if (p.type == OptionType::Call) {
                if (lower) return 0.0;
                return S_val * std::exp(-q * tau) - p.strike * std::exp(-r * tau);
            } else {
                if (lower) return p.strike * std::exp(-r * tau) - S_val * std::exp(-q * tau);
                return 0.0;
            }
        }
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
            throw std::runtime_error("Non-increasing spatial grid encountered");
        }
        const double denom = h_minus + h_plus;

        double a_i, b_i, c_i;
        if (!p.log_space) {
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
        if (p.upper_boundary == PdeParams::UpperBoundary::Dirichlet || !p.log_space) {
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = 0.0;
            op.rhs[M - 1] = upper_bc;
        } else {
            const double dx = grid.x[M - 1] - grid.x[M - 2];
            double dVdS = (p.type == OptionType::Call) ? std::exp(-q * tau_next) : 0.0;
            double dUdx = grid.S.back() * dVdS;
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = -1.0;
            op.rhs[M - 1] = dx * dUdx;
        }
    }
}

struct InterpResult {
    double value;
    double delta;
    double gamma;
};

InterpResult interpolate_greeks(const std::vector<double>& S,
                                const std::vector<double>& V,
                                double S0) {
    const std::size_t M = S.size();
    if (M < 3) {
        throw std::runtime_error("Need at least three spatial nodes to compute Greeks");
    }
    auto it = std::lower_bound(S.begin(), S.end(), S0);
    std::size_t idx = static_cast<std::size_t>(std::distance(S.begin(), it));
    if (idx == 0) {
        idx = 1;
    } else if (idx >= M - 1) {
        idx = M - 2;
    }
    const std::size_t i0 = idx - 1;
    const std::size_t i1 = idx;
    const std::size_t i2 = idx + 1;

    const double x0 = S[i0];
    const double x1 = S[i1];
    const double x2 = S[i2];
    const double f0 = V[i0];
    const double f1 = V[i1];
    const double f2 = V[i2];

    const double denom0 = (x0 - x1) * (x0 - x2);
    const double denom1 = (x1 - x0) * (x1 - x2);
    const double denom2 = (x2 - x0) * (x2 - x1);

    const double L0 = (S0 - x1) * (S0 - x2) / denom0;
    const double L1 = (S0 - x0) * (S0 - x2) / denom1;
    const double L2 = (S0 - x0) * (S0 - x1) / denom2;

    const double L0_prime = (2.0 * S0 - x1 - x2) / denom0;
    const double L1_prime = (2.0 * S0 - x0 - x2) / denom1;
    const double L2_prime = (2.0 * S0 - x0 - x1) / denom2;

    const double L0_second = 2.0 / denom0;
    const double L1_second = 2.0 / denom1;
    const double L2_second = 2.0 / denom2;

    InterpResult out{};
    out.value = f0 * L0 + f1 * L1 + f2 * L2;
    out.delta = f0 * L0_prime + f1 * L1_prime + f2 * L2_prime;
    out.gamma = f0 * L0_second + f1 * L1_second + f2 * L2_second;
    return out;
}

} // namespace

std::vector<double> solve_tridiagonal(const std::vector<double>& a,
                                      const std::vector<double>& b,
                                      const std::vector<double>& c,
                                      const std::vector<double>& d) {
    const int n = static_cast<int>(b.size());
    if (static_cast<int>(a.size()) != n - 1 || static_cast<int>(c.size()) != n - 1 || static_cast<int>(d.size()) != n) {
        throw std::invalid_argument("Tridiagonal sizes mismatch");
    }
    std::vector<double> cp(c);
    std::vector<double> dp(d);
    std::vector<double> x(n);

    double beta = b[0];
    if (std::abs(beta) < 1e-14) {
        throw std::runtime_error("Singular tridiagonal matrix");
    }
    cp[0] = c[0] / beta;
    dp[0] = d[0] / beta;
    for (int i = 1; i < n - 1; ++i) {
        beta = b[i] - a[i - 1] * cp[i - 1];
        if (std::abs(beta) < 1e-14) {
            throw std::runtime_error("Near-singular tridiagonal (pivot)");
        }
        cp[i] = c[i] / beta;
        dp[i] = (d[i] - a[i - 1] * dp[i - 1]) / beta;
    }
    beta = b[n - 1] - a[n - 2] * cp[n - 2];
    if (std::abs(beta) < 1e-14) {
        throw std::runtime_error("Near-singular tridiagonal (last pivot)");
    }
    dp[n - 1] = (d[n - 1] - a[n - 2] * dp[n - 2]) / beta;

    x[n - 1] = dp[n - 1];
    for (int i = n - 2; i >= 0; --i) {
        x[i] = dp[i] - cp[i] * x[i + 1];
    }
    return x;
}

PdeResult price_crank_nicolson(const PdeParams& p) {
    if (p.grid.num_time <= 0 || p.time <= 0.0) {
        throw std::invalid_argument("PDE grid must have positive time steps and maturity");
    }

    SpaceGrid grid = build_space_grid(p);

    std::vector<double> V(grid.S.size());
    for (std::size_t i = 0; i < grid.S.size(); ++i) {
        if (p.type == OptionType::Call) {
            V[i] = std::max(0.0, grid.S[i] - p.strike);
        } else {
            V[i] = std::max(0.0, p.strike - grid.S[i]);
        }
    }

    OperatorWorkspace op;
    const int M = p.grid.num_space;
    const int N = p.grid.num_time;
    const double dt = p.time / static_cast<double>(N);
    const int rannacher_steps = std::min(2, N);

    std::vector<double> V_prev_for_theta;
    bool capture_theta = p.compute_theta && N > 0;

    for (int step = 0; step < N; ++step) {
        const double theta = (step < rannacher_steps) ? 1.0 : 0.5;
        const double tau_next = p.time - static_cast<double>(step + 1) * dt;
        if (capture_theta && step == N - 1) {
            V_prev_for_theta = V;
        }
        build_system(p, grid, V, dt, theta, tau_next, op);
        V = solve_tridiagonal(op.lower, op.diag, op.upper, op.rhs);
    }

    InterpResult interp = interpolate_greeks(grid.S, V, p.spot);

    std::optional<double> theta_value;
    if (p.compute_theta && N > 0) {
        double prev_price = interpolate_greeks(grid.S, V_prev_for_theta, p.spot).value;
        theta_value = (prev_price - interp.value) / dt;
    }

    return PdeResult{interp.value, interp.delta, interp.gamma, theta_value};
}

} // namespace quant::pde
