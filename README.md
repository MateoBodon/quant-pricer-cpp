# quant-pricer-cpp

Modern C++20 quantitative pricer library with analytics, Monte Carlo, and PDE pricers. Includes CI, tests, and benchmarks.

## Build


## Run CLI

```bash
./build/quant_cli
```

## Benchmarks

```bash
./build/micro_bench --benchmark_min_time=0.01
```


## Features
- Analytic Black–Scholes prices and Greeks
- Monte Carlo with PCG64, antithetic and control variates, MC Greeks (pathwise/LRM)
- PDE Crank–Nicolson with Thomas solver
- OpenMP parallelization (optional), CI with sanitizers and clang-tidy, Doxygen docs

## Quickstart
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure | cat
```

## CLI Examples
```bash
./build/quant_cli bs 100 100 0.03 0.00 0.2 1.0 call
./build/quant_cli mc 100 100 0.03 0.00 0.2 1.0 200000 42 1
./build/quant_cli pde 100 100 0.03 0.00 0.2 1.0 call 201 200 4.0
```

## Benchmark (1e6 paths, Debug build)
```
BM_MC_1e6   ~0.10-0.12 s
```
Use Release for faster timings.
