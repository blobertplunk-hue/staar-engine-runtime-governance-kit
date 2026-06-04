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
# Maximum mapped events stored in the receipt by default. Keeps memory bounded
# regardless of input size. Pass max_events=None only for small/test inputs.
_DEFAULT_MAX_EVENTS = 1000


def _is_tool_failure(entry):
    return isinstance(entry, dict) and entry.get("hook_event_name") == _HOOK_EVENT


def _emit_error(message, exit_code):
    """Emit a bounded JSON error object to stderr and exit."""
    print(json.dumps({"error": message, "exit_code": exit_code}), file=sys.stderr)
    sys.exit(exit_code)


def mine_stream(lines, max_entries=None, max_events=_DEFAULT_MAX_EVENTS):
    """
    Parse JSONL lines, extract PostToolUseFailure entries, map to blocker events.

    Returns a receipt dict. Never writes to the ledger or filesystem.
    Malformed failure payloads are counted as unmappable instead of aborting the run.

    max_events: maximum number of mapped events to store in the receipt.
      - _DEFAULT_MAX_EVENTS (1000): default bounded mode.
      - 0: counts only — events are mapped and counted but never stored (dry-run mode).
      - None: unlimited — disables the cap (use only for small/test inputs).
    All events are mapped and counted regardless of max_events; only storage is capped.
    """
    entries_seen = 0
    parse_errors = 0
    failures_found = 0
    mapped_count = 0        # total successfully mapped (including those beyond the cap)
    events_capped_count = 0 # mapped events not stored due to cap
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
        try:
            event, status = map_payload(entry)
        except (TypeError, ValueError, KeyError, AttributeError):
            unmappable_count += 1
            continue

        if status == "UNMAPPABLE":
            unmappable_count += 1
        else:
            mapped_count += 1
            if max_events is None or len(mapped_events) < max_events:
                mapped_events.append({**event, "_adapter_status": status})
            else:
                events_capped_count += 1

    return {
        "cartridge_id": _CARTRIDGE_ID,
        "runner_stage": _RUNNER_STAGE,
        "entries_seen": entries_seen,
        "parse_errors": parse_errors,
        "failures_found": failures_found,
        "mapped": mapped_count,
        "unmappable": unmappable_count,
        "events": mapped_events,
        "events_cap": max_events,
        "events_capped": events_capped_count > 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="CHAT790 export mining cartridge — Stage001 bounded runner"
    )
    parser.add_argument("--input", help="Path to JSONL chat export (default: stdin)")
    parser.add_argument("--output", help="Path to write JSON receipt (default: stdout)")
    parser.add_argument("--max-entries", type=int, default=None,
                        help="Stop after processing N entries")
    parser.add_argument(
        "--max-events", type=int, default=None,
        help=f"Maximum mapped events stored in receipt (default: {_DEFAULT_MAX_EVENTS}; "
             "0 = counts only). Does not affect mapped/failure counts.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and count only; store no events (sets --max-events 0)")
    args = parser.parse_args()

    # Resolve effective max_events: dry-run always means 0 (never store events).
    if args.dry_run:
        effective_max_events = 0
    elif args.max_events is not None:
        effective_max_events = args.max_events
    else:
        effective_max_events = _DEFAULT_MAX_EVENTS

    if args.input:
        try:
            fh = open(args.input, encoding="utf-8")
        except OSError as exc:
            _emit_error(str(exc), 1)
    else:
        fh = sys.stdin

    try:
        receipt = mine_stream(fh, max_entries=args.max_entries, max_events=effective_max_events)
    except Exception as exc:
        _emit_error(str(exc), 2)
    finally:
        if args.input:
            fh.close()

    if args.dry_run:
        receipt["dry_run"] = True

    out = json.dumps(receipt, indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
        except OSError as exc:
            _emit_error(str(exc), 1)
    else:
        print(out)


if __name__ == "__main__":
    main()
