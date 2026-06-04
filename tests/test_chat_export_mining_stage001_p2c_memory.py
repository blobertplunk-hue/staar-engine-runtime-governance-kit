"""
P2 regression tests (constant-memory enforcement) for CHAT790_EXPORT_MINING_CARTRIDGE_STAGE001.

These tests cover the Codex review finding "Enforce the constant-memory Stage001 guarantee":

  1. --dry-run must NOT accumulate events (max_events=0 so no events are ever appended).
  2. Normal large-input runs use a bounded events list (default max_events=1000).
  3. Counts (mapped, failures_found) remain accurate even when events are capped.
  4. events_capped / events_cap fields accurately report truncation state.
"""
import json
import os
import subprocess
import sys
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "chat_export_mining"))
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "blocker_ledger"))

from governance.chat_export_mining.runner import (  # noqa: E402
    mine_stream,
    _DEFAULT_MAX_EVENTS,
)

_RUNNER_SCRIPT = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "runner.py")
_FIXTURES = os.path.join(_REPO_ROOT, "tests", "fixtures", "chat_export_mining")


def _make_failure(tool_name="file_search", n=0):
    return json.dumps({
        "hook_event_name": "PostToolUseFailure",
        "tool_name": tool_name,
        "tool_input": {"query": f"query-{n}", "target_path": "/mnt/data/Metablooms_OS"},
        "tool_response": f"Error: {tool_name} failed (event {n})",
        "session_id": f"test-memory-{n}",
    })


def _run_runner(fixture_path=None, extra_args=None, stdin_text=None):
    cmd = [sys.executable, _RUNNER_SCRIPT]
    if fixture_path:
        cmd += ["--input", fixture_path]
    if extra_args:
        cmd += extra_args
    result = subprocess.run(
        cmd, input=stdin_text, capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"_raw_stdout": result.stdout, "_stderr": result.stderr}
    return result.returncode, out


# ══════════════════════════════════════════════════════════════════════════════
class TestDryRunDoesNotAccumulateEvents(unittest.TestCase):
    """
    PROVES: --dry-run (max_events=0) never appends to the events list.

    The fix is at the mine_stream level, not post-hoc: with max_events=0,
    events are never added to mapped_events even during processing, so
    memory usage does not grow with the number of failures.
    """

    def test_dry_run_max_events_zero_never_appends(self):
        """mine_stream with max_events=0 → events=[] even when failures are present."""
        lines = [_make_failure(n=i) for i in range(50)]
        r = mine_stream(lines, max_events=0)
        self.assertEqual(r["events"], [],
            "max_events=0 must produce events=[] regardless of failures_found")

    def test_dry_run_counts_are_accurate_with_zero_max_events(self):
        """Counts remain accurate even when no events are stored."""
        lines = [_make_failure(n=i) for i in range(50)]
        r = mine_stream(lines, max_events=0)
        self.assertEqual(r["failures_found"], 50)
        self.assertEqual(r["mapped"], 50,
            "mapped count must reflect all mapped failures, not just stored events")
        self.assertEqual(r["unmappable"], 0)

    def test_dry_run_events_cap_is_zero(self):
        """events_cap=0 in receipt when max_events=0."""
        r = mine_stream([_make_failure()], max_events=0)
        self.assertEqual(r["events_cap"], 0)

    def test_dry_run_events_capped_true_when_failures_present(self):
        """events_capped=True when max_events=0 and there were mapped events."""
        r = mine_stream([_make_failure()], max_events=0)
        self.assertTrue(r["events_capped"],
            "events_capped must be True when max_events=0 and failures were mapped")

    def test_dry_run_subprocess_events_empty(self):
        """subprocess --dry-run produces events=[] and dry_run=True in receipt."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--dry-run"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out["events"], [])
        self.assertTrue(out.get("dry_run"))

    def test_dry_run_subprocess_counts_accurate(self):
        """subprocess --dry-run counts all failures even though events=[]."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--dry-run"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out["failures_found"], 3)
        self.assertEqual(out["mapped"], 3,
            "mapped must count all mapped failures even in dry-run mode")

    def test_dry_run_subprocess_events_cap_zero(self):
        """subprocess --dry-run reports events_cap=0."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--dry-run"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("events_cap"), 0)


# ══════════════════════════════════════════════════════════════════════════════
class TestBoundedEventRetentionPolicy(unittest.TestCase):
    """
    PROVES: normal (non-dry-run) large-input behavior has a bounded event
    retention policy. Events beyond max_events are counted but not stored.
    """

    def test_default_max_events_constant_is_positive(self):
        """_DEFAULT_MAX_EVENTS must be a positive integer."""
        self.assertIsInstance(_DEFAULT_MAX_EVENTS, int)
        self.assertGreater(_DEFAULT_MAX_EVENTS, 0,
            "_DEFAULT_MAX_EVENTS must be positive")

    def test_events_list_capped_at_max_events(self):
        """More failures than max_events → events list is exactly max_events long."""
        cap = 5
        lines = [_make_failure(n=i) for i in range(cap + 10)]
        r = mine_stream(lines, max_events=cap)
        self.assertEqual(len(r["events"]), cap,
            f"events list must be capped at max_events={cap}")

    def test_mapped_count_exceeds_events_when_capped(self):
        """mapped count includes all mapped events, not just stored ones."""
        cap = 3
        total = 8
        lines = [_make_failure(n=i) for i in range(total)]
        r = mine_stream(lines, max_events=cap)
        self.assertEqual(r["mapped"], total,
            "mapped must count all mapped failures regardless of cap")
        self.assertEqual(len(r["events"]), cap)

    def test_events_capped_true_when_over_limit(self):
        """events_capped=True when failures exceed max_events."""
        cap = 2
        lines = [_make_failure(n=i) for i in range(cap + 1)]
        r = mine_stream(lines, max_events=cap)
        self.assertTrue(r["events_capped"],
            "events_capped must be True when mapped events exceed max_events")

    def test_events_capped_false_when_under_limit(self):
        """events_capped=False when failures do not exceed max_events."""
        cap = 100
        lines = [_make_failure(n=i) for i in range(3)]
        r = mine_stream(lines, max_events=cap)
        self.assertFalse(r["events_capped"],
            "events_capped must be False when mapped events are within max_events")

    def test_events_cap_field_reflects_limit(self):
        """events_cap in receipt equals the max_events argument passed."""
        cap = 7
        r = mine_stream([_make_failure()], max_events=cap)
        self.assertEqual(r["events_cap"], cap)

    def test_default_cap_applied_when_no_explicit_limit(self):
        """mine_stream() with no max_events uses _DEFAULT_MAX_EVENTS."""
        r = mine_stream([_make_failure()])
        self.assertEqual(r["events_cap"], _DEFAULT_MAX_EVENTS)

    def test_subprocess_max_events_flag_caps_events(self):
        """--max-events N limits stored events; mapped count is still accurate."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--max-events", "1"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(out["events"]), 1,
            "--max-events 1 must store exactly 1 event")
        self.assertEqual(out["mapped"], 3,
            "mapped count must reflect all 3 mapped failures")
        self.assertTrue(out["events_capped"])

    def test_subprocess_max_events_zero_is_counts_only(self):
        """--max-events 0 acts as counts-only mode (same as --dry-run for storage)."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--max-events", "0"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out["events"], [])
        self.assertEqual(out["mapped"], 3)

    def test_mapped_count_invariant(self):
        """len(events) + capped_count == mapped is always true."""
        cap = 4
        total = 10
        lines = [_make_failure(n=i) for i in range(total)]
        r = mine_stream(lines, max_events=cap)
        # capped_count = mapped - len(events)
        capped = r["mapped"] - len(r["events"])
        self.assertEqual(r["mapped"], len(r["events"]) + capped)
        self.assertEqual(r["mapped"], total)
        self.assertEqual(len(r["events"]), cap)


# ══════════════════════════════════════════════════════════════════════════════
class TestContractReceiptShapeComplete(unittest.TestCase):
    """Contract receipt_shape must include the new events_cap/events_capped fields."""

    def test_contract_has_events_cap_field(self):
        import json as _json
        contract_path = os.path.join(
            _REPO_ROOT, "governance", "chat_export_mining", "BOUNDED_RUNNER_CONTRACT_v1.json"
        )
        with open(contract_path) as f:
            c = _json.load(f)
        self.assertIn("events_cap", c["receipt_shape"],
            "Contract receipt_shape must document events_cap field")

    def test_contract_has_events_capped_field(self):
        import json as _json
        contract_path = os.path.join(
            _REPO_ROOT, "governance", "chat_export_mining", "BOUNDED_RUNNER_CONTRACT_v1.json"
        )
        with open(contract_path) as f:
            c = _json.load(f)
        self.assertIn("events_capped", c["receipt_shape"],
            "Contract receipt_shape must document events_capped field")

    def test_contract_guarantee_references_max_events(self):
        """The constant-memory guarantee must reference --max-events."""
        import json as _json
        contract_path = os.path.join(
            _REPO_ROOT, "governance", "chat_export_mining", "BOUNDED_RUNNER_CONTRACT_v1.json"
        )
        with open(contract_path) as f:
            c = _json.load(f)
        guarantees = " ".join(c.get("guarantees", []))
        self.assertIn("max-events", guarantees,
            "Guarantees must reference --max-events to describe bounded memory")

    def test_contract_flags_include_max_events(self):
        """Contract flags section must document --max-events."""
        import json as _json
        contract_path = os.path.join(
            _REPO_ROOT, "governance", "chat_export_mining", "BOUNDED_RUNNER_CONTRACT_v1.json"
        )
        with open(contract_path) as f:
            c = _json.load(f)
        flags = c.get("invocation", {}).get("flags", {})
        self.assertTrue(
            any("max-events" in k for k in flags),
            "Contract flags must include --max-events"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
