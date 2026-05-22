#!/usr/bin/env bash
set -euo pipefail

# MetaBlooms Stage 13 release bridge helper.
# Uploads the reconciled Stage 12 baseline to GitHub Releases from an authenticated gh CLI environment.

REPO="${REPO:-blobertplunk-hue/staar-engine-runtime-governance-kit}"
TAG="${TAG:-metablooms-stage12-reconciled-20260522T0058Z}"
TITLE="${TITLE:-MetaBlooms Stage 12 Reconciled Boot-Linter + Auto-Audit Baseline}"
PRIMARY="${PRIMARY:-Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.zst}"
EXPECTED_PRIMARY_SHA="${EXPECTED_PRIMARY_SHA:-274e0063dfeac4a0193c181fd5e161c51bd9367665f089cd0960c83b901dc7aa}"
EXPECTED_ROOT="${EXPECTED_ROOT:-Metablooms_OS}"

ASSETS=(
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.zst"
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.zst.sha256"
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip"
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.sha256"
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.provenance.json"
  "Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.provenance.json.sha256"
)

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING_TOOL: $1" >&2; exit 40; }; }
need gh
need sha256sum

for asset in "${ASSETS[@]}"; do
  if [ ! -f "$asset" ]; then
    echo "MISSING_ASSET: $asset" >&2
    exit 41
  fi
done

actual="$(sha256sum "$PRIMARY" | awk '{print $1}')"
if [ "$actual" != "$EXPECTED_PRIMARY_SHA" ]; then
  echo "PRIMARY_SHA_MISMATCH expected=$EXPECTED_PRIMARY_SHA actual=$actual" >&2
  exit 42
fi

gh auth status

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "RELEASE_EXISTS: $TAG" >&2
  echo "Use gh release delete-asset or a new tag if you intend to replace assets." >&2
  exit 43
fi

notes_file="stage13_release_notes.md"
cat > "$notes_file" <<NOTES
MetaBlooms Stage 12 reconciled baseline.

Primary artifact: $PRIMARY
Primary SHA-256: $actual
Includes boot-linter baseline plus automatic audit harness routing.
Claim boundary: release upload is complete only after this script exits successfully; remote audit proof requires the workflow dispatch that follows.
NOTES

gh release create "$TAG" "${ASSETS[@]}" \
  --repo "$REPO" \
  --title "$TITLE" \
  --notes-file "$notes_file"

echo "RELEASE_ASSET_UPLOAD_COMPLETE tag=$TAG primary=$PRIMARY sha256=$actual"

echo "NEXT_WORKFLOW_DISPATCH:"
echo "gh workflow run metablooms-release-audit-harness.yml --repo '$REPO' -f release_tag='$TAG' -f release_asset_name='$PRIMARY' -f expected_root='$EXPECTED_ROOT'"
