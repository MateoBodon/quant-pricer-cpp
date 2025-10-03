#include <benchmark/benchmark.h>
#include "quant/mc.hpp"

static void BM_MC_1e6(benchmark::State& state) {
  quant::mc::McParams mp{
      .spot = 100.0,
      .strike = 100.0,
      .rate = 0.02,
      .dividend = 0.0,
      .vol = 0.2,
      .time = 1.0,
      .num_paths = static_cast<std::uint64_t>(1'000'000),
      .seed = 1337,
      .antithetic = true,
      .control_variate = true};
  for (auto _ : state) {
    auto res = quant::mc::price_european_call(mp);
    benchmark::DoNotOptimize(res.estimate.value);
    benchmark::ClobberMemory();
  }
}

BENCHMARK(BM_MC_1e6);

BENCHMARK_MAIN();

