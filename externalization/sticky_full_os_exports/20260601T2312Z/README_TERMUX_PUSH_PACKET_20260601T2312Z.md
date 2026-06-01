# MetaBlooms STICKY push/readback packet — 20260601T2312Z

## Decision
PASS_TERMUX_STICKY_PUSH_PACKET_PREPARED

## Target
- Full OS asset: `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst`
- Expected SHA-256: `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`
- Expected size bytes: `213513094`
- Release tag: `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`

## Packet
- File: `TERMUX_STICKY_BASELINE_PUSH_READBACK_PACKET_20260601T2312Z.zip`
- Packet SHA-256: `8664176ec8663a3706996893705a3c8b102625e124c3a31517837bfb7dcf4c70`

## What the packet does
1. Locates the STICKY full OS archive in Android Downloads.
2. Verifies local SHA and byte size before upload.
3. Creates or reuses GitHub release tag `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`.
4. Uploads the `.tar.zst` and available sidecars with `gh release upload --clobber`.
5. Downloads the uploaded `.tar.zst` back from the release.
6. Verifies downloaded SHA and byte size.
7. Writes a landed receipt with canonical `downloaded_sha256` populated.
8. Writes `CHECKSUMS.sha256` and a returned `.download` file for import verification.

## Durable floor rule
Do not mark STICKY durable until returned landed receipt contains:

```text
expected_sha256=786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
downloaded_sha256=786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73
sha_match=true
```

The prior shrunk floor remains the fallback until that import passes:

`38fe0f2d5f220a53acd13edc5ea0a25e6a1c4aaca38864ba1a2d8f785ed07add`
