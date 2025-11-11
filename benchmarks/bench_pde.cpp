#include <benchmark/benchmark.h>
#include <cmath>

#include "quant/american.hpp"
#include "quant/black_scholes.hpp"
#include "quant/pde.hpp"

static void BM_PDE_WallTime(benchmark::State& state) {
    const int M = static_cast<int>(state.range(0));
    const int N = static_cast<int>(state.range(1));
    quant::pde::PdeParams params{.spot = 100.0,
                                 .strike = 100.0,
                                 .rate = 0.03,
                                 .dividend = 0.01,
                                 .vol = 0.2,
                                 .time = 1.0,
                                 .type = quant::OptionType::Call,
                                 .grid = quant::pde::GridSpec{M, N, 4.0, 2.0},
                                 .log_space = true,
                                 .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
                                 .compute_theta = false,
                                 .use_rannacher = true};
    quant::pde::PdeResult last{};
    for (auto _ : state) {
        last = quant::pde::price_crank_nicolson(params);
        benchmark::DoNotOptimize(last.price);
    }
    state.counters["price"] = last.price;
}

static void BM_PSOR_Iterations(benchmark::State& state) {
    const double omega = static_cast<double>(state.range(0)) / 100.0;
    quant::american::PsorParams params{.base = {.spot = 100.0,
                                                .strike = 100.0,
                                                .rate = 0.05,
                                                .dividend = 0.02,
                                                .vol = 0.25,
                                                .time = 1.0,
                                                .type = quant::OptionType::Put},
                                       .grid = quant::pde::GridSpec{181, 180, 4.0, 2.0},
                                       .log_space = true,
                                       .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
                                       .stretch = 2.0,
                                       .omega = omega,
                                       .max_iterations = 8000,
                                       .tolerance = 1e-8,
                                       .use_rannacher = true};
    quant::american::PsorResult last{};
    for (auto _ : state) {
        last = quant::american::price_psor(params);
        benchmark::DoNotOptimize(last.price);
    }
    state.counters["iterations"] = static_cast<double>(last.total_iterations);
    state.counters["residual"] = last.max_residual;
}

static void BM_PDE_OrderSlope(benchmark::State& state) {
    const int M = static_cast<int>(state.range(0));
    const int N = static_cast<int>(state.range(1));
    quant::pde::PdeParams params{.spot = 100.0,
                                 .strike = 100.0,
                                 .rate = 0.03,
                                 .dividend = 0.01,
                                 .vol = 0.2,
                                 .time = 1.0,
                                 .type = quant::OptionType::Call,
                                 .grid = quant::pde::GridSpec{M, N, 4.0, 2.0},
                                 .log_space = true,
                                 .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
                                 .compute_theta = false,
                                 .use_rannacher = true};
    const double ref = quant::bs::call_price(params.spot, params.strike, params.rate, params.dividend,
                                             params.vol, params.time);
    quant::pde::PdeResult last{};
    for (auto _ : state) {
        last = quant::pde::price_crank_nicolson(params);
        benchmark::DoNotOptimize(last.price);
    }
    state.counters["abs_error"] = std::abs(last.price - ref);
}

BENCHMARK(BM_PDE_WallTime)->Args({101, 100})->Args({201, 200})->Args({321, 320});
BENCHMARK(BM_PSOR_Iterations)->DenseRange(110, 190, 20);
BENCHMARK(BM_PDE_OrderSlope)->Args({101, 100})->Args({161, 160})->Args({201, 200})->Args({321, 320});

BENCHMARK_MAIN();
