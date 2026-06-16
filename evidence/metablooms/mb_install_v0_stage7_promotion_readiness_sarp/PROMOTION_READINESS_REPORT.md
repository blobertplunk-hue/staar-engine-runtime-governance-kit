# MB_INSTALL v0 Stage 7 — Promotion-Readiness SARP Report

**Stage ID:** MB_INSTALL_V0_STAGE7_PROMOTION_READINESS_SARP  
**Tested commit:** 0b63bdc77e03bcbc01052c8adcabb80f2922318f  
**Audited evidence chain:** Stage 1 → 92eecde (current 57/57) → 298050f (Stage 6 reproduction)  
**Date (UTC):** 2026-06-16  
**Decision:** PASS_READY_FOR_LIMITED_PROMOTION_PROPOSAL

---

## 1. What MB_INSTALL v0 Currently Proves

### Failure-Mode (FM) Coverage — All 4 FMs Live and Green

| FM | Name | Mechanism | Fixture | Status |
|----|------|-----------|---------|--------|
| FM-A | Floor write without token | `check_protected_writes()` fails closed on empty/whitespace token | `test_mb_install_fm_a_protected_write.py` | LIVE/GREEN |
| FM-B | Non-atomic sidecar write | `restamp_sidecars()` uses atomic temp+replace; Stage 3 fixture proves sidecar integrity on failure | `test_mb_install_fm_b_restamp_atomic.py` | LIVE/GREEN |
| FM-C | Governance drop | `write_receipt()` enforces `score_source="execution"`; `validate_receipt()` rejects drops of governance contracts | `test_mb_install_fm_c_governance_drop.py` | LIVE/GREEN |
| FM-D | Fabrication wound | `verify_bundle()` hashes every listed file and rejects mismatch, missing, undeclared, duplicate manifest paths, duplicate zip members | `test_mb_install_fm_d_fabrication.py` | LIVE/GREEN |

### Additional Coverage

- **Manifest schema gate** (`test_mb_install_schema.py`): Validates JSON Schema draft/2020-12 conformance; rejects traversal, absolute, backslash, out-of-tree, bad sha256, bad semver, exact-duplicate file entries.
- **FM matrix completeness gate** (`test_mb_install_fm_matrix.py`): Fails CI if any FM row lacks mechanism/fixture or if a live fixture path does not exist on disk. Confirms no PENDING rows remain after Stage 3.
- **Unit coverage** (`test_mb_install_unit.py`): `verify_bundle`, `check_protected_writes`, `restamp_sidecars`, `stage_to_tmp`, `write_receipt` — 20+ edge cases.
- **Robustness** (`test_mb_install_robustness.py`): `atomic_swap` rollback on failure, refuses backup-path collision, rejects target/tmp_tree outside allowed_root, bootstrap guard enforced.
- **Stage 5 bootstrap rehearsal**: CI rehearsal harness exercises full pipeline against a throwaway staging tree; ship-bundle attestation generator confirmed.

### Evidence Chain Integrity

| Evidence | Commit | Decision | SHA Chain |
|----------|--------|----------|-----------|
| Stage 1 (42/42) | `d8738e27` | PASS | 5/5 OK, 6/6 manifest |
| Current state (57/57) | `92eecde7` | PASS | 5/5 OK, 6/6 manifest |
| Stage 6 independent reproduction | `298050f7` | PASS | 5/5 OK, 6/6 manifest |

Independent reproduction used `git worktree` to start from a clean checkout of commit `0b63bdc7`; all 57 tests passed without any prior state dependency.

---

## 2. Promotion Risk Register

### RISK-01 — Live-tree apply has not been authorized
**Classification:** BLOCKER (for actual live-tree promotion; not a code defect)  
**Detail:** No role, token, or formal authorization document grants permission to run `atomic_swap` against a real (non-throwaway) target tree. The bootstrap guard (`_bootstrap_flag`) exists precisely to enforce this boundary. Any promotion attempt without explicit written authorization violates the hard boundary established in MB_INSTALL_V0_BUILD_SPEC.md.  
**Remediation required:** Explicit promotion authorization naming target tree, responsible principal, and Robert-auth token scope. This is a governance gate, not a code repair.

### RISK-02 — GitHub Actions CI not independently observed by external connector
**Classification:** NONBLOCKING_RISK  
**Detail:** The `mb-install-tests` CI job fires on every push to this branch. The job runs `python3 -m pip install jsonschema` then `python3 -m unittest discover -s tests -p "test_mb_install_*.py" -v`. However, the ChatGPT connector has not directly fetched CI run logs via the GitHub API. Passing from the repo-side evidence alone is strong but not independently cross-checked via CI artifact URL.  
**Remediation:** External connector fetches CI run log at the specific run ID for commit `0b63bdc7` and confirms `Ran 57 tests` / `OK` in the job output.

### RISK-03 — `atomic_swap` has not been exercised against a real target tree outside CI
**Classification:** NONBLOCKING_RISK  
**Detail:** The Stage 4 `atomic_swap` implementation is proven against a throwaway temp-dir target inside CI. It has not been run against an actual module install target (even a non-protected one). The bootstrap guard is the design intent; this risk is about operational confidence, not correctness.  
**Remediation:** A single supervised rehearsal against an explicitly designated throwaway (non-OS, non-protected) tree, logged and attested.

### RISK-04 — Protected-surface writes never exercised with a real Robert-auth token
**Classification:** NONBLOCKING_RISK  
**Detail:** FM-A proves the guard (`check_protected_writes`) fails closed on empty/whitespace token. But no test has supplied an actual non-empty Robert-auth token and then written to a real protected surface. The guard is proven structurally; the token's semantics (how it is issued, validated upstream) are out of scope for v0.  
**Remediation:** Token issuance and validation spec to be defined before protected-surface writes are attempted.

### RISK-05 — External (non-Claude/non-ChatGPT) reproduction not yet performed
**Classification:** NONBLOCKING_RISK  
**Detail:** All reproduction to date has been performed within the Claude Code agent environment or by ChatGPT connector verification of repo artifacts. An independent human developer or third CI system has not cloned the repo and run the suite.  
**Remediation:** Any human developer running `bash REPRODUCE.sh` from the tested commit would satisfy this. Not required before limited promotion proposal; required before production promotion.

### RISK-06 — Sidecar atomicity proof scope
**Classification:** DOCUMENTATION_ONLY  
**Detail:** FM-B Stage 3 proves that `restamp_sidecars()` uses atomic temp+replace (write to `.tmp`, then `os.replace`). The proof covers the sidecar write path. It does not cover concurrent writes from external processes during the replace window. For v0 single-agent installs this is acceptable; concurrent-write safety is a Stage N+ concern.  
**Remediation:** Document in spec that FM-B atomicity is single-agent scope only.

### RISK-07 — No integrity check between `stage_to_tmp` and `atomic_swap` in end-to-end flow
**Classification:** NONBLOCKING_RISK  
**Detail:** `stage_to_tmp` re-verifies hashes against the manifest after staging. `atomic_swap` does not re-verify hashes before swapping. A TOCTOU (time-of-check/time-of-use) window exists between staging and swap if the staging directory is on a writable filesystem accessible to other processes.  
**Remediation:** Stage 4+ could add a final hash check inside `atomic_swap` before rename. Low priority for single-agent installs but worth documenting.

---

## 3. Promotion Decision

**Decision: PASS_READY_FOR_LIMITED_PROMOTION_PROPOSAL**

**Rationale:**  
All four FM fixtures are live and green. The test suite is independently reproducible from a clean checkout (57/57). The evidence chain is SHA-pinned through three audited stages. No code defects or test failures have been identified. The FM matrix gate ensures no row can go silently missing. The `atomic_swap` bootstrap guard prevents unauthorized live-tree mutation.

The blockers and risks identified are:
- One **BLOCKER** (RISK-01) is a process/authorization gate, not a code defect. It blocks *actual* live-tree promotion, not the promotion *proposal*.
- All remaining risks are NONBLOCKING or DOCUMENTATION_ONLY.

A **limited promotion proposal** is appropriate now, subject to:
1. Naming the specific target tree (must be explicitly designated throwaway or isolated test environment — no live OS surfaces)
2. Obtaining explicit authorization document naming responsible principal and token scope
3. External connector confirming CI green on commit `0b63bdc7` (RISK-02 remediation)
4. Supervised rehearsal log for `atomic_swap` against the named target (RISK-03 remediation)

Production promotion (live OS surfaces) requires all NONBLOCKING_RISKs to be resolved and an external human auditor sign-off.

---

## 4. Exact Next Stage

**Next stage:** `MB_INSTALL_V0_STAGE8_LIMITED_PROMOTION_PROPOSAL`

Required inputs for Stage 8:
- Explicit authorization document: target tree name, responsible principal, Robert-auth token scope
- CI run ID confirmation from external connector (resolves RISK-02)
- Optional but recommended: RISK-03 supervised rehearsal log

**What Stage 8 must NOT do:**
- Apply to any live OS tree
- Write any protected surface
- Prune, delete, rollback, or staging-swap any production path
- Skip RISK-01 authorization gate
