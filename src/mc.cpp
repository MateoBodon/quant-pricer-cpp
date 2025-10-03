#include "quant/mc.hpp"

#include "quant/qmc/brownian_bridge.hpp"
#include "quant/qmc/sobol.hpp"

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

double inverse_normal_cdf(double p) {
    if (p <= 0.0) return -INFINITY;
    if (p >= 1.0) return INFINITY;

    static const double a1 = -3.969683028665376e+01;
    static const double a2 =  2.209460984245205e+02;
    static const double a3 = -2.759285104469687e+02;
    static const double a4 =  1.383577518672690e+02;
    static const double a5 = -3.066479806614716e+01;
    static const double a6 =  2.506628277459239e+00;

    static const double b1 = -5.447609879822406e+01;
    static const double b2 =  1.615858368580409e+02;
    static const double b3 = -1.556989798598866e+02;
    static const double b4 =  6.680131188771972e+01;
    static const double b5 = -1.328068155288572e+01;

    static const double c1 = -7.784894002430293e-03;
    static const double c2 = -3.223964580411365e-01;
    static const double c3 = -2.400758277161838e+00;
    static const double c4 = -2.549732539343734e+00;
    static const double c5 =  4.374664141464968e+00;
    static const double c6 =  2.938163982698783e+00;

    static const double d1 =  7.784695709041462e-03;
    static const double d2 =  3.224671290700398e-01;
    static const double d3 =  2.445134137142996e+00;
    static const double d4 =  3.754408661907416e+00;

    const double plow  = 0.02425;
    const double phigh = 1 - plow;
    double q, r, x;
    if (p < plow) {
        q = std::sqrt(-2.0 * std::log(p));
        x = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
            ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    } else if (p <= phigh) {
        q = p - 0.5;
        r = q * q;
        x = (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
            (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0);
    } else {
        q = std::sqrt(-2.0 * std::log(1.0 - p));
        x = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
              ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0);
    }

    double e = 0.5 * std::erfc(-x / std::sqrt(2.0)) - p;
    double u = e * std::sqrt(2.0 * std::numbers::pi) * std::exp(0.5 * x * x);
    x = x - u / (1.0 + 0.5 * x * u);
    return x;
}

struct WelfordAccumulator {
    std::uint64_t count{0};
    double mean{0.0};
    double m2{0.0};

    void add(double value) {
        ++count;
        const double delta = value - mean;
        mean += delta / static_cast<double>(count);
        const double delta2 = value - mean;
        m2 += delta * delta2;
    }

    void merge(const WelfordAccumulator& other) {
        if (other.count == 0) {
            return;
        }
        if (count == 0) {
            *this = other;
            return;
        }
        const double total = static_cast<double>(count + other.count);
        const double delta = other.mean - mean;
        mean += delta * static_cast<double>(other.count) / total;
        m2 += other.m2 + delta * delta * (static_cast<double>(count) * other.count / total);
        count += other.count;
    }

    double variance() const {
        return (count > 1) ? m2 / static_cast<double>(count - 1) : 0.0;
    }
};

constexpr double kZ95 = 1.95996398454005423552;

McStatistic summarize(const WelfordAccumulator& acc) {
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
        const double half_width = kZ95 * se;
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
    WelfordAccumulator delta;
    WelfordAccumulator vega;
    WelfordAccumulator gamma_lrm;
    WelfordAccumulator gamma_mixed;

    void merge(const GreekAccumulators& other) {
        delta.merge(other.delta);
        vega.merge(other.vega);
        gamma_lrm.merge(other.gamma_lrm);
        gamma_mixed.merge(other.gamma_mixed);
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
};

double evolve_terminal(double spot,
                       double rate,
                       double dividend,
                       double vol,
                       double maturity,
                       int steps,
                       const double* normals,
                       std::vector<double>& increments,
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
};

WelfordAccumulator simulate_range(std::uint64_t begin,
                                  std::uint64_t end,
                                  std::uint64_t seed_offset,
                                  const WorkerContext& ctx) {
    WelfordAccumulator acc;
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
    if (ctx.use_bridge && ctx.steps > 1) {
        bridge = std::make_unique<qmc::BrownianBridge>(ctx.steps, ctx.params.time);
    }

    pcg64 rng(seed_offset);
    std::normal_distribution<double> normal(0.0, 1.0);

    for (std::uint64_t idx = begin; idx < end; ++idx) {
        if (ctx.use_qmc) {
            ctx.sobol->generate(idx, inputs.uniforms.data());
            for (int j = 0; j < ctx.steps; ++j) {
                const double u = std::clamp(inputs.uniforms[j], std::numeric_limits<double>::min(), 1.0 - std::numeric_limits<double>::epsilon());
                const double z = inverse_normal_cdf(u);
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

        const double ST1 = evolve_terminal(ctx.params.spot,
                                           ctx.params.rate,
                                           ctx.params.dividend,
                                           ctx.params.vol,
                                           ctx.params.time,
                                           ctx.steps,
                                           inputs.normals.data(),
                                           inputs.increments,
                                           bridge.get());
        const double payoff1 = std::max(0.0, ST1 - ctx.params.strike);
        double sample = ctx.discount * payoff1;
        double cv_obs = ctx.discount * ST1;

        if (ctx.params.antithetic) {
            const double ST2 = evolve_terminal(ctx.params.spot,
                                               ctx.params.rate,
                                               ctx.params.dividend,
                                               ctx.params.vol,
                                               ctx.params.time,
                                               ctx.steps,
                                               inputs.normals_antithetic.data(),
                                               inputs.increments_antithetic,
                                               bridge.get());
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

GreekAccumulators simulate_greeks_range(std::uint64_t begin,
                                        std::uint64_t end,
                                        std::uint64_t seed_offset,
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

    for (std::uint64_t idx = begin; idx < end; ++idx) {
        const double z = normal(rng);
        const double ST1 = ctx.spot * std::exp(ctx.drift + ctx.vol_sqrt_time * z);
        const double payoff1 = std::max(0.0, ST1 - ctx.strike);

        double delta1 = 0.0;
        double vega1 = 0.0;
        if (payoff1 > 0.0) {
            delta1 = ctx.discount * (ST1 / ctx.spot);
            const double dST_dsigma = ST1 * (-ctx.vol * ctx.time + ctx.sqrt_time * z);
            vega1 = ctx.discount * dST_dsigma;
        }
        const double gamma_lrm1 = ctx.discount * payoff1 * gamma_weight(z);
        const double gamma_mixed1 = delta1 * (ctx.score_coeff * z)
                                    - (payoff1 > 0.0 ? ctx.discount * (ST1 / (ctx.spot * ctx.spot)) : 0.0);

        double delta_sample = delta1;
        double vega_sample = vega1;
        double gamma_lrm_sample = gamma_lrm1;
        double gamma_mixed_sample = gamma_mixed1;

        if (ctx.antithetic) {
            const double z2 = -z;
            const double ST2 = ctx.spot * std::exp(ctx.drift + ctx.vol_sqrt_time * z2);
            const double payoff2 = std::max(0.0, ST2 - ctx.strike);
            double delta2 = 0.0;
            double vega2 = 0.0;
            if (payoff2 > 0.0) {
                delta2 = ctx.discount * (ST2 / ctx.spot);
                const double dST_dsigma2 = ST2 * (-ctx.vol * ctx.time + ctx.sqrt_time * z2);
                vega2 = ctx.discount * dST_dsigma2;
            }
            const double gamma_lrm2 = ctx.discount * payoff2 * gamma_weight(z2);
            const double gamma_mixed2 = delta2 * (ctx.score_coeff * z2)
                                        - (payoff2 > 0.0 ? ctx.discount * (ST2 / (ctx.spot * ctx.spot)) : 0.0);

            delta_sample = 0.5 * (delta1 + delta2);
            vega_sample = 0.5 * (vega1 + vega2);
            gamma_lrm_sample = 0.5 * (gamma_lrm1 + gamma_lrm2);
            gamma_mixed_sample = 0.5 * (gamma_mixed1 + gamma_mixed2);
        }

        accum.delta.add(delta_sample);
        accum.vega.add(vega_sample);
        accum.gamma_lrm.add(gamma_lrm_sample);
        accum.gamma_mixed.add(gamma_mixed_sample);
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

    const double discount = std::exp(-p.rate * p.time);
    const double cv_expectation = p.spot * std::exp(-p.dividend * p.time);

    std::unique_ptr<qmc::SobolSequence> sobol;
    if (use_qmc) {
        sobol = std::make_unique<qmc::SobolSequence>(steps, scrambled, p.seed);
    }

    WorkerContext ctx{
        .params = p,
        .discount = discount,
        .cv_expectation = cv_expectation,
        .steps = steps,
        .use_qmc = use_qmc,
        .scrambled = scrambled,
        .use_bridge = use_bridge,
        .sobol = sobol.get()
    };

    WelfordAccumulator total;

#ifdef QUANT_HAS_OPENMP
    const std::uint64_t N = p.num_paths;
    const int max_threads = omp_get_max_threads();
    std::vector<WelfordAccumulator> partial(max_threads);

    #pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        const int nthreads = omp_get_num_threads();
        const std::uint64_t begin = (tid * N) / nthreads;
        const std::uint64_t end = ((tid + 1) * N) / nthreads;
        const std::uint64_t seed_offset = p.seed + 0x9E3779B97F4A7C15ULL * static_cast<std::uint64_t>(tid + 1);
        partial[tid] = simulate_range(begin, end, seed_offset, ctx);
    }

    for (const auto& part : partial) {
        total.merge(part);
    }
#else
    const std::uint64_t seed_offset = p.seed ? p.seed : 0x9E3779B97F4A7C15ULL;
    total = simulate_range(0, p.num_paths, seed_offset, ctx);
#endif

    return McResult{summarize(total)};
}

GreeksResult greeks_european_call(const McParams& p) {
    GreeksResult result{};
    if (p.num_paths == 0) {
        return result;
    }

    const double sqrt_time = std::sqrt(std::max(p.time, 0.0));
    const double vol_sqrt_time = p.vol * sqrt_time;
    const double discount = std::exp(-p.rate * p.time);
    const double drift = (p.rate - p.dividend - 0.5 * p.vol * p.vol) * p.time;
    const double inv_gamma_denom = (p.vol > 0.0 && p.time > 0.0)
                                       ? 1.0 / (p.spot * p.spot * p.vol * p.vol * p.time)
                                       : 0.0;
    const double score_coeff = (p.vol > 0.0 && p.time > 0.0)
                                   ? 1.0 / (p.spot * p.vol * sqrt_time)
                                   : 0.0;

    GreeksContext ctx{
        .spot = p.spot,
        .strike = p.strike,
        .rate = p.rate,
        .dividend = p.dividend,
        .vol = p.vol,
        .time = p.time,
        .antithetic = p.antithetic,
        .discount = discount,
        .drift = drift,
        .sqrt_time = sqrt_time,
        .vol_sqrt_time = vol_sqrt_time,
        .inv_gamma_denom = inv_gamma_denom,
        .score_coeff = score_coeff
    };

    GreekAccumulators totals;

#ifdef QUANT_HAS_OPENMP
    const std::uint64_t N = p.num_paths;
    const int max_threads = omp_get_max_threads();
    std::vector<GreekAccumulators> partial(max_threads);

    #pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        const int nthreads = omp_get_num_threads();
        const std::uint64_t begin = (tid * N) / nthreads;
        const std::uint64_t end = ((tid + 1) * N) / nthreads;
        const std::uint64_t seed_offset = p.seed + 0x517cc1b727220a95ULL * static_cast<std::uint64_t>(tid + 1);
        partial[tid] = simulate_greeks_range(begin, end, seed_offset, ctx);
    }

    for (const auto& part : partial) {
        totals.merge(part);
    }
#else
    const std::uint64_t seed_offset = p.seed ? p.seed : 0x517cc1b727220a95ULL;
    totals = simulate_greeks_range(0, p.num_paths, seed_offset, ctx);
#endif

    result.delta = summarize(totals.delta);
    result.vega = summarize(totals.vega);
    result.gamma_lrm = summarize(totals.gamma_lrm);
    result.gamma_mixed = summarize(totals.gamma_mixed);
    return result;
}

} // namespace quant::mc
