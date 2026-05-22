# MetaBlooms Stage 10 Release Asset / Dispatch Bridge Runbook

## Purpose

This runbook bridges the gap left by the current ChatGPT GitHub connector. The connector can write repo files and read workflow evidence, but it does not expose GitHub Release asset upload or workflow_dispatch execution.

## Artifact to publish

- File: `Metablooms_OS_v8_STAGE8_BASELINE_20260521T2303Z.zip`
- SHA-256: `dfb863720faee62b110533850fb669aaecc1193e6b9fdfce39af5f8c02981bc8`
- Size: `118,080,893` bytes

## Required proof path

1. Upload the Stage 8 baseline ZIP as a GitHub Release asset or otherwise place it in a durable release channel.
2. Trigger `.github/workflows/metablooms-release-audit-harness.yml` through workflow_dispatch with `artifact_path` pointing at the release artifact path or a checked-out artifact path available to the runner.
3. Capture workflow run ID, job ID, audit packet artifact ID, artifact digest, attestation URL, Rekor log URL, and `gh attestation verify` output.
4. Do not claim full public release certification until all proof fields are present.

## Recommended manual/PC path

Use GitHub CLI from an authenticated PC/Termux environment:

```bash
gh auth status
REPO="blobertplunk-hue/staar-engine-runtime-governance-kit"
TAG="metablooms-stage8-baseline-20260521T2303Z"
ZIP="Metablooms_OS_v8_STAGE8_BASELINE_20260521T2303Z.zip"
SHA="dfb863720faee62b110533850fb669aaecc1193e6b9fdfce39af5f8c02981bc8"
sha256sum "$ZIP" | grep "$SHA"
gh release create "$TAG" "$ZIP" "$ZIP.sha256" --repo "$REPO" --title "MetaBlooms Stage 8 Baseline" --notes "Stage 8 baseline export with default auto-audit routing."
```

Then use a dispatch-capable path or update the workflow so the runner downloads the release asset by tag before invoking the audit harness.

## Claim boundary

This runbook is not itself proof of upload or dispatch. It is a bridge plan. Proof requires the completed external run evidence.
