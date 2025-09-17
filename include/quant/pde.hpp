/// Finite-difference PDE pricer (Crank–Nicolson) for European options
#pragma once

#include <vector>

namespace quant::pde {

/// Grid specification for PDE solver
struct GridSpec {
    int num_space;      // number of spatial nodes (including boundaries)
    int num_time;       // number of time steps
    double s_max_mult;  // S_max multiple of spot for upper boundary
};

/// Solve tridiagonal system Ax = d with Thomas algorithm.
/// a: sub-diagonal (size n-1), b: main diagonal (size n), c: super-diagonal (size n-1)
/// d: RHS (size n). Returns x of size n.
std::vector<double> solve_tridiagonal(const std::vector<double>& a,
                                      const std::vector<double>& b,
                                      const std::vector<double>& c,
                                      const std::vector<double>& d);

enum class OptionType { Call, Put };

/// PDE pricing parameters and grid configuration.
struct PdeParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    OptionType type;
    GridSpec grid;
    /// Use log-space grid x = ln(S) for improved stability near boundaries
    bool log_space{false};
    /// Upper boundary condition type
    enum class UpperBoundary { Dirichlet, Neumann };
    UpperBoundary upper_boundary{UpperBoundary::Dirichlet};
};

/// Price European option via Crank–Nicolson (S-space or log-space).
/// Boundary conditions: Dirichlet at S=0, Dirichlet or Neumann at Smax.
double price_crank_nicolson(const PdeParams& p);

} // namespace quant::pde


