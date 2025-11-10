# WORKLOG

## 2025-11-10
- Hardened the Doxygen GitHub Pages workflow (main + tags) and removed the legacy duplicate job.
- Swapped the README docs badge to track the docs deployment workflow status.
- Commands run: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel && ctest --test-dir build -L FAST --output-on-failure -VV` (2×).
- Artifacts: n/a (CI-only workflow updates).
