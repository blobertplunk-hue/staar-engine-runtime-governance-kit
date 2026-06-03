"""
Tests for META_TOOL_ROUTER_AND_REPEATED_BLOCKER_LEDGER_STAGE001.

Runnable with:
  python3 -m pytest tests/test_tool_routing_and_blocker_ledger.py
  python3 tests/test_tool_routing_and_blocker_ledger.py   (stdlib runner fallback)

Imports the guard modules directly so no subprocess is needed and tests are
deterministic without touching the filesystem ledger.
"""
import json
import os
import sys
import tempfile
import unittest

# Ensure repo root is on path for consistent imports
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

import governance.tool_routing.tool_route_guard as trg
import governance.blocker_ledger.repeated_blocker_guard as rbg

FIXTURES_TOOL = os.path.join(_REPO_ROOT, "tests", "fixtures", "tool_routing")
FIXTURES_BLOCKER = os.path.join(_REPO_ROOT, "tests", "fixtures", "blocker_ledger")
SCHEMA_PATH = os.path.join(
    _REPO_ROOT, "governance", "blocker_ledger",
    "REPEATED_BLOCKER_LEDGER_SCHEMA_v1.json"
)


def _load(path):
    with open(path) as fh:
        return json.load(fh)


class TestToolRouteGuard(unittest.TestCase):

    def setUp(self):
        self.policy = trg.load_policy()

    # ── fixture: blocked_mnt_data_file_search ──────────────────────────────

    def test_blocked_mnt_data_file_search_fixture_valid(self):
        """Fixture JSON is well-formed and contains required fields."""
        fx = _load(os.path.join(FIXTURES_TOOL, "blocked_mnt_data_file_search.json"))
        self.assertIn("input", fx)
        self.assertIn("expected", fx)
        self.assertEqual(fx["expected"]["decision"], "BLOCKED")

    def test_blocked_mnt_data_file_search(self):
        """file_search for /mnt/data/Metablooms_OS must be BLOCKED."""
        fx = _load(os.path.join(FIXTURES_TOOL, "blocked_mnt_data_file_search.json"))
        result = trg.route(
            fx["input"]["tool_name"],
            fx["input"]["tool_input"],
            self.policy,
        )
        self.assertEqual(result["decision"], fx["expected"]["decision"])
        self.assertTrue(result["forbidden_tool_check"])
        self.assertEqual(result["input_classification"],
                         fx["expected"]["input_classification"])

    # ── fixture: allowed_uploaded_semantic_query ───────────────────────────

    def test_allowed_uploaded_semantic_query_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_TOOL, "allowed_uploaded_semantic_query.json"))
        self.assertIn("input", fx)
        self.assertEqual(fx["expected"]["decision"], "ALLOW_WHEN_EXPLICITLY_APPROPRIATE")

    def test_allowed_uploaded_semantic_query(self):
        """file_search for uploaded semantic document (no mounted path) must be ALLOW_WHEN_EXPLICITLY_APPROPRIATE."""
        fx = _load(os.path.join(FIXTURES_TOOL, "allowed_uploaded_semantic_query.json"))
        result = trg.route(
            fx["input"]["tool_name"],
            fx["input"]["tool_input"],
            self.policy,
        )
        self.assertEqual(result["decision"], fx["expected"]["decision"])
        self.assertFalse(result["forbidden_tool_check"])
        self.assertEqual(result["input_classification"],
                         fx["expected"]["input_classification"])

    # ── regression: explicit-domain bypass ────────────────────────────────

    def test_explicit_domain_bypass_blocked_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_TOOL, "explicit_domain_bypass_blocked.json"))
        self.assertEqual(fx["expected"]["decision"], "BLOCKED")

    def test_explicit_domain_bypass_blocked(self):
        """domain=uploaded_semantic_document_query with target_path=/mnt/data must still BLOCK.

        Mounted-path detection dominates explicit domain field; no bypass is possible."""
        fx = _load(os.path.join(FIXTURES_TOOL, "explicit_domain_bypass_blocked.json"))
        result = trg.route(
            fx["input"]["tool_name"],
            fx["input"]["tool_input"],
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED",
                         "Mounted-path detection must win over explicit domain field")
        self.assertEqual(result["input_classification"], "mounted_mnt_data_os_artifact_truth")

    def test_explicit_domain_bypass_via_query_field(self):
        """domain=uploaded_semantic_document_query with /mnt/data in query string must still BLOCK."""
        result = trg.route(
            "file_search",
            {
                "domain": "uploaded_semantic_document_query",
                "uploaded": True,
                "query": "summarize /mnt/data/Metablooms_OS boot log",
            },
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")

    # ── regression: namespaced file_search canonicalization ───────────────

    def test_namespaced_file_search_blocked_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_TOOL, "namespaced_file_search_blocked.json"))
        self.assertEqual(fx["expected"]["decision"], "BLOCKED")
        self.assertEqual(fx["expected"]["selected_tool"], "file_search")

    def test_namespaced_file_search_blocked(self):
        """file_search.msearch canonicalizes to file_search and is BLOCKED for mounted paths."""
        fx = _load(os.path.join(FIXTURES_TOOL, "namespaced_file_search_blocked.json"))
        result = trg.route(
            fx["input"]["tool_name"],
            fx["input"]["tool_input"],
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["selected_tool"], "file_search",
                         "Namespaced tool must be canonicalized to 'file_search'")

    def test_various_file_search_aliases_all_blocked(self):
        """Multiple file_search name variants all canonicalize and block on mounted paths."""
        variants = [
            "file_search.msearch",
            "openai.file_search",
            "file_search.v2",
            "FILE_SEARCH",
        ]
        input_ = {"target_path": "/mnt/data/Metablooms_OS"}
        for name in variants:
            with self.subTest(tool_name=name):
                result = trg.route(name, input_, self.policy)
                self.assertEqual(result["decision"], "BLOCKED",
                                 f"'{name}' should be canonicalized and blocked")
                self.assertEqual(result["selected_tool"], "file_search")

    def test_non_file_search_alias_not_collapsed(self):
        """A tool with 'search' in its name but not 'file_search' is not collapsed."""
        result = trg.route(
            "web_search",
            {"query": "STAAR governance schema"},
            self.policy,
        )
        self.assertNotEqual(result.get("selected_tool"), "file_search")

    # ── regression: recursive nested-path scanning ────────────────────────

    def test_nested_mnt_data_in_queries_array_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_TOOL, "nested_mnt_data_in_queries_array_blocked.json"))
        self.assertEqual(fx["expected"]["decision"], "BLOCKED")

    def test_nested_mnt_data_in_queries_array_blocked(self):
        """Mounted path buried in queries[] array must BLOCK."""
        fx = _load(os.path.join(FIXTURES_TOOL, "nested_mnt_data_in_queries_array_blocked.json"))
        result = trg.route(
            fx["input"]["tool_name"],
            fx["input"]["tool_input"],
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["input_classification"], "mounted_mnt_data_os_artifact_truth")

    def test_nested_mnt_data_in_deeply_nested_dict_blocked(self):
        """Mounted path in a nested dict value must BLOCK."""
        result = trg.route(
            "file_search",
            {"options": {"filter": {"path": "/mnt/data/Metablooms_OS/archive.zip"}}},
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")

    def test_queries_array_without_mounted_path_not_blocked(self):
        """queries[] with no mounted paths must not BLOCK."""
        result = trg.route(
            "file_search",
            {"queries": ["what is the governance schema?", "list receipts"]},
            self.policy,
        )
        self.assertNotEqual(result["decision"], "BLOCKED")

    # ── existing coverage ─────────────────────────────────────────────────

    def test_path_field_also_triggers_block(self):
        """Mounted path in 'path' field (not 'target_path') also triggers block."""
        result = trg.route(
            "file_search",
            {"path": "/mnt/data/Metablooms_OS/scripts/mpp/mpp.sh"},
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")

    def test_query_field_triggers_block(self):
        """Mounted path reference in 'query' field triggers block."""
        result = trg.route(
            "file_search",
            {"query": "find mpp.sh in /mnt/data/Metablooms_OS"},
            self.policy,
        )
        self.assertEqual(result["decision"], "BLOCKED")

    def test_non_file_search_tool_on_mounted_path_not_blocked(self):
        """sha256sum on /mnt/data path is allowed (file_search is the forbidden tool)."""
        result = trg.route(
            "sha256sum",
            {"target_path": "/mnt/data/Metablooms_OS/scripts/mpp/mpp.sh"},
            self.policy,
        )
        self.assertNotEqual(result["decision"], "BLOCKED")

    def test_unrelated_file_search_not_blocked(self):
        """file_search with no mounted-path reference should not be blocked."""
        result = trg.route(
            "file_search",
            {"query": "what is the STAAR governance schema version?"},
            self.policy,
        )
        self.assertNotEqual(result["decision"], "BLOCKED")


class TestRepeatedBlockerGuard(unittest.TestCase):

    # ── fixture: first_blocker_logs ────────────────────────────────────────

    def test_first_blocker_logs_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_BLOCKER, "first_blocker_logs.json"))
        self.assertIn("input", fx)
        self.assertEqual(fx["expected"]["decision"], "LOG_ONLY")

    def test_first_blocker_logs(self):
        """First occurrence of a normalized blocker → LOG_ONLY, no RCA."""
        fx = _load(os.path.join(FIXTURES_BLOCKER, "first_blocker_logs.json"))
        ledger = {"entries": {}}
        result = rbg.classify(
            fx["input"]["event"],
            ledger,
            ledger_path="<test-no-write>",
            write=False,
        )
        self.assertEqual(result["decision"], fx["expected"]["decision"])
        self.assertFalse(result["rca_required"])
        self.assertEqual(result["occurrence_count"], fx["expected"]["occurrence_count"])
        self.assertFalse(result["changed_inputs"])

    # ── fixture: repeat_blocker_forces_rca ────────────────────────────────

    def test_repeat_blocker_forces_rca_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_BLOCKER, "repeat_blocker_forces_rca.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "FORCE_RCA")

    def test_repeat_blocker_forces_rca(self):
        """Same normalized blocker twice with unchanged inputs → FORCE_RCA on second."""
        fx = _load(os.path.join(FIXTURES_BLOCKER, "repeat_blocker_forces_rca.json"))
        ledger = {"entries": {}}

        r1 = rbg.classify(fx["event"], ledger, "<test>", write=False)
        self.assertEqual(r1["decision"], fx["pass1_expected"]["decision"])
        self.assertEqual(r1["occurrence_count"], fx["pass1_expected"]["occurrence_count"])

        r2 = rbg.classify(fx["event"], ledger, "<test>", write=False)
        self.assertEqual(r2["decision"], fx["pass2_expected"]["decision"])
        self.assertTrue(r2["rca_required"])
        self.assertEqual(r2["occurrence_count"], fx["pass2_expected"]["occurrence_count"])

    # ── fixture: changed_inputs_not_repeat ────────────────────────────────

    def test_changed_inputs_not_repeat_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_BLOCKER, "changed_inputs_not_repeat.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "LOG_NEW_VARIANT")

    def test_changed_inputs_not_repeat(self):
        """Same blocker_type/operation but changed input_digest → LOG_NEW_VARIANT, not FORCE_RCA."""
        fx = _load(os.path.join(FIXTURES_BLOCKER, "changed_inputs_not_repeat.json"))
        ledger = {"entries": {}}

        r1 = rbg.classify(fx["event_pass1"], ledger, "<test>", write=False)
        self.assertEqual(r1["decision"], fx["pass1_expected"]["decision"])
        self.assertFalse(r1["rca_required"])

        r2 = rbg.classify(fx["event_pass2"], ledger, "<test>", write=False)
        self.assertEqual(r2["decision"], fx["pass2_expected"]["decision"])
        self.assertFalse(r2["rca_required"])
        self.assertTrue(r2["changed_inputs"])
        self.assertEqual(r2["occurrence_count"], fx["pass2_expected"]["occurrence_count"])

    # ── fingerprint stability ──────────────────────────────────────────────

    def test_timestamp_normalization_same_fingerprint(self):
        """Events differing only in volatile timestamps get the same fingerprint."""
        e1 = {
            "blocker_type": "tool_denied",
            "component": "tool_route_guard",
            "operation": "file_search",
            "normalized_command": "file_search /mnt/data 2026-06-03T12:00:00Z",
            "target_path": "/mnt/data",
            "input_digest": "aaa",
            "evidence_digest": "bbb",
        }
        e2 = dict(e1)
        e2["normalized_command"] = "file_search /mnt/data 2026-06-04T09:30:00Z"
        self.assertEqual(rbg.compute_fingerprint(e1), rbg.compute_fingerprint(e2))

    def test_input_digest_not_in_fingerprint(self):
        """input_digest/evidence_digest are NOT identity fingerprint fields; changing them
        keeps the same fingerprint. Changed-inputs detection uses ledger comparison."""
        e1 = {
            "blocker_type": "tool_denied",
            "component": "c",
            "operation": "op",
            "normalized_command": "cmd",
            "target_path": "/x",
            "input_digest": "digest_A",
            "evidence_digest": "ev_A",
        }
        e2 = dict(e1, input_digest="digest_B", evidence_digest="ev_B")
        self.assertEqual(rbg.compute_fingerprint(e1), rbg.compute_fingerprint(e2),
                         "variant_fields must not affect identity fingerprint")

    def test_different_operation_different_fingerprint(self):
        """Events with different identity fields produce different fingerprints."""
        e1 = {
            "blocker_type": "tool_denied",
            "component": "c",
            "operation": "file_search",
            "normalized_command": "cmd",
            "target_path": "/x",
            "input_digest": "d",
            "evidence_digest": "e",
        }
        e2 = dict(e1, operation="web_fetch")
        self.assertNotEqual(rbg.compute_fingerprint(e1), rbg.compute_fingerprint(e2))

    def test_ledger_write_read_roundtrip(self):
        """Ledger written to temp file can be reloaded and produces correct second-pass decision."""
        event = {
            "blocker_type": "tool_denied",
            "component": "tool_route_guard",
            "operation": "file_search",
            "normalized_command": "file_search /mnt/data/Metablooms_OS mpp.sh",
            "target_path": "/mnt/data/Metablooms_OS",
            "input_digest": "stable_digest_123",
            "evidence_digest": "stable_evidence_456",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "test_ledger.json")

            ledger1 = rbg.load_ledger(ledger_path)
            r1 = rbg.classify(event, ledger1, ledger_path, write=True)
            self.assertEqual(r1["decision"], "LOG_ONLY")

            ledger2 = rbg.load_ledger(ledger_path)
            r2 = rbg.classify(event, ledger2, ledger_path, write=True)
            self.assertEqual(r2["decision"], "FORCE_RCA")
            self.assertTrue(r2["rca_required"])


class TestPolicySchemaCoverage(unittest.TestCase):
    """Ensure policy JSON covers all domains referenced in GATES_AND_FIXTURES_SPEC."""

    def test_policy_has_required_domains(self):
        policy = trg.load_policy()
        domains = {r["domain"] for r in policy["routes"]}
        required = {
            "mounted_mnt_data_os_artifact_truth",
            "github_repo_state",
            "external_current_evidence",
            "uploaded_semantic_document_query",
        }
        self.assertTrue(required.issubset(domains),
                        f"Missing domains: {required - domains}")

    def test_file_search_forbidden_only_for_mounted(self):
        policy = trg.load_policy()
        for r in policy["routes"]:
            if r["domain"] != "mounted_mnt_data_os_artifact_truth":
                self.assertNotIn(
                    "file_search", r.get("forbidden_tools", []),
                    f"file_search should only be forbidden for mounted domain, "
                    f"not '{r['domain']}'",
                )

    # ── regression: schema-vs-implementation consistency ──────────────────

    def test_schema_identity_fingerprint_fields_match_implementation(self):
        """REPEATED_BLOCKER_LEDGER_SCHEMA_v1.json identity_fingerprint_fields must
        exactly match repeated_blocker_guard.FINGERPRINT_FIELDS."""
        schema = _load(SCHEMA_PATH)
        schema_fields = set(schema["identity_fingerprint_fields"])
        impl_fields = set(rbg.FINGERPRINT_FIELDS)
        self.assertEqual(
            schema_fields, impl_fields,
            f"Schema identity_fingerprint_fields {schema_fields} "
            f"!= implementation FINGERPRINT_FIELDS {impl_fields}",
        )

    def test_schema_variant_fields_not_in_fingerprint(self):
        """variant_fields in schema must NOT be in implementation FINGERPRINT_FIELDS."""
        schema = _load(SCHEMA_PATH)
        variant_fields = set(schema["variant_fields"])
        impl_fields = set(rbg.FINGERPRINT_FIELDS)
        overlap = variant_fields & impl_fields
        self.assertFalse(
            overlap,
            f"variant_fields {overlap} should not appear in FINGERPRINT_FIELDS",
        )

    def test_schema_has_identity_and_variant_field_keys(self):
        """Schema must use identity_fingerprint_fields / variant_fields (not the old fingerprint_fields)."""
        schema = _load(SCHEMA_PATH)
        self.assertIn("identity_fingerprint_fields", schema,
                      "Schema must have 'identity_fingerprint_fields' key")
        self.assertIn("variant_fields", schema,
                      "Schema must have 'variant_fields' key")
        self.assertNotIn("fingerprint_fields", schema,
                         "Old 'fingerprint_fields' key must not exist in updated schema")


if __name__ == "__main__":
    # stdlib runner fallback (pytest not required)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
