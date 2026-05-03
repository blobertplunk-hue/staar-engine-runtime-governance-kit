#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be owner/name}"

RULESET_PATH="${1:-.github/rulesets/main-protection.evaluate.json}"
API_VERSION="2022-11-28"

if [[ ! -f "$RULESET_PATH" ]]; then
  echo "Ruleset JSON not found: $RULESET_PATH" >&2
  exit 2
fi

if ! grep -q '"enforcement"[[:space:]]*:[[:space:]]*"evaluate"' "$RULESET_PATH"; then
  echo "Refusing to apply a non-evaluate ruleset by default." >&2
  echo "Promote to active only in a separate governed stage." >&2
  exit 3
fi

curl -fsS \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: ${API_VERSION}" \
  "https://api.github.com/repos/${GITHUB_REPOSITORY}/rulesets" \
  --data-binary "@${RULESET_PATH}"
