# MB_INSTALL v0 — Rollback Plan

**Stage ID:** MB_INSTALL_V0_STAGE9_EXECUTION_PREFLIGHT_AUTHORIZATION  
**Status:** DRAFTED — NOT AUTHORIZED FOR EXECUTION — NOT EXECUTED  
**Target tree:** UNNAMED (rollback cannot be finalized until target tree is named)

---

## Rollback Plan Template

This is a template rollback plan. It must be completed with exact paths and confirmed by the responsible principal before any execution-stage apply action begins.

### Pre-Execution Backup Requirement

Before any `atomic_swap` is invoked:

1. A complete backup of the target tree must exist at a named backup path.
2. The backup must be verified as complete and restorable.
3. The responsible principal must confirm the backup.

```
TARGET_TREE_PATH:   <UNNAMED — must be filled before execution>
BACKUP_PATH:        <UNNAMED — must be filled before execution>
BACKUP_CONFIRMED_BY: <UNNAMED responsible principal>
BACKUP_TIMESTAMP:   <UTC timestamp of backup creation>
```

### Rollback Trigger Conditions

Rollback is triggered if any of the following occur during or after the install:

- `verify_bundle()` raises any exception
- `check_protected_writes()` raises `ProtectedWriteError`
- `stage_to_tmp()` raises any exception
- `atomic_swap()` raises any exception
- `restamp_sidecars()` raises any exception
- Post-install verification finds any hash mismatch
- The responsible principal issues a rollback order within the rollback window

### Rollback Procedure (template — fill paths before execution)

```bash
# Step R1: Stop any processes using files in the target tree (if applicable)
# <fill in process stop commands if needed>

# Step R2: Remove the partially-applied target tree (if atomic_swap completed)
# CAUTION: Only run if the backup at BACKUP_PATH is confirmed restorable
rm -rf <TARGET_TREE_PATH>

# Step R3: Restore from backup
cp -a <BACKUP_PATH> <TARGET_TREE_PATH>

# Step R4: Verify restoration
# Compare file counts and spot-check key files
ls <TARGET_TREE_PATH>

# Step R5: Write rollback receipt
echo "ROLLBACK COMPLETE: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> <TARGET_TREE_PATH>/ROLLBACK_RECEIPT.txt
```

### Rollback Window

Maximum time from install completion to rollback decision: **TBD** (fill before execution — recommended: 15 minutes for limited promotion).

After the rollback window expires, escalation to responsible principal is required before any further action.

### Responsible Principal for Rollback

```
Name: <UNNAMED — must be filled before execution>
Contact: <fill>
Authorization scope: <fill>
```

### What atomic_swap Does Internally (for rollback planning)

`atomic_swap` in Stage 4 implementation:
1. Renames the existing target tree to a backup path (`target_tree + ".bak_<id>"`)
2. Renames the staging tmp_tree to the target_tree path
3. On failure at step 2, attempts to restore the backup by renaming it back

If the atomic_swap internal restore fails, the backup copy (`target_tree.bak_<id>`) remains on disk and should be manually renamed to restore the target.

### Blocker

This rollback plan cannot be finalized until `TARGET_TREE_CANDIDATE.json` `target_tree_status` changes from `UNNAMED` to `NAMED`. All `<UNNAMED>` and `<fill>` placeholders must be replaced with exact values and confirmed by the responsible principal before execution begins.
