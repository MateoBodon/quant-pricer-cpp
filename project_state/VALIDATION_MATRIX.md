# Validation Matrix

| Check | Command | Proves | Expected cost | When required |
|---|---|---|---|---|
| Git state | `git status --short` | Exact dirty/untracked state | Fast | Every ticket |
| Bundle helper syntax | `python3 -m compileall tools/agentic/ai_os_bundle.py` | New bundle/archive helper parses | Fast | Bundle/tooling changes |
| Data policy | `python3 scripts/check_data_policy.py` | Tracked data/artifacts avoid restricted raw WRDS fields | Fast | Data/docs/bundle changes touching artifacts |
| Configure | `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` | CMake config and dependency discovery still work | Fast/medium | Code/build/test changes; T-000 baseline |
| Build | `cmake --build build -j` | C++ targets compile | Medium | Code/build/test changes; T-000 baseline |
| FAST suite | `ctest --test-dir build -L FAST --output-on-failure` | Unit, docs, artifact, policy, and sample-pipeline guards | Medium | Most nontrivial tickets |
| Sample reproduction | `REPRO_FAST=1 WRDS_USE_SAMPLE=1 ./scripts/reproduce_all.sh` | Curated sample artifacts regenerate through official pipeline | Heavy/medium | Result/artifact/claim changes |
| Validation pack | `python3 scripts/package_validation.py --artifacts docs/artifacts --output docs/validation_pack.zip` | Release validation pack can be rebuilt | Fast after artifacts exist | Release/result packaging |
| MARKET tests | `ctest --test-dir build -L MARKET --output-on-failure` | Live/local WRDS market path when enabled | Gated/heavy | Explicit market-data tickets only |

## T-000 Validation Level

T-000 is a docs/tooling/state ticket. Required validation is L1/L2 targeted:

- Git state.
- Bundle helper syntax.
- Data-policy guard.
- CMake configure/build.
- FAST CTest suite if environment allows.
- Bundle generation and manifest inspection.

Full sample reproduction is intentionally deferred unless Pro/Heavy decides a metrics refresh is part of the next phase.
