# Stage 8 Phone-Easy Ruleset Automation Receipt and Handoff

Stage ID: `PROFESSIONALIZATION_CONVERGENCE_STAGE8_PHONE_EASY_RULESET_AUTOMATION_REPAIR`

## Problem recovered

The prior Termux path got too hard because `gh workflow run` failed with:

`Resource not accessible by personal access token (HTTP 403)`

Even though the same token could access the repository and set `METABLOOMS_ADMIN_TOKEN`, dispatching the workflow required additional Actions write authority. That made the phone workflow brittle.

## Research-backed redesign

GitHub supports `workflow_dispatch` for manual runs and `push` triggers with branch/path filters. Repository rulesets are created and updated through the repository rulesets REST API using repository Administration write permission. Therefore the easiest phone-safe path is:

1. set `METABLOOMS_ADMIN_TOKEN` once;
2. merge this PR;
3. let the `push` to `main` trigger the ruleset workflow automatically;
4. keep manual dispatch as a fallback, not the primary path.

## Files changed

- `.github/workflows/apply-ruleset-evaluate.yml`
- `scripts/apply-github-ruleset.sh`
- `runtime/professionalization/stage8/PHONE_EASY_RULESET_AUTOMATION_RECEIPT_AND_HANDOFF.md`

## Safety behavior

The workflow still checks that the ruleset is `evaluate` before applying.
The script is now idempotent: it lists existing repository rulesets, updates an existing ruleset with the same name, or creates it if missing.
The workflow verifies the repository secret exists before calling the script.

## Expected user workload

The user should not need Termux dispatch anymore. The user only needs to have set the `METABLOOMS_ADMIN_TOKEN` secret. The secret was already set successfully in the observed Termux run.

## Next stage

After this PR is merged, observe whether `apply-ruleset-evaluate` ran automatically on `main` and whether it applied/updated the evaluate-mode ruleset.

Next valid stage:

`PROFESSIONALIZATION_CONVERGENCE_STAGE9_AUTO_RULESET_WORKFLOW_OBSERVATION_AND_INSIGHTS_CAPTURE`
