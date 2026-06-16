# REPRODUCE.ps1 - Reproduce MB_INSTALL v0 current full-suite evidence
# Usage: pwsh REPRODUCE.ps1  (run from anywhere inside the repo)
$ErrorActionPreference = "Stop"

$Commit = "0b63bdc77e03bcbc01052c8adcabb80f2922318f"

$RepoRoot = git rev-parse --show-toplevel
Set-Location $RepoRoot

Write-Host "Checking out commit $Commit ..."
git fetch origin "claude/new-session-g7ll2w"
git checkout $Commit

Write-Host "Installing test dependencies ..."
python3 -m pip install jsonschema

Write-Host "Running MB_INSTALL v0 full test suite ..."
python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v

Write-Host "EXPECTED: 57 tests, 57 passed, 0 failures, 0 errors"
