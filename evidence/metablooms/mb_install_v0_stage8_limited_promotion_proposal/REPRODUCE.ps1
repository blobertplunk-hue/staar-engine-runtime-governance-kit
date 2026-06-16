# REPRODUCE.ps1 - Verify MB_INSTALL v0 Stage 8 limited promotion proposal artifacts
# Usage: pwsh REPRODUCE.ps1  (run from anywhere inside the repo)
$ErrorActionPreference = "Stop"

$Stage7Commit   = "6b5cc7e95278ab2b03fcb9ae24ef749d22cf1d49"
$Stage6Commit   = "298050f756f6cba3c3ffba7eb8365a7bd7255f8d"
$Evidence57     = "92eecde7ac009d466c6f94801c81f63ed3772b2b"
$TestedCommit   = "0b63bdc77e03bcbc01052c8adcabb80f2922318f"
$Stage8Evidence = "evidence/metablooms/mb_install_v0_stage8_limited_promotion_proposal"

$RepoRoot = git rev-parse --show-toplevel
Set-Location $RepoRoot

Write-Host "=== Step 1: Verify Stage 8 artifact SHA chain ==="
Set-Location (Join-Path $RepoRoot $Stage8Evidence)
$lines = Get-Content ARTIFACT_SHA256SUMS.txt
foreach ($line in $lines) {
    $parts = $line -split '  ', 2
    $expected = $parts[0]; $fname = $parts[1]
    $actual = (Get-FileHash $fname -Algorithm SHA256).Hash.ToLower()
    if ($actual -eq $expected) { Write-Host "${fname}: OK" }
    else { Write-Host "${fname}: MISMATCH"; exit 1 }
}

Write-Host "=== Step 2: Confirm authorization scope has live_apply_authorized=false ==="
python3 -c @"
import json, sys
scope = json.loads(open('AUTHORIZATION_SCOPE.json').read())
fields = ['live_apply_authorized','protected_surface_write_authorized','prune_authorized',
          'rollback_authorized','staging_swap_authorized','target_tree_authorized',
          'atomic_swap_authorized','delete_authorized']
ok = True
for f in fields:
    val = scope.get(f)
    status = 'OK (false)' if val is False else f'FAIL (expected false, got {repr(val)})'
    print(f'{f}: {status}')
    if val is not False: ok = False
sys.exit(0 if ok else 1)
"@

Write-Host "=== Step 3: Confirm no mutations performed ==="
python3 -c @"
import json, sys
r = json.loads(open('EXECUTION_RECEIPT.json').read())
mp = r.get('mutations_performed', [])
print('mutations_performed:', mp)
if mp: sys.exit(1)
print('OK: no mutations performed')
"@

Write-Host ""
Write-Host "EXPECTED: Stage 8 proposal artifacts validate; no live apply authorized; no mutations performed."
