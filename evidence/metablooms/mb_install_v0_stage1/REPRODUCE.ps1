# REPRODUCE.ps1 - Reproduce MB_INSTALL v0 Stage 1 evidence
# Usage: pwsh REPRODUCE.ps1  (run from anywhere inside the repo)
$ErrorActionPreference = "Stop"

$Commit = "d8738e27ec7d588434cbea111cf82cdf61e08e9c"

$RepoRoot = git rev-parse --show-toplevel
Set-Location $RepoRoot

Write-Host "Checking out commit $Commit ..."
git fetch origin "claude/new-session-g7ll2w"
git checkout $Commit

Write-Host "Installing test dependencies ..."
python3 -m pip install jsonschema

Write-Host "Running MB_INSTALL v0 Stage 1 tests ..."
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

Write-Host "EXPECTED: 42 tests, 42 passed, 0 failures, 0 errors"
