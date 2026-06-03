#!/usr/bin/env python3
"""
Repeated blocker guard: PostToolUseFailure hook and standalone validator.

Fingerprints blocker events, maintains a file-based ledger, and forces RCA
routing when the same normalized blocker recurs without changed inputs.

Decisions:
  LOG_ONLY        — first occurrence; ledger entry written.
  FORCE_RCA       — same fingerprint with unchanged inputs; RCA required.
  LOG_NEW_VARIANT — same fingerprint but input_digest or evidence_digest changed.

In hook mode (--hook-stdin --mode record-or-route): reads event JSON from
stdin, writes updated ledger to disk, prints decision JSON, exits non-zero
on FORCE_RCA to signal the routing engine.

In classify-only mode (--mode classify-only): accepts {"event": {...},
"ledger": {...}} on stdin; prints decision without writing to disk.
"""
import sys
import json
import hashlib
import os
import re
import argparse

_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEDGER_PATH = os.path.join(_DIR, "ledger.json")

_NORMALIZE = [
    # ISO-8601 timestamps
    (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?"), "<TIMESTAMP>"),
    # Temp directories (Unix and Windows)
    (re.compile(r"/tmp/[A-Za-z0-9_.\-]+"), "<TMP>"),
    (re.compile(r"C:\\Users\\[^\\]+\\AppData\\Local\\Temp\\[^\s]+"), "<TMP>"),
    # Collapse whitespace
    (re.compile(r"\s+"), " "),
]

# Identity fields: stable structural fields used to compute the fingerprint hash.
# input_digest / evidence_digest are NOT included here — they are stored in the
# ledger entry and compared separately to detect changed-inputs vs. true recurrence.
FINGERPRINT_FIELDS = [
    "blocker_type",
    "component",
    "operation",
    "normalized_command",
    "target_path",
]


def _normalize(v):
    s = str(v) if not isinstance(v, str) else v
    for pattern, repl in _NORMALIZE:
        s = pattern.sub(repl, s)
    return s.strip()


def compute_fingerprint(event):
    """SHA-256 over normalized, ordered fingerprint fields."""
    parts = [f"{f}={_normalize(event.get(f, ''))}" for f in FINGERPRINT_FIELDS]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def load_ledger(path):
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return {"entries": {}}


def save_ledger(ledger, path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(ledger, fh, indent=2)


def classify(event, ledger, ledger_path, write=True):
    """
    Classify the event against the ledger.
    Mutates ledger in-place. Writes to disk when write=True.
    Returns a receipt dict.
    """
    fp = compute_fingerprint(event)
    existing = ledger["entries"].get(fp)

    if existing is None:
        ledger["entries"][fp] = {
            "fingerprint": fp,
            "occurrence_count": 1,
            "last_input_digest": event.get("input_digest", ""),
            "last_evidence_digest": event.get("evidence_digest", ""),
            "events": [event],
        }
        if write:
            save_ledger(ledger, ledger_path)
        return {
            "fingerprint": fp,
            "occurrence_count": 1,
            "changed_inputs": False,
            "decision": "LOG_ONLY",
            "rca_required": False,
            "ledger_path": ledger_path,
        }

    cur_input = event.get("input_digest", "")
    cur_evidence = event.get("evidence_digest", "")
    prev_input = existing.get("last_input_digest", "")
    prev_evidence = existing.get("last_evidence_digest", "")
    changed = (cur_input != prev_input) or (cur_evidence != prev_evidence)

    existing["occurrence_count"] += 1
    existing.setdefault("events", []).append(event)

    if changed:
        existing["last_input_digest"] = cur_input
        existing["last_evidence_digest"] = cur_evidence
        decision, rca = "LOG_NEW_VARIANT", False
    else:
        decision, rca = "FORCE_RCA", True

    if write:
        save_ledger(ledger, ledger_path)

    return {
        "fingerprint": fp,
        "occurrence_count": existing["occurrence_count"],
        "changed_inputs": changed,
        "decision": decision,
        "rca_required": rca,
        "ledger_path": ledger_path,
    }


def main():
    parser = argparse.ArgumentParser(description="MetaBlooms repeated blocker guard")
    parser.add_argument("--hook-stdin", action="store_true",
                        help="Read event JSON from stdin (Claude Code hook mode)")
    parser.add_argument("--mode", default="record-or-route",
                        choices=["record-or-route", "classify-only"],
                        help="record-or-route writes ledger; classify-only is read-only")
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH,
                        help="Path to ledger JSON file")
    args = parser.parse_args()

    data = json.load(sys.stdin)

    # Accept {"event": {...}, "ledger": {...}} for classify-only or
    # a bare event dict for hook mode.
    if "event" in data:
        event = data["event"]
        inline_ledger = data.get("ledger")
    else:
        event = data
        inline_ledger = None

    ledger_path = data.get("ledger_path", args.ledger_path)

    if args.mode == "classify-only" and inline_ledger is not None:
        ledger = inline_ledger
        write = False
    else:
        ledger = load_ledger(ledger_path)
        write = (args.mode == "record-or-route")

    result = classify(event, ledger, ledger_path, write=write)
    print(json.dumps(result, indent=2))

    sys.exit(2 if result["decision"] == "FORCE_RCA" else 0)


if __name__ == "__main__":
    main()
