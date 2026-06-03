# CLAUDE_CODE_IMPLEMENTATION_PLAN_FOR_CHAT790_OS_REPAIRS

## Decision

`PASS_PLAN_READY_FOR_CLAUDE_CODE_IMPLEMENTATION`

This is a bounded implementation plan, not an implementation commit. It converts the 790-chat extraction lessons into a Claude Code work order that can be applied to the `staar-engine-runtime-governance-kit` repository on branch `claude/metablooms-os-audit-hr5ET`.

## Constraints

- Do not use `file_search` for mounted `/mnt/data` artifact work.
- Use direct filesystem, Python, tar/zip member reads, checksums, manifests, and GitHub/git operations as the primary tools.
- Preserve root-cause evidence; do not hide failed attempts.
- Make the smallest valid staged changes.
- Do not claim implementation complete until tests/receipts prove it.
- Keep stage outputs reviewable by Claude Code and external auditors.

## Source facts from this chat

1. Live boot root was unsound until restored from `METABLOOMS_FULL_OS_WITH_CLAUDE_GITHUB_WORK_20260603T021048Z.tar.zst`.
2. `turn-boot` now passes in `/mnt/data/Metablooms_OS` after root promotion.
3. Improvement log entry exists on branch `claude/metablooms-os-audit-hr5ET` at `governance/improvement_log/METABLOOMS_CHAT790_POSTMORTEM_URGENT_OS_CHANGES_20260602.md`.
4. The 790-chat extraction/export workflow produced a download-safe final packet and proved a reusable pattern: chunk -> SAR -> windowing repair -> supersede -> recheck -> final consolidation -> download-safe export.
5. The urgent changes are not yet implemented as durable OS behavior.

## Implementation strategy

Implement as four small PR-sized stages, not one broad patch.

### Stage A — Boot-root and tool-routing guard foundation

Goal: make the OS refuse the two failure classes that recurred in this chat: unsound boot roots and weak tool routing.

Files to add or modify:

- `governance/tool_routing/FILE_SEARCH_BAN_FOR_MOUNTED_ARTIFACTS_v1.md`
- `governance/tool_routing/TOOL_ROUTING_POLICY_v1.json`
- `governance/boot/BOOT_ROOT_REPAIR_POLICY_v1.md`
- `tests/governance/test_tool_routing_policy.py`
- `tests/governance/test_boot_root_repair_policy.py`

Required behavior:

- Mounted `/mnt/data` OS artifacts route to direct filesystem/Python/archive reads.
- `file_search` is explicitly banned for mounted artifact truth unless a human override is present.
- Boot-root repair policy requires `scripts/mpp/mpp.sh` and a same-run boot receipt.

Exit gate:

- Tests prove `file_search` is rejected for mounted artifact work.
- Tests prove missing `scripts/mpp/mpp.sh` is a blocker, not a soft warning.

### Stage B — Chat export mining cartridge skeleton

Goal: create a real cartridge receptor target for the proven 790-chat workflow.

Files to add:

- `cartridges/chat_export_mining/CARTRIDGE_MANIFEST.json`
- `cartridges/chat_export_mining/CARTRIDGE_CAPABILITY_DESCRIPTOR.json`
- `cartridges/chat_export_mining/CARTRIDGE_ACTION_DESCRIPTOR.json`
- `cartridges/chat_export_mining/schemas/chat_index.schema.json`
- `cartridges/chat_export_mining/schemas/product_index.schema.json`
- `cartridges/chat_export_mining/schemas/component_parent_binding.schema.json`
- `cartridges/chat_export_mining/schemas/process_event.schema.json`
- `cartridges/chat_export_mining/README.md`
- `tests/cartridges/chat_export_mining/test_manifest_schema.py`

Required behavior:

- Cartridge can be discovered by manifest.
- Schemas encode stable `case_thread_id`, `artifact_class`, `product_identity`, parent binding, evidence reference, and lifecycle metadata.
- Action descriptor exposes bounded stage names but does not yet run full extraction.

Exit gate:

- Manifest validates.
- Schema fixtures for good and bad rows pass/fail correctly.

### Stage C — R7/R8/R8C validators and fixtures

Goal: codify the exact gates that prevented false-complete extraction.

Files to add:

- `cartridges/chat_export_mining/validators/r7_placeholder_parent_binding.py`
- `cartridges/chat_export_mining/validators/r8_giant_chat_coverage.py`
- `cartridges/chat_export_mining/validators/r8c_supersede_manifest.py`
- `cartridges/chat_export_mining/fixtures/r7/generic_placeholder_promoted_fail.jsonl`
- `cartridges/chat_export_mining/fixtures/r7/parent_bound_component_pass.jsonl`
- `cartridges/chat_export_mining/fixtures/r8/windowed_giant_chat_fail.json`
- `cartridges/chat_export_mining/fixtures/r8/full_scan_giant_chat_pass.json`
- `cartridges/chat_export_mining/fixtures/r8c/supersede_manifest_pass.jsonl`
- `tests/cartridges/chat_export_mining/test_r7_r8_r8c_validators.py`

Required behavior:

- Promoted `unnamed_artifact` and generic standalone product IDs fail.
- Giant chat partial windows below the configured floor fail.
- R8C requires proof that partial rows were removed and full-scan rows were added.

Exit gate:

- Fixture suite passes.
- Failure messages identify the violated rule and required repair stage.

### Stage D — Download-safe export and sluggy countdown gates

Goal: prevent the two operator-facing problems from recurring: non-downloadable exports and unclear progress.

Files to add:

- `governance/export/DOWNLOAD_SAFE_EXPORT_POLICY_v1.md`
- `tools/export/download_safe_packet_builder.py`
- `tools/tracker/sluggy_countdown.py`
- `tests/export/test_download_safe_packet_builder.py`
- `tests/tracker/test_sluggy_countdown.py`

Required behavior:

- Export builder detects nested duplicate source ZIPs.
- Export builder emits an integrity-checked smaller relay packet when the canonical packet is too large or duplicative.
- Sluggy countdown reports percent done, next exact stage, best/likely/risk turns left, blocker, and forbidden actions.

Exit gate:

- Test fixture proves nested duplicate ZIPs are excluded from download-safe packet while final expanded indexes remain.
- Countdown output is deterministic and artifact-backed.

## Non-goals for this implementation wave

- Do not rerun the full 790-chat extraction.
- Do not baseline-lock a new full OS bundle in the same stage.
- Do not implement deep strategic analysis of the 790 chats yet.
- Do not delete or rewrite historical packets.

## Claude Code execution prompt

Use this as the next Claude Code prompt:

```text
You are working in repo blobertplunk-hue/staar-engine-runtime-governance-kit on branch claude/metablooms-os-audit-hr5ET. Implement Stage A only from governance/implementation_plans/CLAUDE_CODE_IMPLEMENTATION_PLAN_FOR_CHAT790_OS_REPAIRS.md. Do not use file_search. Use direct repo reads and tests. Add boot-root repair policy and mounted-artifact tool-routing policy with tests. Keep changes minimal, run tests, write a receipt, and stop after Stage A.
```

## Risks

- Branch may already contain related Claude changes; Claude Code must inspect before writing.
- If repo layout differs from the planned paths, Claude Code should adapt using existing governance directories rather than creating duplicate policy families.
- If tests infrastructure differs, add minimal standalone tests without destabilizing existing CI.

## Final recommendation

Proceed with `CHAT790_OS_REPAIRS_STAGE_A_BOOT_ROOT_AND_TOOL_ROUTING_GUARDS` before implementing the cartridge. Stage A prevents the recurring failure class that caused repeated operator correction in this chat.
