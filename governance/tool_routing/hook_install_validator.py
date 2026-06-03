#!/usr/bin/env python3
"""
Hook install validator for BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_STAGE001.

Validates that .claude/settings.json is present and correctly wires the
tool_route_guard.py and repeated_blocker_guard.py scripts. Runs a structural
check and a subprocess smoke test of each hook command.

Exit codes:
  0 — all checks PASS
  1 — one or more checks FAILED or BLOCKED
"""
import json
import os
import re
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(_REPO_ROOT, ".claude", "settings.json")

EXPECTED_PRE_TOOL_USE_CMD = "python3 governance/tool_routing/tool_route_guard.py --hook-stdin"
EXPECTED_POST_TOOL_FAILURE_CMD = (
    "python3 governance/blocker_ledger/post_tool_failure_adapter.py --hook-stdin --mode record-or-route"
)

# Safe, non-blocking smoke input for tool_route_guard
_SAFE_ROUTE_INPUT = json.dumps({
    "tool_name": "read_file",
    "tool_input": {"path": "README.md"},
})

# Safe first-occurrence raw CC payload for post_tool_failure_adapter (classify-only)
_SAFE_BLOCKER_INPUT = json.dumps({
    "event": {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "bash",
        "tool_input": {"command": "echo smoke-test"},
        "tool_response": "smoke-test",
        "session_id": "smoke-session-000",
    },
    "ledger": {"entries": {}},
})


def _check(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    line = f"  [{status}] {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return passed


def _extract_script_path(command):
    """Return the filesystem path of the python3 script in a hook command string."""
    m = re.search(r"python3\s+(\S+\.py)", command)
    return m.group(1) if m else None


def validate():
    results = []
    print("Hook install validator — BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_STAGE001")
    print("=" * 70)

    # 1. settings.json exists
    exists = os.path.isfile(SETTINGS_PATH)
    results.append(_check("settings_json_exists", exists, SETTINGS_PATH))
    if not exists:
        print("\nBLOCKED: settings.json absent; remaining checks skipped.")
        return False

    # 2. settings.json is valid JSON
    try:
        with open(SETTINGS_PATH) as fh:
            cfg = json.load(fh)
        results.append(_check("settings_json_valid_json", True))
    except json.JSONDecodeError as exc:
        results.append(_check("settings_json_valid_json", False, str(exc)))
        return False

    # 3. PreToolUse hook configured
    pre_hooks = cfg.get("hooks", {}).get("PreToolUse", [])
    pre_cmds = [h["command"] for entry in pre_hooks for h in entry.get("hooks", [])]
    has_pre = any(EXPECTED_PRE_TOOL_USE_CMD in c for c in pre_cmds)
    results.append(_check("pre_tool_use_hook_configured", has_pre,
                          f"expected: {EXPECTED_PRE_TOOL_USE_CMD!r}"))

    # 4. PostToolUseFailure hook configured
    post_hooks = cfg.get("hooks", {}).get("PostToolUseFailure", [])
    post_cmds = [h["command"] for entry in post_hooks for h in entry.get("hooks", [])]
    has_post = any(EXPECTED_POST_TOOL_FAILURE_CMD in c for c in post_cmds)
    results.append(_check("post_tool_use_failure_hook_configured", has_post,
                          f"expected: {EXPECTED_POST_TOOL_FAILURE_CMD!r}"))

    # 5 & 6. Guard scripts exist on disk
    for cmd in pre_cmds + post_cmds:
        rel_path = _extract_script_path(cmd)
        if rel_path:
            full = os.path.join(_REPO_ROOT, rel_path)
            exists = os.path.isfile(full)
            label = os.path.basename(rel_path) + "_script_exists"
            results.append(_check(label, exists, full))

    # 7. Smoke test: tool_route_guard with safe non-blocking input
    try:
        proc = subprocess.run(
            [sys.executable, "governance/tool_routing/tool_route_guard.py", "--hook-stdin"],
            input=_SAFE_ROUTE_INPUT,
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
        )
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
        smoke_ok = proc.returncode == 0 and out.get("decision") not in ("BLOCKED",)
        results.append(_check(
            "tool_route_guard_smoke_test",
            smoke_ok,
            f"exit={proc.returncode} decision={out.get('decision')}",
        ))
    except Exception as exc:
        results.append(_check("tool_route_guard_smoke_test", False, str(exc)))

    # 8. Smoke test: post_tool_failure_adapter with safe classify-only raw CC payload
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "governance/blocker_ledger/post_tool_failure_adapter.py",
                "--hook-stdin", "--mode", "classify-only",
            ],
            input=_SAFE_BLOCKER_INPUT,
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
        )
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
        smoke_ok = proc.returncode == 0 and out.get("decision") == "LOG_ONLY"
        results.append(_check(
            "post_tool_failure_adapter_smoke_test",
            smoke_ok,
            f"exit={proc.returncode} decision={out.get('decision')}",
        ))
    except Exception as exc:
        results.append(_check("post_tool_failure_adapter_smoke_test", False, str(exc)))

    print("=" * 70)
    passed = sum(results)
    total = len(results)
    overall = all(results)
    print(f"Result: {'PASS' if overall else 'FAIL'}  ({passed}/{total} checks passed)")
    return overall


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
