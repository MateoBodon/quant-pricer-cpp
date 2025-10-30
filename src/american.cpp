#include "quant/american.hpp"
#include "quant/grid_utils.hpp"

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

using quant::grid_utils::OperatorWorkspace;
using quant::grid_utils::SpaceGrid;

SpaceGrid make_space_grid(const PsorParams& params) {
    if (params.grid.num_space < 3) {
        throw std::invalid_argument("PSOR grid requires at least 3 spatial nodes");
    }
    quant::grid_utils::StretchedGridParams gp{};
    gp.nodes = params.grid.num_space;
    gp.stretch = params.stretch;
    gp.log_space = params.log_space;
    gp.anchor = params.base.strike;
    if (!params.log_space) {
        gp.lower = 0.0;
        gp.upper = std::max(params.base.spot * params.grid.s_max_mult,
                            params.base.strike * params.grid.s_max_mult);
        if (!(gp.upper > gp.lower)) {
            throw std::invalid_argument("Invalid S_max for American grid");
        }
    } else {
        gp.lower = std::max(1e-8, params.base.spot / params.grid.s_max_mult);
        gp.upper = params.base.spot * params.grid.s_max_mult;
        if (!(gp.upper > gp.lower)) {
            throw std::invalid_argument("Invalid log-space bounds for American grid");
        }
    }
    return quant::grid_utils::build_space_grid(gp);
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
    if (static_cast<int>(grid.spot.size()) != M) {
        throw std::invalid_argument("grid size mismatch for PSOR operator");
    }

    quant::grid_utils::DiffusionCoefficients coeffs{
        params.base.vol,
        params.base.rate,
        params.base.dividend,
        params.log_space
    };
    quant::grid_utils::assemble_operator(grid, coeffs, dt, theta, V_curr, op);

    quant::grid_utils::PayoffBoundaryParams boundary_params{
        params.base.type,
        params.base.strike,
        params.base.rate,
        params.base.dividend,
        tau_next
    };

    const double lower_bc = quant::grid_utils::dirichlet_boundary(boundary_params, grid.spot.front(), true);
    const double upper_bc = quant::grid_utils::dirichlet_boundary(boundary_params, grid.spot.back(), false);

    op.diag[0] = 1.0;
    op.rhs[0] = lower_bc;
    if (M > 1) {
        op.upper[0] = 0.0;
    }

    if (M > 1) {
        if (params.upper_boundary == quant::pde::PdeParams::UpperBoundary::Dirichlet || !params.log_space) {
            op.diag[M - 1] = 1.0;
            op.lower[M - 2] = 0.0;
            op.rhs[M - 1] = upper_bc;
        } else {
            const double dx = grid.coordinate.back() - grid.coordinate[static_cast<std::size_t>(M - 2)];
            const double df_q = std::exp(-params.base.dividend * tau_next);
            double dVdS = (params.base.type == OptionType::Call) ? df_q : 0.0;
            double dUdx = grid.spot.back() * dVdS;
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

struct RegressionSolution {
    std::array<double, 4> beta{};
    double condition_number{0.0};
    bool success{false};
};

namespace {

std::array<double, 4> mat_vec(const double mat[4][4], const std::array<double, 4>& v) {
    std::array<double, 4> out{};
    for (int i = 0; i < 4; ++i) {
        double sum = 0.0;
        for (int j = 0; j < 4; ++j) {
            sum += mat[i][j] * v[j];
        }
        out[i] = sum;
    }
    return out;
}

double dot(const std::array<double, 4>& a, const std::array<double, 4>& b) {
    double sum = 0.0;
    for (int i = 0; i < 4; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}

double normalize(std::array<double, 4>& v) {
    double norm_sq = dot(v, v);
    double norm = std::sqrt(norm_sq);
    if (norm > 0.0) {
        for (double& x : v) {
            x /= norm;
        }
    }
    return norm;
}

bool solve_linear_system(const double mat_in[4][4], const double rhs_in[4], double sol_out[4]) {
    double a[4][5];
    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 4; ++j) {
            a[i][j] = mat_in[i][j];
        }
        a[i][4] = rhs_in[i];
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
            return false;
        }
        if (pivot != i) {
            for (int c = i; c < 5; ++c) {
                std::swap(a[i][c], a[pivot][c]);
            }
        }
        const double pivot_inv = 1.0 / a[i][i];
        for (int c = i; c < 5; ++c) {
            a[i][c] *= pivot_inv;
        }
        for (int r = 0; r < 4; ++r) {
            if (r == i) {
                continue;
            }
            const double factor = a[r][i];
            for (int c = i; c < 5; ++c) {
                a[r][c] -= factor * a[i][c];
            }
        }
    }
    for (int i = 0; i < 4; ++i) {
        sol_out[i] = a[i][4];
    }
    return true;
}

double rayleigh_quotient(const double mat[4][4], const std::array<double, 4>& v) {
    auto Av = mat_vec(mat, v);
    return dot(v, Av);
}

double largest_eigenvalue(const double mat[4][4]) {
    std::array<double, 4> v{1.0, 0.3, -0.2, 0.1};
    normalize(v);
    double lambda = 0.0;
    for (int iter = 0; iter < 30; ++iter) {
        auto w = mat_vec(mat, v);
        double norm = normalize(w);
        if (norm < 1e-15) {
            return 0.0;
        }
        const double next_lambda = rayleigh_quotient(mat, w);
        if (std::abs(next_lambda - lambda) < 1e-10) {
            lambda = next_lambda;
            break;
        }
        lambda = next_lambda;
        v = w;
    }
    return lambda;
}

double smallest_eigenvalue(const double mat[4][4]) {
    std::array<double, 4> v{0.5, -0.4, 0.3, 0.2};
    normalize(v);
    double lambda = 0.0;
    for (int iter = 0; iter < 30; ++iter) {
        double rhs[4]{v[0], v[1], v[2], v[3]};
        double y_arr[4]{};
        if (!solve_linear_system(mat, rhs, y_arr)) {
            return 0.0;
        }
        std::array<double, 4> y{y_arr[0], y_arr[1], y_arr[2], y_arr[3]};
        double norm = normalize(y);
        if (norm < 1e-15) {
            return 0.0;
        }
        const double next_lambda = rayleigh_quotient(mat, y);
        if (std::abs(next_lambda - lambda) < 1e-10) {
            lambda = next_lambda;
            break;
        }
        lambda = next_lambda;
        v = y;
    }
    return lambda;
}

double compute_condition_number(const double mat_in[4][4]) {
    double mat[4][4];
    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 4; ++j) {
            mat[i][j] = mat_in[i][j];
        }
    }
    const double max_eval = largest_eigenvalue(mat);
    if (max_eval <= 0.0) {
        return std::numeric_limits<double>::infinity();
    }
    const double min_eval = smallest_eigenvalue(mat);
    if (min_eval <= 0.0) {
        return std::numeric_limits<double>::infinity();
    }
    return max_eval / min_eval;
}

RegressionSolution solve_normal_equations(NormalEquations eq, double ridge_lambda) {
    eq.symmetrize();
    for (int i = 0; i < 4; ++i) {
        eq.ata[i][i] += ridge_lambda;
    }

    RegressionSolution result{};
    result.condition_number = compute_condition_number(eq.ata);

    double rhs[4];
    for (int i = 0; i < 4; ++i) {
        rhs[i] = eq.atb[i];
    }

    double beta_raw[4]{};
    if (solve_linear_system(eq.ata, rhs, beta_raw)) {
        for (int i = 0; i < 4; ++i) {
            result.beta[i] = beta_raw[i];
        }
        result.success = true;
    } else {
        result.success = false;
    }
    return result;
}

} // namespace

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
    SpaceGrid grid = make_space_grid(params);
    const int M = params.grid.num_space;
    std::vector<double> V(M);
    std::vector<double> intrinsic(M);
    for (int i = 0; i < M; ++i) {
        intrinsic[i] = intrinsic_value(params.base.type, params.base.strike, grid.spot[i]);
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

    double price = interpolate_price(grid.spot, V, params.base.spot);
    return PsorResult{price, total_iters, final_residual};
}

LsmcResult price_lsmc(const LsmcParams& params) {
    if (params.num_paths == 0 || params.num_steps <= 0) {
        throw std::invalid_argument("LSMC requires positive paths and time steps");
    }
    if (params.ridge_lambda < 0.0) {
        throw std::invalid_argument("LSMC ridge lambda must be non-negative");
    }
    if (params.itm_moneyness_eps < 0.0) {
        throw std::invalid_argument("LSMC moneyness band must be non-negative");
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
    if (path_count == 0) {
        throw std::invalid_argument("LSMC requires at least one simulated path");
    }

    const std::size_t shock_cols = use_antithetic ? base_paths : path_count;
    std::vector<double> spot_curr(path_count, params.base.spot);
    std::vector<double> spot_next(path_count, params.base.spot);
    std::vector<float> shocks(steps * shock_cols, 0.0f);

    pcg64 rng(params.seed);
    std::normal_distribution<double> normal(0.0, 1.0);

    for (std::size_t step = 0; step < steps; ++step) {
        float* row = shocks.data() + step * shock_cols;
        if (!use_antithetic) {
            for (std::size_t i = 0; i < path_count; ++i) {
                double z = normal(rng);
                row[i] = static_cast<float>(z);
                spot_next[i] = spot_curr[i] * std::exp(drift + vol_step * z);
            }
        } else {
            for (std::size_t pair = 0; pair < base_paths; ++pair) {
                double z = normal(rng);
                row[pair] = static_cast<float>(z);
                std::size_t idx = pair * 2;
                const double mult_plus = std::exp(drift + vol_step * z);
                const double mult_minus = std::exp(drift - vol_step * z);
                spot_next[idx] = spot_curr[idx] * mult_plus;
                spot_next[idx + 1] = spot_curr[idx + 1] * mult_minus;
            }
        }
        spot_curr.swap(spot_next);
    }

    std::vector<double> spot_tp1 = spot_curr;
    std::vector<double> spot_t(path_count, params.base.spot);

    std::vector<double> cashflow(path_count);
    std::vector<char> exercised(path_count, 0);

    for (std::size_t i = 0; i < path_count; ++i) {
        cashflow[i] = intrinsic_value(params.base.type, params.base.strike, spot_tp1[i]);
    }

    std::vector<std::size_t> itm_counts_rev;
    std::vector<std::size_t> reg_counts_rev;
    std::vector<double> cond_rev;
    itm_counts_rev.reserve(steps > 1 ? steps - 1 : 0);
    reg_counts_rev.reserve(itm_counts_rev.capacity());
    cond_rev.reserve(itm_counts_rev.capacity());

    for (int step = static_cast<int>(steps) - 1; step >= 1; --step) {
#ifdef _OPENMP
#pragma omp parallel for
#endif
        for (std::size_t i = 0; i < path_count; ++i) {
            cashflow[i] *= disc;
        }

        float* row = shocks.data() + static_cast<std::size_t>(step) * shock_cols;
        if (!use_antithetic) {
            for (std::size_t i = 0; i < path_count; ++i) {
                double z = static_cast<double>(row[i]);
                const double step_mult = std::exp(drift + vol_step * z);
                spot_t[i] = spot_tp1[i] / step_mult;
            }
        } else {
            for (std::size_t pair = 0; pair < base_paths; ++pair) {
                double z = static_cast<double>(row[pair]);
                const double mult_plus = std::exp(drift + vol_step * z);
                const double mult_minus = std::exp(drift - vol_step * z);
                std::size_t idx = pair * 2;
                spot_t[idx] = spot_tp1[idx] / mult_plus;
                spot_t[idx + 1] = spot_tp1[idx + 1] / mult_minus;
            }
        }

        NormalEquations eq;
        std::size_t regression_samples = 0;
        std::size_t itm_count = 0;

        for (std::size_t i = 0; i < path_count; ++i) {
            if (exercised[i]) {
                continue;
            }
            const double S = spot_t[i];
            const double intrinsic = intrinsic_value(params.base.type, params.base.strike, S);
            const double moneyness = S / params.base.strike - 1.0;
            if (intrinsic > 0.0) {
                ++itm_count;
            }
            if (intrinsic > 0.0 || std::abs(moneyness) <= params.itm_moneyness_eps) {
                eq.add(polynomial_features(moneyness), cashflow[i]);
                ++regression_samples;
            }
        }

        RegressionSolution solution{};
        bool allow_exercise = itm_count >= params.min_itm && regression_samples >= 4;
        if (allow_exercise) {
            solution = solve_normal_equations(eq, params.ridge_lambda);
            if (!solution.success || !std::isfinite(solution.condition_number) || solution.condition_number > 1.0e12) {
                allow_exercise = false;
            }
        }

        cond_rev.push_back(solution.success ? solution.condition_number : std::numeric_limits<double>::infinity());
        itm_counts_rev.push_back(itm_count);
        reg_counts_rev.push_back(regression_samples);

        if (allow_exercise && solution.success) {
            const auto& beta = solution.beta;
#ifdef _OPENMP
#pragma omp parallel for
#endif
            for (std::size_t i = 0; i < path_count; ++i) {
                if (exercised[i]) {
                    continue;
                }
                const double S = spot_t[i];
                const double intrinsic = intrinsic_value(params.base.type, params.base.strike, S);
                if (intrinsic <= 0.0) {
                    continue;
                }
                const double x = S / params.base.strike - 1.0;
                const double cont = beta[0] + beta[1] * x + beta[2] * x * x + beta[3] * x * x * x;
                if (cont <= intrinsic) {
                    cashflow[i] = intrinsic;
                    exercised[i] = 1;
                }
            }
        }

        spot_tp1.swap(spot_t);
    }

    double sum = 0.0;
    double sumsq = 0.0;
    for (std::size_t i = 0; i < path_count; ++i) {
        const double pv = disc * cashflow[i];
        sum += pv;
        sumsq += pv * pv;
    }
    const double mean = sum / static_cast<double>(path_count);
    double variance = (sumsq / static_cast<double>(path_count)) - mean * mean;
    variance = std::max(0.0, variance);
    const double se = std::sqrt(variance / static_cast<double>(path_count));

    std::reverse(itm_counts_rev.begin(), itm_counts_rev.end());
    std::reverse(reg_counts_rev.begin(), reg_counts_rev.end());
    std::reverse(cond_rev.begin(), cond_rev.end());

    LsmcDiagnostics diagnostics{std::move(itm_counts_rev), std::move(reg_counts_rev), std::move(cond_rev)};
    return LsmcResult{mean, se, std::move(diagnostics)};
}

} // namespace quant::american

namespace quant::american {

Greeks greeks_psor_bump(PsorParams params, double rel_bump) {
    const double S0 = params.base.spot;
    const double h = std::max(1e-6, std::abs(rel_bump) * std::max(1.0, S0));
    params.base.spot = S0 + h;
    const double up = price_psor(params).price;
    params.base.spot = S0 - h;
    const double dn = price_psor(params).price;
    params.base.spot = S0;
    const double mid = price_psor(params).price;
    const double delta = (up - dn) / (2.0 * h);
    const double gamma = (up - 2.0 * mid + dn) / (h * h);
    return Greeks{delta, gamma};
}

} // namespace quant::american
