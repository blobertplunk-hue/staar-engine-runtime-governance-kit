# Claude Code work order: META_TOOL_ROUTER_AND_REPEATED_BLOCKER_LEDGER_STAGE001

You are Claude Code operating in the STAAR / MetaBlooms governance repository. This is not an open-ended prompt. Execute the repo workflow pack in this directory.

## Required first actions

1. Read `WORKFLOW_CONTRACT.json`.
2. Read `EVIDENCE_AND_JUSTIFICATION.md`.
3. Read `GATES_AND_FIXTURES_SPEC.json`.
4. Inspect these repo process files if present:
   - `governance/improvement_log/METABLOOMS_CHAT790_POSTMORTEM_URGENT_OS_CHANGES_20260602.md`
   - `audits/METABLOOMS_COMPARATIVE_GOVERNANCE_RUBRIC_20260602.md`
   - `governance/improvement_log/NATIVE_METABLOOMS_OS_SOURCE_PATCH_LOCATION_AND_EXPORT_LINEAGE_BINDING_20260602.md`
5. Create a branch named `claude/meta-tool-router-blocker-ledger-stage001`.

## Build requirements

Implement the smallest repo-native machinery that satisfies the contract. Recommended file layout, adjustable only if repo conventions demand another location:

```text
governance/tool_routing/TOOL_ROUTING_POLICY_v1.json
governance/tool_routing/tool_route_guard.py
governance/blocker_ledger/REPEATED_BLOCKER_LEDGER_SCHEMA_v1.json
governance/blocker_ledger/repeated_blocker_guard.py
tests/fixtures/tool_routing/*.json
tests/fixtures/blocker_ledger/*.json
tests/test_tool_routing_and_blocker_ledger.py
receipts/META_TOOL_ROUTER_AND_REPEATED_BLOCKER_LEDGER_STAGE001_RECEIPT.json
```

If the repo already has equivalent paths, extend the existing system rather than duplicating.

## Mandatory fixtures

- `blocked_mnt_data_file_search`: attempts file_search for `/mnt/data/Metablooms_OS` truth; expected BLOCKED.
- `allowed_uploaded_semantic_query`: uploaded semantic document query; expected ALLOW_FILE_SEARCH.
- `first_blocker_logs`: first normalized blocker; expected LOG_ONLY.
- `repeat_blocker_forces_rca`: repeated normalized blocker with unchanged inputs; expected FORCE_RCA.
- `changed_inputs_not_repeat`: same symptom with changed artifact hash/command/input; expected LOG_NEW_VARIANT.

## Validation commands

Run the most appropriate available commands, then record exact commands and outputs in the receipt. Minimum expected commands:

```bash
python3 -m py_compile governance/tool_routing/tool_route_guard.py governance/blocker_ledger/repeated_blocker_guard.py
python3 -m pytest tests/test_tool_routing_and_blocker_ledger.py
```

If pytest is not available, add a stdlib runner and record that fallback explicitly.

## PR rules

Open one PR. The PR body must include:

- what was implemented;
- test commands and results;
- whether changes are native repo machinery, proof/artifact carrier, or both;
- limitations;
- next stage recommendation.

Stop after the PR. Do not start the chat_export_mining cartridge.
