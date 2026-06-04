"""Tests for visual_teacher_final_response_binding_gate_v1.py — Stage006."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.metablooms.visual_teacher_final_response_binding_gate_v1 import (
    _blocker_value,
    _format_red_alert,
    _format_tracker,
)

SUPPRESS = "WCUQ stale/unavailable; numeric score suppressed"
WORK = {
    "status": "Working",
    "current_stage": "VISUAL_TRACKER_STAGE006_PARITY_AND_MANUAL_ALERT_INTEGRATION",
    "current_job": "test job",
    "next_action": "NEXT",
    "tracker_source": "runtime/state/ACTIVE_WORK.json",
    "stale_archive_progress_hidden": True,
    "machine_details": "Raw archive floor preserved in receipts.",
}
PARITY = {
    "parity_pct": 99.9966,
    "resolved": 58847,
    "total": 58849,
    "remaining_deviations": 2,
    "unclassified": 0,
    "source_path": "runtime/receipts/github_os_sync_stage0u/STAGE0U_20260603T214100Z/STAGE0T_PARITY_BASELINE.json",
}


# ── _blocker_value ───────────────────────────────────────────────────────────

def test_blocker_value_none_string():
    assert _blocker_value({"manual_action_blocker": "none"}) == ""

def test_blocker_value_empty_string():
    assert _blocker_value({"manual_action_blocker": ""}) == ""

def test_blocker_value_missing_key():
    assert _blocker_value({}) == ""

def test_blocker_value_none_alerts():
    assert _blocker_value(None) == ""  # type: ignore[arg-type]

def test_blocker_value_active():
    assert _blocker_value({"manual_action_blocker": "PR approval required"}) == "PR approval required"


# ── No-blocker fixture ───────────────────────────────────────────────────────

def test_no_blocker_tracker_does_not_start_with_red_alert():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/no_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert not text.startswith("🚨"), "tracker must NOT start with red alert when blocker is none"
    assert text.startswith("🧭 MetaBlooms Work Status"), "tracker must start with Work Status section"

def test_no_blocker_evidence_health_says_none():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/no_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert "Manual action blocker: none" in text

def test_no_blocker_no_red_emoji_in_text():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/no_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert "🚨" not in text
    assert "🔴" not in text


# ── Active-blocker fixture ───────────────────────────────────────────────────

def test_active_blocker_tracker_starts_with_red_alert():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/active_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert text.startswith("🚨🔴 MANUAL ACTION NEEDED"), (
        "tracker MUST start with red alert when blocker is active"
    )

def test_active_blocker_red_block_before_work_status():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/active_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    red_pos = text.index("🚨🔴 MANUAL ACTION NEEDED")
    work_pos = text.index("🧭 MetaBlooms Work Status")
    assert red_pos < work_pos, "red alert block must appear before Work Status section"

def test_active_blocker_block_fields():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/active_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert "Blocker: PR approval required" in text
    assert "Why I can't do it here: GitHub rejects self-approval." in text
    assert "You can fix it by: Approve the PR manually in GitHub." in text
    assert "After you do it, send: GITHUB_STAGE_NEXT" in text

def test_active_blocker_evidence_health_says_present():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/active_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert "Manual action blocker: present" in text
    assert "Manual action blocker: none" not in text

def test_active_blocker_all_four_sections_present():
    alerts = json.loads(
        (ROOT / "tests/fixtures/visual_tracker/active_blocker_alerts.json").read_text()
    )
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    for section in ("🧭 MetaBlooms Work Status", "📊 Sync Parity", "🧪 Evidence Health", "🧱 Machine Details"):
        assert section in text, f"missing section: {section}"


# ── Stale-pattern regression ─────────────────────────────────────────────────

def test_no_stale_patterns_in_no_blocker_output():
    alerts = {"manual_action_blocker": "none"}
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    for pattern in ("score 90.35", "All 10/12 083%", "STAGE011I2_ARCHIVE_INSPECT_ONLY_E4_RERUN", "K2 archive"):
        assert pattern not in text, f"stale pattern found: {pattern!r}"

def test_suppress_text_present_in_no_blocker_output():
    alerts = {"manual_action_blocker": "none"}
    text = _format_tracker(SUPPRESS, "runtime/state/WCUQ_STATUS.json", WORK, PARITY, alerts)
    assert SUPPRESS in text


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
