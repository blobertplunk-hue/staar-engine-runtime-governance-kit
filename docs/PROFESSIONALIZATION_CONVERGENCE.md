# Professionalization Convergence Guide

Stage: `PROFESSIONALIZATION_CONVERGENCE_STAGE3_AUTHORIZED_GITHUB_BRANCH_AND_PR_PROJECTION`

## Purpose

This document turns the MetaBlooms sandbox professionalization plan into reviewable repository controls. The ChatGPT sandbox can create artifacts, receipts, validators, and export bundles; GitHub must enforce durable repository controls such as required reviews, branch protection/rulesets, required status checks, Scorecard, and issue tracking.

## Architecture map

1. **Authority layer**: bootable ZIP, `.sha256` sidecar, boot authority manifest, export provenance.
2. **Runtime layer**: receipts, handoffs, runtime state, validators, stage ledgers.
3. **Governance layer**: invariants, registry entries, scorecards, replay proof, artifact completeness checks.
4. **Professionalization layer**: CI, PR templates, issue templates, CODEOWNERS, security policy, release process, ruleset plan.
5. **External enforcement layer**: GitHub branch/ruleset enforcement, Actions status checks, code review, security scanning, releases.

## Repository hygiene target

- Keep generated exports under explicit release/export paths, not mixed into source directories.
- Keep stage receipts and handoffs under runtime-governed paths.
- Require PRs for changes to runtime, governance, workflow, release, and security paths.
- Treat direct pushes to `main` as forbidden once the ruleset is active.

## CI/CD target

- CI must run on pull requests and `main` pushes.
- The portable boot verifier is the baseline required check.
- The professionalization projection validator becomes a required check once the repo layout stabilizes.
- Workflow permissions must stay least-privilege by default.

## Typed tests target

- Prefer stdlib-only validators for sandbox parity.
- Add typed Python interfaces where the codebase stabilizes.
- Every code-bearing stage should include a validator or fixture.

## Code review target

- Require at least one approving review before merge.
- Require CODEOWNERS review for workflow, governance, runtime, security, and boot-verifier paths.
- Dismiss stale approvals when new commits are pushed.
- Require review-thread resolution before merge.

## Release process target

Every release/export should include:

- ZIP artifact;
- SHA-256 sidecar;
- manifest/provenance;
- replay proof;
- validator output;
- clear boot instructions;
- changelog or stage summary.

## Security review target

Review each change for:

- workflow token permissions;
- secret exposure;
- dependency and lockfile changes;
- write-path changes;
- artifact integrity and hash synchronization;
- direct external mutation authority.

## Activation path

1. Merge this PR after CI passes.
2. Run Scorecard once and inspect findings.
3. Apply the branch ruleset in `evaluate` mode.
4. Review rule impact.
5. Promote the ruleset to `active` only after the repo has passing required checks.
