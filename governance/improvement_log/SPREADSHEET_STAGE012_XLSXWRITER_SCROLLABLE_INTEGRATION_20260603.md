# SPREADSHEET_STAGE012_XLSXWRITER_SCROLLABLE_INTEGRATION

Date: 2026-06-03
Branch target: `claude/metablooms-os-audit-hr5ET`
Status: improvement-log entry

## Purpose

Record Stage012 integration of the promoted XlsxWriter route for scrollable production spreadsheet templates.

## Result

Stage012 integrated XlsxWriter as the approved scrollable production export route for:

- gradebook tracker;
- finance reconciliation tracker;
- project/action tracker.

Each route built a 40-row scrollable workbook and passed:

- base workbook validator;
- `.xlsx` OOXML readback validator;
- formula DAG validator;
- freeze-pane policy validator;
- rendered layout gate;
- rendered visual strictness gate;
- formula error scan.

## Root-cause repairs

- The readback validator was patched to count custom-width column spans correctly when OOXML compresses column definitions.
- The rendered preview range was expanded so the visual gate does not falsely classify a preview cut through a scrollable table as bottom-edge clipping.

## Policy update

Scrollable production templates may now pass when routed through XlsxWriter and direct OOXML readback proves frozen panes on required sheets.

Artifact_tool remains valid for compact/preview flows, but it is not promoted for scrollable freeze-pane production until it proves serialized panes by readback.

## Required preservation

Future spreadsheet cartridge stages must preserve:

- XlsxWriter scrollable route;
- OOXML frozen-pane readback;
- formula DAG enforcement;
- visual contract and rendered strictness gates;
- provenance and formula error scans;
- no unsupported hidden workbook mutation.
