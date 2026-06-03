#!/usr/bin/env python3
"""
CHAT790_EXPORT_MINING_CARTRIDGE_STAGE001 bounded runner.

Stage001 scope (see BOUNDED_RUNNER_CONTRACT_v1.json):
  - Accept a JSONL chat export via --input <path> or stdin.
  - Filter for PostToolUseFailure entries.
  - Map each through post_tool_failure_adapter.map_payload (no ledger writes).
  - Emit a JSON mining receipt to stdout or --output.

Stage001 does NOT write to the ledger, does NOT access /mnt/data, and does
NOT perform pattern clustering. Those are Stage002+ concerns.
"""
import argparse
import json
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_DIR))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "blocker_ledger"))

from post_tool_failure_adapter import map_payload  # noqa: E402

_CARTRIDGE_ID = "CHAT790_EXPORT_MINING_CARTRIDGE"
_RUNNER_STAGE = "STAGE001"
_HOOK_EVENT = "PostToolUseFailure"


def _is_tool_failure(entry):
    return isinstance(entry, dict) and entry.get("hook_event_name") == _HOOK_EVENT


def mine_stream(lines, max_entries=None):
    """
    Parse JSONL lines, extract PostToolUseFailure entries, map to blocker events.

    Returns a receipt dict. Never writes to the ledger or filesystem.
    """
    entries_seen = 0
    parse_errors = 0
    failures_found = 0
    mapped_events = []
    unmappable_count = 0

    for line in lines:
        if max_entries is not None and entries_seen >= max_entries:
            break
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue

        entries_seen += 1

        if not _is_tool_failure(entry):
            continue

        failures_found += 1
        event, status = map_payload(entry)

        if status == "UNMAPPABLE":
            unmappable_count += 1
        else:
            mapped_events.append({**event, "_adapter_status": status})

    return {
        "cartridge_id": _CARTRIDGE_ID,
        "runner_stage": _RUNNER_STAGE,
        "entries_seen": entries_seen,
        "parse_errors": parse_errors,
        "failures_found": failures_found,
        "mapped": len(mapped_events),
        "unmappable": unmappable_count,
        "events": mapped_events,
    }


def main():
    parser = argparse.ArgumentParser(
        description="CHAT790 export mining cartridge — Stage001 bounded runner"
    )
    parser.add_argument("--input", help="Path to JSONL chat export (default: stdin)")
    parser.add_argument("--output", help="Path to write JSON receipt (default: stdout)")
    parser.add_argument("--max-entries", type=int, default=None,
                        help="Stop after processing N entries")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and count only; emit events=[] in receipt")
    args = parser.parse_args()

    if args.input:
        try:
            fh = open(args.input, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": str(exc), "exit_code": 1}), file=sys.stderr)
            sys.exit(1)
    else:
        fh = sys.stdin

    try:
        receipt = mine_stream(fh, max_entries=args.max_entries)
    except Exception as exc:
        print(json.dumps({"error": str(exc), "exit_code": 2}), file=sys.stderr)
        sys.exit(2)
    finally:
        if args.input:
            fh.close()

    if args.dry_run:
        receipt["events"] = []
        receipt["dry_run"] = True

    out = json.dumps(receipt, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        print(out)


if __name__ == "__main__":
    main()
