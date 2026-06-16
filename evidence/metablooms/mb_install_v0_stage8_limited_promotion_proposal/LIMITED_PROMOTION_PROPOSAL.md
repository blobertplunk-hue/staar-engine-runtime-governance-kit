# MB_INSTALL v0 — Limited Promotion Proposal

**Stage ID:** MB_INSTALL_V0_STAGE8_LIMITED_PROMOTION_PROPOSAL_AND_AUTHORIZATION_SCOPE  
**Date (UTC):** 2026-06-16  
**Proposal status:** READY_FOR_AUDIT — live apply NOT YET AUTHORIZED  
**Authorizing principal:** Robert (planning and artifact creation only)

---

## 1. Audited Evidence Chain Summary

| Stage | Commit | Decision |
|-------|--------|----------|
| Stage 1 — skeleton + FM-D fixture (42/42) | `d8738e27` | PASS (audited) |
| Stage 1 correction — reproduce scripts 34→42 | `0b63bdc7` | PASS (audited) |
| Current state — full 57/57 evidence | `92eecde7` | PASS (audited) |
| Stage 6 — independent clean-worktree reproduction | `298050f7` | PASS (audited) |
| Stage 7 — promotion-readiness SARP | `6b5cc7e9` | PASS (audited) |

All four failure-mode (FM) fixtures are live and green:

| FM | Name | Fixture | Status |
|----|------|---------|--------|
| FM-A | Floor write without token | `test_mb_install_fm_a_protected_write.py` | LIVE/GREEN |
| FM-B | Non-atomic sidecar write | `test_mb_install_fm_b_restamp_atomic.py` | LIVE/GREEN |
| FM-C | Governance drop | `test_mb_install_fm_c_governance_drop.py` | LIVE/GREEN |
| FM-D | Fabrication wound | `test_mb_install_fm_d_fabrication.py` | LIVE/GREEN |

57/57 tests pass, independently reproduced from a clean worktree checkout. FM matrix gate enforced: no PENDING rows remain. Evidence chain is SHA-pinned through 5 audited stages.

---

## 2. What "Limited Promotion" Means

"Limited promotion" in this context means execution of the MB_INSTALL v0 install primitive (`verify_bundle` → `check_protected_writes` → `stage_to_tmp` → `atomic_swap` → `restamp_sidecars` → `write_receipt`) against a single, explicitly designated, non-live, non-OS target tree, for the purpose of operational rehearsal and confidence-building.

**Constraints that define "limited":**

- Target tree must be explicitly designated as throwaway/isolated (see TARGET_TREE_SELECTION_CRITERIA.md)
- No live OS surface, no production module path, no protected surface may be the target
- Robert-auth token scope must be explicitly named and bounded
- Rollback plan must be written and pre-authorized before execution begins
- A dry-run receipt and preflight receipt must be produced and reviewed before final execution
- A go/no-go confirmation is required immediately before live `atomic_swap` invocation

---

## 3. Live Apply Remains Blocked Until Later Execution Stage

**This Stage 8 artifact authorizes planning and documentation only.**

No `atomic_swap`, `apply`, `prune`, `delete`, `rollback`, `staging_swap`, or protected-surface write is authorized by this document.

Live-tree execution requires a later, separately-audited execution stage that must supply:

1. **Target tree** — exact path, named and pre-approved as throwaway
2. **Responsible principal** — human accountable for the target tree
3. **Robert-auth token scope** — which files (if any) are protected-class in this bundle
4. **Exact command** — the precise invocation string, reviewed before execution
5. **Rollback plan** — pre-written, pre-authorized steps to undo the apply
6. **Preflight receipt** — output of `verify_bundle` + `check_protected_writes` + `stage_to_tmp` in dry mode before swap
7. **Dry-run receipt** — confirmation that all pre-conditions pass without side effects
8. **Final go/no-go confirmation** — explicit human confirmation immediately before `atomic_swap`

---

## 4. Exact Preconditions for Execution

Before any execution-stage action is taken, all of the following must be satisfied:

### Hard requirements (execution is blocked if any are missing)

- [ ] Target tree named and confirmed as throwaway (not any live OS path)
- [ ] Responsible principal named and present for the execution
- [ ] Robert-auth token scope stated (or confirmed empty for no-protected-class bundle)
- [ ] Exact bundle commit SHA pinned for the install
- [ ] Rollback plan written, reviewed, and pre-authorized
- [ ] RISK-02 resolved: CI run log for commit `0b63bdc7` confirmed green by external connector
- [ ] Preflight receipt produced and reviewed (no swap initiated until this passes)
- [ ] Dry-run receipt produced (confirms stage_to_tmp succeeds without side effects)
- [ ] Final go/no-go confirmation given by responsible principal

### Soft requirements (should be resolved; carry-forward permitted with documented justification)

- [ ] RISK-03: At least one prior supervised rehearsal log exists for `atomic_swap` against a real (non-CI) throwaway
- [ ] RISK-05: At least one external (non-Claude/non-ChatGPT) reproduction logged
- [ ] RISK-07: Hash re-verify inside `atomic_swap` before rename confirmed or waived with documented reasoning

---

## 5. What the Execution Stage Must NOT Do

- Apply to any live OS tree or production module path
- Write any protected surface without explicit, scoped Robert-auth token
- Prune, delete, or rollback any path not pre-authorized in the rollback plan
- Invoke `staging_swap` outside the pre-authorized target tree scope
- Skip the preflight/dry-run/go-no-go gate sequence
- Proceed if preflight or dry-run receipt indicates any failure
