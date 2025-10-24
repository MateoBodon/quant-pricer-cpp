#include "quant/mc_barrier.hpp"

#include "quant/black_scholes.hpp"
#include "quant/qmc/brownian_bridge.hpp"
#include "quant/qmc/sobol.hpp"
#include "quant/math.hpp"
#include "quant/stats.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <memory>
#include <numbers>
#include <random>
#include <stdexcept>
#include <vector>

#include <pcg_random.hpp>

#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

namespace quant::mc {

namespace {

bool is_knock_out(const BarrierSpec& spec) {
    return spec.type == BarrierType::DownOut || spec.type == BarrierType::UpOut;
}

bool is_up_barrier(const BarrierSpec& spec) {
    return spec.type == BarrierType::UpOut || spec.type == BarrierType::UpIn;
}

bool barrier_triggered(const BarrierSpec& spec, double S) {
    return is_up_barrier(spec) ? (S >= spec.B) : (S <= spec.B);
}

double crossing_probability(double S_prev,
                            double S_next,
                            double B,
                            double sigma,
                            double dt,
                            bool up_barrier) {
    if (up_barrier) {
        if (S_prev >= B || S_next >= B) {
            return 1.0;
        }
        const double log1 = std::log(B / S_prev);
        const double log2 = std::log(B / S_next);
        const double exponent = -2.0 * log1 * log2 / (sigma * sigma * dt);
        return std::clamp(std::exp(std::min(exponent, 0.0)), 0.0, 1.0);
    } else {
        if (S_prev <= B || S_next <= B) {
            return 1.0;
        }
        const double log1 = std::log(S_prev / B);
        const double log2 = std::log(S_next / B);
        const double exponent = -2.0 * log1 * log2 / (sigma * sigma * dt);
        return std::clamp(std::exp(std::min(exponent, 0.0)), 0.0, 1.0);
    }
}

McStatistic summarize(const quant::stats::Welford& acc) {
    McStatistic stat{};
    if (acc.count == 0) {
        stat.value = 0.0;
        stat.std_error = 0.0;
        stat.ci_low = 0.0;
        stat.ci_high = 0.0;
        return stat;
    }
    stat.value = acc.mean;
    const double variance = acc.variance();
    if (acc.count > 1 && variance >= 0.0) {
        const double se = std::sqrt(variance / static_cast<double>(acc.count));
        const double half_width = quant::math::kZ95 * se;
        stat.std_error = se;
        stat.ci_low = stat.value - half_width;
        stat.ci_high = stat.value + half_width;
    } else {
        stat.std_error = 0.0;
        stat.ci_low = stat.value;
        stat.ci_high = stat.value;
    }
    return stat;
}

struct BarrierMcContext {
    const McParams& params;
    double strike;
    OptionType opt;
    BarrierSpec barrier;
    int steps;
    bool use_qmc;
    bool scrambled;
    bool use_bridge;
    double dt;
    double drift_dt;
    double sqrt_dt;
    double discount;
    double cv_expectation;
    bool knock_out;
    bool up_barrier;
    bool use_cv;
};

struct WorkerContext {
    const BarrierMcContext& ctx;
    const qmc::SobolSequence* sobol;
    int sobol_dim;
};

struct PathWorkspace {
    std::vector<double> normals;
    std::vector<double> uniforms;
    std::vector<double> normals_antithetic;
    std::vector<double> uniforms_antithetic;
    std::vector<double> increments;
    std::vector<double> increments_antithetic;
    std::vector<double> sobol_point;
};

double run_path(const BarrierMcContext& ctx,
                const std::vector<double>& increments,
                const std::vector<double>& uniforms) {
    const double sigma = ctx.params.vol;
    double logS = std::log(ctx.params.spot);
    double S_prev = ctx.params.spot;

    bool knocked_out = false;
    bool knocked_in = false;
    double rebate_pv = 0.0;

    const int steps = ctx.steps;
    const double dt = ctx.dt;

    for (int i = 0; i < steps; ++i) {
        const double incr = increments[i];
        const double logS_next = logS + ctx.drift_dt + sigma * incr;
        const double S_next = std::exp(logS_next);

        bool cross = false;
        if (ctx.up_barrier) {
            if (S_prev >= ctx.barrier.B || S_next >= ctx.barrier.B) {
                cross = true;
            } else {
                const double p_hit = crossing_probability(S_prev, S_next, ctx.barrier.B, sigma, dt, true);
                if (p_hit > 0.0) {
                    const double u = uniforms[i];
                    cross = (u < p_hit);
                }
            }
        } else {
            if (S_prev <= ctx.barrier.B || S_next <= ctx.barrier.B) {
                cross = true;
            } else {
                const double p_hit = crossing_probability(S_prev, S_next, ctx.barrier.B, sigma, dt, false);
                if (p_hit > 0.0) {
                    const double u = uniforms[i];
                    cross = (u < p_hit);
                }
            }
        }

        if (cross) {
            if (ctx.knock_out) {
                knocked_out = true;
                if (ctx.barrier.rebate > 0.0) {
                    const double tau = dt * static_cast<double>(i + 1);
                    rebate_pv = ctx.barrier.rebate * std::exp(-ctx.params.rate * tau);
                }
                logS = logS_next;
                S_prev = S_next;
                break;
            } else {
                knocked_in = true;
            }
        }

        logS = logS_next;
        S_prev = S_next;
    }

    if (ctx.knock_out) {
        if (knocked_out) {
            if (rebate_pv > 0.0) {
                return rebate_pv;
            }
            return ctx.barrier.rebate * ctx.discount;
        }
    const double payoff = (ctx.opt == OptionType::Call)
                                  ? std::max(0.0, S_prev - ctx.strike)
                                  : std::max(0.0, ctx.strike - S_prev);
    double sample = ctx.discount * payoff;
    if (ctx.use_cv) {
        const double cv_obs = ctx.discount * S_prev;
        sample += (ctx.cv_expectation - cv_obs);
    }
    return sample;
    }

    // knock-in
    if (knocked_in) {
        const double payoff = (ctx.opt == OptionType::Call)
                                  ? std::max(0.0, S_prev - ctx.strike)
                                  : std::max(0.0, ctx.strike - S_prev);
        double sample = ctx.discount * payoff;
        if (ctx.use_cv) {
            const double cv_obs = ctx.discount * S_prev;
            sample += (ctx.cv_expectation - cv_obs);
        }
        return sample;
    }

    return ctx.barrier.rebate * ctx.discount;
}

quant::stats::Welford simulate_range(std::uint64_t begin,
                                  std::uint64_t end,
                                  std::uint64_t seed_offset,
                                  const WorkerContext& worker) {
    quant::stats::Welford acc;
    if (begin >= end) {
        return acc;
    }

    const BarrierMcContext& ctx = worker.ctx;
    PathWorkspace workspace;
    workspace.normals.resize(ctx.steps);
    workspace.uniforms.resize(ctx.steps);
    workspace.increments.resize(ctx.steps);
    if (ctx.params.antithetic) {
        workspace.normals_antithetic.resize(ctx.steps);
        workspace.uniforms_antithetic.resize(ctx.steps);
        workspace.increments_antithetic.resize(ctx.steps);
    }
    if (ctx.use_qmc) {
        workspace.sobol_point.resize(static_cast<std::size_t>(worker.sobol_dim));
    }

    std::unique_ptr<qmc::BrownianBridge> bridge;
    std::unique_ptr<qmc::BrownianBridge> bridge_antithetic;
    if (ctx.use_bridge && ctx.steps > 1) {
        bridge = std::make_unique<qmc::BrownianBridge>(ctx.steps, ctx.params.time);
        if (ctx.params.antithetic) {
            bridge_antithetic = std::make_unique<qmc::BrownianBridge>(ctx.steps, ctx.params.time);
        }
    }

    pcg64 rng(seed_offset);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::uniform_real_distribution<double> uniform(0.0, 1.0);

    for (std::uint64_t idx = begin; idx < end; ++idx) {
        if (ctx.use_qmc) {
            worker.sobol->generate(idx, workspace.sobol_point.data());
            for (int j = 0; j < ctx.steps; ++j) {
                const double eps = std::numeric_limits<double>::min();
                const double maxu = 1.0 - std::numeric_limits<double>::epsilon();
                double u_norm = std::clamp(workspace.sobol_point[j], eps, maxu);
                double u_hit = std::clamp(workspace.sobol_point[ctx.steps + j], eps, maxu);
                workspace.normals[j] = quant::math::inverse_normal_cdf(u_norm);
                workspace.uniforms[j] = u_hit;
                if (ctx.params.antithetic) {
                    workspace.normals_antithetic[j] = -workspace.normals[j];
                    workspace.uniforms_antithetic[j] = 1.0 - u_hit;
                }
            }
        } else {
            for (int j = 0; j < ctx.steps; ++j) {
                workspace.normals[j] = normal(rng);
                workspace.uniforms[j] = uniform(rng);
                if (ctx.params.antithetic) {
                    workspace.normals_antithetic[j] = -workspace.normals[j];
                    workspace.uniforms_antithetic[j] = 1.0 - workspace.uniforms[j];
                }
            }
        }

        if (ctx.use_bridge && ctx.steps > 1) {
            bridge->transform(workspace.normals.data(), workspace.increments.data());
            if (ctx.params.antithetic) {
                bridge_antithetic->transform(workspace.normals_antithetic.data(), workspace.increments_antithetic.data());
            }
        } else {
            for (int j = 0; j < ctx.steps; ++j) {
                workspace.increments[j] = ctx.sqrt_dt * workspace.normals[j];
                if (ctx.params.antithetic) {
                    workspace.increments_antithetic[j] = ctx.sqrt_dt * workspace.normals_antithetic[j];
                }
            }
        }

        double sample = run_path(ctx, workspace.increments, workspace.uniforms);
        if (ctx.params.antithetic) {
            const double sample_antithetic = run_path(ctx, workspace.increments_antithetic, workspace.uniforms_antithetic);
            sample = 0.5 * (sample + sample_antithetic);
        }
        acc.add(sample);
    }

    return acc;
}

} // namespace

McResult price_barrier_option(const McParams& base,
                              double strike,
                              OptionType opt,
                              const BarrierSpec& barrier) {
    if (base.num_paths == 0) {
        return McResult{McStatistic{0.0, 0.0, 0.0, 0.0}};
    }
    if (strike <= 0.0) {
        throw std::invalid_argument("Strike must be positive");
    }
    if (barrier.B <= 0.0) {
        throw std::invalid_argument("Barrier level must be positive");
    }
    if (base.spot <= 0.0) {
        throw std::invalid_argument("Spot must be positive");
    }

    const bool knocked = barrier_triggered(barrier, base.spot);
    if (knocked) {
        if (is_knock_out(barrier)) {
            const double value = barrier.rebate;
            return McResult{McStatistic{value, 0.0, value, value}};
        }
        const double vanilla = (opt == OptionType::Call)
                                   ? ::quant::bs::call_price(base.spot, strike, base.rate, base.dividend, base.vol, base.time)
                                   : ::quant::bs::put_price(base.spot, strike, base.rate, base.dividend, base.vol, base.time);
        return McResult{McStatistic{vanilla, 0.0, vanilla, vanilla}};
    }

    const int steps = std::max(1, base.num_steps);
    const bool use_qmc = base.qmc != McParams::Qmc::None;
    const bool scrambled = base.qmc == McParams::Qmc::SobolScrambled;
    const bool use_bridge = (base.bridge == McParams::Bridge::BrownianBridge);

    const int dims_per_step = 2; // normal + uniform
    const int sobol_dim = steps * dims_per_step;
    if (use_qmc && sobol_dim > static_cast<int>(qmc::SobolSequence::kMaxSupportedDimension)) {
        throw std::invalid_argument("Sobol dimension exceeded; reduce num_steps or disable QMC");
    }

    const double dt = base.time / static_cast<double>(steps);
    const BarrierMcContext ctx{
        base,
        strike,
        opt,
        barrier,
        steps,
        use_qmc,
        scrambled,
        use_bridge,
        dt,
        (base.rate - base.dividend - 0.5 * base.vol * base.vol) * dt,
        std::sqrt(dt),
        std::exp(-base.rate * base.time),
        base.spot * std::exp(-base.dividend * base.time),
        is_knock_out(barrier),
        is_up_barrier(barrier),
        base.control_variate
    };

    std::unique_ptr<qmc::SobolSequence> sobol;
    if (use_qmc) {
        sobol = std::make_unique<qmc::SobolSequence>(sobol_dim, scrambled, base.seed);
    }

    WorkerContext worker{ctx, sobol.get(), sobol_dim};

    quant::stats::Welford total;

#ifdef QUANT_HAS_OPENMP
    const std::uint64_t N = base.num_paths;
    const int max_threads = omp_get_max_threads();
    std::vector<quant::stats::Welford> partial(max_threads);

    #pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        const int nthreads = omp_get_num_threads();
        const std::uint64_t begin = (tid * N) / nthreads;
        const std::uint64_t end = ((tid + 1) * N) / nthreads;
        const std::uint64_t seed_offset = base.seed + 0x517cc1b727220a95ULL * static_cast<std::uint64_t>(tid + 1);
        partial[tid] = simulate_range(begin, end, seed_offset, worker);
    }

    for (const auto& part : partial) {
        total.merge(part);
    }
#else
    const std::uint64_t seed_offset = base.seed ? base.seed : 0x517cc1b727220a95ULL;
    total = simulate_range(0, base.num_paths, seed_offset, worker);
#endif

    return McResult{summarize(total)};
}

} // namespace quant::mc
