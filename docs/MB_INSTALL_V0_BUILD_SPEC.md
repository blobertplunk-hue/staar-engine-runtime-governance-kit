# MB_INSTALL v0 — Build Spec (Governing Document, Stages 1–5)

**Repo:** staar-engine-runtime-governance-kit
**Status:** Stage 3 FM-B/FM-C fixtures live; Stage 4 pending

---

## Purpose

MB_INSTALL v0 is the staged-shadow-apply install primitive for the MetaBlooms kernel module
system. It governs how signed, hashed bundles are unpacked, verified, and applied to a target
tree — without ever mutating a live surface until all pre-conditions pass.

This document is the governing spec for stages 1–5. Each stage builds toward FM-matrix-green
(all four failure-mode fixtures live and passing). Stage 6 is the escape hatch if stage 5 is
not green.

---

## Failure-Mode (FM) Catalog

| ID | Name | Stakes | Governing mechanism |
|----|------|--------|---------------------|
| FM-A | Floor write without token | Protected surface written without Robert-auth token | `check_protected_writes()` fails closed on missing or blank token; fixture live in Stage 2 |
| FM-B | Payload/sidecar write non-atomic | Sidecar diverges from payload after partial write | `restamp_sidecars()` uses same-directory temp file, fsync, and `os.replace`; fixture live in Stage 3 |
| FM-C | Governance drop | Governance contract silently removed during install | `write_receipt()` preserves governance contracts and `validate_receipt()` rejects drops; fixture live in Stage 3 |
| FM-D | Fabrication wound (Stage-003B) | Bundle sha256 declared without matching actual bytes | `verify_bundle()` hashes every file and rejects undeclared/missing/duplicate payloads |

---

## Architecture: staged-shadow-apply flow

```
verify_bundle(zip_path) → manifest          # hash every file; fail on mismatch/extra/missing/duplicate [FM-D]
check_protected_writes(manifest, token)     # fail closed if protected file + missing/blank token [FM-A]
stage_to_tmp(manifest, zip_path) → dir      # copy to staging dir; re-verify staged bytes
atomic_swap(tmp_dir)                        # live-tree swap [STAGE 4 only, guard remains active]
restamp_sidecars(touched_files)             # temp+fsync+replace sidecar write [FM-B]
write_receipt(manifest, install_id)         # deterministic receipt [FM-C]
validate_receipt(receipt, manifest)         # receipt completeness/governance-drop guard [FM-C]
```

The guard on `atomic_swap` is still the live mutation boundary: it raises `NotImplementedError`
unless the explicit bootstrap flag is set, and even with the flag the real implementation is
not built until Stage 4.

---

## Stage 1 — Skeleton + schema + FM-D fixture

**Rule:** No live-tree mutation. No protected-surface writes. No swap. Repo-side code + tests only.

**Deliverables:**
- `docs/MB_INSTALL_V0_BUILD_SPEC.md` — this document
- `contracts/KERNEL_MODULE_MANIFEST_SCHEMA_v1.json` — JSON Schema for module manifests
- `tools/metablooms/mb_install_v0.py` — full function skeleton, `atomic_swap` guarded
- `tests/test_mb_install_schema.py` — executable schema validation/rejection gate
- `tests/test_mb_install_fm_d_fabrication.py` — FM-D fixture (RED without hash check, GREEN with it)
- `tests/test_mb_install_unit.py` — unit coverage for verify_bundle, check_protected_writes, restamp_sidecars
- `tests/test_mb_install_fm_matrix.py` — matrix completeness gate (fails if any row lacks mechanism/fixture)
- `contracts/MB_INSTALL_FM_COVERAGE_MATRIX_v1.json` — FM matrix, FM-D real, FM-A/B/C pending
- CI job `mb-install-tests` wired into `metablooms-ci.yml`

**Definition of Done:**
- Spec committed to `docs/`
- Manifest schema validates a good manifest and rejects traversal / absolute / out-of-tree / backslash paths
- Schema test validates the schema itself against the declared JSON Schema draft
- `verify_bundle()` rejects hash mismatch, missing declared files, undeclared payload files, duplicate manifest paths, duplicate zip members, traversal, absolute, out-of-tree, and backslash paths
- `mb_install_v0.py` imports clean; verify_bundle + check_protected_writes + restamp_sidecars implemented and unit-covered
- `atomic_swap` is guarded NotImplemented — proven by test that refuses to run without bootstrap flag
- FM-D fixture GREEN with check present, RED with it removed
- FM matrix file present, all 4 rows, matrix-completeness test green
- CI runs new tests and passes
- Nothing in this stage installs, swaps, shrinks, or touches any live OS tree

---

## Stage 2 — FM-A fixture + protected-class enforcement live

**Rule:** Only make FM-A live. Do not implement FM-B/FM-C, atomic swap, install execution, or live-tree mutation.

**Deliverables:**
- `tests/test_mb_install_fm_a_protected_write.py` — FM-A fixture
- `check_protected_writes()` tested for:
  - protected file + empty token → raise `ProtectedWriteError`
  - protected file + whitespace-only token → raise `ProtectedWriteError`
  - protected file + non-empty token → pass
  - unprotected file + empty token → pass
- FM matrix: FM-A row updated from `PENDING_STAGE_2` to live fixture

**Definition of Done:**
- FM-A fixture runs in the existing `mb-install-tests` CI pattern
- FM-A matrix row points to the real fixture
- FM-B and FM-C remain pending
- No install, swap, shrink, or live OS mutation behavior is added

---

## Stage 3 — FM-B and FM-C fixtures

**Rule:** Make FM-B/FM-C live without implementing `atomic_swap()` or live-tree mutation.

**Deliverables:**
- `tests/test_mb_install_fm_b_restamp_atomic.py` — FM-B fixture proving sidecar replacement preserves the previous sidecar if `os.replace()` fails
- `tests/test_mb_install_fm_c_governance_drop.py` — FM-C fixture proving receipt validation rejects missing governance contracts and non-execution score sources
- `restamp_sidecars()` uses same-directory temp files, fsync, cleanup on failure, and `os.replace()`
- `write_receipt()` emits deterministic files and governance contracts
- `validate_receipt()` rejects incomplete receipts, file-list drift, governance-contract drops, and non-execution score sources
- FM matrix: FM-B and FM-C rows updated from PENDING to live fixtures

**Definition of Done:**
- FM-A/B/C/D rows all point to real fixture files
- No PENDING FM rows remain
- Existing `mb-install-tests` CI passes
- `atomic_swap()` remains disabled and no live OS mutation behavior is added

---

## Stage 4 — Robustness + real atomic_swap behind the guard

**Deliverables:**
- `tests/test_mb_install_robustness.py` — crash/rollback/corrupt-bundle/self-dep/determinism fixtures
- `atomic_swap()` real implementation, behind the bootstrap guard
- Rollback behavior on partial write proven by test

---

## Stage 5 — Bootstrap rehearsal + full FM matrix green + ship bundle

**Deliverables:**
- Bootstrap rehearsal in CI against a throwaway target tree
- All four FM fixtures live and GREEN
- FM matrix fully resolved (no PENDING rows)
- Ship bundle prepared and attested

---

## Hard boundaries (all stages)

- `atomic_swap` cannot mutate any tree that is not an explicitly designated throwaway
- Protected-surface writes require a non-empty Robert-auth token — no exceptions
- Sidecar and payload atomicity is proven only for the Stage 3 `restamp_sidecars()` helper; full live-tree atomicity remains Stage 4
- Receipt `score_source` must be `"execution"` (not `"inferred"`)
- Determinism: same bundle in → same receipt shape out
- No FM row may be silently absent from the coverage matrix

---

## Path restrictions for bundle files

Bundle file paths must:
- Start with one of: `0_kernel/`, `tools/`, `contracts/`, `schemas/`
- Not contain `..` (traversal)
- Not be absolute (must not start with `/`)
- Not contain backslash separators
- Not contain empty or dot path segments
