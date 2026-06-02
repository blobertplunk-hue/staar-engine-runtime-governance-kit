#!/usr/bin/env bash
set -Eeuo pipefail

REPO="${REPO:-blobertplunk-hue/staar-engine-runtime-governance-kit}"
TAG="${TAG:-MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z}"
ASSET="${ASSET:-METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst}"
EXPECTED_SHA="${EXPECTED_SHA:-786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73}"
TASK="${TASK:-Codex Linux repo-side OS audit}"
OPERATION="${OPERATION:-validate}"
WORKDIR="${WORKDIR:-$PWD/metablooms_codex_linux_restore}"
AUTO_INSTALL_DEPS="${AUTO_INSTALL_DEPS:-1}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOGDIR="$WORKDIR/audit_logs_$STAMP"

mkdir -p "$WORKDIR" "$LOGDIR"
exec > >(tee "$LOGDIR/COMMAND_LOG.txt") 2>&1

say(){ printf '\n[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
need(){ command -v "$1" >/dev/null 2>&1 || { echo "BLOCKED: missing dependency: $1"; exit 10; }; }

run_pkg_install(){
  local pkg="$1"
  if [ "${AUTO_INSTALL_DEPS}" != "1" ]; then
    return 1
  fi
  if command -v apt-get >/dev/null 2>&1; then
    say "Installing dependency via apt-get: $pkg"
    sudo apt-get update
    sudo apt-get install -y "$pkg"
    return 0
  fi
  if command -v apk >/dev/null 2>&1; then
    say "Installing dependency via apk: $pkg"
    sudo apk add --no-cache "$pkg"
    return 0
  fi
  if command -v dnf >/dev/null 2>&1; then
    say "Installing dependency via dnf: $pkg"
    sudo dnf install -y "$pkg"
    return 0
  fi
  if command -v yum >/dev/null 2>&1; then
    say "Installing dependency via yum: $pkg"
    sudo yum install -y "$pkg"
    return 0
  fi
  return 1
}

ensure_zstd(){
  if command -v unzstd >/dev/null 2>&1 || command -v zstd >/dev/null 2>&1; then
    return 0
  fi
  say "zstd/unzstd missing; attempting bounded dependency repair"
  run_pkg_install zstd || true
  if command -v unzstd >/dev/null 2>&1 || command -v zstd >/dev/null 2>&1; then
    say "zstd/unzstd dependency repaired"
    return 0
  fi
  echo "BLOCKED: missing zstd/unzstd and automatic install failed or was disabled. Install zstd first."
  exit 11
}

ensure_downloader(){
  if command -v gh >/dev/null 2>&1 || command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1; then
    return 0
  fi
  say "No release downloader found; attempting bounded dependency repair for curl"
  run_pkg_install curl || true
  if command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 || command -v gh >/dev/null 2>&1; then
    say "release downloader dependency repaired"
    return 0
  fi
  echo "BLOCKED: missing release downloader and automatic install failed or was disabled. Need gh, curl, or wget."
  exit 12
}

download_asset(){
  local url="https://github.com/${REPO}/releases/download/${TAG}/${ASSET}"
  rm -f "$ASSET"

  if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then
      say "Downloading release asset via authenticated gh"
      gh release download "$TAG" --repo "$REPO" --pattern "$ASSET" --dir .
      return 0
    fi
    say "gh exists but is not authenticated; trying direct HTTPS fallback"
  else
    say "gh not found; trying direct HTTPS fallback"
  fi

  if command -v curl >/dev/null 2>&1; then
    say "Downloading release asset via curl"
    curl -fL --retry 3 --retry-delay 2 -o "$ASSET" "$url"
    return 0
  fi

  if command -v wget >/dev/null 2>&1; then
    say "Downloading release asset via wget"
    wget -O "$ASSET" "$url"
    return 0
  fi

  echo "BLOCKED: no release-download method available after dependency repair. Need authenticated gh, curl, or wget."
  exit 12
}

say "Checking dependencies"
need bash
need tar
need sha256sum
ensure_zstd
ensure_downloader

cd "$WORKDIR"

download_asset

say "Verifying SHA-256"
printf '%s  %s\n' "$EXPECTED_SHA" "$ASSET" | sha256sum -c -

say "Testing compressed archive"
if command -v zstd >/dev/null 2>&1; then
  zstd -t "$ASSET"
fi

say "Extracting OS"
rm -rf restore_root
mkdir -p restore_root
if command -v unzstd >/dev/null 2>&1; then
  tar --use-compress-program=unzstd -xf "$ASSET" -C restore_root
else
  tar --use-compress-program="zstd -d" -xf "$ASSET" -C restore_root
fi

OS_ROOT="$(find restore_root -maxdepth 3 -type f -path '*/scripts/mpp/mpp.sh' -print -quit | sed 's#/scripts/mpp/mpp.sh$##')"
[ -n "$OS_ROOT" ] || { echo "BLOCKED: extracted OS root with scripts/mpp/mpp.sh not found"; exit 13; }

say "Booting MetaBlooms OS at $OS_ROOT"
cd "$OS_ROOT"
bash scripts/mpp/mpp.sh turn-boot --task "$TASK" --operation "$OPERATION" --print-summary

say "Creating audit packet scaffold"
PKT="runtime/generated/codex_linux_repo_side_audit_$STAMP"
mkdir -p "$PKT/VALIDATOR_OUTPUTS" "$PKT/FIXTURES"
cat > "$PKT/AUDIT_REPORT.md" <<REPORT
# Codex Linux repo-side audit scaffold — $STAMP

## Restore
- Repo: \`$REPO\`
- Release tag: \`$TAG\`
- Asset: \`$ASSET\`
- Expected SHA-256: \`$EXPECTED_SHA\`
- Boot task: \`$TASK\`
- Operation: \`$OPERATION\`
- Auto-install dependencies: \`$AUTO_INSTALL_DEPS\`

## Result
Restore, hash verification, extraction, and turn-boot completed. Continue the bounded audit from the active Codex prompt/issue.
REPORT
cat > "$PKT/MACHINE_FINDINGS.json" <<JSON
{
  "schema": "mb.codex.linux.audit.scaffold.v1",
  "created_at_utc": "$STAMP",
  "repo": "$REPO",
  "release_tag": "$TAG",
  "asset": "$ASSET",
  "expected_sha256": "$EXPECTED_SHA",
  "auto_install_deps": "$AUTO_INSTALL_DEPS",
  "decision": "PASS_RESTORE_BOOT_SCAFFOLD_READY"
}
JSON
cp "$LOGDIR/COMMAND_LOG.txt" "$PKT/COMMAND_LOG.md"
cat > "$PKT/PATCH_PLAN.md" <<'PLAN'
# Patch plan

No patch is implied by this scaffold. Perform audit-first work, then propose the smallest validated repair PR if defects are found.
PLAN
cat > "$PKT/SELF_SAR.md" <<'SAR'
# Self-SAR seed

Check for overclaims:
- Did Codex actually verify the release asset bytes?
- Did turn-boot pass from extracted bytes?
- Were any durable claims made from pointers only?
- Were failed commands preserved?
SAR
: > "$PKT/CHANGED_FILES.txt"

say "Audit scaffold written: $PKT"
