#!/usr/bin/env python3
"""MetaBlooms Visual Teacher final-response binding gate.

Reads WCUQ status, active work, sync parity baseline, and manual alerts, then
writes the MetaBlooms Visual Tracker display to
runtime/state/ACTIVE_TRACKER_PREVIEW.txt in the human-facing four-section
emoji format.

Sections:
  🧭 MetaBlooms Work Status   — current stage, job, next action
  📊 Sync Parity              — parity %, progress bar, deviation counts
  🧪 Evidence Health          — WCUQ, sources, stale suppression, manual blocker
  🧱 Machine Details          — static machine context note

WCUQ freshness rules (v2 schema):
  status_state == "live_score"  → display live score only if created_at_utc is
    within max_age_seconds of the current turn.
  status_state != "live_score"  → always render suppression message.
  v1 legacy .txt file           → always render suppression message.
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
PARITY_DEFAULT = (
    ROOT
    / "runtime"
    / "receipts"
    / "github_os_sync_stage0u"
    / "STAGE0U_20260603T214100Z"
    / "STAGE0T_PARITY_BASELINE.json"
)
ALERTS_DEFAULT = ROOT / "runtime" / "state" / "MANUAL_ALERTS.json"

SUPPRESS = "WCUQ stale/unavailable; numeric score suppressed"
DEFAULT_MAX_AGE = 3600  # seconds
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
BAR_WIDTH = 20
SCHEMA = "mb.visual_tracker.binding_gate.receipt.v2"


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


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data, err = _read_json_safe(path)
    return data if not err else {"_read_error": err}


def _progress_bar(pct: float, width: int = BAR_WIDTH) -> str:
    if pct >= 100.0:
        filled = width
    else:
        filled = min(int(pct / 100.0 * width), width)
    empty = width - filled
    return "[" + "█" * filled + "░" * empty + "]"


# ---------------------------------------------------------------------------
# WCUQ status reader with v2 schema support and freshness gate
# ---------------------------------------------------------------------------

def _read_wcuq_status(
    json_path: Path,
    txt_path: Path,
    max_age_seconds: int,
    evidence: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Return (display_text, evidence) with v2 schema freshness enforcement."""
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
                live_score = (
                    data.get("live_score")
                    if isinstance(data.get("live_score"), dict)
                    else None
                )
                if status_state == "live_score" and live_score:
                    raw_text = str(
                        data.get("display_text") or live_score.get("score_text") or ""
                    )
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
        evidence["freshness_decision"] = (
            "fresh" if 0 <= age <= max_age_seconds else "stale"
        )

    if (schema or "").endswith(".v2") and status_state != "live_score":
        evidence["freshness_decision"] = status_state or evidence["freshness_decision"]
        return SUPPRESS, evidence
    if evidence["freshness_decision"] != "fresh":
        return SUPPRESS, evidence
    return raw_text or "WCUQ current but empty", evidence


# ---------------------------------------------------------------------------
# tracker formatter — four-section emoji format
# ---------------------------------------------------------------------------

def _format_tracker(
    wcuq_text: str,
    wcuq_source: str,
    work: dict[str, Any],
    parity: dict[str, Any],
    alerts: dict[str, Any],
) -> str:
    lines: list[str] = []

    # ── 🧭 Work Status ──────────────────────────────────────────────────────
    lines += ["🧭 MetaBlooms Work Status", DIVIDER]
    lines.append(f"Status: {work.get('status', 'Working')}")
    current_job = work.get("current_job", work.get("current_work", ""))
    if current_job:
        lines.append(f"Current job: {current_job}")
    current_stage = work.get("current_stage", "")
    if current_stage:
        lines.append(f"Current stage: {current_stage}")
    next_action = work.get("next_action", "")
    if next_action:
        lines.append(f"Next action: {next_action}")
    lines.append("")

    # ── 📊 Sync Parity ──────────────────────────────────────────────────────
    lines += ["📊 Sync Parity", DIVIDER]
    if parity:
        pct: float = float(parity.get("parity_pct", parity.get("resolved_pct", 0.0)))
        resolved: int = int(parity.get("resolved", 0))
        total: int = int(parity.get("total", 0))
        remaining: int = int(
            parity.get("remaining_deviations", parity.get("remaining", 0))
        )
        unclassified: int = int(parity.get("unclassified", 0))
        parity_source: str = str(parity.get("source_path", ""))
        bar = _progress_bar(pct)
        lines += [
            f"[{pct:.4f}%] {bar}",
            f"Resolved: {resolved} / {total}",
            f"Remaining deviations: {remaining}",
            f"Unclassified: {unclassified}",
        ]
        if parity_source:
            lines.append(f"Source: {parity_source}")
    else:
        lines.append("Parity data unavailable")
    lines.append("")

    # ── 🧪 Evidence Health ──────────────────────────────────────────────────
    lines += ["🧪 Evidence Health", DIVIDER]
    tracker_source = work.get("tracker_source", "runtime/state/ACTIVE_WORK.json")
    stale_hidden = work.get("stale_archive_progress_hidden", True)
    blocker = (alerts.get("manual_action_blocker", "none") if alerts else "none") or "none"
    lines += [
        f"Tracker source: {tracker_source}",
        f"WCUQ: {wcuq_text}",
        f"WCUQ source: {wcuq_source}",
        f"Stale archive progress: {'hidden' if stale_hidden else 'visible'}",
        f"Manual action blocker: {blocker}",
    ]
    lines.append("")

    # ── 🧱 Machine Details ──────────────────────────────────────────────────
    lines += ["🧱 Machine Details", DIVIDER]
    machine_detail = work.get(
        "machine_details",
        "Raw archive floor and legacy quality telemetry are preserved in receipts,"
        " not displayed as current work.",
    )
    lines.append(machine_detail)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Write MetaBlooms Visual Tracker preview")
    ap.add_argument("--wcuq-json", default=str(WCUQ_JSON_DEFAULT))
    ap.add_argument("--wcuq-txt", default=str(WCUQ_TXT_DEFAULT))
    ap.add_argument("--work-json", default=str(WORK_JSON_DEFAULT))
    ap.add_argument("--parity-json", default=str(PARITY_DEFAULT))
    ap.add_argument("--alerts-json", default=str(ALERTS_DEFAULT))
    ap.add_argument("--tracker", default=str(TRACKER_DEFAULT))
    ap.add_argument("--receipt", default="")
    ap.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE)
    args = ap.parse_args()

    evidence: dict[str, Any] = {"freshness_decision": "no_timestamp"}
    wcuq_json_path = Path(args.wcuq_json)
    wcuq_text, evidence = _read_wcuq_status(
        wcuq_json_path,
        Path(args.wcuq_txt),
        args.max_age,
        evidence,
    )
    wcuq_source = (
        str(wcuq_json_path.relative_to(ROOT))
        if wcuq_json_path.is_relative_to(ROOT)
        else args.wcuq_json
    )

    work = _read_optional_json(Path(args.work_json))
    parity = _read_optional_json(Path(args.parity_json))
    alerts = _read_optional_json(Path(args.alerts_json))

    tracker_text = _format_tracker(wcuq_text, wcuq_source, work, parity, alerts)

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
        "parity_loaded": bool(parity),
        "alerts_loaded": bool(alerts),
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
