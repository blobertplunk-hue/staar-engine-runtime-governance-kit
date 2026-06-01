# MetaBlooms STICKY durable floor imported — 20260601T2326Z

## Decision
PASS_STICKY_BASELINE_DURABLE_FLOOR_IMPORTED

## Binary readback proof
- Release tag: `MB-FULL-STICKY-RECEIPT-KEY-SELFVERIFY-20260601T2251Z`
- Asset: `METABLOOMS_FULL_OS_STICKY_AFTER_RECEIPT_KEY_SELFVERIFY_20260601T2251Z.tar.zst`
- Expected SHA-256: `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`
- Local SHA-256: `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`
- Downloaded SHA-256: `786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`
- Downloaded size bytes: `213513094`
- sha_match: `true`

## Durable floor
STICKY is now the durable floor:

`786fd1118a7a3be4f13bf618de2826e161765c0ba7ff5772b85eae98e42f9e73`

Prior floor retained as fallback archive reference:

`38fe0f2d5f220a53acd13edc5ea0a25e6a1c4aaca38864ba1a2d8f785ed07add`

## New post-import full OS bundle
- File: `METABLOOMS_FULL_OS_STICKY_DURABLE_FLOOR_IMPORTED_20260601T2326Z.tar.zst`
- SHA-256: `e27f0768850c626e3a1e2b70cc820ee8f1a59ac2cd65c77216a3f698c4e4ea27`
- Size bytes: `212688238`

## Export verification
- `sha256sum -c`: PASS
- `zstd -t`: PASS
- tar member check: PASS
- smoke extract of imported receipt + durability ledger: PASS

## Included OS paths
- `runtime/receipts/sticky_baseline_release_asset_readback/LANDED_ASSET_STICKY_BASELINE_20260601T2251Z_20260601T232024Z.json`
- `runtime/durability/STICKY_DURABLE_FLOOR_LEDGER.json`
- `runtime/durability/CURRENT_DURABLE_FLOOR.txt`
