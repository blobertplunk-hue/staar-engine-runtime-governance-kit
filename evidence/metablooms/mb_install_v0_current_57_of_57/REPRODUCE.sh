#!/usr/bin/env bash
# REPRODUCE.sh — Reproduce MB_INSTALL v0 current full-suite evidence
# Usage: bash REPRODUCE.sh  (run from anywhere; locates repo root via git)
set -euo pipefail

COMMIT="0b63bdc77e03bcbc01052c8adcabb80f2922318f"

cd "$(git rev-parse --show-toplevel)"
echo "Checking out commit $COMMIT ..."
git fetch origin "claude/new-session-g7ll2w"
git checkout "$COMMIT"

echo "Installing test dependencies ..."
python3 -m pip install jsonschema

echo "Running MB_INSTALL v0 full test suite ..."
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

echo "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
