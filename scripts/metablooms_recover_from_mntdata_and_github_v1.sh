#!/usr/bin/env bash
set -euo pipefail
ROOT="/mnt/data/Metablooms_OS"
STAGE="/mnt/data/metablooms_recovery_stage"
ARCHIVE="/mnt/data/METABLOOMS_FULL_OS_EXPORT_SARP_V2_THREAD_A_STAGE10A_FINAL_POINTER_LOCK_20260530T115100Z_tar.zst"
EXPECTED_SHA="c02432759e07036b4a672c2a0501e2ff9186e4c71fdcd5b7c6f4101516d0f8b4"
REPO="blobertplunk-hue/staar-engine-runtime-governance-kit"
TAG="MB-FLOOR-STAGE10A-20260530T115100Z"
ASSET="METABLOOMS_FULL_OS_EXPORT_SARP_V2_THREAD_A_STAGE10A_FINAL_POINTER_LOCK_20260530T115100Z_tar.zst"
TASK="recover from mntdata and github"
log(){ printf '[metablooms-recover] %s\n' "$*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
boot_root(){ (cd "$1" && bash scripts/mpp/mpp.sh turn-boot --task "$TASK" --operation validate --print-summary); }
if [ -d "$ROOT" ] && [ -f "$ROOT/scripts/mpp/mpp.sh" ]; then
  log "live root present; attempting fast-path boot"
  if boot_root "$ROOT"; then log "PASS live root booted"; exit 0; fi
  log "WARN live root failed; attempting archive recovery"
fi
if [ ! -f "$ARCHIVE" ]; then
  log "local archive missing; attempting GitHub release download via gh"
  command -v gh >/dev/null 2>&1 || { log "BLOCKED: gh missing and local archive absent"; exit 20; }
  gh release download "$TAG" --repo "$REPO" --pattern "$ASSET" --dir /mnt/data
fi
[ -f "$ARCHIVE" ] || { log "BLOCKED: archive absent after local/GitHub attempts"; exit 21; }
ACTUAL="$(sha "$ARCHIVE")"
[ "$ACTUAL" = "$EXPECTED_SHA" ] || { log "BLOCKED: archive sha mismatch actual=$ACTUAL expected=$EXPECTED_SHA"; exit 22; }
log "archive hash PASS"
rm -rf "$STAGE"; mkdir -p "$STAGE"
case "$ARCHIVE" in
  *.tar.zst|*.tar.zstd) tar --zstd -xf "$ARCHIVE" -C "$STAGE" ;;
  *.tar.gz|*.tgz) tar -xzf "$ARCHIVE" -C "$STAGE" ;;
  *.zip) unzip -oq "$ARCHIVE" -d "$STAGE" ;;
  *) log "BLOCKED: unsupported archive format"; exit 23 ;;
esac
CAND="$(find "$STAGE" -maxdepth 3 -type f -path '*/scripts/mpp/mpp.sh' -print -quit | sed 's#/scripts/mpp/mpp.sh$##')"
[ -n "$CAND" ] || { log "BLOCKED: no staged MetaBlooms root found"; exit 24; }
log "staged root candidate: $CAND"
boot_root "$CAND" || { log "BLOCKED: staged boot failed; live root not overwritten"; exit 25; }
if [ -d "$ROOT" ]; then mv "$ROOT" "/mnt/data/Metablooms_OS.previous.$(date -u +%Y%m%dT%H%M%SZ)"; fi
mv "$CAND" "$ROOT"
log "PASS promoted staged root to $ROOT"
boot_root "$ROOT"
