# NATIVE_METABLOOMS_OS_SOURCE_PATCH_LOCATION_AND_EXPORT_LINEAGE_BINDING

Date: 2026-06-02
Status: PASS in ChatGPT sandbox.

## Decision

The native MetaBlooms WCUQ/rootless source patch is located in `/mnt/data/Metablooms_OS`, not in `blobertplunk-hue/staar-engine-runtime-governance-kit`.

PR #9 is a governance/proof carrier and remote patch artifact carrier. It must not be described as native OS source application.

## Native source locations verified

- `tools/metablooms/visual_teacher_final_response_binding_gate_v1.py`
- `tools/metablooms/web_coding_usage_score_status_surface_v1.py`
- `tools/metablooms/wcuq_status_schema_validator_v1.py`
- `0_kernel/registry/wcuq/WCUQ_STATUS_SCHEMA_v2.json`
- `runtime/state/WCUQ_STATUS.json`
- `runtime/state/WCUQ_STATUS.txt`
- `METABLOOMS_ROOTLESS_PREBOOT_BOOTSTRAP_v1.py`
- `METABLOOMS_PREBOOT_RESCUE_v1.sh`
- `tools/metablooms/preboot_bundle_rescue_self_heal_v1.py`
- `scripts/mpp/mpp.sh`

## Validation

- Boot: PASS.
- WCUQ validator: PASS.
- Active tracker contains `WCUQ stale/unavailable; numeric score suppressed`.
- Active tracker does not contain `score 90.35`.
- File search used: false.

## Export lineage

Relevant local artifacts are bound in the sandbox packet:

```text
/mnt/data/NATIVE_METABLOOMS_OS_SOURCE_PATCH_LOCATION_AND_EXPORT_LINEAGE_BINDING_20260602T234014Z.zip
```

This packet contains:

- native source path manifest;
- source SHA-256 manifest;
- relevant artifact path manifest;
- relevant artifact SHA-256 manifest;
- WCUQ validator receipt;
- lineage binding manifest.

## Lineage roles

- Live OS source: `/mnt/data/Metablooms_OS` contains the actual patched native source/runtime files.
- Repo carrier: PR #9 carries proof records and a remote base64 patch artifact.
- Full export lineage: WCUQ/rootless `tar.zst` files in `/mnt/data` preserve portable OS lineage.
- Stage packets: ZIP packets in `/mnt/data` preserve receipts, diffs, and handoffs.

## Next stage

```text
MERGE_PR9_AS_PROOF_CARRIER_OR_BUILD_NATIVE_OS_SOURCE_REPO_EXPORT
```

Decision needed: merge PR #9 only as a proof/artifact carrier, or create a separate native OS source repository/export lane for actual source patch application.
