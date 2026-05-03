# Stage 11 Branch Protection Fallback Receipt and Handoff

Stage ID: `PROFESSIONALIZATION_CONVERGENCE_STAGE11_BRANCH_PROTECTION_FALLBACK_FOR_PRIVATE_FREE_REPO`

## Root cause correction

The prior assumption that classic branch protection would bypass ruleset private-repo limitations is not guaranteed. GitHub plan limitations also affect protected branches for private repositories. Therefore this stage creates a guarded branch-protection attempt plus soft governance fallback, rather than claiming hard protection is available.

## Files added

- `scripts/apply-branch-protection-main.sh`
- `.github/workflows/apply-branch-protection-main.yml`
- `.github/workflows/soft-main-governance-guard.yml`
- `docs/PRIVATE_REPO_PROTECTION_FALLBACK.md`
- `runtime/professionalization/stage11/BRANCH_PROTECTION_FALLBACK_RECEIPT_AND_HANDOFF.md`

## Expected next behavior

After merge, GitHub should run the branch-protection apply workflow on `main` because the workflow/script paths changed. If it fails with HTTP 403, record plan/token-authority block. If it succeeds, verify branch protection exists on `main`.

The soft guard should run on every future push to `main` and emit actor/ref/commit observation into the workflow summary.

## Next stage

`PROFESSIONALIZATION_CONVERGENCE_STAGE12_BRANCH_PROTECTION_APPLY_OBSERVATION_AND_PRIVATE_REPO_PLAN_DECISION`
