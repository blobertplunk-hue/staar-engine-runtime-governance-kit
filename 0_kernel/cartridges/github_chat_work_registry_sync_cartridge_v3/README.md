# GitHub Chat Work Registry Sync Cartridge v3

Status: projected from ChatGPT sandbox artifact on 2026-06-04.

Authoritative sandbox artifact:

- `github_chat_work_registry_sync_cartridge_v3_20260604T203120Z.zip`
- SHA-256: `80c5c5a0797c5d0197a9544e796bba156cd4c9374c3fc3e6e5f55f6b645f6ed2`

## Purpose

This cartridge makes every substantive ChatGPT work session register its intended work, chat URL or durable chat identifier, current stage, artifacts, receipts, blockers, and next step into a GitHub-backed registry so another chat can discover and resume the work.

## Mandatory invariant

Every substantive turn must resolve or create a registered work session before claiming durable progress:

```text
REGISTERED_WORK_SESSION == true
```

A valid session records:

- `work_id`
- `intended_work`
- `chat.chat_url_status`
- `chat.chat_url` or explicit blocker when unavailable
- `github.repository_full_name`
- `resume.current_stage`
- `resume.last_completed_step`
- `resume.next_step`
- `artifacts[]` with digest-backed pointers
- `receipts[]`
- `updated_at_utc`

## Chat URL rule

The assistant does not know its own canonical ChatGPT URL unless the user provides it. If no URL or stable chat ID is known, the cartridge must ask the user for it before declaring the session fully resumable.

Allowed chat URL states:

- `SHARE_URL_PROVIDED`
- `PROVIDED`
- `EXPORTED_CONVERSATION_ID`
- `UNAVAILABLE_IN_TOOL_CONTEXT`

`UNAVAILABLE_IN_TOOL_CONTEXT` is only valid for partial/emergency logging and must not be represented as fully resumable.

## Repo resolution rule

The cartridge decides the GitHub repository. It must not ask the user for a repo first.

Resolution order:

1. existing `.metablooms/chat_work_registry/` entries;
2. artifact provenance and manifests;
3. local `.git/config` remotes;
4. prior MetaBlooms receipts;
5. installed GitHub repository search;
6. GitHub code/file search for strong marker files;
7. name similarity only as weak evidence.

Ask the user only if no candidate passes the safe evidence threshold or multiple candidates tie too closely.

## Default GitHub workflow

```text
resolve repo
→ create/load work session
→ create/update GitHub issue
→ write registry session JSON
→ claim lock before mutation
→ heartbeat after every meaningful stage
→ create branch and draft PR for code changes
→ observe Actions/status checks
→ update resume state and release/renew lock
```

Default mode is a new branch plus draft PR, never direct push to `main`.

## Registry layout

```text
.metablooms/chat_work_registry/
├── index.json
├── sessions/<work_id>.json
├── events/<work_id>/...
├── artifacts/<work_id>/...
└── locks/<work_id>.json
```

## Included support files

- `cartridge_contract.json`
- `schemas/chat_work_session.schema.json`
- `resolve_github_registry_repo.py`
- `start_chat_work_session.py`
- `validate_chat_work_registry.py`
- `validate_v3_repo_resolution_policy.py`
- issue/comment/workflow templates

## Current chat registration evidence

User-provided share URL:

```text
https://chatgpt.com/share/6a21debb-b41c-83ea-b4b4-7f0784844f04
```

Parsed share ID:

```text
6a21debb-b41c-83ea-b4b4-7f0784844f04
```
