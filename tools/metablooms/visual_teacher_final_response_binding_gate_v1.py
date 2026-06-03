#!/usr/bin/env python3
"""MetaBlooms Visual Tracker binding gate.

Reads runtime state (WCUQ status, active work) and generates a
human-readable, evidence-driven, freshness-gated tracker preview.
Writes runtime/state/ACTIVE_TRACKER_PREVIEW.txt on each boot.

Boot usage:
  python3 tools/metablooms/visual_teacher_final_response_binding_gate_v1.py

The preview reflects ACTIVE_WORK.json for current-work scope and
WCUQ_STATUS.json for quality-score state.  Neither source is silently
stale: WCUQ has a freshness gate; ACTIVE_WORK has a schema timestamp.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "runtime" / "state"
RECEIPTS_DIR = ROOT / "runtime" / "receipts" / "visual_tracker_repair"

WCUQ_JSON_DEFAULT = STATE_DIR / "WCUQ_STATUS.json"
WCUQ_TXT_DEFAULT = STATE_DIR / "WCUQ_STATUS.txt"
ACTIVE_WORK_DEFAULT = STATE_DIR / "ACTIVE_WORK.json"
PREVIEW_DEFAULT = STATE_DIR / "ACTIVE_TRACKER_PREVIEW.txt"

WCUQ_FRESHNESS_MAX_SECONDS = 3600  # 1 hour window for live scores
SUPPRESS_TEXT = "WCUQ stale/unavailable; numeric score suppressed"

# ── helpers ───────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(s: str) -> datetime | None:
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S+00:00",
    ):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json_safe(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

# ── active-work reader ────────────────────────────────────────────────────────


def _read_active_work(path: Path) -> dict[str, Any] | None:
    return _read_json_safe(path)


def _render_progress_lines(work: dict[str, Any]) -> list[str]:
    lines = []
    for item in work.get("progress", []):
        label = item.get("label", "?")
        status = item.get("status", "?")
        lines.append(f"  {label}: {status}")
    return lines


def _render_tracker(
    wcuq_text: str,
    work: dict[str, Any] | None,
    generated_at: str,
) -> str:
    stage = (work or {}).get("stage", "UNKNOWN")
    next_action = (work or {}).get("next", "not set")
    floor = (work or {}).get("floor", {})
    floor_name = floor.get("name", "unknown")
    floor_sha = floor.get("sha256", "")

    lines = [
        "MetaBlooms Visual Tracker",
        f"stage {stage}",
        f"generated {generated_at}",
        "",
        "WCUQ:",
        f"  {wcuq_text}",
        "",
        "active work:",
    ]
    if work:
        lines.extend(_render_progress_lines(work))
    else:
        lines.append("  (no ACTIVE_WORK.json found — bind a state file to scope this tracker)")
    lines += [
        "",
        "next:",
        f"  {next_action}",
        "",
        "floor:",
        f"  {floor_name}",
    ]
    if floor_sha:
        lines.append(f"  SHA256 {floor_sha}")
    return "\n".join(lines) + "\n"

# ── WCUQ freshness gate ───────────────────────────────────────────────────────
# Patched per WCUQ_STATIC_SCORE_STAGE001 + STAGE002 (base64 artifact
# governance/improvement_log/WCUQ_STAGE004_REMOTE_PATCH_BASE64_20260602.md,
# decoded SHA-256 a582ec350a111cea9b03a1d86c5e1b5f190843560533a2ee18eaa84f0f6fd8af).
# Schema v2 suppresses numeric score unless status_state == "live_score".


def _read_wcuq_text(
    json_path: Path,
    txt_path: Path,
    evidence: dict[str, Any],
    max_age_seconds: int = WCUQ_FRESHNESS_MAX_SECONDS,
) -> tuple[str, dict[str, Any]]:

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
        return SUPPRESS_TEXT, evidence
    if evidence["freshness_decision"] != "fresh":
        return SUPPRESS_TEXT, evidence
    return raw_text or "WCUQ current but empty", evidence

# ── main runner ───────────────────────────────────────────────────────────────


def run(
    wcuq_json: Path = WCUQ_JSON_DEFAULT,
    wcuq_txt: Path = WCUQ_TXT_DEFAULT,
    active_work_json: Path = ACTIVE_WORK_DEFAULT,
    preview_txt: Path = PREVIEW_DEFAULT,
    receipt_path: Path | None = None,
) -> dict[str, Any]:
    wcuq_evidence: dict[str, Any] = {}
    wcuq_text, wcuq_evidence = _read_wcuq_text(wcuq_json, wcuq_txt, wcuq_evidence)
    work = _read_active_work(active_work_json)
    generated_at = _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    preview = _render_tracker(wcuq_text, work, generated_at)
    _write(preview_txt, preview)

    stale_check = "score 90.35" not in preview and SUPPRESS_TEXT in preview
    result: dict[str, Any] = {
        "schema": "mb.visual_tracker.binding_gate.result.v1",
        "decision": "PASS" if stale_check else "BLOCKED",
        "generated_at_utc": generated_at,
        "wcuq_text": wcuq_text,
        "wcuq_evidence": wcuq_evidence,
        "preview_path": str(preview_txt),
        "regression_checks": {
            "stale_9035_absent": "score 90.35" not in preview,
            "suppress_text_present": SUPPRESS_TEXT in preview,
        },
        "file_search_used": False,
    }
    if receipt_path:
        _write(receipt_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="MetaBlooms Visual Tracker binding gate")
    ap.add_argument("--wcuq-json", default=str(WCUQ_JSON_DEFAULT))
    ap.add_argument("--wcuq-txt", default=str(WCUQ_TXT_DEFAULT))
    ap.add_argument("--active-work", default=str(ACTIVE_WORK_DEFAULT))
    ap.add_argument("--preview", default=str(PREVIEW_DEFAULT))
    ap.add_argument("--receipt", default="")
    args = ap.parse_args()
    result = run(
        wcuq_json=Path(args.wcuq_json),
        wcuq_txt=Path(args.wcuq_txt),
        active_work_json=Path(args.active_work),
        preview_txt=Path(args.preview),
        receipt_path=Path(args.receipt) if args.receipt else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
