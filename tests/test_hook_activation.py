"""
Tests for BOOT_ROOT_REPAIR_AND_CHAT790_LESSONS_STAGE001 hook activation.

Validates that .claude/settings.json is correctly structured and that the
guard scripts behave correctly when invoked via subprocess (simulating the
Claude Code hook execution path).

Runnable with:
  python3 -m pytest tests/test_hook_activation.py
  python3 tests/test_hook_activation.py   (stdlib runner fallback)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(_REPO_ROOT, ".claude", "settings.json")
FIXTURES_HOOK = os.path.join(_REPO_ROOT, "tests", "fixtures", "hook_activation")
ROUTE_GUARD = os.path.join(_REPO_ROOT, "governance", "tool_routing", "tool_route_guard.py")
BLOCKER_GUARD = os.path.join(_REPO_ROOT, "governance", "blocker_ledger", "repeated_blocker_guard.py")
VALIDATOR = os.path.join(_REPO_ROOT, "governance", "tool_routing", "hook_install_validator.py")


def _load(path):
    with open(path) as fh:
        return json.load(fh)


def _run_hook(script, args, stdin_obj, cwd=_REPO_ROOT, timeout=10):
    """Invoke a hook script via subprocess and return (exit_code, parsed_stdout)."""
    proc = subprocess.run(
        [sys.executable, script] + args,
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


class TestSettingsJsonStructure(unittest.TestCase):
    """Structural validation of .claude/settings.json."""

    def test_settings_json_exists(self):
        self.assertTrue(os.path.isfile(SETTINGS_PATH),
                        f".claude/settings.json not found at {SETTINGS_PATH}")

    def test_settings_json_is_valid_json(self):
        with open(SETTINGS_PATH) as fh:
            cfg = json.load(fh)
        self.assertIsInstance(cfg, dict)

    def test_settings_has_hooks_key(self):
        cfg = _load(SETTINGS_PATH)
        self.assertIn("hooks", cfg, "settings.json must have a 'hooks' key")

    def test_pre_tool_use_hook_present(self):
        cfg = _load(SETTINGS_PATH)
        hooks = cfg.get("hooks", {})
        self.assertIn("PreToolUse", hooks, "PreToolUse hook must be configured")
        cmds = [h["command"] for e in hooks["PreToolUse"] for h in e.get("hooks", [])]
        self.assertTrue(
            any("tool_route_guard.py" in c for c in cmds),
            f"tool_route_guard.py not referenced in PreToolUse hooks: {cmds}",
        )

    def test_post_tool_use_failure_hook_present(self):
        cfg = _load(SETTINGS_PATH)
        hooks = cfg.get("hooks", {})
        self.assertIn("PostToolUseFailure", hooks,
                      "PostToolUseFailure hook must be configured")
        cmds = [h["command"] for e in hooks["PostToolUseFailure"] for h in e.get("hooks", [])]
        self.assertTrue(
            any("post_tool_failure_adapter.py" in c for c in cmds),
            f"post_tool_failure_adapter.py not referenced in PostToolUseFailure hooks: {cmds}",
        )

    def test_guard_scripts_exist_on_disk(self):
        self.assertTrue(os.path.isfile(ROUTE_GUARD),
                        f"tool_route_guard.py not found at {ROUTE_GUARD}")
        self.assertTrue(os.path.isfile(BLOCKER_GUARD),
                        f"repeated_blocker_guard.py not found at {BLOCKER_GUARD}")


class TestHookInstallValidator(unittest.TestCase):
    """hook_install_validator.py must pass all structural checks."""

    def test_validator_script_exists(self):
        self.assertTrue(os.path.isfile(VALIDATOR))

    def test_validator_passes(self):
        proc = subprocess.run(
            [sys.executable, VALIDATOR],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=30,
        )
        self.assertEqual(proc.returncode, 0,
                         f"hook_install_validator.py failed:\n{proc.stdout}\n{proc.stderr}")


class TestToolRouteGuardHookPath(unittest.TestCase):
    """Subprocess tests for tool_route_guard.py invoked as a PreToolUse hook."""

    # ── fixture: hook_blocked_mnt_data_file_search ─────────────────────────

    def test_hook_blocked_mnt_data_file_search_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_blocked_mnt_data_file_search.json"))
        self.assertEqual(fx["expected"]["exit_code"], 1)
        self.assertEqual(fx["expected"]["decision"], "BLOCKED")

    def test_hook_blocked_mnt_data_file_search(self):
        """Hook subprocess exit 1 + BLOCKED for file_search on /mnt/data."""
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_blocked_mnt_data_file_search.json"))
        rc, out = _run_hook(ROUTE_GUARD, fx["hook_args"], fx["stdin"])
        self.assertEqual(rc, fx["expected"]["exit_code"],
                         f"Expected exit {fx['expected']['exit_code']}, got {rc}. stdout: {out}")
        self.assertEqual(out.get("decision"), fx["expected"]["decision"])
        self.assertTrue(out.get("forbidden_tool_check"))
        self.assertEqual(out.get("input_classification"),
                         fx["expected"]["input_classification"])

    # ── fixture: hook_allowed_uploaded_semantic_query ──────────────────────

    def test_hook_allowed_uploaded_semantic_query_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_allowed_uploaded_semantic_query.json"))
        self.assertEqual(fx["expected"]["exit_code"], 0)
        self.assertEqual(fx["expected"]["decision"], "ALLOW_WHEN_EXPLICITLY_APPROPRIATE")

    def test_hook_allowed_uploaded_semantic_query(self):
        """Hook subprocess exit 0 + ALLOW_WHEN_EXPLICITLY_APPROPRIATE for uploaded semantic query."""
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_allowed_uploaded_semantic_query.json"))
        rc, out = _run_hook(ROUTE_GUARD, fx["hook_args"], fx["stdin"])
        self.assertEqual(rc, fx["expected"]["exit_code"],
                         f"Expected exit 0, got {rc}. stdout: {out}")
        self.assertEqual(out.get("decision"), fx["expected"]["decision"])
        self.assertFalse(out.get("forbidden_tool_check"))

    # ── additional hook coverage ───────────────────────────────────────────

    def test_hook_explicit_domain_bypass_still_blocked(self):
        """domain=uploaded_semantic_document_query with /mnt/data path must still exit 1."""
        rc, out = _run_hook(ROUTE_GUARD, ["--hook-stdin"], {
            "tool_name": "file_search",
            "tool_input": {
                "domain": "uploaded_semantic_document_query",
                "uploaded": True,
                "target_path": "/mnt/data/Metablooms_OS",
            },
        })
        self.assertEqual(rc, 1, f"Expected exit 1 (BLOCKED), got {rc}. out: {out}")
        self.assertEqual(out.get("decision"), "BLOCKED")

    def test_hook_namespaced_file_search_blocked(self):
        """file_search.msearch on /mnt/data must exit 1 through subprocess hook path."""
        rc, out = _run_hook(ROUTE_GUARD, ["--hook-stdin"], {
            "tool_name": "file_search.msearch",
            "tool_input": {"target_path": "/mnt/data/Metablooms_OS"},
        })
        self.assertEqual(rc, 1)
        self.assertEqual(out.get("decision"), "BLOCKED")
        self.assertEqual(out.get("selected_tool"), "file_search")

    def test_hook_nested_array_path_blocked(self):
        """Mounted path in queries[] must exit 1 through subprocess hook path."""
        rc, out = _run_hook(ROUTE_GUARD, ["--hook-stdin"], {
            "tool_name": "file_search",
            "tool_input": {
                "queries": [
                    "what is the STAAR schema?",
                    "/mnt/data/Metablooms_OS/scripts/mpp/mpp.sh",
                ]
            },
        })
        self.assertEqual(rc, 1)
        self.assertEqual(out.get("decision"), "BLOCKED")

    def test_hook_normal_tool_passes_through(self):
        """A non-file-search tool with no mounted path must exit 0."""
        rc, out = _run_hook(ROUTE_GUARD, ["--hook-stdin"], {
            "tool_name": "bash",
            "tool_input": {"command": "echo hello"},
        })
        self.assertEqual(rc, 0, f"Normal tool must not be blocked. out: {out}")
        self.assertNotEqual(out.get("decision"), "BLOCKED")

    def test_hook_read_tool_passes_through(self):
        """Read tool with non-mounted path must exit 0."""
        rc, out = _run_hook(ROUTE_GUARD, ["--hook-stdin"], {
            "tool_name": "read_file",
            "tool_input": {"path": "governance/tool_routing/TOOL_ROUTING_POLICY_v1.json"},
        })
        self.assertEqual(rc, 0)


class TestRepeatedBlockerGuardHookPath(unittest.TestCase):
    """Subprocess tests for repeated_blocker_guard.py invoked as a PostToolUseFailure hook."""

    # ── fixture: hook_repeat_blocker_forces_rca ────────────────────────────

    def test_hook_repeat_blocker_forces_rca_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_repeat_blocker_forces_rca.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "FORCE_RCA")

    def test_hook_repeat_blocker_forces_rca(self):
        """Two subprocess calls with identical event: pass1=LOG_ONLY(0), pass2=FORCE_RCA(2)."""
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_repeat_blocker_forces_rca.json"))
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.json")
            args = fx["hook_args"] + ["--ledger-path", ledger_path]

            rc1, out1 = _run_hook(BLOCKER_GUARD, args, fx["event"])
            self.assertEqual(rc1, fx["pass1_expected"]["exit_code"],
                             f"pass1: expected exit {fx['pass1_expected']['exit_code']}, got {rc1}")
            self.assertEqual(out1.get("decision"), fx["pass1_expected"]["decision"])
            self.assertEqual(out1.get("occurrence_count"),
                             fx["pass1_expected"]["occurrence_count"])

            rc2, out2 = _run_hook(BLOCKER_GUARD, args, fx["event"])
            self.assertEqual(rc2, fx["pass2_expected"]["exit_code"],
                             f"pass2: expected exit {fx['pass2_expected']['exit_code']}, got {rc2}")
            self.assertEqual(out2.get("decision"), fx["pass2_expected"]["decision"])
            self.assertTrue(out2.get("rca_required"))
            self.assertEqual(out2.get("occurrence_count"),
                             fx["pass2_expected"]["occurrence_count"])

    # ── fixture: hook_changed_inputs_not_repeat ────────────────────────────

    def test_hook_changed_inputs_not_repeat_fixture_valid(self):
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_changed_inputs_not_repeat.json"))
        self.assertEqual(fx["pass1_expected"]["decision"], "LOG_ONLY")
        self.assertEqual(fx["pass2_expected"]["decision"], "LOG_NEW_VARIANT")

    def test_hook_changed_inputs_not_repeat(self):
        """Different input_digest: pass1=LOG_ONLY(0), pass2=LOG_NEW_VARIANT(0)."""
        fx = _load(os.path.join(FIXTURES_HOOK, "hook_changed_inputs_not_repeat.json"))
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.json")
            args = fx["hook_args"] + ["--ledger-path", ledger_path]

            rc1, out1 = _run_hook(BLOCKER_GUARD, args, fx["event_pass1"])
            self.assertEqual(rc1, fx["pass1_expected"]["exit_code"])
            self.assertEqual(out1.get("decision"), fx["pass1_expected"]["decision"])

            rc2, out2 = _run_hook(BLOCKER_GUARD, args, fx["event_pass2"])
            self.assertEqual(rc2, fx["pass2_expected"]["exit_code"])
            self.assertEqual(out2.get("decision"), fx["pass2_expected"]["decision"])
            self.assertFalse(out2.get("rca_required"))
            self.assertTrue(out2.get("changed_inputs"))

    # ── bare event dict (simulating hook invocation without wrapper) ───────

    def test_bare_event_dict_accepted(self):
        """repeated_blocker_guard.py accepts a bare event dict (no 'event' wrapper key)."""
        event = {
            "blocker_type": "tool_denied",
            "component": "tool_route_guard",
            "operation": "file_search",
            "normalized_command": "file_search /mnt/data/Metablooms_OS bare_test",
            "target_path": "/mnt/data/Metablooms_OS",
            "input_digest": "bare_test_digest_111",
            "evidence_digest": "bare_test_evidence_222",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.json")
            rc, out = _run_hook(
                BLOCKER_GUARD,
                ["--hook-stdin", "--mode", "record-or-route", "--ledger-path", ledger_path],
                event,
            )
            self.assertEqual(rc, 0)
            self.assertEqual(out.get("decision"), "LOG_ONLY")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
