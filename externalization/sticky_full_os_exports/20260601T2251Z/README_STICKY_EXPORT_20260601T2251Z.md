# MetaBlooms sticky full OS export — 20260601T2251Z

## Decision
PASS_STICKY_FULL_OS_EXPORT_READY_FOR_RELEASE_ASSET_UPLOAD

## Why this exists
This export preserves the repairs for three serious governance defects:

1. **Live sidecar false FAIL class** — mutable `codified_robert` live projections were treated as frozen sidecar targets, causing recurring false FAILs.
2. **Receipt-key mismatch** — real landed readback proofs used `downloaded_sha256`, while some consumers looked for `download_sha256`, making valid durability proofs appear null.
3. **Durability proof fragility** — landed receipts now normalize both key spellings and self-verify rather than relying on manual `.download` rehashing.

## Full OS archive
- File: `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst`
- SHA-256: `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`
- Size bytes: `213513094`
- Source root: `/mnt/data/Metablooms_OS`

## Local archive verification performed
- `sha256sum -c`: PASS
- `zstd -t`: PASS
- tar member check for sticky manifest and self-verifier: PASS
- smoke extract of internal manifest and self-verifier: PASS

## Included critical paths checked in archive
- `Metablooms_OS/runtime/exports/STICKY_FULL_OS_EXPORT_20260601T2248Z_INTERNAL_MANIFEST.json`
- `Metablooms_OS/tools/metablooms/landed_receipt_self_verify_v1.py`
- `Metablooms_OS/runtime/receipts/export_after_shrink_protection/STAGE008B_PHONE_READBACK_IMPORT_RECEIPT_20260601T2222Z.json`

## GitHub release asset status
The ChatGPT GitHub connector available in this turn supports repository text-file writes but does **not** expose a release-asset upload function for binary `.tar.zst` files. This README is safe to commit as a GitHub pointer. The full archive must be uploaded as a release asset through Termux/GitHub CLI or another binary-capable route.

## Required release upload target
Repository: `blobertplunk-hue/staar-engine-runtime-governance-kit`
Suggested release tag: `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`
Required uploaded assets:
- `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst`
- `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst.sha256`
- `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst.provenance.json`

## Next gate
After release upload, perform binary readback and produce a landed receipt requiring:

```text
expected_sha256=786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
downloaded_sha256=786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
sha_match=true
```
