#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be owner/name}"

API_VERSION="2022-11-28"
BRANCH="${1:-main}"
API="https://api.github.com/repos/${GITHUB_REPOSITORY}/branches/${BRANCH}/protection"
TMP_BODY="${TMPDIR:-/tmp}/metablooms_branch_protection_$$.json"
TMP_RESP="${TMPDIR:-/tmp}/metablooms_branch_protection_resp_$$.json"
trap 'rm -f "$TMP_BODY" "$TMP_RESP"' EXIT

cat > "$TMP_BODY" <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["professionalization-projection"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": false,
  "lock_branch": false,
  "allow_fork_syncing": true
}
JSON

echo "Applying classic branch protection to ${GITHUB_REPOSITORY}:${BRANCH}"
echo "If this returns 403 on a private repo, GitHub plan/feature availability is likely the blocker."

HTTP_CODE="$(curl -sS -o "$TMP_RESP" -w '%{http_code}' \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: ${API_VERSION}" \
  "$API" \
  --data-binary "@${TMP_BODY}")"

cat "$TMP_RESP"
echo

case "$HTTP_CODE" in
  200)
    echo "PASS: branch protection applied/updated."
    ;;
  403)
    echo "BLOCKED: GitHub returned 403 for branch protection. Likely private-repo plan limitation or missing Administration write authority." >&2
    exit 43
    ;;
  *)
    echo "FAIL: unexpected HTTP ${HTTP_CODE} from branch protection API." >&2
    exit 44
    ;;
esac
