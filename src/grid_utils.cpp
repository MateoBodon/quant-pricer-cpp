#include "quant/grid_utils.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace quant::grid_utils {

double stretch_map(double xi, double anchor, double stretch) {
    if (stretch <= 0.0) {
        return xi;
    }
    const double eps = 1e-10;
    anchor = std::clamp(anchor, eps, 1.0 - eps);
    if (xi <= anchor) {
        const double ratio = xi / anchor;
        return anchor * std::tanh(stretch * ratio) / std::tanh(stretch);
    }
    const double ratio = (1.0 - xi) / (1.0 - anchor);
    return 1.0 - (1.0 - anchor) * std::tanh(stretch * ratio) / std::tanh(stretch);
}

SpaceGrid build_space_grid(const StretchedGridParams& params) {
    if (params.nodes < 1) {
        throw std::invalid_argument("grid requires at least one node");
    }
    if (!(params.upper > params.lower)) {
        throw std::invalid_argument("grid upper bound must exceed lower bound");
    }
    if (params.log_space && params.lower <= 0.0) {
        throw std::invalid_argument("log-space grid requires positive lower bound");
    }

    SpaceGrid grid;
    grid.coordinate.resize(params.nodes);
    grid.spot.resize(params.nodes);

    const double anchor_clamped = std::clamp(params.anchor, params.lower, params.upper);
    const double denom = params.upper - params.lower;
    const double xi_anchor = (params.nodes == 1)
                                 ? 0.0
                                 : std::clamp((anchor_clamped - params.lower) / denom, 0.0, 1.0);

    if (!params.log_space) {
        for (int i = 0; i < params.nodes; ++i) {
            const double xi = (params.nodes == 1)
                                  ? 0.0
                                  : static_cast<double>(i) / static_cast<double>(params.nodes - 1);
            const double mapped = stretch_map(xi, xi_anchor, params.stretch);
            const double S = params.lower + (params.upper - params.lower) * mapped;
            grid.coordinate[static_cast<std::size_t>(i)] = S;
            grid.spot[static_cast<std::size_t>(i)] = S;
        }
    } else {
        const double x_lower = std::log(params.lower);
        const double x_upper = std::log(params.upper);
        const double denom_x = x_upper - x_lower;
        const double xi0 = (params.nodes == 1)
                               ? 0.0
                               : std::clamp((std::log(anchor_clamped) - x_lower) / denom_x, 0.0, 1.0);
        for (int i = 0; i < params.nodes; ++i) {
            const double xi = (params.nodes == 1)
                                  ? 0.0
                                  : static_cast<double>(i) / static_cast<double>(params.nodes - 1);
            const double mapped = stretch_map(xi, xi0, params.stretch);
            const double x = x_lower + (x_upper - x_lower) * mapped;
            const double S = std::exp(x);
            grid.coordinate[static_cast<std::size_t>(i)] = x;
            grid.spot[static_cast<std::size_t>(i)] = S;
        }
    }
    return grid;
}

void assemble_operator(const SpaceGrid& grid,
                       const DiffusionCoefficients& coeffs,
                       double dt,
                       double theta,
                       const std::vector<double>& v_curr,
                       OperatorWorkspace& op) {
    const std::size_t M = grid.spot.size();
    if (grid.coordinate.size() != M) {
        throw std::invalid_argument("grid coordinate/spot size mismatch");
    }
    if (v_curr.size() != M) {
        throw std::invalid_argument("state vector size mismatch");
    }
    if (M < 3) {
        throw std::invalid_argument("grid requires at least three nodes for operator assembly");
    }

    op.lower.assign(M > 1 ? M - 1 : 0, 0.0);
    op.diag.assign(M, 0.0);
    op.upper.assign(M > 1 ? M - 1 : 0, 0.0);
    op.rhs.assign(M, 0.0);

    const double sigma2 = coeffs.sigma * coeffs.sigma;
    const double r = coeffs.rate;
    const double q = coeffs.dividend;

    for (std::size_t i = 1; i + 1 < M; ++i) {
        const double h_minus = grid.coordinate[i] - grid.coordinate[i - 1];
        const double h_plus = grid.coordinate[i + 1] - grid.coordinate[i];
        if (!(h_minus > 0.0 && h_plus > 0.0)) {
            throw std::runtime_error("non-increasing grid detected");
        }
        const double denom = h_minus + h_plus;

        double a_i;
        double b_i;
        double c_i = -r;
        if (!coeffs.log_space) {
            const double S_i = grid.spot[i];
            a_i = 0.5 * sigma2 * S_i * S_i;
            b_i = (r - q) * S_i;
        } else {
            a_i = 0.5 * sigma2;
            b_i = (r - q - 0.5 * sigma2);
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

        op.rhs[i] = v_curr[i] + (1.0 - theta) * dt *
            (L_im1 * v_curr[i - 1] + L_i * v_curr[i] + L_ip1 * v_curr[i + 1]);
    }
}

double dirichlet_boundary(const PayoffBoundaryParams& params,
                          double spot,
                          bool is_lower) {
    const double df_r = std::exp(-params.rate * params.tau);
    const double df_q = std::exp(-params.dividend * params.tau);
    switch (params.type) {
        case ::quant::OptionType::Call:
            if (is_lower) {
                return 0.0;
            }
            return spot * df_q - params.strike * df_r;
        case ::quant::OptionType::Put:
            if (is_lower) {
                return params.strike * df_r - spot * df_q;
            }
            return 0.0;
    }
    throw std::logic_error("unknown option type");
}

} // namespace quant::grid_utils
