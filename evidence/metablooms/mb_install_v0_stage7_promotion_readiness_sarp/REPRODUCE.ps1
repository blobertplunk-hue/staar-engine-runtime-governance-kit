# REPRODUCE.ps1 - Reproduce MB_INSTALL v0 Stage 7 SARP promotion-readiness review
# Usage: pwsh REPRODUCE.ps1  (run from anywhere inside the repo)
$ErrorActionPreference = "Stop"

$TestedCommit = "0b63bdc77e03bcbc01052c8adcabb80f2922318f"
$Evidence57Commit = "92eecde7ac009d466c6f94801c81f63ed3772b2b"
$WorktreePath = Join-Path ([System.IO.Path]::GetTempPath()) "mb_stage7_repro_$PID"
$RepoRoot = git rev-parse --show-toplevel

Write-Host "=== Step 1: Clean worktree at tested commit ==="
git -C $RepoRoot worktree add $WorktreePath $TestedCommit

try {
    Write-Host "=== Step 2: Run full test suite ==="
    python3 -m pip install jsonschema -q
    Set-Location $WorktreePath
    python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

    Write-Host "=== Step 3: Verify FM coverage matrix has no PENDING rows ==="
    python3 -c @"
import json, pathlib, sys
m = json.loads(pathlib.Path('contracts/MB_INSTALL_FM_COVERAGE_MATRIX_v1.json').read_text())
pending = [r['fm'] for r in m['rows'] if r['fixture'].startswith('PENDING')]
if pending:
    print('FAIL: PENDING FM rows remain:', pending); sys.exit(1)
print('PASS: All FM rows have live fixtures:', [r['fm'] for r in m['rows']])
"@
} finally {
    git -C $RepoRoot worktree remove --force $WorktreePath 2>$null
}

Write-Host ""
Write-Host "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
Write-Host "DECISION: PASS_READY_FOR_LIMITED_PROMOTION_PROPOSAL"
Write-Host "BLOCKER: RISK-01 (live-tree apply not authorized — process gate, not code defect)"
