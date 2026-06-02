# WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK

Date: 2026-06-02
Status: PASS in ChatGPT sandbox; proof summary committed to branch.

## Summary

Stage002 implemented the WCUQ Visual Tracker status schema split and produced a full export plus cold-restore readback proof. The active tracker can no longer display the historical `score 90.35` calibration surface as a live score.

## Implemented schema split

New schema descriptor:

```text
0_kernel/registry/wcuq/WCUQ_STATUS_SCHEMA_v2.json
```

The runtime status now separates:

- `live_score`
- `last_known_calibration`
- `stale_or_unavailable`

The migrated current state is `stale_or_unavailable`, with the old `score 90.35` text preserved only under `last_known_calibration` as historical evidence, not as the tracker display surface.

## Patched code

- `tools/metablooms/web_coding_usage_score_status_surface_v1.py`
- `tools/metablooms/visual_teacher_final_response_binding_gate_v1.py`
- `tools/metablooms/wcuq_status_schema_validator_v1.py`
- `0_kernel/registry/wcuq/WCUQ_STATUS_SCHEMA_v2.json`
- `runtime/state/WCUQ_STATUS.json`
- `runtime/state/WCUQ_STATUS.txt`

## Machine-enforced checks

- `file_search_used:false`.
- Python compile passed for all patched WCUQ/tracker scripts.
- WCUQ v2 schema validator passed before boot.
- Visual Tracker binding regenerated active preview.
- WCUQ v2 schema validator passed after boot.
- Full export built with native `tar --zstd`.
- Full export SHA-256 sidecar produced.
- Full export `zstd -t` passed.
- Required full-export members were checked.
- Diff packet produced and `unzip -t` passed.
- Cold restore extracted the full export into an isolated directory.
- Cold restore contains the WCUQ v2 schema and validator.
- Cold-restored WCUQ validator passed before boot.
- Cold-restored boot returned rc `0`.
- Cold-restored WCUQ validator passed after boot.
- Cold-restored tracker contains `WCUQ stale/unavailable; numeric score suppressed`.
- Cold-restored tracker does not contain `score 90.35`.

## Artifact hashes

Full export:

```text
/mnt/data/WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK_20260602T230014Z/full_export/METABLOOMS_FULL_OS_WCUQ_STAGE002_20260602T230014Z.tar.zst
```

SHA-256:

```text
d704021d6788f22d2dad6da0923a1195b4e9561815f5327239d3806916ca15b5
```

Diff packet:

```text
/mnt/data/WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK_20260602T230014Z/diff_packet/WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK_20260602T230014Z_DIFF_PACKET.zip
```

SHA-256:

```text
a11541cf63256179f71a92c29a883413539e3d1aa0e59f0905d48e739ace96e2
```

Stage packet:

```text
/mnt/data/WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK_20260602T230014Z.zip
```

SHA-256:

```text
dc026b10b380eb63d61425e46e71be13df8dcf780ca61d68a898adcf65a4c9b2
```

## Limitation

This proof record is committed to the branch, but the actual full export and stage packets remain sandbox artifacts rather than GitHub release artifacts. The next stage should either open a PR or add repo-side patch files/scripts so the branch can reproduce the code changes without relying on the sandbox bundle.

## Next stage

```text
WCUQ_STATIC_SCORE_STAGE003_BRANCH_PATCH_OR_PR_AND_MAINLINE_EXPORT_POLICY
```
