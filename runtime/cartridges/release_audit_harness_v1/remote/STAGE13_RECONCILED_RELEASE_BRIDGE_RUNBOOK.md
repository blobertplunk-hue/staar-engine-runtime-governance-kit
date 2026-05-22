# AUDIT-CARTRIDGE-13 Release Bridge Runbook

## Release candidate

Use the reconciled Stage 12 baseline, not the older Stage 8 export.

Primary release asset:

`Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.zst`

Primary SHA-256:

`274e0063dfeac4a0193c181fd5e161c51bd9367665f089cd0960c83b901dc7aa`

Release tag:

`metablooms-stage12-reconciled-20260522T0058Z`

## Termux / PC execution

Place all Stage 12 release files in the current directory, then run:

```bash
bash upload_stage12_reconciled_release_bridge.sh
```

After release upload completes, dispatch the workflow:

```bash
gh workflow run metablooms-release-audit-harness.yml \
  --repo blobertplunk-hue/staar-engine-runtime-governance-kit \
  -f release_tag=metablooms-stage12-reconciled-20260522T0058Z \
  -f release_asset_name=Metablooms_OS_BOOT_LINTER_AUTO_AUDIT_RECONCILED_STAGE12_20260522T0058Z.zip.zst \
  -f expected_root=Metablooms_OS
```

Then capture:

- workflow run ID
- job ID
- audit packet artifact ID
- artifact digest
- attestation URL
- Rekor log URL
- `gh attestation verify` output

## Claim boundary

This PR update makes the workflow release-asset-aware and provides bridge scripts. It does not prove upload or workflow dispatch until the external authenticated run completes.
