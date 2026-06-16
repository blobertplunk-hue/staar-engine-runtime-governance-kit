#!/usr/bin/env bash
# REPRODUCE.sh — Independently reproduce MB_INSTALL v0 Stage 6 evidence
# Usage: bash REPRODUCE.sh  (run from anywhere; locates repo root via git)
set -euo pipefail

TESTED_COMMIT="0b63bdc77e03bcbc01052c8adcabb80f2922318f"
EVIDENCE_COMMIT="92eecde7ac009d466c6f94801c81f63ed3772b2b"
WORKTREE_PATH="/tmp/mb_stage6_repro_$$"

REPO_ROOT="$(git rev-parse --show-toplevel)"

echo "Creating clean worktree at $TESTED_COMMIT ..."
git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$TESTED_COMMIT"

cleanup() { git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true; }
trap cleanup EXIT

echo "Installing test dependencies ..."
python3 -m pip install jsonschema -q

echo "Running MB_INSTALL v0 full test suite from clean worktree ..."
cd "$WORKTREE_PATH"
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

echo ""
echo "Verifying evidence packet at commit $EVIDENCE_COMMIT ..."
cd "$REPO_ROOT"
git checkout "$EVIDENCE_COMMIT" -- evidence/metablooms/mb_install_v0_current_57_of_57/ 2>/dev/null || \
  git show "$EVIDENCE_COMMIT":evidence/metablooms/mb_install_v0_current_57_of_57/ARTIFACT_SHA256SUMS.txt > /dev/null
echo "Evidence packet present."

echo "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
