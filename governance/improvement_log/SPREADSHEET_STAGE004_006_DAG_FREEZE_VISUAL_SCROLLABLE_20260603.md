# SPREADSHEET_STAGE004_006_DAG_FREEZE_VISUAL_SCROLLABLE

Date: 2026-06-03
Branch target: `claude/metablooms-os-audit-hr5ET`
Status: improvement-log entry

## Purpose

Preserve the middle spreadsheet cartridge improvement block from MetaBlooms Stages 004-006.

## Stage004: DAG, freeze, and visual gates

- Ingested peer review of the Stage003 workbook and preview.
- Added formula DAG validation to prove data moves through intended layers.
- Required production flow: Inputs -> Calculations -> Dashboard.
- Added freeze-pane policy based on workbook scale.
- Added deterministic visual preview checks.

## Stage005: native builder and freeze route

- Added a native spreadsheet builder route.
- Builder emits workbook spec, xlsx file, rendered preview, and validation receipts.
- Attempted supported artifact_tool freeze pane calls.
- Recorded that exported OOXML still lacked serialized frozen panes.
- Kept the gap visible instead of using unsupported direct workbook mutation.

## Stage006: rendered layout and scrollable blocker

- Added rendered layout gate for preview existence, size, nonblank output, variance, edge/crowding risk, and advisory OCR posture.
- Added row-count support to generate larger tracker fixtures.
- Built a 40-row scrollable fixture.
- Proved missing freeze panes become a hard blocker for scrollable trackers.

## Required preservation

Future spreadsheet work must retain:

- formula DAG validation;
- no direct Dashboard bypass from Inputs unless explicitly whitelisted;
- viewport-aware freeze-pane policy;
- rendered preview checks;
- visible warning/blocker receipts;
- no unsupported hidden OOXML mutation.
