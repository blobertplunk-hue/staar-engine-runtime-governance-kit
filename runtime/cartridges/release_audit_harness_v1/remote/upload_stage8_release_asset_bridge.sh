#!/usr/bin/env bash
set -euo pipefail

# MetaBlooms Stage 10 bridge helper.
# Requires an authenticated GitHub CLI environment with release-write capability.

REPO="${REPO:-blobertplunk-hue/staar-engine-runtime-governance-kit}"
TAG="${TAG:-metablooms-stage8-baseline-20260521T2303Z}"
ZIP="${ZIP:-Metablooms_OS_v8_STAGE8_BASELINE_20260521T2303Z.zip}"
EXPECTED_SHA="${EXPECTED_SHA:-dfb863720faee62b110533850fb669aaecc1193e6b9fdfce39af5f8c02981bc8}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING_TOOL: $1" >&2; exit 40; }; }
need gh
need sha256sum

if [ ! -f "$ZIP" ]; then
  echo "MISSING_ARTIFACT: $ZIP" >&2
  exit 41
fi

ACTUAL_SHA="$(sha256sum "$ZIP" | awk '{print $1}')"
if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
  echo "SHA_MISMATCH expected=$EXPECTED_SHA actual=$ACTUAL_SHA" >&2
  exit 42
fi

if [ ! -f "$ZIP.sha256" ]; then
  printf '%s  %s\n' "$ACTUAL_SHA" "$ZIP" > "$ZIP.sha256"
fi

gh auth status

gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1 && {
  echo "RELEASE_EXISTS: $TAG" >&2
  exit 43
}

gh release create "$TAG" "$ZIP" "$ZIP.sha256" \
  --repo "$REPO" \
  --title "MetaBlooms Stage 8 Baseline" \
  --notes "Stage 8 baseline export with default auto-audit routing. SHA-256: $ACTUAL_SHA"

echo "RELEASE_ASSET_UPLOAD_BRIDGE_COMPLETE tag=$TAG sha256=$ACTUAL_SHA"
