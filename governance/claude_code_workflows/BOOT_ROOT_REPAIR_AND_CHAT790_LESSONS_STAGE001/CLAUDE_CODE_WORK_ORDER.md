# Claude Code work order: BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_STAGE001

Predecessor: META_TOOL_ROUTER_AND_REPEATED_BLOCKER_LEDGER_STAGE001 (merged, PR #11).

## Goal

Activate the merged guard scripts as repo-level Claude Code hooks so that future sessions
on this repo are protected by the tool router and repeated-blocker ledger.

## Deliverables

1. `.claude/settings.json` — repo-level Claude Code settings wiring:
   - `PreToolUse` → `python3 governance/tool_routing/tool_route_guard.py --hook-stdin`
   - `PostToolUseFailure` → `python3 governance/blocker_ledger/repeated_blocker_guard.py --hook-stdin --mode record-or-route`

2. `governance/tool_routing/hook_install_validator.py` — validates hook config integrity:
   - settings.json present, valid JSON
   - hook commands reference existing scripts
   - smoke-tests each command with a safe synthetic input

3. `tests/fixtures/hook_activation/` — 5 fixtures testing the hook path end-to-end.

4. `tests/test_hook_activation.py` — subprocess-based tests for all 5 fixtures.

5. `receipts/BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_STAGE001_RECEIPT.json`.

## Validation commands

```bash
python3 -m py_compile governance/tool_routing/tool_route_guard.py \
                       governance/blocker_ledger/repeated_blocker_guard.py
python3 tests/test_tool_routing_and_blocker_ledger.py
python3 tests/test_hook_activation.py
python3 governance/tool_routing/hook_install_validator.py
```

## Hard constraints

- Do not start the full chat_export_mining cartridge.
- Do not claim native MetaBlooms OS source patching in this repo.
- Do not use file_search for mounted /mnt/data OS artifact truth.
- Stop after one PR.
