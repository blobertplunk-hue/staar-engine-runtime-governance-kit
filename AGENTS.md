# MetaBlooms OS — Codex operating instructions

## Authority order
1. MetaBlooms OS artifacts, receipts, ledgers, schemas, validators, manifests, and durable-floor records.
2. This `AGENTS.md`.
3. The active task prompt or GitHub issue.
4. Model inference.

Do not override artifact evidence with chat claims, README pointers, or assumptions.

## Mandatory boot rule
Before any MetaBlooms OS audit, repair, export, or validation work:

```bash
bash scripts/mpp/mpp.sh turn-boot --task "<specific bounded task>" --operation validate --print-summary
```

For repairs, use `--operation repair`; for exports, use `--operation export`; for analysis only, use `--operation analyze`.

If boot fails, stop and report the blocker. Do not patch before root cause is identified.

## Durable-floor rule
The current GitHub binary-readback-proven STICKY floor is:

```text
786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
```

Release tag:

```text
MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z
```

Asset:

```text
METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst
```

Prior fallback floor:

```text
38fe0f2d5f220a53acd13edc5ea0a25e6a1c4aaca38864ba1a2d8f785ed07add
```

Never replace, promote, retire, or rewrite durable floors unless the task explicitly requires a bounded durable-floor stage and binary release readback passes.

## Binary durability rule
A GitHub README, pointer, issue, provenance file, or chat claim is not durability proof. Durability requires a landed receipt with:

- non-null `downloaded_sha256`,
- `sha_match: true`,
- expected/local/downloaded hashes matching where present,
- returned bytes re-hashed when the asset is available.

`downloaded_sha256` is canonical. `download_sha256` is legacy-only and must normalize to `downloaded_sha256`. If both keys exist and differ, block.

## Sidecar rule
Mutable live projections must not cause false FAILs, but they must not be blindly ignored. They require structural validation before any current-hash/sidecar refresh. Corrupted live files must still be flagged.

## Export rule
Never report export success for a partial archive. Full exports require at least:

- archive file,
- SHA-256 sidecar,
- provenance JSON,
- internal manifest when the export stage requires it,
- `sha256sum -c` PASS,
- compression integrity PASS,
- critical member check PASS,
- receipt/handoff written.

## Repair rule
Every repair needs:

- root cause,
- smallest safe change,
- negative fixture or regression check,
- validator output,
- receipt or audit packet,
- changed-file list.

Do not perform broad recursive rewrites unless the task explicitly authorizes them and sets stage bounds.

## Required output for audits
Create a timestamped packet under `runtime/generated/` containing:

- `AUDIT_REPORT.md`
- `MACHINE_FINDINGS.json`
- `COMMAND_LOG.md`
- `PATCH_PLAN.md`
- `SELF_SAR.md`
- `CHANGED_FILES.txt`
- `VALIDATOR_OUTPUTS/` when validators run
- `FIXTURES/` when fixtures are added

## Safety constraints
- Do not upload release assets unless explicitly asked.
- Do not delete durable-floor artifacts.
- Do not mark durable from pointer-only evidence.
- Do not hide failed commands; record them in `COMMAND_LOG.md`.
- Do not change generated exports without writing provenance.
