# BOOT_ROOT_REPAIR_POLICY_v1

Date: 2026-06-03  
Status: ACTIVE  
Machine-readable source: `BOOT_ROOT_REPAIR_POLICY_v1.json`  
Source: METABLOOMS_CHAT790_POSTMORTEM_URGENT_OS_CHANGES_20260602 + 20260602_preboot_unsound_root_recovery.md

## Root cause this policy prevents

**Failure class: `directory_existence_treated_as_runtime_soundness`**

```
BAD assumption: /mnt/data/Metablooms_OS exists → the runtime is bootable
```

```
CORRECT invariant: directory existence only proves the directory exists.
Boot proceeds only after verifying boot-critical paths, running turn-boot,
and writing a same-run receipt.
```

This failure class recurred in the 790-chat workflow. `scripts/mpp/mpp.sh` was missing from the live root, causing a hard blocker mid-session. The root was repaired from a verified full-OS archive, but the check that would have caught it earlier was absent.

## Blocking checks (must pass before governed work)

### Check 1 — `scripts/mpp/mpp.sh` present

| Field | Value |
|-------|-------|
| Path | `scripts/mpp/mpp.sh` (relative to live root) |
| Severity | **BLOCKER** |
| Repair action | `restore_from_verified_archive` |
| Error if absent | `BLOCKED: /mnt/data/Metablooms_OS exists but scripts/mpp/mpp.sh is missing` |

A missing `mpp.sh` is not a warning. Governed work must not proceed past this check.

### Check 2 — `turn-boot` passes

| Field | Value |
|-------|-------|
| Command | `bash scripts/mpp/mpp.sh turn-boot --task boot_verify --operation check --print-summary` |
| Expected exit | 0 |
| Severity | **BLOCKER** |
| Repair action | `restore_from_verified_archive` |

If `mpp.sh` is present but `turn-boot` fails, the root is structurally unsound and must be restored before work proceeds.

## Receipt requirements

**A boot receipt must be written in the same run that performs the repair.**

A receipt from a prior session does not satisfy this requirement. The same-run constraint prevents stale or transferred receipts from masking a newly unsound root.

### Required receipt fields

```json
{
  "boot_policy_id": "BOOT_ROOT_REPAIR_POLICY_v1",
  "live_root": "/mnt/data/Metablooms_OS",
  "mpp_sh_verified": true,
  "turn_boot_exit_code": 0,
  "repair_performed": false,
  "verified_archive_source": "<archive name or null>",
  "receipt_timestamp": "<ISO 8601>",
  "session_id": "<session UUID>"
}
```

## Repair strategy

1. Identify the latest verified full-OS archive (primary: `METABLOOMS_FULL_OS_WITH_CLAUDE_GITHUB_WORK_20260603T021048Z.tar.zst` or the current sticky durable-floor archive).
2. Extract to a staging location.
3. Verify `scripts/mpp/mpp.sh` is present in the extracted root.
4. Run `turn-boot` in the extracted root — it must exit 0.
5. Promote the extracted root to the live location.
6. Re-run all blocking checks against the live location.
7. Write the same-run boot receipt.
8. Only then proceed with governed work.

## Failure mode

Policy is fail-closed. If any blocking check cannot be verified, governed work does not start.
