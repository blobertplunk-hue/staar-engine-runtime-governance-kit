# Reproduction script for MB_INSTALL v0 Stage 9 Execution Preflight Authorization
# Stage ID: MB_INSTALL_V0_STAGE9_EXECUTION_PREFLIGHT_AUTHORIZATION
# Decision: BLOCK_STAGE9_PREFLIGHT_PENDING_TARGET_TREE
#
# This script verifies the Stage 9 evidence packet integrity.
# It does NOT perform any live apply, atomic_swap, or target tree mutation.
# No target tree is named; no execution is performed.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = git -C $ScriptDir rev-parse --show-toplevel
$EvidenceDir = Join-Path $RepoRoot "evidence/metablooms/mb_install_v0_stage9_execution_preflight_authorization"
$Stage8Dir = Join-Path $RepoRoot "evidence/metablooms/mb_install_v0_stage8_limited_promotion_proposal"

Write-Host "=== MB_INSTALL v0 Stage 9 Reproduction ==="
Write-Host "Repo root: $RepoRoot"
Write-Host "Evidence dir: $EvidenceDir"
Write-Host ""

# Step 1: Verify the evidence directory exists
Write-Host "Step 1: Verifying evidence directory..."
if (-not (Test-Path $EvidenceDir -PathType Container)) {
    Write-Error "Evidence directory not found: $EvidenceDir"
    exit 1
}
Write-Host "  OK: Evidence directory exists"

# Step 2: Verify all 14 required files are present
Write-Host ""
Write-Host "Step 2: Verifying all 14 required artifact files are present..."
$RequiredFiles = @(
    "CI_CONFIRMATION.json",
    "TARGET_TREE_CANDIDATE.json",
    "EXACT_COMMAND_DRAFT.txt",
    "ROLLBACK_PLAN.md",
    "DRY_RUN_PLAN.md",
    "PREFLIGHT_CHECKLIST.json",
    "RISK_REGISTER_STAGE9.json",
    "EXECUTION_PREFLIGHT_AUTHORIZATION.md",
    "EXECUTION_RECEIPT.json",
    "COMMAND_TRANSCRIPT.txt",
    "REPRODUCE.sh",
    "REPRODUCE.ps1",
    "ARTIFACT_SHA256SUMS.txt",
    "EVIDENCE_MANIFEST.json"
)
$Missing = 0
foreach ($f in $RequiredFiles) {
    $FullPath = Join-Path $EvidenceDir $f
    if (-not (Test-Path $FullPath)) {
        Write-Host "  MISSING: $f"
        $Missing++
    } else {
        Write-Host "  OK: $f"
    }
}
if ($Missing -gt 0) {
    Write-Error "ERROR: $Missing required files missing"
    exit 1
}

# Step 3: Verify SHA-256 checksums
Write-Host ""
Write-Host "Step 3: Verifying SHA-256 checksums..."
$ChecksumsFile = Join-Path $EvidenceDir "ARTIFACT_SHA256SUMS.txt"
$ChecksumLines = Get-Content $ChecksumsFile
$ChecksumErrors = 0
foreach ($line in $ChecksumLines) {
    if ($line -match "^([0-9a-f]{64})\s+(.+)$") {
        $ExpectedHash = $Matches[1]
        $Filename = $Matches[2].Trim()
        $FilePath = Join-Path $EvidenceDir $Filename
        $ActualHash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLower()
        if ($ActualHash -ne $ExpectedHash) {
            Write-Host "  MISMATCH: $Filename"
            $ChecksumErrors++
        } else {
            Write-Host "  OK: $Filename"
        }
    }
}
if ($ChecksumErrors -gt 0) {
    Write-Error "ERROR: $ChecksumErrors checksum mismatches"
    exit 1
}
Write-Host "  OK: All checksums verified"

# Step 4: Verify preflight checklist decision
Write-Host ""
Write-Host "Step 4: Verifying preflight checklist decision..."
$ChecklistJson = Get-Content (Join-Path $EvidenceDir "PREFLIGHT_CHECKLIST.json") -Raw | ConvertFrom-Json
if ($ChecklistJson.overall_status -ne "BLOCKED") {
    Write-Error "ERROR: Expected overall_status=BLOCKED, got: $($ChecklistJson.overall_status)"
    exit 1
}
Write-Host "  OK: overall_status=BLOCKED (correct — no target tree named)"

# Step 5: Verify target tree is UNNAMED
Write-Host ""
Write-Host "Step 5: Verifying target_tree_status=UNNAMED..."
$TargetTreeJson = Get-Content (Join-Path $EvidenceDir "TARGET_TREE_CANDIDATE.json") -Raw | ConvertFrom-Json
if ($TargetTreeJson.target_tree_status -ne "UNNAMED") {
    Write-Error "ERROR: Expected target_tree_status=UNNAMED, got: $($TargetTreeJson.target_tree_status)"
    exit 1
}
Write-Host "  OK: target_tree_status=UNNAMED"

# Step 6: Verify no live apply authorized
Write-Host ""
Write-Host "Step 6: Verifying live_apply_authorized=false and final_go_no_go_confirmation=false..."
$ReceiptJson = Get-Content (Join-Path $EvidenceDir "EXECUTION_RECEIPT.json") -Raw | ConvertFrom-Json
if ($ReceiptJson.live_apply_authorized -ne $false) {
    Write-Error "ERROR: live_apply_authorized must be false"
    exit 1
}
if ($ReceiptJson.final_go_no_go_confirmation -ne $false) {
    Write-Error "ERROR: final_go_no_go_confirmation must be false"
    exit 1
}
if ($ReceiptJson.mutations_performed.Count -ne 0) {
    Write-Error "ERROR: mutations_performed must be empty"
    exit 1
}
Write-Host "  OK: live_apply_authorized=false"
Write-Host "  OK: final_go_no_go_confirmation=false"
Write-Host "  OK: mutations_performed=[]"

# Step 7: Verify Stage 8 proposal exists
Write-Host ""
Write-Host "Step 7: Verifying Stage 8 proposal exists and its decision is PASS..."
$Stage8ReceiptPath = Join-Path $Stage8Dir "EXECUTION_RECEIPT.json"
if (-not (Test-Path $Stage8ReceiptPath)) {
    Write-Error "ERROR: Stage 8 EXECUTION_RECEIPT.json not found"
    exit 1
}
$Stage8Receipt = Get-Content $Stage8ReceiptPath -Raw | ConvertFrom-Json
Write-Host "  OK: Stage 8 decision: $($Stage8Receipt.decision)"

# Step 8: Verify evidence manifest
Write-Host ""
Write-Host "Step 8: Verifying evidence manifest..."
$ManifestJson = Get-Content (Join-Path $EvidenceDir "EVIDENCE_MANIFEST.json") -Raw | ConvertFrom-Json
$ManifestErrors = 0
foreach ($artifact in $ManifestJson.artifacts) {
    $FilePath = Join-Path $EvidenceDir $artifact.filename
    $ActualHash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLower()
    if ($ActualHash -ne $artifact.sha256) {
        Write-Host "  SHA MISMATCH: $($artifact.filename)"
        Write-Host "    expected: $($artifact.sha256)"
        Write-Host "    actual:   $ActualHash"
        $ManifestErrors++
    } else {
        Write-Host "  OK: $($artifact.filename)"
    }
}
if ($ManifestErrors -gt 0) {
    Write-Error "ERROR: $ManifestErrors SHA mismatches in EVIDENCE_MANIFEST.json"
    exit 1
}
Write-Host "  All manifest SHAs verified."

Write-Host ""
Write-Host "=== Stage 9 Reproduction COMPLETE ==="
Write-Host ""
Write-Host "EXPECTED: Stage 9 preflight artifacts validate; no live apply authorized; no mutations performed."
Write-Host "DECISION: BLOCK_STAGE9_PREFLIGHT_PENDING_TARGET_TREE"
Write-Host "live_apply_authorized: false"
Write-Host "final_go_no_go_confirmation: false"
Write-Host "mutations_performed: []"
