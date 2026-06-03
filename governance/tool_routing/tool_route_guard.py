#!/usr/bin/env python3
"""
Tool route guard: PreToolUse hook and standalone validator.

Classifies tool calls against TOOL_ROUTING_POLICY_v1.json.
In hook mode (--hook-stdin): reads JSON from stdin, writes decision JSON to
stdout, exits non-zero to block the tool call.
In CLI mode: accepts --tool-name and --tool-input for unit testing.
"""
import sys
import json
import os
import re
import argparse

_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_PATH = os.path.join(_DIR, "TOOL_ROUTING_POLICY_v1.json")

# Patterns that identify mounted OS artifact paths
_MOUNTED_PATTERNS = [r"/mnt/data", r"Metablooms_OS"]


def load_policy(policy_path=POLICY_PATH):
    with open(policy_path) as fh:
        return json.load(fh)


def _matches_mounted(text):
    return any(re.search(p, str(text)) for p in _MOUNTED_PATTERNS)


def classify_domain(tool_name, tool_input):
    """Return the domain string for a given tool call."""
    # Explicit domain field overrides heuristics
    explicit = tool_input.get("domain", "")
    if explicit:
        return explicit

    # Mounted OS artifact: check target_path, path, query, and tool_input values
    candidates = [
        tool_input.get("target_path", ""),
        tool_input.get("path", ""),
        tool_input.get("query", ""),
    ]
    if any(_matches_mounted(c) for c in candidates if c):
        return "mounted_mnt_data_os_artifact_truth"

    # Uploaded semantic document
    if tool_input.get("uploaded"):
        return "uploaded_semantic_document_query"

    # GitHub / git tooling
    if tool_name in ("git", "gh", "github"):
        return "github_repo_state"

    return "unknown"


def route(tool_name, tool_input, policy):
    """Return a routing-decision dict for the given tool call."""
    domain = classify_domain(tool_name, tool_input)

    for r in policy.get("routes", []):
        if r["domain"] == domain:
            is_forbidden = tool_name in r.get("forbidden_tools", [])
            if is_forbidden:
                decision = "BLOCKED"
            else:
                decision = r["decision"]
            return {
                "route_id": domain,
                "input_classification": domain,
                "selected_tool": tool_name,
                "forbidden_tool_check": is_forbidden,
                "decision": decision,
                "evidence_path": POLICY_PATH,
                "preferred_tools": r.get("preferred_tools", []),
                "message": (
                    f"Tool '{tool_name}' is forbidden for domain '{domain}'. "
                    f"Use: {r.get('preferred_tools', [])}"
                ) if is_forbidden else f"Domain '{domain}' → {decision}",
            }

    # Unclassified domain: allow with note
    return {
        "route_id": "unknown",
        "input_classification": "unknown",
        "selected_tool": tool_name,
        "forbidden_tool_check": False,
        "decision": "ALLOW_UNCLASSIFIED",
        "evidence_path": POLICY_PATH,
        "message": f"Domain unclassified for tool '{tool_name}'; defaulting to allow.",
    }


def main():
    parser = argparse.ArgumentParser(description="MetaBlooms tool route guard")
    parser.add_argument("--hook-stdin", action="store_true",
                        help="Read tool call JSON from stdin (Claude Code hook mode)")
    parser.add_argument("--tool-name", default="",
                        help="Tool name (CLI test mode)")
    parser.add_argument("--tool-input", default="{}",
                        help="Tool input JSON string (CLI test mode)")
    parser.add_argument("--policy-path", default=POLICY_PATH,
                        help="Path to TOOL_ROUTING_POLICY_v1.json")
    args = parser.parse_args()

    policy = load_policy(args.policy_path)

    if args.hook_stdin:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", data.get("tool", ""))
        tool_input = data.get("tool_input", data.get("input", {}))
    else:
        tool_name = args.tool_name
        tool_input = json.loads(args.tool_input)

    result = route(tool_name, tool_input, policy)
    print(json.dumps(result, indent=2))

    sys.exit(1 if result["decision"] == "BLOCKED" else 0)


if __name__ == "__main__":
    main()
