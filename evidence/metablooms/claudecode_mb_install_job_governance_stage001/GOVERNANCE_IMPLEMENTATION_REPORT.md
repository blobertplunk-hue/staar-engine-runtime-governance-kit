# Claude Code MB_INSTALL Job Governance Stage001

Decision: `PASS_CLAUDECODE_MB_INSTALL_JOB_GOVERNANCE_STAGE001`

This stage adds a repo-local MB_INSTALL v0 governance contract, a self-contained pre-report validator, unit tests, and an evidence packet. The validator fails closed for placeholder commit fields, stale SHA chains, manifest self-hash claims, unqualified CI closure claims, unauthorized live apply or atomic swap, and attempted advancement from BLOCK decisions to execution.

`.claude/settings.json` was inspected at base SHA `5454d8232ce42e171c290bd4d416f13c62fa1176` and was not modified. Existing hooks already use `${CLAUDE_PROJECT_DIR}` exec-form commands; this Stage001 supplies a job-local callable validator rather than broadening global hooks.

No live apply, live atomic_swap, protected-surface write, prune, delete, rollback, or staging_swap was performed.
