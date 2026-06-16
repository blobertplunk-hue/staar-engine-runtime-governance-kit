# MB_INSTALL v0 — Target Tree Selection Criteria

**Stage ID:** MB_INSTALL_V0_STAGE8_LIMITED_PROMOTION_PROPOSAL_AND_AUTHORIZATION_SCOPE  
**Purpose:** Define what constitutes an eligible target tree for a limited promotion execution.

---

## 1. Eligibility Requirements

A target tree is eligible for a limited MB_INSTALL v0 promotion execution if and only if ALL of the following are true:

### 1.1 Designation and Isolation

- The target tree path is **explicitly named** in the execution-stage authorization document.
- The target tree is **designated as throwaway or isolated** — it is not a live OS path, not a production module path, not a shared system directory, and not any path that would affect running processes or OS integrity.
- The target tree exists solely for the purpose of rehearsal or validation. If it contains data, that data is either reproducible from source or backed up per requirement 1.2.
- The target tree is on a filesystem writable by the executing process and not concurrently written by any other process during the install window.

### 1.2 Backup and Recoverability

- A current, complete backup of the target tree exists **before** any apply action begins.
- The backup is on a separate path or device from the target tree.
- The responsible principal has confirmed the backup is complete and restorable.
- The rollback plan names the exact backup path and the exact command to restore it.

### 1.3 Source Bundle Integrity

- The bundle to be installed is SHA-pinned: its `sha256` is declared in a manifest, and `verify_bundle()` must pass before any staging or swap occurs.
- The bundle commit SHA is pinned in the execution-stage authorization document.
- No bundle that has not been verified by `verify_bundle()` may be staged or applied.

### 1.4 Rollback Plan

- A written rollback plan is produced **before** execution begins.
- The rollback plan names:
  - Exact target tree path
  - Exact backup path
  - Exact restore command
  - Maximum time window for rollback (after which escalation is required)
  - Responsible principal for executing the rollback
- The rollback plan is pre-authorized by the responsible principal.
- The rollback plan is committed to the evidence packet before execution starts.

### 1.5 Pre-Execution Gate Sequence

Before `atomic_swap` is invoked, the following receipts must be produced and reviewed in order:

1. **Preflight receipt** — output of `verify_bundle()` + `check_protected_writes()` + `stage_to_tmp()` with no swap initiated. Must show no errors.
2. **Dry-run receipt** — confirms all staged files match manifest hashes. Must show no errors.
3. **Go/no-go confirmation** — explicit human sign-off immediately before `atomic_swap` is called. No automated or scripted bypass permitted.

---

## 2. Ineligible Target Trees (Absolute Exclusions)

The following target trees are **never eligible** for any MB_INSTALL v0 execution under this authorization, regardless of other conditions:

- Any path under `/`, `/usr`, `/lib`, `/bin`, `/sbin`, `/etc`, `/boot`, `/sys`, `/proc`, `/dev`
- Any path under `/home` (user home directories)
- Any live kernel module path
- Any path managed by the MetaBlooms OS runtime as a live production surface
- Any path that a running process depends on for its current operation
- Any protected-class file (as defined by `protected_class: true` in the bundle manifest) unless the Robert-auth token scope explicitly names that file's path and protection class

---

## 3. Protected-Surface Write Constraints

- Any file with `protected_class: true` in the bundle manifest requires a non-empty, non-whitespace Robert-auth token passed to `check_protected_writes()`.
- The token scope must be explicitly named in the execution-stage authorization document: which files are protected, what token value authorizes them, and who issued the token.
- No protected-surface write may occur without this explicit scope naming.

---

## 4. FM-B Atomicity Scope Note (RISK-06)

`restamp_sidecars()` uses atomic temp+replace (`os.replace`). This atomicity guarantee is for single-agent installs only. If two processes could write the same sidecar concurrently during the install window, the atomicity guarantee does not hold. Target trees for limited promotion must not be subject to concurrent sidecar writes from other processes.

---

## 5. Criteria Summary Checklist

Before any execution-stage action is approved, the responsible principal must confirm:

- [ ] Target tree path explicitly named and confirmed as throwaway/isolated
- [ ] No live OS surface in scope
- [ ] No production module path in scope
- [ ] Complete current backup confirmed at named backup path
- [ ] Bundle SHA pinned and `verify_bundle()` pre-confirmed
- [ ] Rollback plan written, named, and pre-authorized
- [ ] Preflight receipt produced and reviewed (no errors)
- [ ] Dry-run receipt produced and reviewed (no errors)
- [ ] Go/no-go confirmation given by responsible principal
- [ ] No concurrent writers to target tree during install window
- [ ] Protected-class scope explicitly stated (or confirmed absent from bundle)
