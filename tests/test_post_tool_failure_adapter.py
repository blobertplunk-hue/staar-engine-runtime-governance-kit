"""
Tests for CHAT790_FORMAT_ADAPTER_AND_LEDGER_GITIGNORE:
  post_tool_failure_adapter.py mapping and end-to-end subprocess behaviour.

Runnable with:
  python3 -m pytest tests/test_post_tool_failure_adapter.py
  python3 tests/test_post_tool_failure_adapter.py   (stdlib runner fallback)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import governance.blocker_ledger.post_tool_failure_adapter as adapter
import governance.blocker_ledger.repeated_blocker_guard as rbg

ADAPTER_SCRIPT = os.path.join(
    _REPO_ROOT, "governance", "blocker_ledger", "post_tool_failure_adapter.py"
)
FIXTURES_ADAPTER = os.path.join(_REPO_ROOT, "tests", "fixtures", "adapter")


def _load(path):
    with open(path) as fh:
        return json.load(fh)


def _run_adapter(stdin_obj, extra_args=None, cwd=_REPO_ROOT, timeout=10):
    """Invoke the adapter via subprocess; return (exit_code, parsed_stdout)."""
    args = [sys.executable, ADAPTER_SCRIPT, "--hook-stdin"] + (extra_args or [])
    proc = subprocess.run(
        args,
        input=json.dumps(stdin_obj),
        capture_output=True, text=True, cwd=cwd, timeout=timeout,
    )
    out = {}
    if proc.stdout.strip():
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return proc.returncode, out


# ── Sample payloads used across multiple tests ─────────────────────────────

_RAW_FILE_SEARCH_PAYLOAD = {
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "file_search",
    "tool_input": {
        "query": "mpp.sh turn-boot",
        "target_path": "/mnt/data/Metablooms_OS",
    },
    "tool_response": "Error: file_search forbidden for mounted OS artifacts",
    "session_id": "unit-test-session",
}

_RAW_BASH_PAYLOAD = {
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "bash",
    "tool_input": {"command": "cat /mnt/data/Metablooms_OS/scripts/mpp/mpp.sh"},
    "tool_response": "cat: /mnt/data/...: Permission denied",
    "session_id": "unit-test-session",
}


class TestAdapterMapping(unittest.TestCase):
    """Unit tests for map_payload() and adapt_and_classify() logic."""

    # ── fixture: raw_cc_payload_mapped_to_blocker ─────────────────────────

    def test_raw_cc_payload_mapped_to_blocker_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_mapped_to_blocker.json"))
        self.assertIn("raw_payload", fx)
        self.assertEqual(fx["expected_adapter_status"], "MAPPED")

    def test_map_payload_produces_all_fingerprint_fields(self):
        """Mapped event contains every FINGERPRINT_FIELD and none are empty."""
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_mapped_to_blocker.json"))
        event, status = adapter.map_payload(fx["raw_payload"])
        self.assertEqual(status, "MAPPED")
        for field in rbg.FINGERPRINT_FIELDS:
            self.assertIn(field, event, f"Missing fingerprint field: {field}")
            self.assertNotEqual(
                event[field], "",
                f"Fingerprint field '{field}' must not be empty after mapping",
            )

    def test_map_payload_sets_correct_static_fields(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_mapped_to_blocker.json"))
        event, _ = adapter.map_payload(fx["raw_payload"])
        for field, expected in fx["expected_mapped_fields"].items():
            self.assertEqual(event[field], expected,
                             f"Field '{field}': expected {expected!r}, got {event[field]!r}")

    def test_map_payload_input_digest_is_sha256_hex(self):
        """input_digest must be a 64-char hex string."""
        event, status = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        self.assertEqual(status, "MAPPED")
        self.assertRegex(event["input_digest"], r"^[0-9a-f]{64}$",
                         "input_digest must be a full SHA-256 hex string")

    def test_map_payload_evidence_digest_is_sha256_hex(self):
        event, status = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        self.assertEqual(status, "MAPPED")
        self.assertRegex(event["evidence_digest"], r"^[0-9a-f]{64}$",
                         "evidence_digest must be a full SHA-256 hex string")

    def test_fingerprints_discriminate_by_tool_name(self):
        """Different tool_name → different fingerprint (operation is an identity field)."""
        e_fs, _ = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        e_bash, _ = adapter.map_payload(_RAW_BASH_PAYLOAD)
        fp_fs = rbg.compute_fingerprint(e_fs)
        fp_bash = rbg.compute_fingerprint(e_bash)
        self.assertNotEqual(fp_fs, fp_bash,
                            "Different tool_name must produce different fingerprints")

    def test_fingerprints_not_all_empty_collision(self):
        """Fingerprint of a mapped event must differ from the all-empty-fields fingerprint."""
        empty_event = {f: "" for f in rbg.FINGERPRINT_FIELDS}
        empty_fp = rbg.compute_fingerprint(empty_event)

        event, _ = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        real_fp = rbg.compute_fingerprint(event)
        self.assertNotEqual(real_fp, empty_fp,
                            "Mapped fingerprint must not collide with the all-empty fingerprint")

    def test_map_payload_same_input_same_fingerprint(self):
        """Identical CC payloads produce identical fingerprints (deterministic)."""
        e1, _ = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        e2, _ = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        self.assertEqual(rbg.compute_fingerprint(e1), rbg.compute_fingerprint(e2))

    def test_map_payload_different_tool_input_different_input_digest(self):
        """Different tool_input → different input_digest (changed-inputs detection)."""
        p1 = dict(_RAW_FILE_SEARCH_PAYLOAD)
        p1["tool_input"] = {"query": "version-alpha", "target_path": "/mnt/data/Metablooms_OS"}
        p2 = dict(_RAW_FILE_SEARCH_PAYLOAD)
        p2["tool_input"] = {"query": "version-beta", "target_path": "/mnt/data/Metablooms_OS"}
        e1, _ = adapter.map_payload(p1)
        e2, _ = adapter.map_payload(p2)
        self.assertNotEqual(e1["input_digest"], e2["input_digest"],
                            "Different tool_input must yield different input_digest")

    def test_same_tool_input_same_fingerprint_different_response_different_evidence(self):
        """Same tool_input → same fingerprint AND same input_digest;
        different tool_response → different evidence_digest."""
        p1 = dict(_RAW_FILE_SEARCH_PAYLOAD, tool_response="Error: version A")
        p2 = dict(_RAW_FILE_SEARCH_PAYLOAD, tool_response="Error: version B")
        e1, _ = adapter.map_payload(p1)
        e2, _ = adapter.map_payload(p2)
        self.assertEqual(rbg.compute_fingerprint(e1), rbg.compute_fingerprint(e2),
                         "Same structural fields must share fingerprint")
        self.assertEqual(e1["input_digest"], e2["input_digest"])
        self.assertNotEqual(e1["evidence_digest"], e2["evidence_digest"],
                            "Different tool_response must yield different evidence_digest")

    # ── pass-through ──────────────────────────────────────────────────────

    def test_already_adapted_event_passes_through(self):
        """If payload already has all FINGERPRINT_FIELDS, adapter returns PASS_THROUGH."""
        already = {
            "blocker_type": "tool_denied",
            "component": "tool_route_guard",
            "operation": "file_search",
            "normalized_command": "file_search /mnt/data/Metablooms_OS mpp.sh",
            "target_path": "/mnt/data/Metablooms_OS",
            "input_digest": "pre_adapted_digest",
            "evidence_digest": "pre_adapted_evidence",
        }
        event, status = adapter.map_payload(already)
        self.assertEqual(status, "PASS_THROUGH")
        self.assertEqual(event, already, "Pass-through must not mutate the event")

    # ── malformed payload ──────────────────────────────────────────────────

    def test_malformed_payload_returns_review_unmapped_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "malformed_payload_review.json"))
        self.assertEqual(fx["expected"]["decision"], "REVIEW_UNMAPPED_PAYLOAD")
        self.assertIsNone(fx["expected"]["fingerprint"])

    def test_malformed_payload_returns_review_unmapped(self):
        """Payload without tool_name → REVIEW_UNMAPPED_PAYLOAD, no fingerprint."""
        fx = _load(os.path.join(FIXTURES_ADAPTER, "malformed_payload_review.json"))
        ledger = {"entries": {}}
        result = adapter.adapt_and_classify(
            fx["raw_payload"], ledger, "<test-no-write>", write=False
        )
        self.assertEqual(result["decision"], "REVIEW_UNMAPPED_PAYLOAD")
        self.assertIsNone(result.get("fingerprint"))
        self.assertFalse(result.get("rca_required"))

    def test_empty_dict_returns_review_unmapped(self):
        """Empty dict payload → REVIEW_UNMAPPED_PAYLOAD."""
        ledger = {"entries": {}}
        result = adapter.adapt_and_classify({}, ledger, "<test>", write=False)
        self.assertEqual(result["decision"], "REVIEW_UNMAPPED_PAYLOAD")

    # ── adapt_and_classify in-memory tests ────────────────────────────────

    def test_first_raw_cc_payload_logs_only(self):
        """First occurrence of a raw CC payload → LOG_ONLY."""
        ledger = {"entries": {}}
        result = adapter.adapt_and_classify(
            _RAW_FILE_SEARCH_PAYLOAD, ledger, "<test>", write=False
        )
        self.assertEqual(result["decision"], "LOG_ONLY")
        self.assertFalse(result["rca_required"])
        self.assertEqual(result["occurrence_count"], 1)

    def test_repeat_raw_cc_payload_forces_rca(self):
        """Two identical raw CC payloads → LOG_ONLY then FORCE_RCA."""
        ledger = {"entries": {}}
        r1 = adapter.adapt_and_classify(
            _RAW_FILE_SEARCH_PAYLOAD, ledger, "<test>", write=False
        )
        self.assertEqual(r1["decision"], "LOG_ONLY")

        r2 = adapter.adapt_and_classify(
            _RAW_FILE_SEARCH_PAYLOAD, ledger, "<test>", write=False
        )
        self.assertEqual(r2["decision"], "FORCE_RCA")
        self.assertTrue(r2["rca_required"])
        self.assertEqual(r2["occurrence_count"], 2)

    def test_changed_tool_input_yields_log_new_variant(self):
        """Same tool, different tool_input → LOG_ONLY then LOG_NEW_VARIANT."""
        p1 = dict(_RAW_FILE_SEARCH_PAYLOAD)
        p1["tool_input"] = {"query": "variant-alpha", "target_path": "/mnt/data/Metablooms_OS"}
        p2 = dict(_RAW_FILE_SEARCH_PAYLOAD)
        p2["tool_input"] = {"query": "variant-beta", "target_path": "/mnt/data/Metablooms_OS"}

        ledger = {"entries": {}}
        r1 = adapter.adapt_and_classify(p1, ledger, "<test>", write=False)
        self.assertEqual(r1["decision"], "LOG_ONLY")

        r2 = adapter.adapt_and_classify(p2, ledger, "<test>", write=False)
        self.assertEqual(r2["decision"], "LOG_NEW_VARIANT")
        self.assertFalse(r2["rca_required"])
        self.assertTrue(r2["changed_inputs"])

    def test_target_path_extracted_from_tool_input(self):
        """target_path is extracted from tool_input.target_path."""
        event, _ = adapter.map_payload(_RAW_FILE_SEARCH_PAYLOAD)
        self.assertEqual(event["target_path"], "/mnt/data/Metablooms_OS")

    def test_target_path_fallback_to_path_key(self):
        """target_path falls back to tool_input['path'] when target_path absent."""
        p = {
            "tool_name": "read_file",
            "tool_input": {"path": "/some/file.txt"},
            "tool_response": "Error",
        }
        event, _ = adapter.map_payload(p)
        self.assertEqual(event["target_path"], "/some/file.txt")


class TestAdapterSubprocess(unittest.TestCase):
    """Subprocess tests — adapter invoked the same way Claude Code would."""

    def test_adapter_script_exists(self):
        self.assertTrue(os.path.isfile(ADAPTER_SCRIPT))

    # ── fixture: raw_cc_payload_repeat_forces_rca ─────────────────────────

    def test_raw_cc_payload_repeat_forces_rca_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_repeat_forces_rca.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "FORCE_RCA")

    def test_raw_cc_payload_repeat_forces_rca(self):
        """Two identical raw CC payloads via subprocess: LOG_ONLY then FORCE_RCA(exit 2)."""
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_repeat_forces_rca.json"))
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.json")
            extra = ["--mode", "record-or-route", "--ledger-path", ledger_path]

            rc1, out1 = _run_adapter(fx["raw_payload"], extra)
            self.assertEqual(rc1, fx["pass1_expected"]["exit_code"],
                             f"pass1: expected exit {fx['pass1_expected']['exit_code']}, got {rc1}")
            self.assertEqual(out1.get("decision"), fx["pass1_expected"]["decision"])
            self.assertEqual(out1.get("occurrence_count"),
                             fx["pass1_expected"]["occurrence_count"])

            rc2, out2 = _run_adapter(fx["raw_payload"], extra)
            self.assertEqual(rc2, fx["pass2_expected"]["exit_code"],
                             f"pass2: expected exit {fx['pass2_expected']['exit_code']}, got {rc2}")
            self.assertEqual(out2.get("decision"), fx["pass2_expected"]["decision"])
            self.assertTrue(out2.get("rca_required"))

    # ── fixture: raw_cc_payload_changed_input_variant ─────────────────────

    def test_raw_cc_payload_changed_input_variant_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_changed_input_variant.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "LOG_NEW_VARIANT")

    def test_raw_cc_payload_changed_input_variant(self):
        """Different tool_input between calls: LOG_ONLY then LOG_NEW_VARIANT (exit 0 both)."""
        fx = _load(os.path.join(FIXTURES_ADAPTER, "raw_cc_payload_changed_input_variant.json"))
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.json")
            extra = ["--mode", "record-or-route", "--ledger-path", ledger_path]

            rc1, out1 = _run_adapter(fx["raw_payload_pass1"], extra)
            self.assertEqual(rc1, fx["pass1_expected"]["exit_code"])
            self.assertEqual(out1.get("decision"), fx["pass1_expected"]["decision"])

            rc2, out2 = _run_adapter(fx["raw_payload_pass2"], extra)
            self.assertEqual(rc2, fx["pass2_expected"]["exit_code"])
            self.assertEqual(out2.get("decision"), fx["pass2_expected"]["decision"])
            self.assertFalse(out2.get("rca_required"))
            self.assertTrue(out2.get("changed_inputs"))

    # ── fixture: malformed_payload_review ─────────────────────────────────

    def test_malformed_payload_review_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_ADAPTER, "malformed_payload_review.json"))
        self.assertEqual(fx["expected"]["decision"], "REVIEW_UNMAPPED_PAYLOAD")
        self.assertEqual(fx["expected"]["exit_code"], 0)

    def test_malformed_payload_exits_0_review_unmapped(self):
        """Malformed payload exits 0 with REVIEW_UNMAPPED_PAYLOAD — does not crash."""
        fx = _load(os.path.join(FIXTURES_ADAPTER, "malformed_payload_review.json"))
        rc, out = _run_adapter(fx["raw_payload"],
                               ["--mode", "classify-only"])
        self.assertEqual(rc, fx["expected"]["exit_code"],
                         f"Expected exit 0 for unmappable payload, got {rc}")
        self.assertEqual(out.get("decision"), fx["expected"]["decision"])
        self.assertFalse(out.get("rca_required", True))

    # ── additional subprocess coverage ────────────────────────────────────

    def test_adapter_mapped_status_in_output(self):
        """adapter_status=MAPPED present in stdout for a valid CC payload."""
        rc, out = _run_adapter(_RAW_FILE_SEARCH_PAYLOAD, ["--mode", "classify-only"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("adapter_status"), "MAPPED")

    def test_pass_through_adapted_event(self):
        """Pre-adapted blocker event passes through with adapter_status=PASS_THROUGH."""
        already = {
            "blocker_type": "tool_denied",
            "component": "tool_route_guard",
            "operation": "file_search",
            "normalized_command": "file_search /mnt/data mpp.sh",
            "target_path": "/mnt/data/Metablooms_OS",
            "input_digest": "pre_digest_xxx",
            "evidence_digest": "pre_evidence_yyy",
        }
        rc, out = _run_adapter({"event": already, "ledger": {"entries": {}}},
                               ["--mode", "classify-only"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.get("adapter_status"), "PASS_THROUGH")
        self.assertEqual(out.get("decision"), "LOG_ONLY")

    def test_parse_error_exits_0_review_unmapped(self):
        """A non-JSON stdin must exit 0 with REVIEW_UNMAPPED_PAYLOAD (not crash)."""
        proc = subprocess.run(
            [sys.executable, ADAPTER_SCRIPT, "--hook-stdin", "--mode", "classify-only"],
            input="this is not valid json {{{",
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
        )
        self.assertEqual(proc.returncode, 0,
                         f"Non-JSON stdin must exit 0. stderr: {proc.stderr}")
        out = json.loads(proc.stdout) if proc.stdout.strip() else {}
        self.assertEqual(out.get("decision"), "REVIEW_UNMAPPED_PAYLOAD")
        self.assertEqual(out.get("adapter_status"), "PARSE_ERROR")


class TestExistingSuiteNotBroken(unittest.TestCase):
    """Smoke-check that the existing test suites still pass with the adapter in place."""

    def _run_suite(self, suite_path, timeout=60):
        proc = subprocess.run(
            [sys.executable, suite_path],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_tool_routing_and_blocker_ledger_suite_still_passes(self):
        rc, stdout, _ = self._run_suite(
            os.path.join(_REPO_ROOT, "tests", "test_tool_routing_and_blocker_ledger.py")
        )
        self.assertEqual(rc, 0,
                         f"test_tool_routing_and_blocker_ledger.py failed:\n{stdout}")

    def test_hook_activation_suite_still_passes(self):
        rc, stdout, _ = self._run_suite(
            os.path.join(_REPO_ROOT, "tests", "test_hook_activation.py")
        )
        self.assertEqual(rc, 0,
                         f"test_hook_activation.py failed:\n{stdout}")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
