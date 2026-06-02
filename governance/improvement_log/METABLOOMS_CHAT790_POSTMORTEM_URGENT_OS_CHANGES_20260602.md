# MetaBlooms 790-chat workflow urgent OS improvements

Date: 2026-06-02
Source workflow: ChatGPT export mining / 790-chat extraction, consolidation, and final export packet
Repository area: `governance/improvement_log/`
Status: improvement-log entry only; not implementation-complete

## Summary

The 790-chat extraction workflow completed and produced a download-safe final export packet, but the workflow exposed urgent MetaBlooms OS changes that should be promoted from chat-level practice into durable, machine-enforced OS behavior.

The primary lesson is that large artifact-governed workflows must be artifact-first, chunked, SAR-gated, coverage-proven, better-tool-routed, and download-safe. Several of these rules were enforced during the chat by generated stage scripts and receipts, but they are not yet fully integrated into the repo/OS as reusable cartridges, validators, gates, or runtime policies.

## Urgent changes required

### 1. Restore and prove a boot-sound live OS root

**Problem:** The live sandbox root `/mnt/data/Metablooms_OS` was directly probed and found unsound because `scripts/mpp/mpp.sh` was missing. The older sticky durable-floor archive contained `Metablooms_OS/scripts/mpp/mpp.sh`, but staged boot still hit a root-location/entrypoint guard failure.

**Required OS change:** Add a deterministic boot-root repair/recovery path that can restore a boot-sound live root from the latest verified durable-floor archive, then prove `turn-boot` with receipts before any governed work proceeds.

**Acceptance criteria:**

- `/mnt/data/Metablooms_OS/scripts/mpp/mpp.sh` exists in the live root.
- `bash scripts/mpp/mpp.sh turn-boot --task <task> --operation <op> --print-summary` passes from the live root.
- Staged archive extraction does not fail with root-location guard errors.
- Boot repair writes a receipt and updates the active tracker.

### 2. Enforce better-tool routing for mounted artifacts

**Problem:** The workflow repeatedly showed that `file_search` is the wrong tool for mounted `/mnt/data` OS/artifact work. Direct container/Python/filesystem/ZIP reads were more accurate and auditable. The user explicitly banned `file_search` for this workflow.

**Required OS change:** Install a machine-enforced tool router for MetaBlooms OS artifact work:

- Mounted `/mnt/data` artifacts: use container shell, Python, direct filesystem reads, direct ZIP/tar member reads, checksums, manifests.
- GitHub repo changes: use GitHub connector or verified git tooling.
- Web evidence: use `web.run` only when external evidence is required.
- Do not use `file_search` for mounted OS artifact truth unless explicitly re-authorized.

**Acceptance criteria:**

- A pre-tool gate blocks `file_search` for `/mnt/data` OS artifact workflows.
- Receipts record tool path selected and why it is the strongest available path.
- Final reports include `file_search_used: false` for mounted-artifact stages.

### 3. Promote the 790-chat extraction workflow into a reusable cartridge

**Problem:** The extraction succeeded, but much of the logic was created as staged generated scripts rather than a durable OS cartridge.

**Required OS change:** Create a `chat_export_mining` cartridge with:

- manifest and capability descriptor;
- schemas for chat index, product index, component bindings, sidecars, evidence references, process events, commands, and code-block markers;
- bounded chunk runner;
- R7/R8/R8C repair loops;
- SAR/noise gates;
- final consolidation and export stages;
- fixtures covering giant chats, missing optional files, stale wording, corrupt ZIP recovery, and download-safe repackaging.

**Acceptance criteria:**

- A single cartridge entrypoint can reproduce the bounded workflow from source export zips.
- Every stage writes receipts and handoffs.
- Chunking and stop conditions are enforced by machine gates, not operator memory.

### 4. Make giant-chat full-scan coverage mandatory

**Problem:** Multiple chunks initially appeared complete but used partial 3,000,000-character window scans on giant chats. SAR later found coverage failures, requiring R8/R8C repairs.

**Required OS change:** Add a default giant-chat policy:

- detect giant chats before promotion;
- scan serially, one giant chat per receipt;
- use direct ZIP member streaming;
- require 100% source coverage or an explicit blocked state;
- supersede any prior partial/windowed rows before downstream consolidation.

**Acceptance criteria:**

- Windowed giant-chat coverage below the configured floor blocks next-stage authorization.
- R8 deepening writes per-chat receipts with source hash and coverage.
- R8C supersede manifests prove partial rows were removed and full-scan rows added.

### 5. Install R7 placeholder parent-binding as a reusable validator

**Problem:** Generic IDs such as `receipt`, `handoff`, `artifact`, `validation`, `index`, `file`, and `unnamed_artifact` can be real evidence but are not stable product identities. Earlier extraction promoted too many placeholder/generic IDs.

**Required OS change:** Promote R7 parent-binding rules into reusable validation:

- generic placeholders cannot be promoted as standalone products;
- bind components to nearby stable parent workflow/product/stage where evidence supports it;
- hold unbound placeholders;
- attach checksum sidecars to base artifacts;
- route external references to evidence indexes.

**Acceptance criteria:**

- `promoted unnamed_artifact rows = 0` in product indexes.
- component rows always include parent binding or are held.
- validators fail promoted generic standalone product IDs.

### 6. Add pilot-before-scale gates for large-corpus workflows

**Problem:** Early pilot stages exposed missing case/thread IDs, unstable product identities, insufficient recall, and noise risk. Scaling before those gates would have produced bad results.

**Required OS change:** Any large corpus workflow must require:

- representative pilot;
- real corpus regeneration or location proof;
- product identity / case coherence validation;
- precision/recall/noise thresholds;
- bounded first chunk only;
- post-chunk SAR before continuation.

**Acceptance criteria:**

- Full-scale processing is blocked until pilot gates pass.
- Recall and precision are measured separately.
- The OS refuses `FULL_*` scale authorization until pilot and chunk SAR gates pass.

### 7. Add download-safe export packaging gate

**Problem:** The first final packet was valid but too large for reliable ChatGPT download relay because it contained duplicate nested source ZIPs. A smaller download-safe packet was required.

**Required OS change:** Export tooling should include a download-safe relay gate:

- detect nested duplicate source packets;
- preserve expanded final indexes and receipts;
- exclude redundant nested ZIPs unless specifically required;
- enforce size budget or split/relay strategy;
- always emit SHA-256 sidecar and internal manifest.

**Acceptance criteria:**

- Final export packet is integrity-checked and download-safe.
- Large canonical packets may exist, but a smaller relay packet is produced when needed.
- Export receipt explains what was removed and why integrity is preserved.

### 8. Add context-first adjudication workflow

**Problem:** The gold review initially pushed too much uncertainty onto the user. The system should infer from source context first and ask the user only when evidence is genuinely insufficient.

**Required OS change:** Add a context-first adjudication gate:

- gather source evidence around candidate claims;
- machine-prelabel obvious rows;
- present only unresolved rows to the user;
- show compact chat-card review when human input is needed;
- never rely on user memory when corpus context can answer.

**Acceptance criteria:**

- Human review packets include source-context summaries.
- User input is requested only for unresolved claims.
- Review UI passes runtime click/smoke checks before use.

### 9. Add HTML/tool runtime smoke gates

**Problem:** Earlier review HTML opened to a screen that did not work. That indicates artifact generation cannot rely on static source presence alone.

**Required OS change:** Any generated HTML/tool used for review must pass deterministic runtime smoke validation:

- opens correctly;
- controls respond to clicks;
- required data is embedded or correctly loaded;
- no giant controls block the evidence view;
- final artifact matches the user’s intended workflow.

**Acceptance criteria:**

- HTML review tools cannot be shipped on source-only validation.
- A rendered-state or DOM interaction smoke receipt is required.

### 10. Add manifest-driven optional-member handling

**Problem:** Final consolidation initially failed because an optional `DEMOTED_STATUS_CONSTANTS` member was missing from one chunk packet. The script had to be repaired to treat optional files as zero-row entries.

**Required OS change:** Consolidation/export tools should distinguish required and optional members via manifest, not brittle path assumptions.

**Acceptance criteria:**

- Missing required members block.
- Missing optional members become explicit zero-row manifest entries.
- Consolidation receipts record optional-member absences.

### 11. Make sluggy countdown a standard long-workflow tracker mode

**Problem:** Long staged workflows are hard to follow without a visible progress model.

**Required OS change:** Add a standard long-workflow tracker mode that reports:

- percent done;
- completed stages;
- next exact stage;
- turns remaining best/likely/risk;
- forbidden actions;
- current blocker if any.

**Acceptance criteria:**

- Long workflows automatically include a concise countdown after each stage.
- Tracker content is written to artifact and surfaced in final response.

## Evidence artifacts from the chat workflow

Key artifact names produced in `/mnt/data` during the workflow:

- `FINAL_790_EXPORT_PACKET_20260602T175420Z.zip`
- `FINAL_790_EXPORT_PACKET_DOWNLOAD_SAFE_20260602T1819Z.zip`
- `FULL_790_FINAL_CONSOLIDATION_PACKET_20260602T173511Z.zip`
- `FULL_790_FINAL_CONSOLIDATION_SAR_AND_EXPORT_GATE_PACKET_20260602T1748Z.zip`
- stage packets from `STAGE2C*`, including R7, R8, and R8C repair packets for chunks 04 through 08.

## Recommended next implementation stage

`BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_INTEGRATION`

Scope:

1. repair/promote boot-sound live root from verified sticky durable-floor archive;
2. install better-tool router and `file_search` ban for mounted OS artifacts;
3. add chat-export mining cartridge shell;
4. promote R7/R8/R8C rules into validators/gates;
5. add download-safe export packaging gate;
6. add sluggy countdown tracker mode;
7. write fixtures and regression tests for this workflow class.

## Risk if not implemented

If these lessons remain only in chat history and standalone packets, MetaBlooms will likely repeat the same failure classes:

- unsound live boot root;
- wrong tool path for mounted artifacts;
- monolithic extraction timeouts;
- false-complete partial giant-chat scans;
- generic placeholder products polluting product indexes;
- oversized export packets that cannot be downloaded;
- repeated user correction instead of automatic routing.
