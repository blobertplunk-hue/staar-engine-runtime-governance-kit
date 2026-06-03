#!/usr/bin/env python3
"""
PostToolUseFailure format adapter for Claude Code hook integration.

Maps Claude Code's native PostToolUseFailure event payload to the blocker
event schema consumed by repeated_blocker_guard.classify(), then routes to
the ledger and returns a structured decision.

Decisions (from repeated_blocker_guard):
  LOG_ONLY             — first occurrence of this blocker fingerprint.
  FORCE_RCA            — same fingerprint with unchanged inputs; RCA required.
  LOG_NEW_VARIANT      — same fingerprint but input_digest/evidence_digest changed.

Additional adapter-only decisions:
  REVIEW_UNMAPPED_PAYLOAD — payload lacks tool_name/tool and blocker schema
                            fields; recorded for manual review, exit 0.

Claude Code sends PostToolUseFailure events as JSON on stdin, e.g.:
  {
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "file_search",
    "tool_input": {"query": "...", "target_path": "..."},
    "tool_response": "Error: ...",
    "session_id": "..."
  }

The adapter accepts that format, a bare blocker-schema dict (pass-through),
or any dict containing at least tool_name/tool (partial mapping).

Pass-through: if the input already contains all FINGERPRINT_FIELDS from
repeated_blocker_guard, it is routed directly to classify() unchanged.
This lets tests and callers inject pre-adapted events.
"""
import hashlib
import json
import os
import sys
import argparse

# Re-use classify, ledger IO, and normalization from the sibling guard.
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_DIR))   # repo root → enables "governance.*" imports
sys.path.insert(0, _DIR)                    # enables direct sibling import

from repeated_blocker_guard import (
    FINGERPRINT_FIELDS,
    classify,
    load_ledger,
    _normalize,
    DEFAULT_LEDGER_PATH,
)

# Claude Code payload field names (primary + aliases)
_CC_TOOL_NAME_KEYS = ("tool_name", "tool")
_CC_TOOL_INPUT_KEYS = ("tool_input", "input")
_CC_RESPONSE_KEYS = ("tool_response", "error", "output", "result")


def _first(d, keys, default=""):
    for k in keys:
        if k in d:
            return d[k]
    return default


def _extract_target_path(tool_input):
    """Return the most specific path-like value from tool_input, or ''."""
    for key in ("target_path", "path", "file_path", "filepath"):
        v = tool_input.get(key, "")
        if v and isinstance(v, str):
            return v
    # Scan all string values for a path-like string
    for v in tool_input.values():
        if isinstance(v, str) and ("/" in v or "\\" in v):
            return v
    return ""


def _input_digest(tool_input):
    """SHA-256 of canonically serialised tool_input (deterministic across equal dicts)."""
    canonical = json.dumps(tool_input, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _evidence_digest(response_text):
    """SHA-256 of the (truncated) tool response text."""
    s = str(response_text)[:8192]
    return hashlib.sha256(s.encode()).hexdigest()


# Only structural/location fields enter normalized_command (an identity fingerprint field).
# Free-text fields (query, content, text, …) are excluded so that different queries
# targeting the same path produce the same normalized_command — and therefore the same
# identity fingerprint. Variability in free-text inputs is captured by input_digest.
_STRUCTURAL_INPUT_KEYS = ("target_path", "path", "file_path", "filepath", "url", "pattern")


def _build_normalized_command(tool_name, tool_input):
    """Stable command string: tool name + structural (path/location) fields only."""
    parts = [tool_name]
    for key in _STRUCTURAL_INPUT_KEYS:
        val = tool_input.get(key, "")
        if val and isinstance(val, str) and len(val) <= 500:
            parts.append(f"{key}={val}")
    raw = " ".join(parts)
    return _normalize(raw)


def _is_already_adapted(raw):
    """True if the payload already contains all identity fingerprint fields."""
    return all(f in raw for f in FINGERPRINT_FIELDS)


def map_payload(raw):
    """
    Map a raw payload to a blocker event dict.

    Returns (event_or_None, status_string) where status is one of:
      PASS_THROUGH     — raw already has all blocker schema fields
      MAPPED           — successfully mapped from Claude Code payload
      UNMAPPABLE       — lacks tool_name and blocker schema fields
    """
    if _is_already_adapted(raw):
        return raw, "PASS_THROUGH"

    tool_name = _first(raw, _CC_TOOL_NAME_KEYS)
    if not tool_name:
        return None, "UNMAPPABLE"

    tool_input = _first(raw, _CC_TOOL_INPUT_KEYS, {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    response = _first(raw, _CC_RESPONSE_KEYS, "")

    event = {
        "blocker_type": "tool_failure",
        "component": "claude_code_hook",
        "operation": tool_name,
        "normalized_command": _build_normalized_command(tool_name, tool_input),
        "target_path": _extract_target_path(tool_input),
        "input_digest": _input_digest(tool_input),
        "evidence_digest": _evidence_digest(response),
        # Provenance fields — not used in fingerprint but preserved in ledger
        "_adapter": "post_tool_failure_adapter.py",
        "_source_event": raw.get("hook_event_name", "PostToolUseFailure"),
        "_raw_tool_name": tool_name,
        "_session_id": raw.get("session_id", ""),
    }
    return event, "MAPPED"


def adapt_and_classify(raw, ledger, ledger_path, write=True):
    """
    Map raw payload → blocker event → classify against ledger.
    Returns a receipt dict (always, even for unmappable payloads).
    """
    event, status = map_payload(raw)

    if status == "UNMAPPABLE":
        return {
            "decision": "REVIEW_UNMAPPED_PAYLOAD",
            "adapter_status": status,
            "fingerprint": None,
            "occurrence_count": 0,
            "changed_inputs": False,
            "rca_required": False,
            "ledger_path": ledger_path,
            "raw_keys": sorted(raw.keys()),
            "reason": "Payload lacks tool_name/tool and blocker schema fields; "
                      "route to manual review.",
        }

    receipt = classify(event, ledger, ledger_path, write=write)
    receipt["adapter_status"] = status
    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="MetaBlooms PostToolUseFailure format adapter"
    )
    parser.add_argument("--hook-stdin", action="store_true",
                        help="Read payload JSON from stdin (Claude Code hook mode)")
    parser.add_argument("--mode", default="record-or-route",
                        choices=["record-or-route", "classify-only"],
                        help="record-or-route writes ledger; classify-only is read-only")
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH,
                        help="Path to ledger JSON file")
    args = parser.parse_args()

    try:
        raw = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        # Fail-closed on unparseable stdin: emit a review receipt and exit 0.
        result = {
            "decision": "REVIEW_UNMAPPED_PAYLOAD",
            "adapter_status": "PARSE_ERROR",
            "fingerprint": None,
            "occurrence_count": 0,
            "changed_inputs": False,
            "rca_required": False,
            "ledger_path": args.ledger_path,
            "raw_keys": [],
            "reason": f"stdin JSON parse error: {exc}",
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Unwrap {"event": {...}} wrapper (classify-only mode convenience)
    if "event" in raw and isinstance(raw.get("event"), dict):
        inner = raw["event"]
        inline_ledger = raw.get("ledger")
    else:
        inner = raw
        inline_ledger = None

    ledger_path = raw.get("ledger_path", args.ledger_path)

    if args.mode == "classify-only" and inline_ledger is not None:
        ledger = inline_ledger
        write = False
    else:
        ledger = load_ledger(ledger_path)
        write = (args.mode == "record-or-route")

    result = adapt_and_classify(inner, ledger, ledger_path, write=write)
    print(json.dumps(result, indent=2))

    if result["decision"] == "FORCE_RCA":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
