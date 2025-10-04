#include <benchmark/benchmark.h>
#include "quant/mc.hpp"

#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

static void BM_MC_PathsPerSecond(benchmark::State& state) {
  const int threads = static_cast<int>(state.range(0));
  quant::mc::McParams mp{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.02,
      .dividend = 0.0,
      .vol = 0.2,
      .time = 1.0,
      .num_paths = static_cast<std::uint64_t>(1'000'000),
      .seed = 2024,
      .antithetic = true,
      .control_variate = true,
      .qmc = quant::mc::McParams::Qmc::None,
      .bridge = quant::mc::McParams::Bridge::None,
      .num_steps = 1};
#ifdef QUANT_HAS_OPENMP
  omp_set_num_threads(threads);
#else
  (void)threads;
#endif
  for (auto _ : state) {
    auto res = quant::mc::price_european_call(mp);
    benchmark::DoNotOptimize(res.estimate.value);
  }
  state.counters["paths/s"] = benchmark::Counter(static_cast<double>(mp.num_paths),
                                                   benchmark::Counter::kIsIterationInvariantRate);
}

static void BM_MC_Rmse_PRNG(benchmark::State& state) {
  quant::mc::McParams mp{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.03,
      .dividend = 0.0,
      .vol = 0.2,
      .time = 1.0,
      .num_paths = static_cast<std::uint64_t>(400'000),
      .seed = 4242,
      .antithetic = true,
      .control_variate = true,
      .qmc = quant::mc::McParams::Qmc::None,
      .bridge = quant::mc::McParams::Bridge::None,
      .num_steps = 1};
  quant::mc::McResult last{};
  for (auto _ : state) {
    last = quant::mc::price_european_call(mp);
    benchmark::DoNotOptimize(last.estimate.value);
  }
  state.counters["std_error"] = last.estimate.std_error;
}

static void BM_MC_Rmse_QMC(benchmark::State& state) {
  quant::mc::McParams mp{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.03,
      .dividend = 0.0,
      .vol = 0.2,
      .time = 1.0,
      .num_paths = static_cast<std::uint64_t>(400'000),
      .seed = 4242,
      .antithetic = true,
      .control_variate = true,
      .qmc = quant::mc::McParams::Qmc::Sobol,
      .bridge = quant::mc::McParams::Bridge::BrownianBridge,
      .num_steps = 64};
  quant::mc::McResult last{};
  for (auto _ : state) {
    last = quant::mc::price_european_call(mp);
    benchmark::DoNotOptimize(last.estimate.value);
  }
  state.counters["std_error"] = last.estimate.std_error;
}

BENCHMARK(BM_MC_PathsPerSecond)->Arg(1)->Arg(2)->Arg(4)->Arg(8);
BENCHMARK(BM_MC_Rmse_PRNG);
BENCHMARK(BM_MC_Rmse_QMC);

BENCHMARK_MAIN();
