# MB_INSTALL v0 — Dry Run Plan

**Stage ID:** MB_INSTALL_V0_STAGE9_EXECUTION_PREFLIGHT_AUTHORIZATION  
**Status:** PLANNED — NOT EXECUTED — BLOCKED PENDING TARGET TREE  
**Dry run execution status:** BLOCKED (target_tree_status: UNNAMED)

---

## What the Dry Run Would Verify

A dry run for MB_INSTALL v0 consists of running every step up to (but not including) `atomic_swap`. This exercises all read-only and staging operations without mutating the target tree.

### Dry Run Step Sequence

| Step | Function | Mutates target tree? | Dry-run safe? |
|------|----------|----------------------|---------------|
| 1 | `verify_bundle(zip_path)` | No | Yes — reads zip only |
| 2 | `check_protected_writes(manifest, token)` | No | Yes — inspects manifest only |
| 3 | `stage_to_tmp(manifest, zip_path)` | No (writes to temp dir only) | Yes — temp dir is throwaway |
| 4 | `atomic_swap(...)` | **YES — renames target tree** | **NOT part of dry run** |
| 5 | `restamp_sidecars(files)` | Yes (writes sidecars to target) | **NOT part of dry run** |
| 6 | `write_receipt(manifest, id)` | No (returns dict) | Yes — no file I/O |

### Dry Run Output (expected)

A successful dry run produces:

```
verify_bundle: PASS — N files verified, all hashes match
check_protected_writes: PASS — [no protected files / token accepted]
stage_to_tmp: PASS — staged N files to /tmp/mb_install_stage_<id>/
write_receipt (preview): {"install_id": "...", "module_id": "...", "score_source": "execution", "files_installed": [...]}
DRY RUN COMPLETE — no swap performed, no sidecar written, no target tree mutated
```

### Why Dry Run Is Currently Blocked

The dry run requires a **bundle zip path** to pass to `verify_bundle()`. No bundle has been specified for this limited promotion execution. A dry run could be performed with any compliant bundle (even a test bundle), but without knowing what bundle is being promoted, the dry run result would not be meaningful.

Additionally, `stage_to_tmp` would succeed against any readable zip, but the staged result is throwaway — no target tree involvement. The dry run does not require the target tree to be named, but it does require a bundle.

**Block reason:** No bundle zip path has been provided by any principal. The dry run will be run as soon as a bundle is provided, even before the target tree is named (since it does not touch the target tree).

### Partial Dry Run Available Now

Steps 1, 2, and 6 (`verify_bundle`, `check_protected_writes`, `write_receipt`) can be run against the Stage 5 ship bundle attestation once its bundle zip is available. The Stage 5 ship bundle contains 15 files as listed in the CI log attestation. This constitutes a meaningful preflight of the bundle integrity path.

### When Dry Run Becomes Fully Authorized

Full dry run execution (steps 1–3 + 6) is authorized as soon as:
- Bundle zip path is named and SHA-pinned
- Robert-auth token scope is stated (or confirmed empty for no protected-class files)

**No target tree is required for the dry run.** `stage_to_tmp` only writes to a throwaway temp directory.
