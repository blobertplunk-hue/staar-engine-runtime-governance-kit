#!/usr/bin/env python3
"""Validate repository professionalization projection files.

Stdlib-only so it can run in GitHub Actions, Termux, or the ChatGPT sandbox.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path.cwd()
REQUIRED = [
    ".github/workflows/metablooms-ci.yml",
    ".github/workflows/scorecard.yml",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/governed_stage.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/rulesets/main-protection.evaluate.json",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "docs/PROFESSIONALIZATION_CONVERGENCE.md",
    "scripts/apply-github-ruleset.sh",
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        fail("missing required files: " + ", ".join(missing))

    ruleset_path = ROOT / ".github/rulesets/main-protection.evaluate.json"
    ruleset = json.loads(ruleset_path.read_text(encoding="utf-8"))
    if ruleset.get("enforcement") != "evaluate":
        fail("ruleset must remain in evaluate mode until a separate activation stage")
    rule_types = {rule.get("type") for rule in ruleset.get("rules", [])}
    needed = {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}
    if not needed.issubset(rule_types):
        fail(f"ruleset missing required rule types: {sorted(needed - rule_types)}")

    ci = (ROOT / ".github/workflows/metablooms-ci.yml").read_text(encoding="utf-8")
    if "permissions:" not in ci or "contents: read" not in ci:
        fail("CI workflow must declare least-privilege permissions")

    print("PASS: professionalization projection files are present and structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
