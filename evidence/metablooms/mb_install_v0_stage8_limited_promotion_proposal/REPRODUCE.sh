#!/usr/bin/env bash
# REPRODUCE.sh — Verify MB_INSTALL v0 Stage 8 limited promotion proposal artifacts
# Usage: bash REPRODUCE.sh  (run from anywhere; locates repo root via git)
set -euo pipefail

STAGE7_COMMIT="6b5cc7e95278ab2b03fcb9ae24ef749d22cf1d49"
STAGE6_COMMIT="298050f756f6cba3c3ffba7eb8365a7bd7255f8d"
EVIDENCE_57_COMMIT="92eecde7ac009d466c6f94801c81f63ed3772b2b"
TESTED_COMMIT="0b63bdc77e03bcbc01052c8adcabb80f2922318f"
STAGE8_EVIDENCE="evidence/metablooms/mb_install_v0_stage8_limited_promotion_proposal"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "=== Step 1: Verify Stage 8 artifact SHA chain ==="
cd "$REPO_ROOT/$STAGE8_EVIDENCE"
sha256sum -c ARTIFACT_SHA256SUMS.txt

echo "=== Step 2: Verify EVIDENCE_MANIFEST.json artifact pins ==="
python3 -c "
import json, hashlib, pathlib, sys
base = pathlib.Path('.')
manifest = json.loads((base / 'EVIDENCE_MANIFEST.json').read_text())
ok = True
for name, expected in manifest['artifacts'].items():
    actual = hashlib.sha256((base / name).read_bytes()).hexdigest()
    status = 'OK' if actual == expected else f'MISMATCH got={actual}'
    print(f'{name}: {status}')
    if actual != expected: ok = False
sys.exit(0 if ok else 1)
"

echo "=== Step 3: Confirm authorization scope has live_apply_authorized=false ==="
python3 -c "
import json, sys
scope = json.loads(open('AUTHORIZATION_SCOPE.json').read())
fields = ['live_apply_authorized','protected_surface_write_authorized','prune_authorized',
          'rollback_authorized','staging_swap_authorized','target_tree_authorized',
          'atomic_swap_authorized','delete_authorized']
ok = True
for f in fields:
    val = scope.get(f)
    status = 'OK (false)' if val is False else f'FAIL (expected false, got {val!r})'
    print(f'{f}: {status}')
    if val is not False: ok = False
sys.exit(0 if ok else 1)
"

echo "=== Step 4: Confirm EXECUTION_RECEIPT.json mutations_performed is empty ==="
python3 -c "
import json, sys
r = json.loads(open('EXECUTION_RECEIPT.json').read())
mp = r.get('mutations_performed', [])
print('mutations_performed:', mp)
if mp: sys.exit(1)
print('OK: no mutations performed')
"

cd "$REPO_ROOT"
echo "=== Step 5: Confirm pinned input commits are reachable ==="
for commit in "$TESTED_COMMIT" "$EVIDENCE_57_COMMIT" "$STAGE6_COMMIT" "$STAGE7_COMMIT"; do
    git cat-file -t "$commit" > /dev/null && echo "commit $commit: reachable"
done

echo ""
echo "EXPECTED: Stage 8 proposal artifacts validate; no live apply authorized; no mutations performed."
