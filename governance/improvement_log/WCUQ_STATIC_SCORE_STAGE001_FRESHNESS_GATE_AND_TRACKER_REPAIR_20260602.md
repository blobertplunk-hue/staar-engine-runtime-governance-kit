# WCUQ_STATIC_SCORE_STAGE001_FRESHNESS_GATE_AND_TRACKER_REPAIR

Date: 2026-06-02
Status: PASS in ChatGPT sandbox; proof summary committed to branch.

## Summary

Stage001 repaired the active Visual Tracker WCUQ display so a historical WCUQ calibration value is no longer presented as a live per-turn score.

## Root cause

`tools/metablooms/visual_teacher_final_response_binding_gate_v1.py` read `runtime/state/WCUQ_STATUS.txt` directly and rendered its text into `runtime/state/ACTIVE_TRACKER_PREVIEW.txt` without checking freshness.

The status file contained a historical calibration surface:

```text
score 90.35; band A; promotion_ready=True; gate=PASS_WCUQ_CONTROLLER_PROMOTION; field_schema=STRICT_SCHEMA_READY; calibration=INITIAL_BASELINE_NEEDS_FIELD_DATA; controller_injection=STAGE9_BATCH
```

Because no freshness gate existed, that historical score appeared current on every boot.

## Patch

The Visual Tracker binding gate now includes WCUQ freshness logic:

- reads `runtime/state/WCUQ_STATUS.json` when available;
- checks `created_at_utc` against a one-hour freshness window;
- suppresses numeric score unless freshness is proven;
- renders `WCUQ stale/unavailable; numeric score suppressed` when stale or unverifiable;
- records WCUQ freshness evidence in the binding receipt.

## Machine-enforced checks

- `file_search_used:false`.
- `python3 -m py_compile tools/metablooms/visual_teacher_final_response_binding_gate_v1.py`: PASS.
- Visual Tracker binding gate regenerated `runtime/state/ACTIVE_TRACKER_PREVIEW.txt`: PASS.
- Regression check forbids `score 90.35` in active tracker: PASS.
- Regression check requires `WCUQ stale/unavailable; numeric score suppressed`: PASS.
- Post-patch `turn-boot`: PASS.
- Post-boot tracker still suppresses stale score: PASS.

## Current tracker WCUQ block after repair

```text
📊 WCUQ:
  WCUQ stale/unavailable; numeric score suppressed
```

## Artifact packet

ChatGPT sandbox packet:

```text
/mnt/data/WCUQ_STATIC_SCORE_STAGE001_FRESHNESS_GATE_AND_TRACKER_REPAIR_20260602T225434Z.zip
```

SHA-256:

```text
a953e14c905136e3eee9c5cca23aa4a7f46387a00d12a79d111e5ddd017d52fd
```

## Limitation

This stage fixes active tracker rendering and validates behavior after boot. It does not yet formalize the full `live_score` / `last_known_calibration` / `stale_or_unavailable` WCUQ schema, and it does not yet produce a full export/cold-restore readback for this WCUQ patch.

## Next stage

```text
WCUQ_STATIC_SCORE_STAGE002_SCHEMA_AND_EXPORT_READBACK
```

Scope:

1. Add or update WCUQ status schema to separate `live_score`, `last_known_calibration`, and `stale_or_unavailable`.
2. Add a validator fixture that fails if stale numeric WCUQ appears in active tracker.
3. Produce export/diff packet and cold-restore proof.
