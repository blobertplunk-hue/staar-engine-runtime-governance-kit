# Private Repository Protection Fallback

Stage ID: `PROFESSIONALIZATION_CONVERGENCE_STAGE11_BRANCH_PROTECTION_FALLBACK_FOR_PRIVATE_FREE_REPO`

## Finding

GitHub rulesets and protected branches are plan-gated for private repositories. On GitHub Free, they are available for public repositories, while private repository enforcement requires GitHub Pro, Team, or Enterprise-level availability.

## Fallback model

This repository now uses a two-layer fallback:

1. **Classic branch protection apply attempt**
   - `scripts/apply-branch-protection-main.sh`
   - `.github/workflows/apply-branch-protection-main.yml`
   - If GitHub allows classic protected branches for this private repo, the workflow applies the closest equivalent to the ruleset.
   - If GitHub returns `403`, the stage records this as plan/feature or token-authority block.

2. **Soft main governance guard**
   - `.github/workflows/soft-main-governance-guard.yml`
   - Runs on every push to `main`.
   - Emits actor/ref/commit information into the workflow summary.
   - This does not block pushes; it creates observability when hard enforcement is unavailable.

## Closest hard protection target

The classic branch protection payload attempts:

- required status check: `professionalization-projection`;
- strict up-to-date branch requirement;
- stale review dismissal;
- CODEOWNERS review;
- one required approval;
- last-push approval;
- conversation resolution;
- force-push block;
- branch deletion block.

## Active promotion policy

Do not claim active hard protection until GitHub UI/API proves one of these exists on `main`:

- active/evaluate repository ruleset; or
- classic protected branch.

If both are unavailable because of private repository plan limits, keep soft governance and consider one of:

- upgrade account/repository plan;
- temporarily make repository public if appropriate;
- move hard enforcement to local/Termux/PC pre-push and CI observation;
- keep using PR discipline plus issue-based repair tracking.
