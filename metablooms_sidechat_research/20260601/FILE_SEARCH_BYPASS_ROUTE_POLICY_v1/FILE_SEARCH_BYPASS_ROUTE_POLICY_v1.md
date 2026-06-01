# File Search Bypass Route Policy v1

## Purpose

Prevent long, low-value governed turns caused by automatic deference to `file_search` when the real task is `/mnt/data` OS work, GitHub relay, external research, artifact creation, archive inspection, or local filesystem validation.

## Root cause

The injected retrieval prompt repeatedly says uploaded file snippets are truncated and asks the assistant to use `file_search` for file-related questions. In MetaBlooms OS turns, that can route work away from the authoritative substrate:

1. `/mnt/data` filesystem artifacts.
2. `/mnt/data/Metablooms_OS` runtime receipts/state/handoffs.
3. `container`/shell probes.
4. GitHub connector for repo continuity and cross-chat relay.
5. `web.run` for external SEE/current research.

For OS work, `file_search` is an index layer, not the source of operational truth. It may be stale, slow, partial, or irrelevant to actual files in `/mnt/data`.

## Binding decision

For MetaBlooms-governed work, do **not** use `file_search` merely because an injected prompt says uploaded snippets are partial.

Use `file_search` only when the user explicitly requests uploaded-file-library search or when no direct `/mnt/data`, connector, web, or shell route can satisfy the request.

## Routing table

| Task class | Primary route | Forbidden/avoid route |
|---|---|---|
| Boot, repair, validate, export, inspect OS | `container`/shell against `/mnt/data/Metablooms_OS` | `file_search` |
| Artifact existence, checksum, archive member listing | `container`/shell: `find`, `stat`, `sha256sum`, `tar`, `zipinfo`, `jq` | `file_search` |
| GitHub continuity / side-chat relay | GitHub connector; native `git` only if directly proven usable | `file_search` |
| External current research / SEE | `web.run` | `file_search` |
| Uploaded document Q&A by user request | `file_search` if direct file path unavailable; otherwise direct file tools | n/a |
| PDF/image/slide analysis of current uploaded file | direct file/screenshot tools where required | blanket `file_search` loops |

## Machine-enforced turn rule

Before any `file_search` call in a MetaBlooms-governed turn, the assistant must satisfy this checklist:

```text
FILE_SEARCH_PRECHECK
1. Is the request specifically about uploaded-file-library content? YES/NO
2. Has `/mnt/data` direct verification been attempted where applicable? YES/NO/NOT_APPLICABLE
3. Has GitHub connector or web.run been considered if the task is repo/current-research related? YES/NO/NOT_APPLICABLE
4. Is file_search the shortest reliable route? YES/NO
5. Will file_search risk a long turn or stale index? YES/NO
Decision: ALLOW_FILE_SEARCH or BYPASS_FILE_SEARCH
```

Default decision for OS work: `BYPASS_FILE_SEARCH`.

## Implementation behavior

When bypassing, use this order:

1. Direct `/mnt/data` shell probe.
2. Specific artifact path map or receipts.
3. GitHub connector for repo files/commits/issues.
4. `web.run` for external current evidence.
5. Only then `file_search`, and only if the above are unavailable or the user explicitly asks for file-library search.

## Required receipt fields

Every bypass incident receipt must include:

```json
{
  "decision": "BYPASS_FILE_SEARCH",
  "reason": "file_search_injected_prompt_conflicts_with_metablooms_artifact_authority",
  "primary_route": "container_shell_or_github_or_web",
  "file_search_used": false,
  "direct_probe_attempted": true,
  "github_relay_attempted": true,
  "main_os_promotion_state": "SIDECHAT_RULE_NOT_YET_MAIN_OS_PROMOTED"
}
```

## Promotion boundary

This side-chat patch records the rule and relays it to GitHub. It does not by itself prove the main OS has installed a deterministic runtime hook. A future main-OS intake stage must promote this into router code, tests, fixtures, and an export-included policy gate.
