# Stage 6 Ruleset Tool-Extension Receipt and Handoff

Stage ID: `PROFESSIONALIZATION_CONVERGENCE_STAGE6_RULESET_EVALUATE_EXTERNAL_APPLY_VERIFICATION_OR_TOOL_EXTENSION`

## Verified facts

- PR #1 was merged in Stage 5 as squash commit `e3f68c4193040e95bff9f341d0bea342d7b9e11f`.
- `.github/rulesets/main-protection.evaluate.json` exists on `main`.
- `scripts/apply-github-ruleset.sh` exists on `main` and refuses non-`evaluate` rulesets by default.
- GitHub connector shows admin permission for the repository.
- The ChatGPT GitHub connector still does not expose a repository-ruleset mutation tool.
- The sandbox environment does not expose `GITHUB_TOKEN` or `GH_TOKEN`, so direct REST application from `/mnt/data` cannot be performed.

## Tool extension added

This branch adds `.github/workflows/apply-ruleset-evaluate.yml`.

The workflow is manual-only via `workflow_dispatch` and requires repository secret:

`METABLOOMS_ADMIN_TOKEN`

The token must have repository Administration write permission, because repository ruleset creation uses the repository rulesets API.

## Safety gates

Before applying the ruleset, the workflow:

1. validates the professionalization projection files;
2. verifies `.github/rulesets/main-protection.evaluate.json` has `"enforcement": "evaluate"`;
3. calls the guarded script, which also refuses non-evaluate rulesets.

## Next step

Merge this tool-extension PR, add `METABLOOMS_ADMIN_TOKEN` as a GitHub Actions secret, manually run `apply-ruleset-evaluate`, then observe whether the repository ruleset exists in evaluate mode.

Next governed stage:

`PROFESSIONALIZATION_CONVERGENCE_STAGE7_RULESET_WORKFLOW_MERGE_AND_MANUAL_DISPATCH_OBSERVATION`
