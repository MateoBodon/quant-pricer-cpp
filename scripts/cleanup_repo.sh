#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"

# Remove accidentally committed build outputs and install trees
git rm -rf --cached install || true
git rm -rf --cached examples/consumer-cmake/build || true
git rm -f --cached build/install_manifest.txt || true

# Tidy local build artifacts that accumulate over time
find "${ROOT}/build" -maxdepth 1 -type f -name 'compile_commands*.json' ! -name 'compile_commands.json' -delete || true
find "${ROOT}/build" -maxdepth 1 -type f -name 'libquant_pricer *.a' -delete || true
find "${ROOT}/artifacts" -type f -name '* [0-9].*' -delete || true

echo "Removed tracked build artifacts from Git index."
echo "Consider adding a commit with these deletions and pushing."
