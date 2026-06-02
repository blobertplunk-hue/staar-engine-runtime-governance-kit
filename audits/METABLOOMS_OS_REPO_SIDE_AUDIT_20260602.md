# MetaBlooms OS Repo-Side Audit — 2026-06-02

**Auditor:** Claude Code repo-side OS audit
**Release tag:** `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`
**Asset:** `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst`
**Asset size:** 213,513,094 bytes

## Download & SHA-256 Verification

| Step | Result |
|---|---|
| HTTP download | 200 OK |
| Expected SHA-256 | `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73` |
| Observed SHA-256 | `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73` |
| Match | **PASS** |

## `mpp.sh turn-boot --operation validate` Result

```
rc: 0  status: PASS  ux_label: Pass
turn_class: AUDIT  bts_quality: GROUNDED_SYNTHETIC  learning: PASS
```

## Findings Summary

| ID | Class | Severity | Title | Status |
|---|---|---|---|---|
| FIND-01 | sidecar_false_fail_prevention | MEDIUM | No regression fixture for sidecar-present-but-wrong-hash | OPEN |
| FIND-02 | sidecar_false_fail_prevention | LOW | Malformed sidecar silently becomes BLOCKED, undocumented | OPEN |
| FIND-03 | downloaded_sha256 normalization | LOW | Missing canonical_only and neither_key fixture cases | OPEN |
| FIND-04 | landed_receipt_self_verification | LOW | exit code 2 for PASS_RECEIPT_KEY_CONFIRMED in self-verify tool | OPEN |
| FIND-05 | export_timeout_partial_archive | MEDIUM | Partial decompressed file not deleted on zstd timeout | OPEN |
| FIND-06 | github_release_readback_workflow | **HIGH** | Runner cannot process `.tar.zst` releases (BLOCKED) | OPEN |
| FIND-07 | github_release_readback_workflow | LOW | Workflow does not fail-fast on absent sidecar pre-runner | INFORMATIONAL |
| FIND-08 | durable_floor_proof_integrity | — | New sticky release not in durability ledger; K2 floor intact | PASS / NO ACTION |
| FIND-09 | missing_regression_fixtures | MEDIUM | Runner self-test missing sidecar-mismatch and tar.zst cases | OPEN |

---

## Detailed Findings

### FIND-01 — Sidecar present with wrong hash: no regression fixture [MEDIUM]

**File:** `runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py`
**Lines:** 41–47 (`sidecar_hash`), 133 (`audit`)

`sidecar_hash()` reads the `.sha256` companion file and validates it is 64 hex chars. If it is, the hash is compared to the actual artifact digest — a mismatch yields `FAIL`. This is correct. However, the runner self-test (`make_zip`) always writes a **correct** sidecar; there is no case where the sidecar contains a deliberately wrong but validly-formatted hash. A future regression that made `sidecar_hash()` return `None` instead of the wrong hash (converting FAIL → BLOCKED) would not be caught.

**First-pass action:** `fixtures/release_audit_harness/sidecar_regression_validator.py` exercises this case without modifying the runner.

---

### FIND-02 — Malformed sidecar silently becomes BLOCKED [LOW]

**File:** same as FIND-01, lines 41–47

If the `.sha256` file exists but contains non-hex content (`"MISSING"`, `""`, `"not-a-hash"`), `sidecar_hash()` returns `None`. The check decision becomes `BLOCKED` — identical to the absent-sidecar path. A tampered sidecar that replaces the hash with garbage is therefore indistinguishable at the decision level from a legitimately absent sidecar. No test covers this.

**First-pass action:** Documented in `sidecar_regression_validator.py` with expected BLOCKED decision.

---

### FIND-03 — Two fixture edge cases missing for downloaded_sha256 normalization [LOW]

**Location:** `fixtures/landed_receipt_self_verify/` (OS archive)

Existing fixtures:
- `legacy_download_sha256_PASS.json` — only `download_sha256` present (legacy key)
- `both_keys_differ_BLOCKED.json` — both keys present but differ
- `mismatched_asset_BLOCKED.json` — hash doesn't match actual file

**Missing:**
- `canonical_only_PASS.json` — only `downloaded_sha256` present, no legacy key (the canonical path)
- `neither_key_BLOCKED.json` — neither field present; normalizer should produce `BLOCKED`

**First-pass action:** Both files added to `fixtures/landed_receipt_self_verify/` in this PR.

---

### FIND-04 — Self-verify tool exit code 2 for PASS_RECEIPT_KEY_CONFIRMED [LOW]

**File:** `tools/metablooms/landed_receipt_self_verify_v1.py` (OS archive), line 168

```python
return 0 if result["decision"] == "PASS_PROVEN" else 2
```

`PASS_RECEIPT_KEY_CONFIRMED` (asset not local, hashes consistent in receipt) is a valid non-error outcome but returns exit code 2. CI wrappers that rely on exit codes treat this as failure, requiring `|| true` workarounds.

**Recommended fix (not applied this pass):** Return 0 for `PASS_PROVEN` and `PASS_RECEIPT_KEY_CONFIRMED`; return non-zero only for `BLOCKED`.

---

### FIND-05 — Partial archive not cleaned up on zstd timeout [MEDIUM]

**File:** `runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py`
**Lines:** 59–68 (`run_binary_to_file`), 115–117 (`materialize`)

```python
# run_binary_to_file on TimeoutExpired:
return {"returncode": "TIMEOUT", ..., "size_bytes": target.stat().st_size if target.exists() else 0}

# materialize return:
return (target if target.exists() and target.stat().st_size > 0 else None), checks
```

On timeout, `target` (partial decompressed file) may exist with content. `materialize()` sets the check to `FAIL` (correct) but still returns the partial file as `zip_path`. `audit()` then calls `check_zip()` on the corrupt partial file, producing misleading additional check rows.

**Recommended fix (not applied this pass):**
```python
except subprocess.TimeoutExpired as e:
    if target.exists():
        target.unlink(missing_ok=True)  # remove partial file
    ...
```
And in `materialize()`: guard the zip_path return on `dec["returncode"] == 0`.

---

### FIND-06 — Release audit harness workflow BLOCKED on tar.zst releases [HIGH]

**Files:** `runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py` lines 100–118; `.github/workflows/metablooms-release-audit-harness.yml`

The sticky release assets:
- `...tar.zst` (213 MB) — SHA-256 in GitHub asset metadata: `786fd1...`
- `...tar.zst.sha256` — present ✅
- `...tar.zst.provenance.json` — present ✅

The runner's `materialize()` handles only `.zip` and `.zip.zst`:
```python
if artifact.suffix == ".zip":
    return artifact, []
if artifact.name.endswith(".zip.zst"):
    ...
return None, [["artifact_extension", "BLOCKED", "expected .zip or .zip.zst"]]
```

Dispatching the workflow against this release tag would return `BLOCKED` immediately. The required-member check (`scripts/mpp/mpp.sh`, etc.) is also ZIP-member-path based and would not apply to a tar layout.

**The prior durable release** (`metablooms-stage12-reconciled-20260522T0058Z`, `.zip.zst`) remains fully auditable.

**Recommended fix (not applied this pass):** Extend `materialize()` to handle `.tar.zst` + add tar-based required-member inspection; or require future full-OS releases to use `.zip.zst` for harness compatibility.

---

### FIND-07 — Workflow does not fail-fast on absent sidecar [INFORMATIONAL]

**File:** `.github/workflows/metablooms-release-audit-harness.yml` lines 84–88

The workflow downloads the release asset and its `.sha256` sidecar then passes `artifact_path` to the runner. If the sidecar were absent from the release, `gh release download` would error on that asset, but the workflow currently has no explicit pre-runner SHA verification step. The runner would then emit `BLOCKED` rather than a hard workflow failure.

The sidecar **is present** in the current release.

---

### FIND-08 — New sticky release not in durability ledger; K2 floor intact [PASS / NO ACTION]

**Durability ledger:** `runtime/generated/sarp_receipt_key_selfverify_20260601T2232Z/DURABILITY_LEDGER_RECEIPT_KEY_NORMALIZED.json` (created 2026-06-01T22:36Z)

The sticky release was published at 2026-06-01T23:20Z — after the ledger was written. No entry exists for `786fd1...`. Per audit rule: **do not mark durable unless binary readback proof exists.** No action taken.

**Current durable floor (K2):**
```
name:    K2_stage011k2_floor
sha256:  4efc7472396f79311a220d3acc2ddee4a0ec4c5e22dbf2b12c28742d50c50024
binary_readback_real_hash_pass: true
receipt: runtime/generated/k2_readback_import_20260601T1604Z/LANDED_ASSET_STAGE011K2_20260601T154518Z.json
```

K2 floor **not replaced**. Shrunk stage008B baseline (`38fe0f2d...`) remains `PENDING_PHONE_RELEASE_ASSET_READBACK`.

---

### FIND-09 — Runner self-test missing three fixture cases [MEDIUM]

**File:** `runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py` lines 154–181

Current self-test cases: `positive (PASS)`, `missing_mpp (FAIL)`, `traversal (FAIL)`

Missing regression cases:
1. **sidecar_wrong_hash** — sidecar exists with wrong but valid 64-hex hash → `artifact_sha_sidecar: FAIL`
2. **sidecar_malformed** — sidecar exists with non-hex content → `artifact_sha_sidecar: BLOCKED`
3. **tar_zst_blocked** — artifact is `.tar.zst` → `artifact_extension: BLOCKED`

**First-pass action:** Standalone `fixtures/release_audit_harness/sidecar_regression_validator.py` covers all three without modifying the runner.

---

## Constraints Observed

| Constraint | Observed |
|---|---|
| Durable floor replaced | No |
| Release assets uploaded | No |
| Broad repairs made | No |
| Fixtures/validators only in PR | Yes |

## Files Added in This PR

| Path | Purpose |
|---|---|
| `audits/METABLOOMS_OS_REPO_SIDE_AUDIT_20260602.md` | This report |
| `audits/METABLOOMS_OS_REPO_SIDE_AUDIT_20260602.json` | Machine-readable audit record |
| `fixtures/landed_receipt_self_verify/canonical_only_PASS.json` | FIND-03: canonical key fixture |
| `fixtures/landed_receipt_self_verify/neither_key_BLOCKED.json` | FIND-03: neither key fixture |
| `fixtures/release_audit_harness/sidecar_regression_validator.py` | FIND-01/02/09: standalone sidecar regression validator |
