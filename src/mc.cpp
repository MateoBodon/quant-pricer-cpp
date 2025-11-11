#include "quant/mc.hpp"

#include "quant/math.hpp"
#include "quant/qmc/brownian_bridge.hpp"
#include "quant/qmc/sobol.hpp"
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

struct GreekAccumulators {
    quant::stats::Welford delta;
    quant::stats::Welford vega;
    quant::stats::Welford gamma_lrm;
    quant::stats::Welford gamma_mixed;
    quant::stats::Welford theta;

    void merge(const GreekAccumulators& other) {
        delta.merge(other.delta);
        vega.merge(other.vega);
        gamma_lrm.merge(other.gamma_lrm);
        gamma_mixed.merge(other.gamma_mixed);
        theta.merge(other.theta);
    }
};

struct GreeksContext {
    double spot;
    double strike;
    double rate;
    double dividend;
    double vol;
    double time;
    bool antithetic;
    double discount;
    double drift;
    double sqrt_time;
    double vol_sqrt_time;
    double inv_gamma_denom;
    double score_coeff;
    quant::rng::Mode rng_mode;
};

double evolve_terminal(double spot, double rate, double dividend, double vol, double maturity, int steps,
                       const double* normals, std::vector<double>& increments,
                       const qmc::BrownianBridge* bridge) {
    if (steps <= 1) {
        const double z = normals[0];
        const double drift = (rate - dividend - 0.5 * vol * vol) * maturity;
        const double diff = vol * std::sqrt(maturity);
        return spot * std::exp(drift + diff * z);
    }

    if (static_cast<std::size_t>(steps) != increments.size()) {
        increments.assign(steps, 0.0);
    }

    if (bridge) {
        bridge->transform(normals, increments.data());
    } else {
        const double sqrt_dt = std::sqrt(maturity / static_cast<double>(steps));
        for (int i = 0; i < steps; ++i) {
            increments[i] = sqrt_dt * normals[i];
        }
    }

    const double dt = maturity / static_cast<double>(steps);
    const double drift_dt = (rate - dividend - 0.5 * vol * vol) * dt;
    double logS = std::log(spot);
    for (int i = 0; i < steps; ++i) {
        logS += drift_dt + vol * increments[i];
    }
    return std::exp(logS);
}

struct PathInputs {
    std::vector<double> uniforms;
    std::vector<double> normals;
    std::vector<double> normals_antithetic;
    std::vector<double> increments;
    std::vector<double> increments_antithetic;
};

struct WorkerContext {
    const McParams& params;
    double discount;
    double cv_expectation;
    int steps;
    bool use_qmc;
    bool scrambled;
    bool use_bridge;
    const qmc::SobolSequence* sobol;
    // Piecewise-constant schedules (if used)
    bool use_schedule{false};
    std::vector<double> dt;
    std::vector<double> drift_step;
    std::vector<double> sigma;
    std::vector<double> sqrt_dt;
};

quant::stats::Welford simulate_range(std::uint64_t begin, std::uint64_t end, std::uint64_t seed_offset,
                                     const WorkerContext& ctx) {
    quant::stats::Welford acc;
    if (begin >= end) {
        return acc;
    }

    PathInputs inputs;
    inputs.normals.resize(ctx.steps);
    if (ctx.params.antithetic) {
        inputs.normals_antithetic.resize(ctx.steps);
    }
    if (ctx.steps > 1) {
        inputs.increments.resize(ctx.steps, 0.0);
        if (ctx.params.antithetic) {
            inputs.increments_antithetic.resize(ctx.steps, 0.0);
        }
    }
    if (ctx.use_qmc) {
        inputs.uniforms.resize(ctx.steps);
    }

    std::unique_ptr<qmc::BrownianBridge> bridge;
    if (!ctx.use_schedule && ctx.use_bridge && ctx.steps > 1) {
        bridge = std::make_unique<qmc::BrownianBridge>(ctx.steps, ctx.params.time);
    }

    pcg64 rng(seed_offset);
    std::normal_distribution<double> normal(0.0, 1.0);

    for (std::uint64_t idx = begin; idx < end; ++idx) {
        if (ctx.use_qmc) {
            ctx.sobol->generate(idx, inputs.uniforms.data());
            for (int j = 0; j < ctx.steps; ++j) {
                const double u = std::clamp(inputs.uniforms[j], std::numeric_limits<double>::min(),
                                            1.0 - std::numeric_limits<double>::epsilon());
                const double z = quant::math::inverse_normal_cdf(u);
                inputs.normals[j] = z;
                if (ctx.params.antithetic) {
                    inputs.normals_antithetic[j] = -z;
                }
            }
        } else {
            if (ctx.params.rng == quant::rng::Mode::Counter) {
                for (int j = 0; j < ctx.steps; ++j) {
                    const double z =
                        quant::rng::normal(seed_offset, idx, static_cast<std::uint32_t>(j), 0U, 0U);
                    inputs.normals[j] = z;
                    if (ctx.params.antithetic) {
                        inputs.normals_antithetic[j] = -z;
                    }
                }
            } else {
                for (int j = 0; j < ctx.steps; ++j) {
                    const double z = normal(rng);
                    inputs.normals[j] = z;
                    if (ctx.params.antithetic) {
                        inputs.normals_antithetic[j] = -z;
                    }
                }
            }
        }

        double ST1;
        if (ctx.use_schedule) {
            double logS = std::log(ctx.params.spot);
            for (int i = 0; i < ctx.steps; ++i) {
                const double z = inputs.normals[i];
                logS += ctx.drift_step[i] + ctx.sigma[i] * ctx.sqrt_dt[i] * z;
            }
            ST1 = std::exp(logS);
        } else {
            ST1 = evolve_terminal(ctx.params.spot, ctx.params.rate, ctx.params.dividend, ctx.params.vol,
                                  ctx.params.time, ctx.steps, inputs.normals.data(), inputs.increments,
                                  bridge.get());
        }
        const double payoff1 = std::max(0.0, ST1 - ctx.params.strike);
        double sample = ctx.discount * payoff1;
        double cv_obs = ctx.discount * ST1;

        if (ctx.params.antithetic) {
            double ST2;
            if (ctx.use_schedule) {
                double logS2 = std::log(ctx.params.spot);
                for (int i = 0; i < ctx.steps; ++i) {
                    const double z2 = inputs.normals_antithetic[i];
                    logS2 += ctx.drift_step[i] + ctx.sigma[i] * ctx.sqrt_dt[i] * z2;
                }
                ST2 = std::exp(logS2);
            } else {
                ST2 = evolve_terminal(ctx.params.spot, ctx.params.rate, ctx.params.dividend, ctx.params.vol,
                                      ctx.params.time, ctx.steps, inputs.normals_antithetic.data(),
                                      inputs.increments_antithetic, bridge.get());
            }
            const double payoff2 = std::max(0.0, ST2 - ctx.params.strike);
            sample = 0.5 * (sample + ctx.discount * payoff2);
            cv_obs = 0.5 * ctx.discount * (ST1 + ST2);
        }

        if (ctx.params.control_variate) {
            sample += (ctx.cv_expectation - cv_obs);
        }

        acc.add(sample);
    }

    return acc;
}

GreekAccumulators simulate_greeks_range(std::uint64_t begin, std::uint64_t end, std::uint64_t seed_offset,
                                        const GreeksContext& ctx) {
    GreekAccumulators accum;
    if (begin >= end) {
        return accum;
    }

    pcg64 rng(seed_offset);
    std::normal_distribution<double> normal(0.0, 1.0);

    const auto gamma_weight = [&](double z) {
        if (ctx.inv_gamma_denom == 0.0) {
            return 0.0;
        }
        return ((z * z) - 1.0 - ctx.vol_sqrt_time * z) * ctx.inv_gamma_denom;
    };

    const double sigma = ctx.vol;
    const double sqrt_time = ctx.sqrt_time;
    const double time = ctx.time;
    const double inv_sigma = (sigma > 0.0) ? 1.0 / sigma : 0.0;

    for (std::uint64_t idx = begin; idx < end; ++idx) {
        const double z = (ctx.rng_mode == quant::rng::Mode::Counter)
                             ? quant::rng::normal(seed_offset, idx, 0U, 0U, 1U)
                             : normal(rng);
        const double ST1 = ctx.spot * std::exp(ctx.drift + ctx.vol_sqrt_time * z);
        const double payoff1 = std::max(0.0, ST1 - ctx.strike);
        const double priceT1 = ctx.discount * payoff1;

        double delta1 = 0.0;
        if (payoff1 > 0.0) {
            delta1 = ctx.discount * (ST1 / ctx.spot);
        }
        const double vega_weight = (sigma > 0.0) ? ((z * z - 1.0) * inv_sigma - z * sqrt_time) : 0.0;
        const double vega1 = ctx.discount * payoff1 * vega_weight;
        const double gamma_lrm1 = ctx.discount * payoff1 * gamma_weight(z);
        const double gamma_mixed1 = delta1 * (ctx.score_coeff * z) -
                                    (payoff1 > 0.0 ? ctx.discount * (ST1 / (ctx.spot * ctx.spot)) : 0.0);
        double theta_sample;
        if (time > 0.0) {
            const double h = std::max(1e-4, 1e-3 * time);
            const double T_minus = (time > h) ? (time - h) : time;
            auto price_at_T = [&](double T, double zval) {
                if (T <= 0.0)
                    return 0.0;
                const double disc = std::exp(-ctx.rate * T);
                const double driftT = (ctx.rate - ctx.dividend - 0.5 * sigma * sigma) * T;
                const double ST = ctx.spot * std::exp(driftT + sigma * std::sqrt(T) * zval);
                const double payoff = std::max(0.0, ST - ctx.strike);
                return disc * payoff;
            };
            const double p_curr = priceT1;
            const double p_minus = (T_minus < time) ? price_at_T(T_minus, z) : priceT1;
            const double denom = (T_minus < time) ? (time - T_minus) : 1.0;
            theta_sample = (p_minus - p_curr) / denom;
        } else {
            theta_sample = 0.0;
        }

        double delta_sample = delta1;
        double vega_sample = vega1;
        double gamma_lrm_sample = gamma_lrm1;
        double gamma_mixed_sample = gamma_mixed1;

        if (ctx.antithetic) {
            const double z2 = -z;
            const double ST2 = ctx.spot * std::exp(ctx.drift + ctx.vol_sqrt_time * z2);
            const double payoff2 = std::max(0.0, ST2 - ctx.strike);
            double delta2 = 0.0;
            if (payoff2 > 0.0) {
                delta2 = ctx.discount * (ST2 / ctx.spot);
            }
            const double vega_weight2 = (sigma > 0.0) ? ((z2 * z2 - 1.0) * inv_sigma - z2 * sqrt_time) : 0.0;
            const double vega2 = ctx.discount * payoff2 * vega_weight2;
            const double gamma_lrm2 = ctx.discount * payoff2 * gamma_weight(z2);
            const double gamma_mixed2 = delta2 * (ctx.score_coeff * z2) -
                                        (payoff2 > 0.0 ? ctx.discount * (ST2 / (ctx.spot * ctx.spot)) : 0.0);
            const double priceT2 = ctx.discount * payoff2;
            double theta2;
            if (time > 0.0) {
                const double h = std::max(1e-4, 1e-3 * time);
                const double T_minus = (time > h) ? (time - h) : time;
                auto price_at_T = [&](double T, double zval) {
                    if (T <= 0.0)
                        return 0.0;
                    const double disc = std::exp(-ctx.rate * T);
                    const double driftT = (ctx.rate - ctx.dividend - 0.5 * sigma * sigma) * T;
                    const double ST = ctx.spot * std::exp(driftT + sigma * std::sqrt(T) * zval);
                    const double payoff = std::max(0.0, ST - ctx.strike);
                    return disc * payoff;
                };
                const double p_curr2 = priceT2;
                const double p_minus2 = (T_minus < time) ? price_at_T(T_minus, z2) : p_curr2;
                const double denom2 = (T_minus < time) ? (time - T_minus) : 1.0;
                theta2 = (p_minus2 - p_curr2) / denom2;
            } else {
                theta2 = 0.0;
            }

            delta_sample = 0.5 * (delta1 + delta2);
            vega_sample = 0.5 * (vega1 + vega2);
            gamma_lrm_sample = 0.5 * (gamma_lrm1 + gamma_lrm2);
            gamma_mixed_sample = 0.5 * (gamma_mixed1 + gamma_mixed2);
            theta_sample = 0.5 * (theta_sample + theta2);
        }

        accum.delta.add(delta_sample);
        accum.vega.add(vega_sample);
        accum.gamma_lrm.add(gamma_lrm_sample);
        accum.gamma_mixed.add(gamma_mixed_sample);
        accum.theta.add(theta_sample);
    }

    return accum;
}

} // namespace

McResult price_european_call(const McParams& p) {
    if (p.num_paths == 0) {
        return McResult{McStatistic{0.0, 0.0, 0.0, 0.0}};
    }

    const int steps = std::max(1, p.num_steps);
    const bool use_qmc = p.qmc != McParams::Qmc::None;
    const bool scrambled = p.qmc == McParams::Qmc::SobolScrambled;
    const bool use_bridge = (p.bridge == McParams::Bridge::BrownianBridge);

    if (use_qmc && static_cast<std::size_t>(steps) > qmc::SobolSequence::kMaxSupportedDimension) {
        throw std::invalid_argument("Sobol sequence limited to 64 dimensions");
    }

    std::unique_ptr<qmc::SobolSequence> sobol;
    if (use_qmc) {
        sobol = std::make_unique<qmc::SobolSequence>(steps, scrambled, p.seed);
    }

    const bool has_schedule =
        p.rate_schedule.has_value() || p.dividend_schedule.has_value() || p.vol_schedule.has_value();

    double int_rate = p.rate * p.time;
    double int_div = p.dividend * p.time;
    double integrated_var = p.vol * p.vol * p.time;

    WorkerContext ctx{.params = p,
                      .discount = 0.0,
                      .cv_expectation = 0.0,
                      .steps = steps,
                      .use_qmc = use_qmc,
                      .scrambled = scrambled,
                      .use_bridge = use_bridge,
                      .sobol = sobol.get()};

    // If schedules provided, build per-step coefficients on uniform grid over [0,T]
    if (has_schedule) {
        ctx.use_schedule = true;
        ctx.dt.resize(steps);
        ctx.drift_step.resize(steps);
        ctx.sigma.resize(steps);
        ctx.sqrt_dt.resize(steps);
        int_rate = 0.0;
        int_div = 0.0;
        integrated_var = 0.0;
        for (int i = 0; i < steps; ++i) {
            const double t0 = (static_cast<double>(i) / steps) * p.time;
            const double t1 = (static_cast<double>(i + 1) / steps) * p.time;
            const double dt = t1 - t0;
            const double r = p.rate_schedule ? p.rate_schedule->value(0.5 * (t0 + t1)) : p.rate;
            const double q = p.dividend_schedule ? p.dividend_schedule->value(0.5 * (t0 + t1)) : p.dividend;
            const double sig = p.vol_schedule ? p.vol_schedule->value(0.5 * (t0 + t1)) : p.vol;
            int_rate += r * dt;
            int_div += q * dt;
            integrated_var += sig * sig * dt;
            ctx.dt[i] = dt;
            ctx.sqrt_dt[i] = std::sqrt(dt);
            ctx.sigma[i] = sig;
            ctx.drift_step[i] = (r - q - 0.5 * sig * sig) * dt;
        }
    }

    ctx.discount = std::exp(-int_rate);
    ctx.cv_expectation = p.spot * std::exp(-int_div);

    if (!ctx.use_schedule) {
        // Ensure vectors remain empty for the non-schedule path
        integrated_var = std::max(0.0, integrated_var);
    }

    quant::stats::Welford total;

#ifdef QUANT_HAS_OPENMP
    const std::uint64_t N = p.num_paths;
    const int max_threads = omp_get_max_threads();
    std::vector<quant::stats::Welford> partial(max_threads);
    const std::uint64_t counter_seed = p.seed ? p.seed : 0x9E3779B97F4A7C15ULL;

#pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        const int nthreads = omp_get_num_threads();
        const std::uint64_t begin = (tid * N) / nthreads;
        const std::uint64_t end = ((tid + 1) * N) / nthreads;
        const std::uint64_t seed_offset =
            (p.rng == quant::rng::Mode::Counter)
                ? counter_seed
                : p.seed + 0x9E3779B97F4A7C15ULL * static_cast<std::uint64_t>(tid + 1);
        partial[tid] = simulate_range(begin, end, seed_offset, ctx);
    }

    for (const auto& part : partial) {
        total.merge(part);
    }
#else
    const std::uint64_t seed_offset = (p.rng == quant::rng::Mode::Counter)
                                          ? (p.seed ? p.seed : 0x9E3779B97F4A7C15ULL)
                                          : (p.seed ? p.seed : 0x9E3779B97F4A7C15ULL);
    total = simulate_range(0, p.num_paths, seed_offset, ctx);
#endif

    return McResult{summarize(total)};
}

GreeksResult greeks_european_call(const McParams& p) {
    GreeksResult result{};
    if (p.num_paths == 0) {
        return result;
    }

    const double T = p.time;
    const double sqrt_time = std::sqrt(std::max(T, 0.0));

    const bool has_schedule =
        p.rate_schedule.has_value() || p.dividend_schedule.has_value() || p.vol_schedule.has_value();

    double int_rate = p.rate * T;
    double int_div = p.dividend * T;
    double integrated_var = p.vol * p.vol * T;

    if (has_schedule) {
        const int steps = std::max(1, p.num_steps);
        int_rate = 0.0;
        int_div = 0.0;
        integrated_var = 0.0;
        for (int i = 0; i < steps; ++i) {
            const double t0 = (static_cast<double>(i) / steps) * T;
            const double t1 = (static_cast<double>(i + 1) / steps) * T;
            const double dt = t1 - t0;
            const double r = p.rate_schedule ? p.rate_schedule->value(0.5 * (t0 + t1)) : p.rate;
            const double q = p.dividend_schedule ? p.dividend_schedule->value(0.5 * (t0 + t1)) : p.dividend;
            const double sig = p.vol_schedule ? p.vol_schedule->value(0.5 * (t0 + t1)) : p.vol;
            int_rate += r * dt;
            int_div += q * dt;
            integrated_var += sig * sig * dt;
        }
    }

    const double discount = std::exp(-int_rate);
    const double vol_sqrt_time = (integrated_var > 0.0) ? std::sqrt(integrated_var) : 0.0;
    const double drift = int_rate - int_div - 0.5 * integrated_var;
    const double inv_gamma_denom = (integrated_var > 0.0) ? 1.0 / (p.spot * p.spot * integrated_var) : 0.0;
    const double score_coeff = (vol_sqrt_time > 0.0) ? 1.0 / (p.spot * vol_sqrt_time) : 0.0;

    const double rate_eff = (T > 0.0) ? int_rate / T : p.rate;
    const double div_eff = (T > 0.0) ? int_div / T : p.dividend;
    const double sigma_eff = (T > 0.0 && integrated_var > 0.0) ? std::sqrt(integrated_var / T) : 0.0;

    GreeksContext ctx{.spot = p.spot,
                      .strike = p.strike,
                      .rate = rate_eff,
                      .dividend = div_eff,
                      .vol = sigma_eff,
                      .time = T,
                      .antithetic = p.antithetic,
                      .discount = discount,
                      .drift = drift,
                      .sqrt_time = sqrt_time,
                      .vol_sqrt_time = vol_sqrt_time,
                      .inv_gamma_denom = inv_gamma_denom,
                      .score_coeff = score_coeff,
                      .rng_mode = p.rng};

    GreekAccumulators totals;

#ifdef QUANT_HAS_OPENMP
    const std::uint64_t N = p.num_paths;
    const int max_threads = omp_get_max_threads();
    std::vector<GreekAccumulators> partial(max_threads);
    const std::uint64_t counter_seed = p.seed ? p.seed : 0x517cc1b727220a95ULL;

#pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        const int nthreads = omp_get_num_threads();
        const std::uint64_t begin = (tid * N) / nthreads;
        const std::uint64_t end = ((tid + 1) * N) / nthreads;
        const std::uint64_t seed_offset =
            (p.rng == quant::rng::Mode::Counter)
                ? counter_seed
                : p.seed + 0x517cc1b727220a95ULL * static_cast<std::uint64_t>(tid + 1);
        partial[tid] = simulate_greeks_range(begin, end, seed_offset, ctx);
    }

    for (const auto& part : partial) {
        totals.merge(part);
    }
#else
    const std::uint64_t seed_offset = (p.rng == quant::rng::Mode::Counter)
                                          ? (p.seed ? p.seed : 0x517cc1b727220a95ULL)
                                          : (p.seed ? p.seed : 0x517cc1b727220a95ULL);
    totals = simulate_greeks_range(0, p.num_paths, seed_offset, ctx);
#endif

    result.delta = summarize(totals.delta);
    result.vega = summarize(totals.vega);
    result.gamma_lrm = summarize(totals.gamma_lrm);
    result.gamma_mixed = summarize(totals.gamma_mixed);
    result.theta = summarize(totals.theta);
    return result;
}

} // namespace quant::mc
