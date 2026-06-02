# Improvement Log: Preboot Unsound Root Recovery Hardening

Date: 2026-06-02
Branch: `claude/metablooms-os-audit-hr5ET`
Source stage: `PREBOOT_UNSOUND_ROOT_RECOVERY_EXPORT_AND_SURVIVAL_GATE`
Status: backlog / urgent implementation required

## Trigger

During MetaBlooms OS boot/recovery work, the runtime hit this blocker:

```text
BLOCKED: /mnt/data/Metablooms_OS exists but scripts/mpp/mpp.sh is missing
```

The immediate repair restored the live sandbox root from a verified full OS tar export and produced a repaired export. However, the course of the chat exposed several urgent OS changes that still need to be implemented in the repository/runtime governance layer so the same failure class cannot recur.

## Root Cause

Failure class:

```text
directory_existence_treated_as_runtime_soundness
```

Bad assumption:

```text
/mnt/data/Metablooms_OS exists -> the runtime is bootable
```

Correct invariant:

```text
/mnt/data/Metablooms_OS exists only proves that a directory exists. Boot may proceed only after validating boot-critical paths and, if unsound, exhausting verified recovery candidates before final BLOCKED.
```

## Urgent Changes Needed

### U1. Rootless first-action recovery

The mandatory first action still assumes this path is executable:

```bash
cd /mnt/data/Metablooms_OS && bash scripts/mpp/mpp.sh turn-boot ...
```

That path fails whenever the canonical root exists as a stale/incomplete stub. Add a rootless preflight/rescue layer that runs before trusting `/mnt/data/Metablooms_OS`.

Required behavior:

1. Probe canonical root soundness.
2. Distinguish `ROOT_MISSING`, `ROOT_UNSOUND`, and `ENTRYPOINT_MISSING`.
3. If recovery candidates exist, verify sidecars/hashes before final failure.
4. Extract to staging.
5. Prove boot-critical entrypoints in staging.
6. Promote staging to canonical root only after validation.
7. Write rescue receipt.

### U2. Patch the active preboot self-heal entrypoint

The boot path currently invokes:

```text
tools/metablooms/preboot_bundle_rescue_self_heal_v1.py
```

This tool needs to be upgraded so it does not report success merely because a rescue script exists. It must prove root soundness and delegate to the rootless recovery path when the canonical root is unsound.

Required additions:

- soundness checks for `scripts/mpp/mpp.sh`, `tools/mpp/mpp_always_on_turn_controller.py`, `runtime/`, and `0_kernel/boot_contracts/`
- `.tar.zst` recovery candidate support
- staged extraction and staged boot proof
- quarantine of unsound roots
- machine-readable receipts for recovery attempt, pass, fail, and promotion

### U3. Standalone rescue kit outside the full archive

The prior repair was included in the full OS tar, but that is insufficient when the canonical root is broken and the recovery tool is trapped inside the archive.

Every full export should also produce a small standalone rescue packet, outside the full archive, containing:

```text
METABLOOMS_ROOTLESS_PREBOOT_BOOTSTRAP_v1.py
METABLOOMS_PREBOOT_RESCUE_v1.sh
checksums
usage receipt
self-test receipt
```

This packet must be downloadable and usable before the OS root exists or boots.

### U4. New-chat hydration survival fixture

Add a blocking regression fixture for the exact failure state observed here:

```text
/mnt/data/Metablooms_OS exists
/mnt/data/Metablooms_OS/scripts/mpp/mpp.sh missing
verified full tar.zst present
standalone rescue available or discoverable
mandatory boot would otherwise try missing mpp.sh
```

Expected result:

```text
RECOVERY_PASSED, not BLOCKED
```

### U5. Boot-state machine expansion

Boot contracts should explicitly represent recovery states, not collapse them into generic pass/block.

Required states:

```text
ROOT_MISSING
ROOT_UNSOUND
ENTRYPOINT_MISSING
RECOVERY_CANDIDATE_AVAILABLE
RECOVERY_ATTEMPTED
RECOVERY_PASSED
RECOVERY_FAILED
RECOVERY_EXHAUSTED
PROMOTION_PASSED
PROMOTION_FAILED
```

Final `BLOCKED` is valid only after recovery has been attempted or proven unavailable with evidence.

### U6. Archive-inspect rerun for latest repaired export

The tracker still pointed to:

```text
STAGE011I2_ARCHIVE_INSPECT_ONLY_E4_RERUN
```

Run it against the latest repaired export and verify:

- required rescue members
- sidecars
- export manifests
- boot receipts
- no placeholder metadata
- no missing declared ledger outputs
- cold-restore proof

### U7. Timeout-resumable export orchestration

The export/survival gate produced valid archives, but combined export+validation commands timed out during cold-restore validation. This was manually resumed and passed.

Make export orchestration deterministic and resumable by splitting it into separately receipt-backed stages:

1. archive build
2. checksum sidecar
3. manifest write
4. diff packet
5. archive listing
6. cold restore extraction
7. cold restore boot
8. final receipt/evidence bundle

Each stage should resume from the last verified artifact rather than restart blindly.

### U8. Comparative-governance rubric amendment cartridge

The adversarial review found the comparative governance rubric needs correction:

- Do not score MetaBlooms as a range while comparators are single fixed scores.
- Separate internal deterministic governance proof from external validation.
- Include production utility and ecosystem maturity as distinct axes.
- Avoid penalizing mainstream frameworks for intentionally not adopting MetaBlooms-style deterministic process locking.

Add a revised rubric cartridge or rubric schema separating:

```text
internal deterministic governance
external validation
production utility
ecosystem maturity
evidence level
methodological symmetry
```

## Priority Order

1. U1-U4: rootless first-action recovery, active self-heal patch, standalone rescue kit, and hydration survival fixture.
2. U5: boot-state machine expansion.
3. U6: archive-inspect rerun.
4. U7: timeout-resumable export orchestration.
5. U8: comparative-governance rubric correction.

## Acceptance Criteria

This improvement entry should not be considered resolved until:

- a fresh sandbox with a deliberately unsound `/mnt/data/Metablooms_OS` root self-recovers from a verified tar.zst without manual extraction;
- the active boot path no longer requires `scripts/mpp/mpp.sh` to exist before it can recover it;
- a standalone rescue packet is produced with every full export;
- the new hydration survival fixture fails on the old behavior and passes on the repaired behavior;
- export validation can resume deterministically after timeout;
- the comparative-governance rubric is amended with symmetric scoring axes.

## Evidence From Chat Runtime

Observed passing repaired root after manual restore:

```text
normalized_status: PASS
LIFECYCLE_BINDING decision=PASS checks=169 missing=0 errors=0
MERKLE_LEDGER decision=PASS files=15792 bytes=129678414 errors=0
```

Known blocker preserved as regression seed:

```text
BLOCKED: /mnt/data/Metablooms_OS exists but scripts/mpp/mpp.sh is missing
```
