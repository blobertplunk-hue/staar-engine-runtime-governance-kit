# MetaBlooms Recovery From /mnt/data + GitHub — Runbook v1

## Purpose
Recover the OS in a new chat from only two sources:

1. files already present in `/mnt/data` at chat start, and
2. continuity artifacts pushed to GitHub.

## Current known-good recovery floor

- Floor: Stage10A v2 full OS archive
- SHA-256: `c02432759e07036b4a672c2a0501e2ff9186e4c71fdcd5b7c6f4101516d0f8b4`
- Local archive: `/mnt/data/METABLOOMS_FULL_OS_EXPORT_SARP_V2_THREAD_A_STAGE10A_FINAL_POINTER_LOCK_20260530T115100Z_tar.zst`
- GitHub release tag: `MB-FLOOR-STAGE10A-20260530T115100Z`
- Landed receipt: `/mnt/data/LANDED_ASSET_20260531T220559Z.json`

## Recovery algorithm

1. **Live-root fast path.** If `/mnt/data/Metablooms_OS` exists, run:

```bash
cd /mnt/data/Metablooms_OS && bash scripts/mpp/mpp.sh turn-boot \
  --task "recover from mntdata and github" \
  --operation validate \
  --print-summary
```

2. **Archive restore path.** If the live root is absent or fails, verify the Stage10A archive hash before extraction. If the archive is absent locally, use the GitHub release asset pointer in the landed receipt to retrieve it; do not trust a metadata-only claim.

3. **Staging extraction.** Extract to a staging directory first. Do not overwrite `/mnt/data/Metablooms_OS` until staging boot/Merkle passes.

4. **Governance overlay.** After the floor boots, import GitHub connector checkpoints as small text continuity artifacts. Do not treat them as arbitrary code patches without validation.

5. **Known unavailable dependency.** Stage003 cold archive is unavailable. Any route requiring it is blocked until original bytes are provided and offsite-proven.

6. **Post-recovery gates.** Run boot/Merkle, external-tool governance fixtures, export-policy math fixtures, and export-policy router fixtures before continuing work.

## GitHub route rule

Use the GitHub connector for small, non-secret text artifacts only: policies, schemas, receipts, handoffs, runbooks, checkpoints. Use self-contained Termux/PowerShell packets for large binary release assets.
