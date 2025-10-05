# Contributing

Thanks for your interest in improving quant-pricer-cpp! This project values correctness, reproducibility, and small, focused changes.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
```

## Tests

```bash
ctest --test-dir build --output-on-failure
```

## Demo artifacts

```bash
./scripts/demo.sh
ls -1 artifacts
```

## Coding style

- C++20, prefer explicit over implicit conversions
- Keep headers self-contained under `include/quant/`
- Add unit tests for new features
- Run benchmarks for perf-sensitive changes

## Pull requests

- Keep commits small with clear messages
- Include rationale and validation (tests/benchmarks/artifacts)
- Avoid unrelated refactors in the same PR

