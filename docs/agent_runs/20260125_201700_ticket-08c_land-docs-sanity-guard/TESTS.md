# TESTS

- Failed: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j && ctest --test-dir build -L FAST --output-on-failure && ctest --test-dir build -R docs_sanity_fast --output-on-failure`
  - Error: `cmake: command not found`.
