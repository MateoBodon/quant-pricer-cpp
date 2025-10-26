#!/usr/bin/env bash
set -euo pipefail

# Remove accidentally committed build outputs and install trees
git rm -rf --cached install || true
git rm -rf --cached examples/consumer-cmake/build || true
git rm -f --cached build/install_manifest.txt || true

echo "Removed tracked build artifacts from Git index."
echo "Consider adding a commit with these deletions and pushing."

