# Commands

- Inspected the isolated worktree at exact `origin/main` base `0318d95d12a947cef2fde2d8932fffd969998bb5`.
- Audited v0.3.2 release assets, frozen metrics, validation pack, API examples, and the verified Heston candidate receipt.
- Ran `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`.
- Ran `cmake --build build -j`.
- Ran `ctest --test-dir build -L FAST --output-on-failure`.
- Ran focused presentation-relevant FAST guards after restoring test-generated artifact churn.
- Syntax-checked the published C++ first-price snippet, installed the built package to a temporary prefix, configured/built `examples/consumer-cmake` against it, and ran the consumer probe.
