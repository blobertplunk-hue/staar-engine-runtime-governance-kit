#!/usr/bin/env bash
# REPRODUCE.sh — Reproduce MB_INSTALL v0 Stage 7 SARP promotion-readiness review
# Usage: bash REPRODUCE.sh  (run from anywhere; locates repo root via git)
set -euo pipefail

TESTED_COMMIT="0b63bdc77e03bcbc01052c8adcabb80f2922318f"
EVIDENCE_57_COMMIT="92eecde7ac009d466c6f94801c81f63ed3772b2b"
STAGE6_COMMIT="298050f756f6cba3c3ffba7eb8365a7bd7255f8d"
WORKTREE_PATH="/tmp/mb_stage7_repro_$$"

REPO_ROOT="$(git rev-parse --show-toplevel)"

echo "=== Step 1: Clean worktree at tested commit ==="
git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$TESTED_COMMIT"
cleanup() { git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH" 2>/dev/null || true; }
trap cleanup EXIT

echo "=== Step 2: Run full test suite ==="
python3 -m pip install jsonschema -q
cd "$WORKTREE_PATH"
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

echo "=== Step 3: Verify FM coverage matrix has no PENDING rows ==="
python3 -c "
import json, pathlib, sys
m = json.loads(pathlib.Path('contracts/MB_INSTALL_FM_COVERAGE_MATRIX_v1.json').read_text())
pending = [r['fm'] for r in m['rows'] if r['fixture'].startswith('PENDING')]
if pending:
    print('FAIL: PENDING FM rows remain:', pending); sys.exit(1)
print('PASS: All FM rows have live fixtures:', [r['fm'] for r in m['rows']])
"

echo "=== Step 4: Verify current-57-evidence packet integrity ==="
cd "$REPO_ROOT"
git show "$EVIDENCE_57_COMMIT":evidence/metablooms/mb_install_v0_current_57_of_57/ARTIFACT_SHA256SUMS.txt \
  > /tmp/stage7_check_sums.txt
python3 -c "
import hashlib, pathlib, sys
lines = open('/tmp/stage7_check_sums.txt').readlines()
base = pathlib.Path('evidence/metablooms/mb_install_v0_current_57_of_57')
ok = True
for line in lines:
    expected_sha, fname = line.strip().split('  ', 1)
    actual = hashlib.sha256((base / fname).read_bytes()).hexdigest()
    status = 'OK' if actual == expected_sha else 'MISMATCH'
    print(f'{fname}: {status}')
    if actual != expected_sha: ok = False
sys.exit(0 if ok else 1)
"

echo ""
echo "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
echo "DECISION: PASS_READY_FOR_LIMITED_PROMOTION_PROPOSAL"
echo "BLOCKER: RISK-01 (live-tree apply not authorized — process gate, not code defect)"
