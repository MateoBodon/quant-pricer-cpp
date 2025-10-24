#include "quant/pde_barrier.hpp"

#include "quant/black_scholes.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace quant::pde {

namespace {

struct GridResult {
    std::vector<double> S;
    std::vector<double> V;
    double x_min;
    double dx;
};

GridResult solve_knockout_grid(const BarrierPdeParams& params, ::quant::OptionType opt) {
    const int M = params.grid.num_space;
    const int N = params.grid.num_time;
    if (M < 3 || N < 1) {
        throw std::invalid_argument("Grid too small for barrier PDE");
    }
    if (!params.log_space) {
        throw std::invalid_argument("Barrier PDE currently requires log-space grid");
    }

    const bool up_barrier = params.barrier.type == BarrierType::UpOut;
    const double S0 = params.spot;
    const double B = params.barrier.B;
    if (up_barrier) {
        if (S0 >= B) {
            throw std::invalid_argument("Spot already above up-and-out barrier");
        }
    } else {
        if (S0 <= B) {
            throw std::invalid_argument("Spot already below down-and-out barrier");
        }
    }

    const double r = params.rate;
    const double q = params.dividend;
    const double sigma = params.vol;
    const double T = params.time;
    const double dt = T / N;
    const double sigma2 = sigma * sigma;

    const double S_max = params.grid.s_max_mult * S0;
    const double S_min = std::max(1e-8, S0 / params.grid.s_max_mult);

    double S_lower = 0.0;
    double S_upper = 0.0;
    if (up_barrier) {
        S_lower = S_min;
        S_upper = B;
        if (S_lower >= S_upper) {
            throw std::invalid_argument("Up-out grid requires S_min < barrier");
        }
    } else {
        S_lower = B;
        S_upper = S_max;
        if (S_lower >= S_upper) {
            throw std::invalid_argument("Down-out grid requires barrier < S_max");
        }
    }

    const double x_min = std::log(S_lower);
    const double x_max = std::log(S_upper);
    const double dx = (x_max - x_min) / (M - 1);

    std::vector<double> X(M);
    std::vector<double> S(M);
    for (int i = 0; i < M; ++i) {
        X[i] = x_min + i * dx;
        S[i] = std::exp(X[i]);
    }

    std::vector<double> V(M);
    for (int i = 0; i < M; ++i) {
        if (up_barrier && i == M - 1) {
            V[i] = params.barrier.rebate;
        } else if (!up_barrier && i == 0) {
            V[i] = params.barrier.rebate;
        } else {
            const double payoff = (opt == ::quant::OptionType::Call)
                                      ? std::max(0.0, S[i] - params.strike)
                                      : std::max(0.0, params.strike - S[i]);
            V[i] = payoff;
        }
    }

    std::vector<double> a(M - 1), b(M), c(M - 1), d(M);
    const double a_coef = 0.5 * sigma2;
    const double b_coef = (r - q - 0.5 * sigma2);
    const double c_coef = -r;
    const double alpha = 0.25 * dt * (2.0 * a_coef / (dx * dx));
    const double beta = 0.25 * dt * (b_coef / dx);

    for (int n = N; n-- > 0;) {
        const double tau = (T - n * dt);
        double lower_bc = 0.0;
        double upper_bc = 0.0;
        if (up_barrier) {
            // lower boundary at S_min
            if (opt == ::quant::OptionType::Call) {
                lower_bc = 0.0;
            } else {
                lower_bc = params.strike * std::exp(-r * tau) - S_lower * std::exp(-q * tau);
                lower_bc = std::max(lower_bc, 0.0);
            }
            upper_bc = params.barrier.rebate;
        } else {
            lower_bc = params.barrier.rebate;
            if (opt == ::quant::OptionType::Call) {
                upper_bc = S_upper * std::exp(-q * tau) - params.strike * std::exp(-r * tau);
                upper_bc = std::max(upper_bc, 0.0);
            } else {
                upper_bc = 0.0;
            }
        }

        for (int i = 1; i < M - 1; ++i) {
            a[i - 1] = -alpha + beta;
            b[i] = 1.0 + 2.0 * alpha - 0.5 * dt * c_coef;
            c[i] = -alpha - beta;
            const double aa = alpha - beta;
            const double bb = 1.0 - 2.0 * alpha + 0.5 * dt * c_coef;
            const double cc = alpha + beta;
            d[i] = aa * V[i - 1] + bb * V[i] + cc * V[i + 1];
        }

        b[0] = 1.0;
        d[0] = lower_bc;
        c[0] = 0.0;
        b[M - 1] = 1.0;
        d[M - 1] = upper_bc;
        a[M - 2] = 0.0;

        V = solve_tridiagonal(a, b, c, d);
    }
    GridResult out{S, V, x_min, dx};
    return out;
}

} // namespace

double price_barrier_crank_nicolson(const BarrierPdeParams& params,
                                    ::quant::OptionType opt) {
    switch (params.barrier.type) {
        case BarrierType::DownOut:
        case BarrierType::UpOut:
            {
                auto g = solve_knockout_grid(params, opt);
                const double x0 = std::log(params.spot);
                const double idx = (x0 - g.x_min) / g.dx;
                if (idx <= 0.0) return g.V.front();
                if (idx >= static_cast<double>(g.S.size() - 1)) return g.V.back();
                const int i0 = static_cast<int>(std::floor(idx));
                const double w = idx - i0;
                return (1.0 - w) * g.V[i0] + w * g.V[i0 + 1];
            }
        case BarrierType::DownIn:
        case BarrierType::UpIn: {
            BarrierPdeParams parity_params = params;
            parity_params.barrier.type = (params.barrier.type == BarrierType::DownIn)
                                             ? BarrierType::DownOut
                                             : BarrierType::UpOut;
            const double ko_price = price_barrier_crank_nicolson(parity_params, opt);
            const double vanilla = (opt == ::quant::OptionType::Call)
                                       ? ::quant::bs::call_price(params.spot, params.strike, params.rate, params.dividend, params.vol, params.time)
                                       : ::quant::bs::put_price(params.spot, params.strike, params.rate, params.dividend, params.vol, params.time);
            const double rebate_discount = params.barrier.rebate * std::exp(-params.rate * params.time);
            return vanilla + rebate_discount - ko_price;
        }
    }
    throw std::logic_error("Unknown barrier type");
}

BarrierPdeGreeksResult price_barrier_crank_nicolson_greeks(const BarrierPdeParams& params,
                                                           ::quant::OptionType opt) {
    if (params.barrier.type == BarrierType::DownIn || params.barrier.type == BarrierType::UpIn) {
        // Use parity for price; Greeks via small centered bump around spot on KO grid
        auto ko_params = params;
        ko_params.barrier.type = (params.barrier.type == BarrierType::DownIn) ? BarrierType::DownOut : BarrierType::UpOut;
        auto grid = solve_knockout_grid(ko_params, opt);
        const double x0 = std::log(params.spot);
        const double idx = (x0 - grid.x_min) / grid.dx;
        if (idx <= 1.0 || idx >= static_cast<double>(grid.S.size() - 2)) {
            double p = price_barrier_crank_nicolson(params, opt);
            return BarrierPdeGreeksResult{p, 0.0, 0.0};
        }
        int i1 = static_cast<int>(std::floor(idx));
        int i0 = i1 - 1;
        int i2 = i1 + 1;
        double S0 = params.spot;
        double price = price_barrier_crank_nicolson(params, opt);
        double delta = (grid.V[i2] - grid.V[i0]) / (grid.S[i2] - grid.S[i0]);
        double gamma = 2.0 * ( (grid.V[i2] - price) / (grid.S[i2] - S0) - (price - grid.V[i0]) / (S0 - grid.S[i0]) ) / (grid.S[i2] - grid.S[i0]);
        return BarrierPdeGreeksResult{price, delta, gamma};
    }
    // Knock-out case: directly compute on knock-out grid
    auto grid = solve_knockout_grid(params, opt);
    const double x0 = std::log(params.spot);
    const double idx = (x0 - grid.x_min) / grid.dx;
    if (idx <= 1.0 || idx >= static_cast<double>(grid.S.size() - 2)) {
        double p = price_barrier_crank_nicolson(params, opt);
        return BarrierPdeGreeksResult{p, 0.0, 0.0};
    }
    int i1 = static_cast<int>(std::floor(idx));
    int i0 = i1 - 1;
    int i2 = i1 + 1;
    double S0 = params.spot;
    // Quadratic interpolation for price at S0
    const double w = (S0 - grid.S[i1]) / (grid.S[i2] - grid.S[i1]);
    const double price = (1.0 - w) * grid.V[i1] + w * grid.V[i2];
    const double delta = (grid.V[i2] - grid.V[i0]) / (grid.S[i2] - grid.S[i0]);
    const double gamma = 2.0 * ( (grid.V[i2] - price) / (grid.S[i2] - S0) - (price - grid.V[i0]) / (S0 - grid.S[i0]) ) / (grid.S[i2] - grid.S[i0]);
    return BarrierPdeGreeksResult{price, delta, gamma};
}

} // namespace quant::pde
