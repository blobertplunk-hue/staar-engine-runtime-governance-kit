"""
Tests for CHAT790_EXPORT_MINING_CARTRIDGE_STAGE001.

Covers:
  - Unit tests for mine_stream() with synthetic and fixture JSONL
  - Manifest, schema, and contract document structure
  - Subprocess invocation matching how the runner would be called from CLI
  - Regression guards: all three prior test suites still pass
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

# ── path setup ──────────────────────────────────────────────────────────────
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "blocker_ledger"))
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "chat_export_mining"))

from governance.chat_export_mining.runner import mine_stream, _CARTRIDGE_ID, _RUNNER_STAGE  # noqa: E402
from governance.blocker_ledger.repeated_blocker_guard import FINGERPRINT_FIELDS  # noqa: E402

_FIXTURES = os.path.join(_REPO_ROOT, "tests", "fixtures", "chat_export_mining")
_RUNNER_SCRIPT = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "runner.py")
_MANIFEST = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "CARTRIDGE_MANIFEST.json")
_SCHEMA = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "CHAT_EXPORT_ENTRY_SCHEMA_v1.json")
_CONTRACT = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "BOUNDED_RUNNER_CONTRACT_v1.json")

# ── helpers ──────────────────────────────────────────────────────────────────


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _lines(path):
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def _run_runner(fixture_path, extra_args=None, stdin_text=None):
    """Invoke runner.py as a subprocess; return (returncode, receipt_dict)."""
    cmd = [sys.executable, _RUNNER_SCRIPT]
    if fixture_path:
        cmd += ["--input", fixture_path]
    if extra_args:
        cmd += extra_args
    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"_raw_stdout": result.stdout, "_stderr": result.stderr}
    return result.returncode, out


# ── synthetic JSONL helpers ───────────────────────────────────────────────────

def _make_failure(tool_name="file_search", target="/mnt/data/Metablooms_OS", query="q"):
    return json.dumps({
        "hook_event_name": "PostToolUseFailure",
        "tool_name": tool_name,
        "tool_input": {"query": query, "target_path": target},
        "tool_response": f"Error: {tool_name} failed",
        "session_id": "test-session-synth",
    })


def _make_non_failure(event="PreToolUse"):
    return json.dumps({"hook_event_name": event, "tool_name": "Read",
                       "tool_input": {"file_path": "/tmp/x"}})


# ══════════════════════════════════════════════════════════════════════════════
class TestRunnerUnit(unittest.TestCase):
    """Unit tests for mine_stream() using synthetic JSONL lines."""

    def test_mine_stream_empty_input_returns_zero_counts(self):
        """Empty input → receipt with all-zero counts."""
        r = mine_stream([])
        self.assertEqual(r["entries_seen"], 0)
        self.assertEqual(r["failures_found"], 0)
        self.assertEqual(r["mapped"], 0)
        self.assertEqual(r["unmappable"], 0)
        self.assertEqual(r["parse_errors"], 0)
        self.assertEqual(r["events"], [])

    def test_mine_stream_single_failure_yields_one_event(self):
        """Single PostToolUseFailure line → 1 mapped event."""
        lines = [_make_failure(), "\n"]
        r = mine_stream(lines)
        self.assertEqual(r["entries_seen"], 1)
        self.assertEqual(r["failures_found"], 1)
        self.assertEqual(r["mapped"], 1)
        self.assertEqual(len(r["events"]), 1)

    def test_mine_stream_no_failures_zero_events(self):
        """Non-failure entries (PreToolUse, Stop, etc.) → 0 events, entries counted."""
        lines = [
            _make_non_failure("PreToolUse"),
            _make_non_failure("PostToolUse"),
            _make_non_failure("Stop"),
        ]
        r = mine_stream(lines)
        self.assertEqual(r["entries_seen"], 3)
        self.assertEqual(r["failures_found"], 0)
        self.assertEqual(r["mapped"], 0)
        self.assertEqual(r["events"], [])

    def test_mine_stream_multi_failure_correct_counts(self):
        """Three failures → mapped=3, events has 3 entries."""
        lines = [
            _make_failure(tool_name="file_search"),
            _make_failure(tool_name="Bash"),
            _make_failure(tool_name="Write"),
        ]
        r = mine_stream(lines)
        self.assertEqual(r["failures_found"], 3)
        self.assertEqual(r["mapped"], 3)
        self.assertEqual(len(r["events"]), 3)

    def test_mine_stream_malformed_lines_are_parse_errors(self):
        """Bad JSON lines are counted as parse_errors without crashing."""
        lines = [
            "this is not json {{{",
            _make_failure(),
            '{"incomplete": true',
        ]
        r = mine_stream(lines)
        self.assertEqual(r["parse_errors"], 2)
        self.assertEqual(r["entries_seen"], 1)
        self.assertEqual(r["mapped"], 1)

    def test_mine_stream_empty_lines_silently_skipped(self):
        """Blank lines do not count as parse_errors or entries."""
        lines = ["\n", "  \n", _make_failure(), "\n"]
        r = mine_stream(lines)
        self.assertEqual(r["parse_errors"], 0)
        self.assertEqual(r["entries_seen"], 1)

    def test_mine_stream_mapped_event_has_fingerprint_fields(self):
        """Every mapped event contains all FINGERPRINT_FIELDS with non-empty values."""
        r = mine_stream([_make_failure()])
        event = r["events"][0]
        for field in FINGERPRINT_FIELDS:
            self.assertIn(field, event, f"Missing fingerprint field: {field}")
            self.assertTrue(event[field], f"Empty fingerprint field: {field}")

    def test_mine_stream_mapped_event_has_adapter_status(self):
        """Mapped events carry _adapter_status (MAPPED or PASS_THROUGH)."""
        r = mine_stream([_make_failure()])
        event = r["events"][0]
        self.assertIn("_adapter_status", event)
        self.assertIn(event["_adapter_status"], ("MAPPED", "PASS_THROUGH"))

    def test_mine_stream_mapped_event_no_decision_field(self):
        """Stage001 runner does not call classify(); receipt has no 'decision' key on events."""
        r = mine_stream([_make_failure()])
        event = r["events"][0]
        self.assertNotIn("decision", event,
                         "Stage001 must not call classify(); no recurrence decisions")

    def test_mine_stream_unmappable_counted_separately(self):
        """Entry with hook_event_name=PostToolUseFailure but no tool_name → UNMAPPABLE."""
        bad = json.dumps({"hook_event_name": "PostToolUseFailure",
                          "tool_response": "Error: no tool_name present"})
        r = mine_stream([bad])
        self.assertEqual(r["failures_found"], 1)
        self.assertEqual(r["unmappable"], 1)
        self.assertEqual(r["mapped"], 0)
        self.assertEqual(r["events"], [])

    def test_mine_stream_max_entries_truncates(self):
        """max_entries=1 stops after the first successfully parsed entry."""
        lines = [_make_failure(query="first"), _make_failure(query="second")]
        r = mine_stream(lines, max_entries=1)
        self.assertEqual(r["entries_seen"], 1)
        self.assertEqual(r["mapped"], 1)

    def test_mine_stream_receipt_has_all_contract_fields(self):
        """Receipt contains every field declared in BOUNDED_RUNNER_CONTRACT_v1."""
        required = {"cartridge_id", "runner_stage", "entries_seen", "parse_errors",
                    "failures_found", "mapped", "unmappable", "events"}
        r = mine_stream([_make_failure()])
        self.assertTrue(required.issubset(r.keys()),
                        f"Missing fields: {required - set(r.keys())}")

    def test_cartridge_id_constant(self):
        """cartridge_id is always CHAT790_EXPORT_MINING_CARTRIDGE."""
        r = mine_stream([])
        self.assertEqual(r["cartridge_id"], "CHAT790_EXPORT_MINING_CARTRIDGE")

    def test_runner_stage_constant(self):
        """runner_stage is always STAGE001."""
        r = mine_stream([])
        self.assertEqual(r["runner_stage"], "STAGE001")

    def test_mine_stream_mixed_events_and_failures(self):
        """Mix of failure and non-failure entries: only failures produce events."""
        lines = [
            _make_non_failure("SessionStart"),
            _make_failure(),
            _make_non_failure("PostToolUse"),
            _make_failure(tool_name="Bash"),
            _make_non_failure("Stop"),
        ]
        r = mine_stream(lines)
        self.assertEqual(r["entries_seen"], 5)
        self.assertEqual(r["failures_found"], 2)
        self.assertEqual(r["mapped"], 2)

    def test_mine_stream_does_not_mutate_input_list(self):
        """mine_stream must not modify the iterable passed in."""
        lines = [_make_failure()]
        original = list(lines)
        mine_stream(lines)
        self.assertEqual(lines, original)


# ══════════════════════════════════════════════════════════════════════════════
class TestFixtureFiles(unittest.TestCase):
    """JSONL fixture files are well-formed and contain expected structure."""

    def test_single_tool_failure_fixture_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(_FIXTURES, "single_tool_failure.jsonl")))

    def test_multi_tool_failure_fixture_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(_FIXTURES, "multi_tool_failure.jsonl")))

    def test_no_tool_failures_fixture_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(_FIXTURES, "no_tool_failures.jsonl")))

    def test_malformed_entry_fixture_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(_FIXTURES, "malformed_entry.jsonl")))

    def test_single_failure_fixture_has_exactly_one_failure(self):
        lines = _lines(os.path.join(_FIXTURES, "single_tool_failure.jsonl"))
        r = mine_stream(lines)
        self.assertEqual(r["failures_found"], 1)
        self.assertEqual(r["mapped"], 1)

    def test_multi_failure_fixture_has_three_failures(self):
        lines = _lines(os.path.join(_FIXTURES, "multi_tool_failure.jsonl"))
        r = mine_stream(lines)
        self.assertEqual(r["failures_found"], 3)
        self.assertEqual(r["mapped"], 3)

    def test_no_failures_fixture_has_zero_failures(self):
        lines = _lines(os.path.join(_FIXTURES, "no_tool_failures.jsonl"))
        r = mine_stream(lines)
        self.assertEqual(r["failures_found"], 0)
        self.assertEqual(r["events"], [])

    def test_malformed_fixture_has_parse_errors(self):
        """malformed_entry.jsonl has bad JSON lines that become parse_errors."""
        lines = _lines(os.path.join(_FIXTURES, "malformed_entry.jsonl"))
        r = mine_stream(lines)
        self.assertGreater(r["parse_errors"], 0)

    def test_malformed_fixture_still_extracts_valid_failure(self):
        """Valid PostToolUseFailure line in malformed fixture is still extracted."""
        lines = _lines(os.path.join(_FIXTURES, "malformed_entry.jsonl"))
        r = mine_stream(lines)
        self.assertGreaterEqual(r["mapped"], 1)

    def test_malformed_fixture_unmappable_entry_counted(self):
        """Entry with no tool_name in malformed fixture counts as unmappable."""
        lines = _lines(os.path.join(_FIXTURES, "malformed_entry.jsonl"))
        r = mine_stream(lines)
        self.assertGreaterEqual(r["unmappable"], 1)


# ══════════════════════════════════════════════════════════════════════════════
class TestManifestAndContracts(unittest.TestCase):
    """CARTRIDGE_MANIFEST.json, CHAT_EXPORT_ENTRY_SCHEMA_v1.json, and BOUNDED_RUNNER_CONTRACT_v1.json are present and structurally valid."""

    def test_manifest_exists(self):
        self.assertTrue(os.path.isfile(_MANIFEST))

    def test_schema_exists(self):
        self.assertTrue(os.path.isfile(_SCHEMA))

    def test_contract_exists(self):
        self.assertTrue(os.path.isfile(_CONTRACT))

    def test_manifest_is_valid_json(self):
        m = _load(_MANIFEST)
        self.assertIsInstance(m, dict)

    def test_schema_is_valid_json(self):
        s = _load(_SCHEMA)
        self.assertIsInstance(s, dict)

    def test_contract_is_valid_json(self):
        c = _load(_CONTRACT)
        self.assertIsInstance(c, dict)

    def test_manifest_cartridge_id_matches_runner(self):
        m = _load(_MANIFEST)
        self.assertEqual(m["cartridge_id"], _CARTRIDGE_ID)

    def test_manifest_stage_is_stage001(self):
        m = _load(_MANIFEST)
        self.assertEqual(m["stage"], "STAGE001")

    def test_manifest_has_scope_section(self):
        m = _load(_MANIFEST)
        self.assertIn("stage001_scope", m)
        self.assertIn("does", m["stage001_scope"])
        self.assertIn("does_not", m["stage001_scope"])

    def test_manifest_has_future_stages(self):
        """Stage001 manifest must document what future stages will cover."""
        m = _load(_MANIFEST)
        self.assertIn("future_stages", m)
        self.assertGreater(len(m["future_stages"]), 0)

    def test_manifest_future_stages_reference_ledger(self):
        """Future stages must reference ledger feed (Stage002) explicitly."""
        m = _load(_MANIFEST)
        combined = " ".join(m["future_stages"]).lower()
        self.assertIn("ledger", combined,
                      "future_stages must document the ledger-feed stage (Stage002+)")

    def test_manifest_does_not_claim_does_access_mnt_data(self):
        """does[] list must not claim /mnt/data access."""
        m = _load(_MANIFEST)
        for item in m["stage001_scope"]["does"]:
            self.assertNotIn("/mnt/data", item)
            self.assertNotIn("mounted", item.lower())

    def test_manifest_does_not_reference_no_ledger_writes(self):
        """does_not[] list must explicitly say no ledger writes."""
        m = _load(_MANIFEST)
        combined = " ".join(m["stage001_scope"]["does_not"]).lower()
        self.assertIn("ledger", combined,
                      "does_not must explicitly state no ledger writes in Stage001")

    def test_schema_filter_condition(self):
        """Schema must document the filter condition for mining."""
        s = _load(_SCHEMA)
        self.assertIn("filter_condition", s)
        self.assertIn("PostToolUseFailure", s["filter_condition"])

    def test_contract_exit_codes_defined(self):
        c = _load(_CONTRACT)
        self.assertIn("exit_codes", c)
        self.assertIn("0", c["exit_codes"])
        self.assertIn("1", c["exit_codes"])

    def test_contract_guarantees_no_ledger_writes(self):
        c = _load(_CONTRACT)
        guarantees = " ".join(c.get("guarantees", [])).lower()
        self.assertIn("ledger", guarantees,
                      "Contract guarantees must explicitly cover no-ledger-writes")

    def test_contract_receipt_shape_matches_runner(self):
        """Contract receipt_shape keys must all appear in a real mine_stream receipt."""
        c = _load(_CONTRACT)
        shape_keys = set(c["receipt_shape"].keys())
        r = mine_stream([])
        runner_keys = set(r.keys())
        missing = shape_keys - runner_keys
        self.assertEqual(missing, set(),
                         f"Contract receipt_shape keys not in runner output: {missing}")


# ══════════════════════════════════════════════════════════════════════════════
class TestRunnerSubprocess(unittest.TestCase):
    """Subprocess tests — runner invoked the way it would be from CLI."""

    def test_runner_script_exists(self):
        self.assertTrue(os.path.isfile(_RUNNER_SCRIPT))

    def test_runner_single_failure_fixture_exit_0(self):
        rc, out = _run_runner(os.path.join(_FIXTURES, "single_tool_failure.jsonl"))
        self.assertEqual(rc, 0)
        self.assertEqual(out["failures_found"], 1)
        self.assertEqual(out["mapped"], 1)

    def test_runner_multi_failure_fixture_exit_0(self):
        rc, out = _run_runner(os.path.join(_FIXTURES, "multi_tool_failure.jsonl"))
        self.assertEqual(rc, 0)
        self.assertEqual(out["failures_found"], 3)
        self.assertEqual(out["mapped"], 3)

    def test_runner_no_failures_fixture_exit_0(self):
        rc, out = _run_runner(os.path.join(_FIXTURES, "no_tool_failures.jsonl"))
        self.assertEqual(rc, 0)
        self.assertEqual(out["failures_found"], 0)
        self.assertEqual(out["events"], [])

    def test_runner_malformed_fixture_exit_0(self):
        """Runner exits 0 even when fixture has bad JSON lines."""
        rc, out = _run_runner(os.path.join(_FIXTURES, "malformed_entry.jsonl"))
        self.assertEqual(rc, 0)
        self.assertGreater(out["parse_errors"], 0)

    def test_runner_dry_run_emits_empty_events(self):
        """--dry-run parses and counts but outputs events=[]."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--dry-run"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out["events"], [])
        self.assertTrue(out.get("dry_run"))
        self.assertEqual(out["failures_found"], 3)

    def test_runner_max_entries_flag(self):
        """--max-entries=1 processes only the first parsed entry."""
        rc, out = _run_runner(
            os.path.join(_FIXTURES, "multi_tool_failure.jsonl"),
            extra_args=["--max-entries", "1"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(out["entries_seen"], 1)

    def test_runner_output_to_file(self):
        """--output writes valid JSON receipt to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            rc, _ = _run_runner(
                os.path.join(_FIXTURES, "single_tool_failure.jsonl"),
                extra_args=["--output", tmp_path],
            )
            self.assertEqual(rc, 0)
            with open(tmp_path, encoding="utf-8") as f:
                receipt = json.load(f)
            self.assertEqual(receipt["mapped"], 1)
        finally:
            os.unlink(tmp_path)

    def test_runner_nonexistent_input_exits_1(self):
        """--input pointing to a missing file exits 1."""
        rc, _ = _run_runner("/tmp/this_file_does_not_exist_fixture_xyz.jsonl")
        self.assertEqual(rc, 1)

    def test_runner_stdin_mode_empty_exits_0(self):
        """Empty stdin → exits 0 with zero-count receipt."""
        rc, out = _run_runner(None, stdin_text="")
        self.assertEqual(rc, 0)
        self.assertEqual(out["entries_seen"], 0)
        self.assertEqual(out["events"], [])

    def test_runner_receipt_cartridge_id(self):
        rc, out = _run_runner(os.path.join(_FIXTURES, "single_tool_failure.jsonl"))
        self.assertEqual(out["cartridge_id"], "CHAT790_EXPORT_MINING_CARTRIDGE")

    def test_runner_receipt_runner_stage(self):
        rc, out = _run_runner(os.path.join(_FIXTURES, "single_tool_failure.jsonl"))
        self.assertEqual(out["runner_stage"], "STAGE001")

    def test_runner_events_have_fingerprint_fields(self):
        """All events in receipt have non-empty FINGERPRINT_FIELDS."""
        rc, out = _run_runner(os.path.join(_FIXTURES, "single_tool_failure.jsonl"))
        self.assertEqual(rc, 0)
        for event in out["events"]:
            for field in FINGERPRINT_FIELDS:
                self.assertIn(field, event, f"event missing field: {field}")
                self.assertTrue(event[field], f"event has empty field: {field}")

    def test_runner_events_have_no_decision_field(self):
        """Stage001 runner does not call classify(); events must have no 'decision' key."""
        rc, out = _run_runner(os.path.join(_FIXTURES, "multi_tool_failure.jsonl"))
        self.assertEqual(rc, 0)
        for event in out["events"]:
            self.assertNotIn("decision", event,
                             "Stage001 events must not contain recurrence decisions")


# ══════════════════════════════════════════════════════════════════════════════
class TestExistingSuiteNotBroken(unittest.TestCase):
    """Regression guard: all three prior test suites still pass."""

    def _run_suite(self, script):
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, cwd=_REPO_ROOT,
        )
        return result.returncode, result.stderr

    def test_tool_routing_and_blocker_ledger_suite_still_passes(self):
        rc, err = self._run_suite(
            os.path.join(_REPO_ROOT, "tests", "test_tool_routing_and_blocker_ledger.py")
        )
        self.assertEqual(rc, 0, f"test_tool_routing_and_blocker_ledger failed:\n{err}")

    def test_hook_activation_suite_still_passes(self):
        rc, err = self._run_suite(
            os.path.join(_REPO_ROOT, "tests", "test_hook_activation.py")
        )
        self.assertEqual(rc, 0, f"test_hook_activation failed:\n{err}")

    def test_post_tool_failure_adapter_suite_still_passes(self):
        rc, err = self._run_suite(
            os.path.join(_REPO_ROOT, "tests", "test_post_tool_failure_adapter.py")
        )
        self.assertEqual(rc, 0, f"test_post_tool_failure_adapter failed:\n{err}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
