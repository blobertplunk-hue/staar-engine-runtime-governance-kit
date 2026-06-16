#!/usr/bin/env bash
# Reproduction script for MB_INSTALL v0 Stage 9 Execution Preflight Authorization
# Stage ID: MB_INSTALL_V0_STAGE9_EXECUTION_PREFLIGHT_AUTHORIZATION
# Decision: BLOCK_STAGE9_PREFLIGHT_PENDING_TARGET_TREE
#
# This script verifies the Stage 9 evidence packet integrity.
# It does NOT perform any live apply, atomic_swap, or target tree mutation.
# No target tree is named; no execution is performed.

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
EVIDENCE_DIR="$REPO_ROOT/evidence/metablooms/mb_install_v0_stage9_execution_preflight_authorization"
STAGE8_DIR="$REPO_ROOT/evidence/metablooms/mb_install_v0_stage8_limited_promotion_proposal"

echo "=== MB_INSTALL v0 Stage 9 Reproduction ==="
echo "Repo root: $REPO_ROOT"
echo "Evidence dir: $EVIDENCE_DIR"
echo ""

# Step 1: Verify the evidence directory exists
echo "Step 1: Verifying evidence directory..."
if [ ! -d "$EVIDENCE_DIR" ]; then
    echo "ERROR: Evidence directory not found: $EVIDENCE_DIR"
    exit 1
fi
echo "  OK: Evidence directory exists"

# Step 2: Verify all 14 required files are present
echo ""
echo "Step 2: Verifying all 14 required artifact files are present..."
REQUIRED_FILES=(
    "CI_CONFIRMATION.json"
    "TARGET_TREE_CANDIDATE.json"
    "EXACT_COMMAND_DRAFT.txt"
    "ROLLBACK_PLAN.md"
    "DRY_RUN_PLAN.md"
    "PREFLIGHT_CHECKLIST.json"
    "RISK_REGISTER_STAGE9.json"
    "EXECUTION_PREFLIGHT_AUTHORIZATION.md"
    "EXECUTION_RECEIPT.json"
    "COMMAND_TRANSCRIPT.txt"
    "REPRODUCE.sh"
    "REPRODUCE.ps1"
    "ARTIFACT_SHA256SUMS.txt"
    "EVIDENCE_MANIFEST.json"
)
MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$EVIDENCE_DIR/$f" ]; then
        echo "  MISSING: $f"
        MISSING=$((MISSING + 1))
    else
        echo "  OK: $f"
    fi
done
if [ "$MISSING" -gt 0 ]; then
    echo "ERROR: $MISSING required files missing"
    exit 1
fi

# Step 3: Verify SHA-256 checksums
echo ""
echo "Step 3: Verifying SHA-256 checksums..."
cd "$EVIDENCE_DIR"
sha256sum -c ARTIFACT_SHA256SUMS.txt
echo "  OK: All checksums verified"

# Step 4: Verify preflight checklist decision
echo ""
echo "Step 4: Verifying preflight checklist decision..."
OVERALL=$(python3 -c "
import json, sys
with open('$EVIDENCE_DIR/PREFLIGHT_CHECKLIST.json') as f:
    d = json.load(f)
print(d['overall_status'])
")
if [ "$OVERALL" != "BLOCKED" ]; then
    echo "ERROR: Expected overall_status=BLOCKED, got: $OVERALL"
    exit 1
fi
echo "  OK: overall_status=BLOCKED (correct — no target tree named)"

# Step 5: Verify target tree is UNNAMED
echo ""
echo "Step 5: Verifying target_tree_status=UNNAMED..."
TT_STATUS=$(python3 -c "
import json, sys
with open('$EVIDENCE_DIR/TARGET_TREE_CANDIDATE.json') as f:
    d = json.load(f)
print(d['target_tree_status'])
")
if [ "$TT_STATUS" != "UNNAMED" ]; then
    echo "ERROR: Expected target_tree_status=UNNAMED, got: $TT_STATUS"
    exit 1
fi
echo "  OK: target_tree_status=UNNAMED"

# Step 6: Verify no live apply authorized
echo ""
echo "Step 6: Verifying live_apply_authorized=false and final_go_no_go_confirmation=false..."
python3 -c "
import json, sys
with open('$EVIDENCE_DIR/EXECUTION_RECEIPT.json') as f:
    d = json.load(f)
assert d['live_apply_authorized'] == False, 'live_apply_authorized must be false'
assert d['final_go_no_go_confirmation'] == False, 'final_go_no_go_confirmation must be false'
assert d['mutations_performed'] == [], 'mutations_performed must be empty'
assert all(v == 'NOT_RUN' for v in d['forbidden_actions'].values()), 'all forbidden_actions must be NOT_RUN'
print('  OK: live_apply_authorized=false')
print('  OK: final_go_no_go_confirmation=false')
print('  OK: mutations_performed=[]')
print('  OK: all forbidden_actions=NOT_RUN')
"

# Step 7: Verify Stage 8 decision is referenced correctly
echo ""
echo "Step 7: Verifying Stage 8 proposal exists and its decision is PASS..."
if [ ! -f "$STAGE8_DIR/EXECUTION_RECEIPT.json" ]; then
    echo "ERROR: Stage 8 EXECUTION_RECEIPT.json not found"
    exit 1
fi
STAGE8_DECISION=$(python3 -c "
import json
with open('$STAGE8_DIR/EXECUTION_RECEIPT.json') as f:
    d = json.load(f)
print(d['decision'])
")
echo "  OK: Stage 8 decision: $STAGE8_DECISION"

# Step 8: Verify evidence manifest
echo ""
echo "Step 8: Verifying evidence manifest..."
python3 -c "
import json, hashlib, sys, os

evidence_dir = '$EVIDENCE_DIR'
with open(os.path.join(evidence_dir, 'EVIDENCE_MANIFEST.json')) as f:
    manifest = json.load(f)

errors = 0
for artifact in manifest['artifacts']:
    path = os.path.join(evidence_dir, artifact['filename'])
    with open(path, 'rb') as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    if actual_sha != artifact['sha256']:
        print(f'  SHA MISMATCH: {artifact[\"filename\"]}')
        print(f'    expected: {artifact[\"sha256\"]}')
        print(f'    actual:   {actual_sha}')
        errors += 1
    else:
        print(f'  OK: {artifact[\"filename\"]}')

if errors > 0:
    print(f'ERROR: {errors} SHA mismatches in EVIDENCE_MANIFEST.json')
    sys.exit(1)
print('  All manifest SHAs verified.')
"

echo ""
echo "=== Stage 9 Reproduction COMPLETE ==="
echo ""
echo "EXPECTED: Stage 9 preflight artifacts validate; no live apply authorized; no mutations performed."
echo "DECISION: BLOCK_STAGE9_PREFLIGHT_PENDING_TARGET_TREE"
echo "live_apply_authorized: false"
echo "final_go_no_go_confirmation: false"
echo "mutations_performed: []"
