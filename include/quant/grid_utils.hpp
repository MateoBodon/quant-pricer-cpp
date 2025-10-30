#pragma once

#include <vector>

#include "quant/barrier.hpp"

namespace quant::grid_utils {

struct SpaceGrid {
    std::vector<double> coordinate; // Differencing coordinate (S or log S)
    std::vector<double> spot;       // Underlying spot values corresponding to coordinate nodes
};

// Hyperbolic-tangent stretch map with anchor in [0,1].
double stretch_map(double xi, double anchor, double stretch);

struct StretchedGridParams {
    int nodes;           // number of grid points (>= 1)
    double lower;        // lower bound in spot space (S-space)
    double upper;        // upper bound in spot space (S-space)
    double anchor;       // anchor spot value to focus grid density (typically strike)
    double stretch;      // tanh stretch parameter (0 => uniform)
    bool log_space;      // when true, coordinate is ln(S)
};

SpaceGrid build_space_grid(const StretchedGridParams& params);

struct DiffusionCoefficients {
    double sigma;    // instantaneous volatility
    double rate;     // risk-free rate
    double dividend; // dividend yield
    bool log_space;  // match grid coordinate system
};

struct OperatorWorkspace {
    std::vector<double> lower;
    std::vector<double> diag;
    std::vector<double> upper;
    std::vector<double> rhs;
};

// Assemble interior tridiagonal coefficients for a backward Euler/Crank-Nicolson step.
// "theta" = 1 corresponds to fully implicit, 0.5 => Crank-Nicolson.
void assemble_operator(const SpaceGrid& grid,
                       const DiffusionCoefficients& coeffs,
                       double dt,
                       double theta,
                       const std::vector<double>& v_curr,
                       OperatorWorkspace& op);

struct PayoffBoundaryParams {
    ::quant::OptionType type;
    double strike;
    double rate;
    double dividend;
    double tau; // remaining time to maturity (years)
};

double dirichlet_boundary(const PayoffBoundaryParams& params,
                          double spot,
                          bool is_lower);

} // namespace quant::grid_utils
