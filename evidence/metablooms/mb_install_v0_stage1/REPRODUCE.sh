#!/usr/bin/env bash
# REPRODUCE.sh — Reproduce MB_INSTALL v0 Stage 1 evidence
# Usage: bash REPRODUCE.sh  (run from anywhere; locates repo root via git)
set -euo pipefail

COMMIT="d8738e27ec7d588434cbea111cf82cdf61e08e9c"

cd "$(git rev-parse --show-toplevel)"
echo "Checking out commit $COMMIT ..."
git fetch origin "claude/new-session-g7ll2w"
git checkout "$COMMIT"

echo "Installing test dependencies ..."
python3 -m pip install jsonschema

echo "Running MB_INSTALL v0 Stage 1 tests ..."
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

echo "EXPECTED: 42 tests, 42 passed, 0 failures, 0 errors"
