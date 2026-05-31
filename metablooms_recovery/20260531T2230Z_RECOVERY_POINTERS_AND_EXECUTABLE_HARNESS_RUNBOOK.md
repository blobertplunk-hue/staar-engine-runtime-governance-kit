# RECOVERY_POINTERS_AND_EXECUTABLE_HARNESS_STAGE004 Runbook

## Decision
Stage004 closes the largest audit gaps by adding stable GitHub pointer files and an executable recovery harness.

## Stable GitHub paths
- `metablooms_recovery/LATEST.json`
- `metablooms_recovery/FLOOR_POINTERS.json`
- `metablooms_recovery/CHECKPOINT_INDEX.json`
- `metablooms_recovery/20260531T2230Z_RECOVERY_POINTERS_AND_EXECUTABLE_HARNESS_RUNBOOK.md`

## Recovery source order
1. Live `/mnt/data/Metablooms_OS` fast path.
2. Local Stage10A archive verified by SHA-256.
3. GitHub release asset fallback by repo/tag/asset name.
4. Connector-pushed text overlays only after schema/receipt validation.

## Executable harness
Run `scripts/metablooms_recover_from_mntdata_and_github_v1.sh` from the packet or installed OS. It stages extraction, boots the staged root, and only then promotes it.

## Known constraint
Stage003 cold archive remains unavailable as a current evidence state. Re-evaluate if bytes later appear.
