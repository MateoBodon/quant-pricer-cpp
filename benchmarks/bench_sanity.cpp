#include <benchmark/benchmark.h>

static void BM_NoOp(benchmark::State& state) {
    for (auto _ : state) {
        benchmark::DoNotOptimize(state.iterations());
    }
}

BENCHMARK(BM_NoOp);

BENCHMARK_MAIN();
