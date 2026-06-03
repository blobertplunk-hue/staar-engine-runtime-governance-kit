# FILE_SEARCH_BAN_FOR_MOUNTED_ARTIFACTS_v1

Date: 2026-06-03  
Status: ACTIVE  
Source: METABLOOMS_CHAT790_POSTMORTEM_URGENT_OS_CHANGES_20260602

## Rule

**`file_search` is forbidden for mounted `/mnt/data` OS artifact work.**

This ban is machine-enforced by `TOOL_ROUTING_POLICY_v1.json` (route `mounted_mnt_data_os_artifact_truth`, decision `BLOCK_FILE_SEARCH`).

## Rationale

The 790-chat extraction workflow showed repeatedly that `file_search` produces:

- incomplete results on mounted paths (partial index coverage);
- stale results (index may not reflect current mount state);
- semantically wrong results (semantic similarity ≠ ground-truth file membership);
- no direct audit trail (cannot produce a checksum, offset, or member proof).

The user explicitly banned `file_search` for this workflow. This document promotes that prohibition into a durable OS policy.

## Forbidden tool

| Tool | Status | Scope |
|------|--------|-------|
| `file_search` | FORBIDDEN | Any work targeting `/mnt/data` or `Metablooms_OS` |

## Preferred alternatives

| Method | When to use |
|--------|-------------|
| `Bash` (direct filesystem read) | Listing, cat, grep, sha256sum on mounted files |
| `Read` (direct file read) | Reading a specific known path |
| `Python open/read` | Structured parsing of text or binary content |
| `zipfile member read` | Reading ZIP archive members without extraction |
| `tarfile member read` | Reading tar archive members without full extraction |
| `checksum verification` | Proving content identity against a known hash |
| `manifest read` | Reading an existing manifest rather than re-indexing |

## Human override

If `file_search` must be used for a mounted artifact (e.g. exploratory work before a verified path is known), a human must explicitly re-authorize it in the session. The override must be recorded in the stage receipt with `file_search_override_authorized: true` and a justification.

## Enforcement

- `TOOL_ROUTING_POLICY_v1.json` is the machine-readable source of truth for this ban.
- Pre-tool guards SHOULD check this policy before routing `file_search` calls.
- Stage receipts MUST include `file_search_used: false` for mounted-artifact stages, or an explicit authorized override entry.
