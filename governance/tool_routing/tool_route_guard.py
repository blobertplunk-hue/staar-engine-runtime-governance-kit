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
_MOUNTED_PATTERNS = [re.compile(r"/mnt/data"), re.compile(r"Metablooms_OS")]

# Canonical tool names derived from namespaced variants.
# file_search.msearch, openai.file_search, file_search.v2, etc. → file_search
_CANONICAL_TOOL_ALIASES = {
    "file_search": re.compile(r"(?:^|[._])file_search(?:[._]|$)", re.IGNORECASE),
}


def load_policy(policy_path=POLICY_PATH):
    with open(policy_path) as fh:
        return json.load(fh)


def canonicalize_tool_name(tool_name):
    """Return the canonical base tool name, collapsing namespace variants.

    Examples:
      file_search.msearch → file_search
      openai.file_search  → file_search
      file_search.v2      → file_search
      file_search         → file_search
    """
    for canonical, pattern in _CANONICAL_TOOL_ALIASES.items():
        if pattern.search(tool_name):
            return canonical
    return tool_name.lower()


def _matches_mounted(text):
    s = str(text)
    return any(p.search(s) for p in _MOUNTED_PATTERNS)


def _any_string_matches_mounted(obj):
    """Recursively scan dicts, lists, and scalar strings for mounted OS paths."""
    if isinstance(obj, str):
        return _matches_mounted(obj)
    if isinstance(obj, dict):
        return any(_any_string_matches_mounted(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_any_string_matches_mounted(item) for item in obj)
    return False


def classify_domain(tool_name, tool_input):
    """Return the domain string for a given tool call.

    Mounted-path detection ALWAYS wins over an explicit domain field.
    This prevents bypass attacks where a caller sets domain=uploaded_semantic_document_query
    while embedding a /mnt/data path in queries[] or a nested value.
    """
    # Mounted OS artifact check: scan ALL string values recursively.
    # This covers target_path, path, query, queries[], and any nested structure.
    if _any_string_matches_mounted(tool_input):
        return "mounted_mnt_data_os_artifact_truth"

    # Explicit domain field (only consulted after mounted-path check).
    explicit = tool_input.get("domain", "")
    if explicit:
        return explicit

    # Uploaded semantic document
    if tool_input.get("uploaded"):
        return "uploaded_semantic_document_query"

    # GitHub / git tooling
    if tool_name in ("git", "gh", "github"):
        return "github_repo_state"

    return "unknown"


def route(tool_name, tool_input, policy):
    """Return a routing-decision dict for the given tool call."""
    canonical = canonicalize_tool_name(tool_name)
    domain = classify_domain(canonical, tool_input)

    for r in policy.get("routes", []):
        if r["domain"] == domain:
            is_forbidden = canonical in r.get("forbidden_tools", [])
            if is_forbidden:
                decision = "BLOCKED"
            else:
                decision = r["decision"]
            return {
                "route_id": domain,
                "input_classification": domain,
                "selected_tool": canonical,
                "raw_tool_name": tool_name,
                "forbidden_tool_check": is_forbidden,
                "decision": decision,
                "evidence_path": POLICY_PATH,
                "preferred_tools": r.get("preferred_tools", []),
                "message": (
                    f"Tool '{canonical}' (raw: '{tool_name}') is forbidden for domain '{domain}'. "
                    f"Use: {r.get('preferred_tools', [])}"
                ) if is_forbidden else f"Domain '{domain}' → {decision}",
            }

    # Unclassified domain: allow with note
    return {
        "route_id": "unknown",
        "input_classification": "unknown",
        "selected_tool": canonical,
        "raw_tool_name": tool_name,
        "forbidden_tool_check": False,
        "decision": "ALLOW_UNCLASSIFIED",
        "evidence_path": POLICY_PATH,
        "message": f"Domain unclassified for tool '{canonical}'; defaulting to allow.",
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
