"""FM-A protected-write fixture for MB_INSTALL v0 Stage 2.

FM-A wound: a protected-class file must never be allowed through the install
preflight without an explicit non-empty authorization token.
"""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

check_protected_writes = _mod.check_protected_writes
ProtectedWriteError = _mod.ProtectedWriteError


def _manifest(protected: bool) -> dict:
    return {
        "id": "fm-a-test-module",
        "semver": "0.2.0",
        "provides": [],
        "requires": [],
        "files": [
            {
                "path": "tools/fm_a_payload.txt",
                "sha256": "a" * 64,
                "size_bytes": 0,
                "protected_class": protected,
            }
        ],
    }


class TestFmAProtectedWrite(unittest.TestCase):

    def test_protected_file_without_token_fails_closed(self):
        with self.assertRaises(ProtectedWriteError):
            check_protected_writes(_manifest(protected=True), "")

    def test_protected_file_with_whitespace_token_fails_closed(self):
        with self.assertRaises(ProtectedWriteError):
            check_protected_writes(_manifest(protected=True), "   \t\n")

    def test_protected_file_with_token_passes(self):
        check_protected_writes(_manifest(protected=True), "robert-auth-token-present")

    def test_unprotected_file_without_token_passes(self):
        check_protected_writes(_manifest(protected=False), "")


if __name__ == "__main__":
    unittest.main()
