#include <gtest/gtest.h>

#include "quant/mc.hpp"

#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

namespace {

quant::mc::McParams make_params() {
    quant::mc::McParams p{};
    p.spot = 100.0;
    p.strike = 100.0;
    p.rate = 0.02;
    p.dividend = 0.01;
    p.vol = 0.25;
    p.time = 1.0;
    p.num_paths = 20000;
    p.seed = 42;
    p.antithetic = true;
    p.control_variate = true;
    p.num_steps = 64;
    p.rng = quant::rng::Mode::Counter;
    return p;
}

quant::mc::McResult run_with_threads(const quant::mc::McParams& base, int threads) {
#ifdef QUANT_HAS_OPENMP
    int previous = omp_get_max_threads();
    omp_set_num_threads(threads);
#endif
    auto params = base;
    auto result = quant::mc::price_european_call(params);
#ifdef QUANT_HAS_OPENMP
    omp_set_num_threads(previous);
#endif
    return result;
}

} // namespace

TEST(RngDeterminism, CounterRngThreadInvariant) {
    const auto params = make_params();
#ifdef QUANT_HAS_OPENMP
    const auto r1 = run_with_threads(params, 1);
    const auto r4 = run_with_threads(params, 4);
    const auto r8 = run_with_threads(params, 8);
    EXPECT_DOUBLE_EQ(r1.estimate.value, r4.estimate.value);
    EXPECT_DOUBLE_EQ(r1.estimate.std_error, r4.estimate.std_error);
    EXPECT_DOUBLE_EQ(r1.estimate.value, r8.estimate.value);
    EXPECT_DOUBLE_EQ(r1.estimate.std_error, r8.estimate.std_error);
#else
    GTEST_SKIP() << "OpenMP not enabled; single-thread check only";
#endif
}
