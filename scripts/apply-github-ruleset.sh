#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be owner/name}"

RULESET_PATH="${1:-.github/rulesets/main-protection.evaluate.json}"
API_VERSION="2022-11-28"
RULESET_NAME="$(python3 - <<'PY' "$RULESET_PATH"
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['name'])
PY
)"
API="https://api.github.com/repos/${GITHUB_REPOSITORY}/rulesets"
TMP_LIST="${TMPDIR:-/tmp}/metablooms_rulesets_$$.json"
TMP_BODY="${TMPDIR:-/tmp}/metablooms_ruleset_body_$$.json"
trap 'rm -f "$TMP_LIST" "$TMP_BODY"' EXIT

if [[ ! -f "$RULESET_PATH" ]]; then
  echo "Ruleset JSON not found: $RULESET_PATH" >&2
  exit 2
fi

python3 - <<'PY' "$RULESET_PATH"
import json, sys
p=sys.argv[1]
data=json.load(open(p, encoding='utf-8'))
if data.get('enforcement') != 'evaluate':
    raise SystemExit(f"Refusing non-evaluate ruleset: {data.get('enforcement')}")
needed={'deletion','non_fast_forward','pull_request','required_status_checks'}
actual={r.get('type') for r in data.get('rules', [])}
missing=needed-actual
if missing:
    raise SystemExit('Ruleset missing required rules: ' + ', '.join(sorted(missing)))
print('PASS: ruleset payload is evaluate-mode and structurally safe')
PY

curl -fsS \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: ${API_VERSION}" \
  "$API" > "$TMP_LIST"

EXISTING_ID="$(python3 - <<'PY' "$TMP_LIST" "$RULESET_NAME"
import json, sys
items=json.load(open(sys.argv[1], encoding='utf-8'))
name=sys.argv[2]
for item in items:
    if item.get('name') == name:
        print(item.get('id'))
        break
PY
)"

if [[ -n "$EXISTING_ID" ]]; then
  echo "Existing ruleset found: ${RULESET_NAME} id=${EXISTING_ID}; updating in evaluate mode"
  METHOD="PUT"
  URL="${API}/${EXISTING_ID}"
else
  echo "No existing ruleset named ${RULESET_NAME}; creating in evaluate mode"
  METHOD="POST"
  URL="$API"
fi

curl -fsS \
  -X "$METHOD" \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: ${API_VERSION}" \
  "$URL" \
  --data-binary "@${RULESET_PATH}" > "$TMP_BODY"

python3 - <<'PY' "$TMP_BODY" "$RULESET_NAME"
import json, sys
body=json.load(open(sys.argv[1], encoding='utf-8'))
expected=sys.argv[2]
if body.get('name') != expected:
    raise SystemExit(f"Unexpected ruleset name: {body.get('name')!r}")
if body.get('enforcement') != 'evaluate':
    raise SystemExit(f"Unexpected enforcement: {body.get('enforcement')!r}")
print('PASS: ruleset applied/updated in evaluate mode')
print(json.dumps({'id': body.get('id'), 'name': body.get('name'), 'enforcement': body.get('enforcement')}, indent=2))
PY
