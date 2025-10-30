#include "quant/pde.hpp"

#include "quant/black_scholes.hpp"
#include "quant/grid_utils.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace quant::pde {

namespace {

using SpaceGrid = quant::grid_utils::SpaceGrid;
using OperatorWorkspace = quant::grid_utils::OperatorWorkspace;

SpaceGrid make_space_grid(const PdeParams& p) {
    if (p.grid.num_space < 3) {
        throw std::invalid_argument("PDE grid requires at least 3 spatial nodes");
    }
    quant::grid_utils::StretchedGridParams gp{};
    gp.nodes = p.grid.num_space;
    gp.stretch = p.grid.stretch;
    gp.log_space = p.log_space;
    gp.anchor = p.strike;
    if (!p.log_space) {
        gp.lower = 0.0;
        gp.upper = std::max(p.spot * p.grid.s_max_mult, p.strike * p.grid.s_max_mult);
        if (!(gp.upper > gp.lower)) {
            throw std::invalid_argument("Upper bound must exceed lower bound in S-grid");
        }
    } else {
        gp.lower = std::max(1e-8, p.spot / p.grid.s_max_mult);
        gp.upper = p.spot * p.grid.s_max_mult;
        if (!(gp.upper > gp.lower)) {
            throw std::invalid_argument("Invalid log-space bounds (check s_max_mult)");
        }
    }
    return quant::grid_utils::build_space_grid(gp);
}

void build_system(const PdeParams& p,
                  const SpaceGrid& grid,
                  const std::vector<double>& V_curr,
                  double dt,
                  double theta,
                  double tau_next,
                  OperatorWorkspace& op) {
    const int M = p.grid.num_space;
    if (static_cast<int>(grid.spot.size()) != M) {
        throw std::invalid_argument("grid size mismatch for PDE operator");
    }

    const double t_mid = std::clamp(p.time - tau_next - 0.5 * dt, 0.0, p.time);
    const double r = p.rate_schedule ? p.rate_schedule->value(t_mid) : p.rate;
    const double q = p.dividend_schedule ? p.dividend_schedule->value(t_mid) : p.dividend;
    const double sigma = p.vol_schedule ? p.vol_schedule->value(t_mid) : p.vol;

    quant::grid_utils::DiffusionCoefficients coeffs{sigma, r, q, p.log_space};
    quant::grid_utils::assemble_operator(grid, coeffs, dt, theta, V_curr, op);

    const double tau = tau_next;
    const auto boundary = [&](bool lower) {
        quant::grid_utils::PayoffBoundaryParams params{
            p.type, p.strike, r, q, tau
        };
        return quant::grid_utils::dirichlet_boundary(params,
                                                     lower ? grid.spot.front() : grid.spot.back(),
                                                     lower);
    };

    const double lower_bc = boundary(true);
    const double upper_bc = boundary(false);

    op.diag[0] = 1.0;
    op.rhs[0] = lower_bc;
    if (M > 1) {
        op.upper[0] = 0.0;
    }

    if (M > 1) {
        if (p.upper_boundary == PdeParams::UpperBoundary::Dirichlet || !p.log_space) {
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = 0.0;
            op.rhs[M - 1] = upper_bc;
        } else {
            const double dx = grid.coordinate.back() - grid.coordinate[static_cast<std::size_t>(M - 2)];
            const double dVdS = (p.type == OptionType::Call) ? std::exp(-q * tau) : 0.0;
            const double dUdx = grid.spot.back() * dVdS;
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

    SpaceGrid grid = make_space_grid(p);

    std::vector<double> V(grid.spot.size());
    for (std::size_t i = 0; i < grid.spot.size(); ++i) {
        if (p.type == OptionType::Call) {
            V[i] = std::max(0.0, grid.spot[i] - p.strike);
        } else {
            V[i] = std::max(0.0, p.strike - grid.spot[i]);
        }
    }

    OperatorWorkspace op;
    const int M = p.grid.num_space;
    const int N = p.grid.num_time;
    const double dt = p.time / static_cast<double>(N);

    std::vector<double> V_prev_for_theta;
    bool capture_theta = p.compute_theta && N > 0;

    int start_step = 0;
    double time_elapsed = 0.0;

    if (p.use_rannacher && N > 0) {
        double dt_half = dt / 2.0;
        int half_iters = std::min(2, std::max(0, N) * 2);
        for (int k = 0; k < half_iters; ++k) {
            double tau_next = p.time - (time_elapsed + dt_half);
            build_system(p, grid, V, dt_half, 1.0, tau_next, op);
            V = solve_tridiagonal(op.lower, op.diag, op.upper, op.rhs);
            time_elapsed += dt_half;
        }
        start_step = std::min(N, 1);
    }

    if (capture_theta && start_step == N) {
        V_prev_for_theta = V;
    }

    for (int step = start_step; step < N; ++step) {
        const double tau_next = p.time - (time_elapsed + dt);
        if (capture_theta && step == N - 1) {
            V_prev_for_theta = V;
        }
        build_system(p, grid, V, dt, 0.5, tau_next, op);
        V = solve_tridiagonal(op.lower, op.diag, op.upper, op.rhs);
        time_elapsed += dt;
    }

    InterpResult interp = interpolate_greeks(grid.spot, V, p.spot);

    std::optional<double> theta_value;
    if (p.compute_theta && N > 0) {
        double prev_price = interpolate_greeks(grid.spot, V_prev_for_theta, p.spot).value;
        theta_value = (prev_price - interp.value) / dt;
    }

    return PdeResult{interp.value, interp.delta, interp.gamma, theta_value};
}

} // namespace quant::pde
