# MetaBlooms Codex Linux audit packet

## Purpose
This packet configures Codex to audit MetaBlooms from a Linux environment using the GitHub binary-readback-proven STICKY baseline.

## Official Codex context
- Codex web can work in cloud environments, connect to GitHub, and create pull requests.
- Codex CLI runs locally from a terminal and can inspect repositories, edit files, and run commands.
- Codex reads `AGENTS.md` before doing work, so MetaBlooms governance rules belong in repo instructions.

## Durable baseline
Repository:

```text
blobertplunk-hue/staar-engine-runtime-governance-kit
```

Release tag:

```text
MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z
```

Asset:

```text
METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst
```

Expected SHA-256:

```text
786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
```

## Linux prerequisites

```bash
sudo apt-get update
sudo apt-get install -y git gh zstd tar coreutils bash
```

Authenticate GitHub CLI:

```bash
gh auth login
```

## Run restore + boot scaffold

From the repository root or any Linux working directory:

```bash
bash tools/codex/linux_restore_and_audit.sh
```

The script downloads the release asset, verifies SHA-256, tests/extracts the archive, finds `Metablooms_OS`, runs `turn-boot`, and creates a timestamped audit scaffold under `runtime/generated/`.

## Codex task prompt

Use the full prompt in `docs/codex/CODEX_AUDIT_PROMPT.md` or create a GitHub issue from `.github/ISSUE_TEMPLATE/codex_metablooms_os_audit.md`.
