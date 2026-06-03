#!/usr/bin/env python3
"""Validate WCUQ Visual Tracker status v2 and stale-score display safety."""
from __future__ import annotations
import argparse, json, math, re, sys
from pathlib import Path

REQUIRED = {
    "schema", "created_at_utc", "status_state", "display_text", "live_score",
    "last_known_calibration", "stale_or_unavailable", "sources"
}
VALID_STATES = {"live_score", "last_known_calibration", "stale_or_unavailable"}
SCORE_RE = re.compile(r"\bscore\s+[0-9]+(?:\.[0-9]+)?\b", re.I)
SUPPRESS = "WCUQ stale/unavailable; numeric score suppressed"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_status(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    data = load_json(path)
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append("MISSING_FIELDS:" + ",".join(missing))
    if data.get("schema") != "mb.quality_scoring.wcuq_visual_teacher_status.v2":
        errors.append("SCHEMA_NOT_V2")
    state = data.get("status_state")
    if state not in VALID_STATES:
        errors.append("INVALID_STATUS_STATE")
    display = str(data.get("display_text") or "")
    live = data.get("live_score")
    stale = data.get("stale_or_unavailable")
    if state == "live_score":
        if not isinstance(live, dict):
            errors.append("LIVE_SCORE_STATE_WITHOUT_LIVE_SCORE_OBJECT")
        else:
            score = live.get("score")
            if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                errors.append("LIVE_SCORE_NONNUMERIC")
        if display == SUPPRESS:
            errors.append("LIVE_SCORE_SUPPRESSED_DISPLAY")
    else:
        if SCORE_RE.search(display):
            errors.append("NONLIVE_STATE_NUMERIC_SCORE_DISPLAY")
        if display != SUPPRESS:
            errors.append("NONLIVE_STATE_MUST_SUPPRESS_NUMERIC_DISPLAY")
        if state == "stale_or_unavailable" and not isinstance(stale, dict):
            errors.append("STALE_STATE_WITHOUT_REASON_OBJECT")
    return not errors, errors


def validate_tracker(path: Path) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    errors: list[str] = []
    if "score 90.35" in text:
        errors.append("TRACKER_CONTAINS_STALE_9035")
    if SUPPRESS not in text:
        errors.append("TRACKER_MISSING_SUPPRESSION_TEXT")
    return not errors, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", default="runtime/state/WCUQ_STATUS.json")
    ap.add_argument("--tracker", default="runtime/state/ACTIVE_TRACKER_PREVIEW.txt")
    ap.add_argument("--receipt", default="")
    args = ap.parse_args()
    status_ok, status_errors = validate_status(Path(args.status))
    tracker_ok, tracker_errors = validate_tracker(Path(args.tracker))
    out = {
        "schema": "mb.wcuq.status_schema_validator.result.v1",
        "decision": "PASS" if status_ok and tracker_ok else "BLOCKED",
        "status_path": args.status,
        "tracker_path": args.tracker,
        "errors": status_errors + tracker_errors,
        "file_search_used": False,
    }
    if args.receipt:
        rp = Path(args.receipt)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["decision"] == "PASS" else 86

if __name__ == "__main__":
    raise SystemExit(main())
