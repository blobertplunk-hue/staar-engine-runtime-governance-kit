# SPREADSHEET_STAGE011_SEE_FREEZE_ROUTE_DISCOVERY

Date: 2026-06-03
Branch target: `claude/metablooms-os-audit-hr5ET`
Status: required next improvement stage

## Purpose

Repair the Stage010 SEE omission and discover the best supported freeze-pane route for scrollable production spreadsheets.

## Governance repair

Spreadsheet cartridge implementation stages must run current external SEE research before:

- locking production policy;
- selecting spreadsheet writer libraries;
- declaring a feature unsupported;
- routing around a blocked feature;
- repairing a spreadsheet blocker.

## Current policy state

Stage010 scrollable freeze-pane policy is safe but provisional:

- compact workbook under 25 rows: missing serialized freeze panes may warn;
- scrollable workbook at or above 25 rows: missing serialized freeze panes must block.

This lock remains provisional until Stage011 tests supported routes.

## Routes Stage011 must test

Stage011 must build minimal and representative workbooks through:

1. artifact_tool native route;
2. openpyxl route;
3. XlsxWriter route;
4. pandas ExcelWriter route using supported engines where useful.

## Required evidence

Promotion requires direct `.xlsx` OOXML readback. The produced workbook must contain worksheet pane evidence under `sheetViews/sheetView/pane`, with frozen state and correct split/top-left attributes for required scrollable sheets.

## Promotion rule

A route may be promoted only if it preserves:

- serialized frozen panes;
- formulas;
- tables or structured regions;
- validation rules;
- charts or dashboard artifacts where required;
- visual contract: borders, fonts, semantic colors, bold hierarchy;
- provenance/readback receipts.

## Failure rule

If no supported route works, retain the Stage010 scrollable-production blocker, but record that decision with same-turn SEE and route-test evidence.
