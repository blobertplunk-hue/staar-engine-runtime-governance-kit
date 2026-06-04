#!/usr/bin/env python3
"""MetaBlooms Visual Teacher final-response binding gate.

Reads WCUQ status from runtime/state/WCUQ_STATUS.json (v2 schema) or
runtime/state/WCUQ_STATUS.txt (v1 legacy), applies freshness rules, and
writes the MetaBlooms Visual Tracker display to
runtime/state/ACTIVE_TRACKER_PREVIEW.txt.

WCUQ freshness rules (v2 schema):
- status_state == "live_score"  →  display live score only if created_at_utc
  is within max_age_seconds of the current turn.
- status_state != "live_score"  →  always render the suppression message,
  regardless of created_at_utc age.
- v1 legacy .txt file  →  render suppression message (never treat as live).
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WCUQ_JSON_DEFAULT = ROOT / "runtime" / "state" / "WCUQ_STATUS.json"
WCUQ_TXT_DEFAULT = ROOT / "runtime" / "state" / "WCUQ_STATUS.txt"
TRACKER_DEFAULT = ROOT / "runtime" / "state" / "ACTIVE_TRACKER_PREVIEW.txt"
WORK_JSON_DEFAULT = ROOT / "runtime" / "state" / "ACTIVE_WORK.json"

SUPPRESS = "WCUQ stale/unavailable; numeric score suppressed"
DEFAULT_MAX_AGE = 3600  # 1 hour in seconds

SCHEMA = "mb.visual_tracker.binding_gate.receipt.v1"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(s: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _read_json_safe(path: Path) -> tuple[dict, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return {}, f"{type(exc).__name__}:{exc}"


def _read_work_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data, err = _read_json_safe(path)
    if err:
        return {"error": err}
    return data


# ---------------------------------------------------------------------------
# WCUQ status reader with v2 schema support and freshness gate
# ---------------------------------------------------------------------------

def _read_wcuq_status(
    json_path: Path,
    txt_path: Path,
    max_age_seconds: int,
    evidence: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Return (display_text, evidence) with v2 schema freshness enforcement.

    Side-effect: populates *evidence* in-place with diagnostic fields.
    """
    data: dict[str, Any] = {}
    raw_text = ""
    schema = None
    status_state = None
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            schema = str(data.get("schema") or "")
            status_state = str(data.get("status_state") or "")
            if schema.endswith(".v2"):
                live_score = data.get("live_score") if isinstance(data.get("live_score"), dict) else None
                if status_state == "live_score" and live_score:
                    raw_text = str(data.get("display_text") or live_score.get("score_text") or "")
                else:
                    raw_text = ""
            else:
                raw_text = str(data.get("text") or "")
        except Exception as exc:
            evidence["freshness_decision"] = "json_unreadable"
            evidence["error"] = f"{type(exc).__name__}:{exc}"
    if not raw_text and txt_path.exists() and not (schema or "").endswith(".v2"):
        raw_text = txt_path.read_text(encoding="utf-8").strip()

    created = _parse_utc(str(data.get("created_at_utc") or ""))
    now = _utc_now()
    evidence["schema"] = schema
    evidence["status_state"] = status_state
    evidence["created_at_utc"] = data.get("created_at_utc")
    evidence["max_age_seconds"] = max_age_seconds
    if created is None:
        evidence.setdefault("freshness_decision", "no_timestamp")
    else:
        age = (now - created).total_seconds()
        evidence["age_seconds"] = age
        evidence["freshness_decision"] = "fresh" if 0 <= age <= max_age_seconds else "stale"

    if (schema or "").endswith(".v2") and status_state != "live_score":
        evidence["freshness_decision"] = status_state or evidence["freshness_decision"]
        return SUPPRESS, evidence
    if evidence["freshness_decision"] != "fresh":
        return SUPPRESS, evidence
    return raw_text or "WCUQ current but empty", evidence


# ---------------------------------------------------------------------------
# tracker formatter
# ---------------------------------------------------------------------------

def _format_tracker(wcuq_text: str, work: dict[str, Any]) -> str:
    current_stage = work.get("current_stage", "")
    current_work = work.get("current_work", "")
    next_action = work.get("next_action", "")
    floor = work.get("floor", "")
    floor_release = work.get("floor_release", "")

    lines = [
        "MetaBlooms Visual Tracker",
        "=========================",
        "",
    ]
    if floor:
        lines += ["Floor:", f"  {floor}"]
        if floor_release:
            lines += [f"  Release: {floor_release}"]
        lines.append("")
    if current_stage:
        lines += ["Current Stage:", f"  {current_stage}", ""]
    if current_work:
        lines += ["Current Work:", f"  {current_work}", ""]
    if next_action:
        lines += ["Next Action:", f"  {next_action}", ""]
    lines += [
        "WCUQ:",
        f"  {wcuq_text}",
        "",
        "file_search_used: false",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Write MetaBlooms Visual Tracker preview")
    ap.add_argument("--wcuq-json", default=str(WCUQ_JSON_DEFAULT))
    ap.add_argument("--wcuq-txt", default=str(WCUQ_TXT_DEFAULT))
    ap.add_argument("--work-json", default=str(WORK_JSON_DEFAULT))
    ap.add_argument("--tracker", default=str(TRACKER_DEFAULT))
    ap.add_argument("--receipt", default="")
    ap.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE)
    args = ap.parse_args()

    evidence: dict[str, Any] = {"freshness_decision": "no_timestamp"}
    wcuq_text, evidence = _read_wcuq_status(
        Path(args.wcuq_json),
        Path(args.wcuq_txt),
        args.max_age,
        evidence,
    )

    work = _read_work_state(Path(args.work_json))
    tracker_text = _format_tracker(wcuq_text, work)

    tracker_path = Path(args.tracker)
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    tracker_path.write_text(tracker_text, encoding="utf-8")

    receipt = {
        "schema": SCHEMA,
        "created_at_utc": _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": "PASS",
        "wcuq_display": wcuq_text,
        "tracker_path": str(tracker_path),
        "wcuq_evidence": evidence,
        "file_search_used": False,
    }

    if args.receipt:
        rp = Path(args.receipt)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
