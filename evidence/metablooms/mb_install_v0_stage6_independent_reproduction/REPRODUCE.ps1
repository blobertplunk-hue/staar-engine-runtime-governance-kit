# REPRODUCE.ps1 - Independently reproduce MB_INSTALL v0 Stage 6 evidence
# Usage: pwsh REPRODUCE.ps1  (run from anywhere inside the repo)
$ErrorActionPreference = "Stop"

$TestedCommit = "0b63bdc77e03bcbc01052c8adcabb80f2922318f"
$EvidenceCommit = "92eecde7ac009d466c6f94801c81f63ed3772b2b"
$WorktreePath = Join-Path ([System.IO.Path]::GetTempPath()) "mb_stage6_repro_$PID"

$RepoRoot = git rev-parse --show-toplevel

Write-Host "Creating clean worktree at $TestedCommit ..."
git -C $RepoRoot worktree add $WorktreePath $TestedCommit

try {
    Write-Host "Installing test dependencies ..."
    python3 -m pip install jsonschema -q

    Write-Host "Running MB_INSTALL v0 full test suite from clean worktree ..."
    Set-Location $WorktreePath
    python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v
} finally {
    git -C $RepoRoot worktree remove --force $WorktreePath 2>$null
}

Write-Host "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
