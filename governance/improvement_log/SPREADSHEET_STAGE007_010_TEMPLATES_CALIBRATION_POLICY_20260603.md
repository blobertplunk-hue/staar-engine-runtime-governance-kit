# SPREADSHEET_STAGE007_010_TEMPLATES_CALIBRATION_POLICY

Date: 2026-06-03
Branch target: `claude/metablooms-os-audit-hr5ET`
Status: improvement-log entry

## Purpose

Preserve the spreadsheet cartridge improvement block from MetaBlooms Stages 007-010.

## Stage007: visual strictness and production templates

- Added rendered visual strictness gate.
- Classified top/left header density differently from right/bottom clipping risk.
- Added negative clipping/spill fixture.
- Added production template set for gradebook tracker, finance reconciliation tracker, and project/action tracker.
- Preserved Robert's visual requirements across templates: borders, fonts, semantic colors, bold hierarchy, text labels, and clear delineation.

## Stage008: real use-case builders

- Added template builder for gradebook, finance reconciliation, and project/action trackers.
- Builder emits xlsx, preview, formula scan, dashboard inspection, readback, DAG, freeze, rendered layout, and visual strictness receipts.
- Repaired a real formula DAG defect where project Dashboard referenced Inputs directly instead of Calculations.

## Stage009: calibration and scrollable variants

- Repaired row-count truncation so scrollable variants are actually scrollable.
- Added calibration runner for compact and scrollable variants across all three template families.
- Confirmed compact variants warn when freeze panes are missing.
- Confirmed scrollable variants block when freeze panes are missing.

## Stage010: provisional policy lock

- Added scrollable freeze policy lock.
- Current safe policy: compact under 25 rows may warn; scrollable 25+ rows must block if serialized freeze panes are absent.
- After governance review, this Stage010 lock must be treated as provisional pending Stage011 SEE-backed route testing.

## Required preservation

Future production spreadsheet templates must include:

- template-specific builders;
- compact and scrollable variants;
- calibration receipts;
- rendered visual strictness checks;
- formula DAG checks;
- freeze policy checks;
- no direct Dashboard bypass from Inputs;
- visible warnings/blockers, not hidden caveats.
