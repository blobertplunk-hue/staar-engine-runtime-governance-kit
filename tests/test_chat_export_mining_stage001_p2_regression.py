"""
P2 regression tests for CHAT790_EXPORT_MINING_CARTRIDGE_STAGE001.

These tests cover Codex review findings on PR #14:
  1. Malformed PostToolUseFailure payloads must be counted as unmappable,
     not crash the runner.
  2. Invalid --output paths must produce bounded JSON error output and exit 1,
     not a traceback.
"""
import json
import os
import subprocess
import sys
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "governance", "chat_export_mining"))

from governance.chat_export_mining.runner import mine_stream  # noqa: E402

_RUNNER_SCRIPT = os.path.join(_REPO_ROOT, "governance", "chat_export_mining", "runner.py")


class TestChatExportMiningStage001P2Regressions(unittest.TestCase):
    def test_malformed_failure_field_types_are_unmappable_not_fatal(self):
        """Malformed field types inside a valid failure entry do not abort mining."""
        bad_failure = json.dumps({
            "hook_event_name": "PostToolUseFailure",
            "tool_name": ["Bash"],
            "tool_input": {"command": ["echo", "bad"]},
            "tool_response": {"error": "bad response type"},
            "session_id": "p2-regression",
        })
        good_failure = json.dumps({
            "hook_event_name": "PostToolUseFailure",
            "tool_name": "Bash",
            "tool_input": {"command": "echo ok"},
            "tool_response": "ok",
            "session_id": "p2-regression",
        })

        receipt = mine_stream([bad_failure, good_failure])

        self.assertEqual(receipt["entries_seen"], 2)
        self.assertEqual(receipt["failures_found"], 2)
        self.assertEqual(receipt["unmappable"], 1)
        self.assertEqual(receipt["mapped"], 1)
        self.assertEqual(len(receipt["events"]), 1)

    def test_invalid_output_path_exits_1_with_structured_stderr_json(self):
        """Missing output directory returns bounded JSON stderr instead of traceback."""
        missing_output = os.path.join(
            _REPO_ROOT,
            "runtime",
            "generated",
            "missing-stage001-p2-dir",
            "receipt.json",
        )
        cmd = [
            sys.executable,
            _RUNNER_SCRIPT,
            "--output",
            missing_output,
        ]
        result = subprocess.run(
            cmd,
            input="",
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        err = json.loads(result.stderr)
        self.assertEqual(err["exit_code"], 1)
        self.assertIn("error", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
