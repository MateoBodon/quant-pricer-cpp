#include <benchmark/benchmark.h>
#include "quant/mc.hpp"
#include "quant/asian.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/barrier.hpp"

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

static quant::asian::McParams make_asian_params(quant::asian::Qmc mode) {
  const std::uint64_t paths = mode == quant::asian::Qmc::None ? 400'000 : 220'000;
  return quant::asian::McParams{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.02,
      .dividend = 0.0,
      .vol = 0.2,
      .time = 1.0,
      .num_paths = paths,
      .seed = 2025,
      .num_steps = 64,
      .antithetic = true,
      .use_geometric_cv = true,
      .payoff = quant::asian::Payoff::FixedStrike,
      .avg = quant::asian::Average::Arithmetic,
      .qmc = mode};
}

static void BM_MC_EqualTime_Asian_PRNG(benchmark::State& state) {
  auto params = make_asian_params(quant::asian::Qmc::None);
  quant::asian::McStatistic last{};
  for (auto _ : state) {
    last = quant::asian::price_mc(params);
    benchmark::DoNotOptimize(last.value);
  }
  state.counters["std_error"] = last.std_error;
}

static void BM_MC_EqualTime_Asian_QMC(benchmark::State& state) {
  auto params = make_asian_params(quant::asian::Qmc::SobolScrambled);
  quant::asian::McStatistic last{};
  for (auto _ : state) {
    last = quant::asian::price_mc(params);
    benchmark::DoNotOptimize(last.value);
  }
  state.counters["std_error"] = last.std_error;
}

static quant::mc::McParams make_barrier_params(quant::mc::McParams::Qmc mode) {
  const std::uint64_t paths = mode == quant::mc::McParams::Qmc::None ? 300'000 : 180'000;
  quant::mc::McParams params{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.02,
      .dividend = 0.0,
      .vol = 0.25,
      .time = 1.0,
      .num_paths = paths,
      .seed = 1337,
      .antithetic = true,
      .control_variate = true,
      .rng = quant::rng::Mode::Counter,
      .qmc = mode,
      .bridge = mode == quant::mc::McParams::Qmc::None ? quant::mc::McParams::Bridge::None
                                                       : quant::mc::McParams::Bridge::BrownianBridge,
      .num_steps = 32};
  return params;
}

static void BM_MC_EqualTime_Barrier_PRNG(benchmark::State& state) {
  auto params = make_barrier_params(quant::mc::McParams::Qmc::None);
  quant::BarrierSpec spec{quant::BarrierType::DownOut, 80.0, 0.0};
  quant::mc::McResult last{};
  for (auto _ : state) {
    last = quant::mc::price_barrier_option(params, params.strike, quant::OptionType::Call, spec);
    benchmark::DoNotOptimize(last.estimate.value);
  }
  state.counters["std_error"] = last.estimate.std_error;
}

static void BM_MC_EqualTime_Barrier_QMC(benchmark::State& state) {
  auto params = make_barrier_params(quant::mc::McParams::Qmc::SobolScrambled);
  quant::BarrierSpec spec{quant::BarrierType::DownOut, 80.0, 0.0};
  quant::mc::McResult last{};
  for (auto _ : state) {
    last = quant::mc::price_barrier_option(params, params.strike, quant::OptionType::Call, spec);
    benchmark::DoNotOptimize(last.estimate.value);
  }
  state.counters["std_error"] = last.estimate.std_error;
}

BENCHMARK(BM_MC_EqualTime_Asian_PRNG)->Name("BM_MC_EqualTime/Asian/PRNG");
BENCHMARK(BM_MC_EqualTime_Asian_QMC)->Name("BM_MC_EqualTime/Asian/QMC");
BENCHMARK(BM_MC_EqualTime_Barrier_PRNG)->Name("BM_MC_EqualTime/Barrier/PRNG");
BENCHMARK(BM_MC_EqualTime_Barrier_QMC)->Name("BM_MC_EqualTime/Barrier/QMC");

BENCHMARK_MAIN();
