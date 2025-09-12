#include "quant/pde.hpp"
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace quant::pde {

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
    if (std::abs(beta) < 1e-14) throw std::runtime_error("Singular tridiagonal matrix");
    cp[0] = c[0] / beta;
    dp[0] = d[0] / beta;
    for (int i = 1; i < n - 1; ++i) {
        beta = b[i] - a[i - 1] * cp[i - 1];
        if (std::abs(beta) < 1e-14) throw std::runtime_error("Near-singular tridiagonal (pivot)");
        cp[i] = c[i] / beta;
        dp[i] = (d[i] - a[i - 1] * dp[i - 1]) / beta;
    }
    beta = b[n - 1] - a[n - 2] * cp[n - 2];
    if (std::abs(beta) < 1e-14) throw std::runtime_error("Near-singular tridiagonal (last pivot)");
    dp[n - 1] = (d[n - 1] - a[n - 2] * dp[n - 2]) / beta;

    x[n - 1] = dp[n - 1];
    for (int i = n - 2; i >= 0; --i) {
        x[i] = dp[i] - cp[i] * x[i + 1];
    }
    return x;
}

double price_crank_nicolson(const PdeParams& p) {
    const int M = p.grid.num_space;   // space nodes
    const int N = p.grid.num_time;    // time steps
    if (M < 3 || N < 1) throw std::invalid_argument("Grid too small");

    const double S0 = p.spot;
    const double K  = p.strike;
    const double r  = p.rate;
    const double q  = p.dividend;
    const double s  = p.vol;
    const double T  = p.time;
    const double dt = T / N;

    std::vector<double> a(M - 1), b(M), c(M - 1);
    std::vector<double> d(M);
    std::vector<double> V(M);

    if (!p.log_space) {
        // S-space grid
        const double S_max = p.grid.s_max_mult * S0;
        const double dS = S_max / (M - 1);
        std::vector<double> S(M);
        for (int i = 0; i < M; ++i) S[i] = i * dS;
        // payoff
        if (p.type == OptionType::Call) {
            for (int i = 0; i < M; ++i) V[i] = std::max(0.0, S[i] - K);
        } else {
            for (int i = 0; i < M; ++i) V[i] = std::max(0.0, K - S[i]);
        }
        for (int n = N; n-- > 0;) {
            const double t = n * dt;
            const double bc_lower = (p.type == OptionType::Call) ? 0.0 : (K * std::exp(-r * (T - t)));
            const double bc_upper = (p.type == OptionType::Call)
                ? (S_max * std::exp(-q * (T - t)) - K * std::exp(-r * (T - t)))
                : 0.0;
            for (int i = 1; i < M - 1; ++i) {
                const double Si = S[i];
                const double alpha = 0.25 * dt * (s * s * Si * Si / (dS * dS));
                const double beta  = 0.25 * dt * ((r - q) * Si / dS);
                a[i - 1] = -alpha + beta;
                b[i]     = 1.0 + 2.0 * alpha + 0.5 * dt * r;
                c[i]     = -alpha - beta;
                const double a_r = alpha - beta;
                const double b_r = 1.0 - 2.0 * alpha - 0.5 * dt * r;
                const double c_r = alpha + beta;
                d[i] = a_r * V[i - 1] + b_r * V[i] + c_r * V[i + 1];
            }
            b[0] = 1.0; d[0] = bc_lower; c[0] = 0.0;
            b[M - 1] = 1.0; d[M - 1] = bc_upper; a[M - 2] = 0.0;
            V = solve_tridiagonal(a, b, c, d);
        }
        // interpolate at S0
        const double idx = S0 / dS;
        const int i0 = static_cast<int>(std::floor(idx));
        if (i0 <= 0) return V[0];
        if (i0 >= M - 1) return V[M - 1];
        const double w = idx - i0;
        return (1.0 - w) * V[i0] + w * V[i0 + 1];
    } else {
        // Log-space grid x = ln(S)
        const double S_max = p.grid.s_max_mult * S0;
        const double S_min = std::max(1e-8, S0 / p.grid.s_max_mult);
        const double x_min = std::log(S_min);
        const double x_max = std::log(S_max);
        const double dx = (x_max - x_min) / (M - 1);
        std::vector<double> X(M);
        std::vector<double> S(M);
        for (int i = 0; i < M; ++i) { X[i] = x_min + i * dx; S[i] = std::exp(X[i]); }
        if (p.type == OptionType::Call) {
            for (int i = 0; i < M; ++i) V[i] = std::max(0.0, S[i] - K);
        } else {
            for (int i = 0; i < M; ++i) V[i] = std::max(0.0, K - S[i]);
        }
        const double a_coef = 0.5 * s * s; // for U_xx
        const double b_coef = (r - q - 0.5 * s * s); // for U_x
        const double c_coef = -r; // for U
        for (int n = N; n-- > 0;) {
            const double t = n * dt;
            const double tau = (T - t);
            const double bc_lower = (p.type == OptionType::Call) ? 0.0 : (K * std::exp(-r * tau));
            const double bc_upper_dir = (p.type == OptionType::Call)
                ? (S.back() * std::exp(-q * tau) - K * std::exp(-r * tau))
                : 0.0;
            const double alpha = 0.25 * dt * (2.0 * a_coef / (dx * dx)); // since a_coef multiplies U_xx with factor a
            const double beta  = 0.25 * dt * (b_coef / dx);
            for (int i = 1; i < M - 1; ++i) {
                a[i - 1] = -alpha + beta;
                b[i]     = 1.0 + 2.0 * alpha - 0.5 * dt * c_coef; // c_coef=-r
                c[i]     = -alpha - beta;
                const double a_r = alpha - beta;
                const double b_r = 1.0 - 2.0 * alpha + 0.5 * dt * c_coef;
                const double c_r = alpha + beta;
                d[i] = a_r * V[i - 1] + b_r * V[i] + c_r * V[i + 1];
            }
            // Lower boundary Dirichlet
            b[0] = 1.0; d[0] = bc_lower; c[0] = 0.0;
            // Upper boundary: Dirichlet or Neumann
            if (p.upper_boundary == PdeParams::UpperBoundary::Dirichlet) {
                b[M - 1] = 1.0; d[M - 1] = bc_upper_dir; a[M - 2] = 0.0;
            } else {
                // Neumann: dV/dS(Smax, t) = e^{-q tau} for call, ~0 for put.
                double dVdS = (p.type == OptionType::Call) ? std::exp(-q * tau) : 0.0;
                double dUdx = S.back() * dVdS; // since dV/dS = (1/S) dU/dx
                // Enforce U_{M-1} - U_{M-2} = dx * dUdx
                a[M - 2] = -1.0;
                b[M - 1] = 1.0;
                d[M - 1] = dx * dUdx;
            }
            V = solve_tridiagonal(a, b, c, d);
        }
        // Interpolate at x0
        const double x0 = std::log(S0);
        const double idx = (x0 - x_min) / dx;
        const int i0 = static_cast<int>(std::floor(idx));
        if (i0 <= 0) return V[0];
        if (i0 >= M - 1) return V[M - 1];
        const double w = idx - i0;
        return (1.0 - w) * V[i0] + w * V[i0 + 1];
    }
}

} // namespace quant::pde


