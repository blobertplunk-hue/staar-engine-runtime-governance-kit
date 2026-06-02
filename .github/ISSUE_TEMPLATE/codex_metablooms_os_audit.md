---
name: Codex MetaBlooms OS audit
description: Bounded Codex Linux audit of MetaBlooms OS durable floor and governance failure classes
title: "Codex audit: MetaBlooms OS durable floor and verifier integrity"
labels: ["codex", "metablooms", "audit", "governance"]
assignees: []
---

@codex

Perform a bounded MetaBlooms OS repo-side audit on Linux.

## Required first action
Run:

```bash
bash tools/codex/linux_restore_and_audit.sh
```

If restore, SHA verification, extraction, or turn-boot fails, stop and report the blocker with command output. Do not patch before root cause is identified.

## Audit scope
- durable floor proof integrity,
- `downloaded_sha256` vs `download_sha256` normalization,
- landed receipt self-verification,
- live-sidecar false FAIL prevention,
- export partial-archive prevention,
- restore/boot reproducibility,
- missing regression fixtures.

## Constraints
- Do not upload release assets.
- Do not replace durable floor.
- Do not mark durable from pointer-only records.
- Do not make broad repairs in this first pass.
- If you make a small fix, include a regression fixture and validator output.

## Required output
Create:

```text
runtime/generated/codex_linux_repo_side_audit_<UTC_TIMESTAMP>/
  AUDIT_REPORT.md
  MACHINE_FINDINGS.json
  COMMAND_LOG.md
  FAILURE_CLASS_MATRIX.md
  PATCH_PLAN.md
  SELF_SAR.md
  CHANGED_FILES.txt
```

Final response must include boot result, serious findings, files changed, commands run, and next recommended repair stage.
