"""
Tests for CHAT790_OS_REPAIRS_STAGE_A — boot-root repair policy.

Proves:
  3. Missing scripts/mpp/mpp.sh is a boot blocker (not a soft warning).
  4. A boot-root repair policy must require a same-run boot receipt.

Tests validate the machine-readable policy document; they do not require
a live /mnt/data mount or a running Metablooms OS instance.
"""
import json
import os
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_POLICY_JSON_PATH = os.path.join(
    _REPO_ROOT, "governance", "boot", "BOOT_ROOT_REPAIR_POLICY_v1.json"
)
_POLICY_MD_PATH = os.path.join(
    _REPO_ROOT, "governance", "boot", "BOOT_ROOT_REPAIR_POLICY_v1.md"
)


def _load_policy():
    with open(_POLICY_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _mpp_sh_check(policy):
    """Return the blocking check for scripts/mpp/mpp.sh, or None."""
    for check in policy.get("blocking_checks", []):
        if check.get("id") == "mpp_sh_exists":
            return check
    return None


def _turn_boot_check(policy):
    """Return the turn-boot blocking check, or None."""
    for check in policy.get("blocking_checks", []):
        if check.get("id") == "turn_boot_passes":
            return check
    return None


class TestPolicyDocumentExists(unittest.TestCase):

    def test_boot_policy_json_exists(self):
        self.assertTrue(os.path.isfile(_POLICY_JSON_PATH),
                        f"BOOT_ROOT_REPAIR_POLICY_v1.json not found at {_POLICY_JSON_PATH}")

    def test_boot_policy_md_exists(self):
        self.assertTrue(os.path.isfile(_POLICY_MD_PATH),
                        f"BOOT_ROOT_REPAIR_POLICY_v1.md not found at {_POLICY_MD_PATH}")

    def test_boot_policy_json_is_valid_json(self):
        policy = _load_policy()
        self.assertIsInstance(policy, dict)

    def test_boot_policy_id(self):
        policy = _load_policy()
        self.assertEqual(policy.get("policy_id"), "BOOT_ROOT_REPAIR_POLICY_v1")

    def test_boot_policy_has_live_root(self):
        policy = _load_policy()
        self.assertIn("live_root", policy)
        self.assertIn("/mnt/data", policy["live_root"])


class TestMppShIsBlocker(unittest.TestCase):
    """
    PROVES: missing scripts/mpp/mpp.sh is a boot blocker, not a soft warning.
    """

    def test_blocking_checks_list_exists(self):
        """Policy must have a non-empty blocking_checks list."""
        policy = _load_policy()
        self.assertIn("blocking_checks", policy)
        self.assertIsInstance(policy["blocking_checks"], list)
        self.assertGreater(len(policy["blocking_checks"]), 0,
            "blocking_checks must be non-empty")

    def test_mpp_sh_check_exists(self):
        """A blocking check for mpp_sh_exists must be present."""
        policy = _load_policy()
        check = _mpp_sh_check(policy)
        self.assertIsNotNone(check,
            "blocking_checks must include id='mpp_sh_exists'")

    def test_mpp_sh_check_path_is_correct(self):
        """mpp_sh_exists check must reference scripts/mpp/mpp.sh."""
        policy = _load_policy()
        check = _mpp_sh_check(policy)
        self.assertIsNotNone(check)
        self.assertIn("scripts/mpp/mpp.sh", check.get("path", ""),
            "mpp_sh_exists check must reference 'scripts/mpp/mpp.sh'")

    def test_mpp_sh_severity_is_blocker_not_warning(self):
        """
        scripts/mpp/mpp.sh absence must be BLOCKER severity, not WARNING or INFO.
        This is the core invariant: directory existence != bootability.
        """
        policy = _load_policy()
        check = _mpp_sh_check(policy)
        self.assertIsNotNone(check)
        severity = check.get("severity", "")
        self.assertEqual(severity, "BLOCKER",
            f"mpp_sh_exists severity must be BLOCKER, not '{severity}'")

    def test_mpp_sh_check_type_is_file_exists(self):
        """Check type must be file_exists (not a soft probe)."""
        policy = _load_policy()
        check = _mpp_sh_check(policy)
        self.assertIsNotNone(check)
        self.assertEqual(check.get("check_type"), "file_exists",
            "mpp_sh_exists check_type must be 'file_exists'")

    def test_mpp_sh_error_message_contains_blocked(self):
        """Error message for missing mpp.sh must contain BLOCKED."""
        policy = _load_policy()
        check = _mpp_sh_check(policy)
        self.assertIsNotNone(check)
        error_msg = check.get("error_message", "")
        self.assertIn("BLOCKED", error_msg,
            "mpp_sh_exists error_message must contain 'BLOCKED'")

    def test_turn_boot_check_also_exists(self):
        """A second blocking check for turn-boot must also be present."""
        policy = _load_policy()
        check = _turn_boot_check(policy)
        self.assertIsNotNone(check,
            "blocking_checks must also include id='turn_boot_passes'")

    def test_turn_boot_severity_is_blocker(self):
        policy = _load_policy()
        check = _turn_boot_check(policy)
        self.assertIsNotNone(check)
        self.assertEqual(check.get("severity"), "BLOCKER",
            "turn_boot_passes severity must be BLOCKER")

    def test_policy_fails_closed(self):
        """failure_mode must be fail_closed."""
        policy = _load_policy()
        self.assertEqual(policy.get("failure_mode"), "fail_closed",
            "Boot policy failure_mode must be 'fail_closed'")


class TestSameRunBootReceiptRequired(unittest.TestCase):
    """
    PROVES: a boot-root repair policy must require a same-run boot receipt.
    """

    def test_receipt_requirements_section_present(self):
        """Policy must have a receipt_requirements section."""
        policy = _load_policy()
        self.assertIn("receipt_requirements", policy,
            "Policy must contain a receipt_requirements section")

    def test_same_run_boot_receipt_is_true(self):
        """same_run_boot_receipt must be explicitly set to true."""
        policy = _load_policy()
        req = policy.get("receipt_requirements", {})
        self.assertTrue(req.get("same_run_boot_receipt"),
            "receipt_requirements.same_run_boot_receipt must be true")

    def test_required_receipt_fields_listed(self):
        """Policy must list required fields for the boot receipt."""
        policy = _load_policy()
        req = policy.get("receipt_requirements", {})
        fields = req.get("required_receipt_fields", [])
        self.assertGreater(len(fields), 0,
            "required_receipt_fields must be non-empty")

    def test_receipt_requires_mpp_sh_verified_field(self):
        """Boot receipt must require mpp_sh_verified field."""
        policy = _load_policy()
        fields = policy["receipt_requirements"]["required_receipt_fields"]
        self.assertIn("mpp_sh_verified", fields,
            "required_receipt_fields must include 'mpp_sh_verified'")

    def test_receipt_requires_turn_boot_exit_code(self):
        """Boot receipt must require turn_boot_exit_code field."""
        policy = _load_policy()
        fields = policy["receipt_requirements"]["required_receipt_fields"]
        self.assertIn("turn_boot_exit_code", fields,
            "required_receipt_fields must include 'turn_boot_exit_code'")

    def test_receipt_requires_session_id(self):
        """Boot receipt must require session_id (proves same-run provenance)."""
        policy = _load_policy()
        fields = policy["receipt_requirements"]["required_receipt_fields"]
        self.assertIn("session_id", fields,
            "required_receipt_fields must include 'session_id'")

    def test_receipt_requires_receipt_timestamp(self):
        """Boot receipt must require a timestamp field."""
        policy = _load_policy()
        fields = policy["receipt_requirements"]["required_receipt_fields"]
        self.assertIn("receipt_timestamp", fields,
            "required_receipt_fields must include 'receipt_timestamp'")


class TestBootPolicyMarkdownContent(unittest.TestCase):

    def _read_md(self):
        with open(_POLICY_MD_PATH, encoding="utf-8") as f:
            return f.read()

    def test_md_mentions_mpp_sh(self):
        content = self._read_md()
        self.assertIn("mpp.sh", content,
            "Boot policy Markdown must mention 'mpp.sh'")

    def test_md_mentions_blocker(self):
        content = self._read_md()
        self.assertIn("BLOCKER", content,
            "Boot policy Markdown must mention 'BLOCKER'")

    def test_md_mentions_same_run_receipt(self):
        content = self._read_md()
        self.assertTrue(
            "same-run" in content or "same_run" in content,
            "Boot policy Markdown must document the same-run receipt requirement"
        )

    def test_md_mentions_directory_existence_failure_class(self):
        content = self._read_md()
        self.assertTrue(
            "directory_existence_treated_as_runtime_soundness" in content
            or ("directory" in content and "existence" in content),
            "Boot policy Markdown must describe the directory-existence failure class"
        )

    def test_md_mentions_fail_closed(self):
        content = self._read_md()
        self.assertTrue(
            "fail_closed" in content
            or "fail closed" in content.lower()
            or "fail-closed" in content.lower(),
            "Boot policy Markdown must state the fail-closed posture"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
