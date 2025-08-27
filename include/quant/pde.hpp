// Finite-difference PDE pricer (Crank–Nicolson) for European options
#pragma once

#include <vector>

namespace quant::pde {

struct GridSpec {
    int num_space;      // number of spatial nodes (including boundaries)
    int num_time;       // number of time steps
    double s_max_mult;  // S_max multiple of spot for upper boundary
};

// Solve tridiagonal system Ax = d with Thomas algorithm.
// a: sub-diagonal (size n-1), b: main diagonal (size n), c: super-diagonal (size n-1)
// d: RHS (size n). Returns x of size n.
std::vector<double> solve_tridiagonal(const std::vector<double>& a,
                                      const std::vector<double>& b,
                                      const std::vector<double>& c,
                                      const std::vector<double>& d);

enum class OptionType { Call, Put };

struct PdeParams {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    OptionType type;
    GridSpec grid;
};

// Price European option via Crank–Nicolson in log-space
double price_crank_nicolson(const PdeParams& p);

} // namespace quant::pde


