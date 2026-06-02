# MetaBlooms release audit attestation policy split — 2026-06-02

## Decision

The release audit workflow now separates **hard audit proof** from **advisory attestation provenance**.

## Hard release-audit proof

A sticky release audit is considered machine-proven when all of the following are true:

1. The workflow resolves the intended release asset instead of silently falling back to a fixture.
2. The release asset sidecar hash matches the downloaded asset bytes.
3. The release audit runner materializes the archive successfully.
4. The runner inspects the archive members.
5. Required boot members are present.
6. `audit_result.json` is produced.
7. `audit_packet.zip` and checksum are uploaded as GitHub Actions artifacts.
8. The GitHub artifact digest is recorded in the run artifact metadata.

For the current sticky release, this hard proof is satisfied by run `26813497301` on branch `claude/metablooms-os-audit-hr5ET`, head SHA `2e545c9615f23225677b53bc819803e32a5a3762`.

## Current sticky release result

Target release tag:

```text
MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z
```

Target asset:

```text
METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst
```

Observed release SHA-256:

```text
786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
```

Audit verdict:

```text
PASS_WITH_FINDINGS
```

Primary remaining finding:

```text
path_length_over_240 = WARN, overlong_gt240 = 165
```

Required boot members were present and no tar traversal/absolute/unsafe link/device violations were reported.

## Advisory attestation lane

GitHub artifact attestation generation is a provenance enhancement. Attestation verification is not currently the hard release-audit gate.

Reason:

- `actions/attest@v4` generation completed successfully in the audited runs.
- `gh attestation verify` did not produce a durable verified PASS result in the recorded attestation-result artifact before this policy split was codified.
- The workflow records attestation verification as a structured artifact so it cannot be silently ignored.

Current advisory status:

```text
ADVISORY_BLOCKED: ATTESTATION_VERIFY_FAILED_AFTER_AUDIT_PASS
```

Root-cause candidate under test:

```text
missing-or-insufficient-artifact-metadata-storage-record-or-attestation-indexing
```

A follow-up patch added:

```yaml
artifact-metadata: write
```

to the workflow permissions. The policy split remains valid unless a later run produces an attestation-result artifact with:

```json
{"decision":"PASS","mode":"ATTESTATION_VERIFIED"}
```

## Merge readiness rule

This PR may be reviewed as merge-ready for:

- `.tar.zst` release audit harness support,
- sticky release remote audit targeting,
- sticky release hard audit proof,
- explicit advisory-attestation policy recording.

This PR must **not** be described as a full attestation verification repair unless the attestation-result artifact says `ATTESTATION_VERIFIED`.

## Required reviewer language

Use this language when summarizing the PR:

```text
Remote sticky .tar.zst release audit is hard-proven as PASS_WITH_FINDINGS. GitHub attestation generation runs, but attestation verification remains an advisory provenance lane unless/until the attestation-result artifact reports ATTESTATION_VERIFIED.
```
