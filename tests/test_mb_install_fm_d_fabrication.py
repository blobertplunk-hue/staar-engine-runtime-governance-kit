"""
FM-D fabrication wound fixture.

This file has two jobs:
  1. Prove that verify_bundle() detects a bundle whose declared sha256 does NOT match
     the file's actual bytes (FM-D, the Stage-003B wound).
     - test_fm_d_fabrication_wound_detected is RED if the hash check is removed,
       GREEN with it in place.
  2. Prove that atomic_swap() refuses to run without the bootstrap flag,
     so stage 1 can never mutate a live tree. Stage 4 adds a guarded throwaway-root
     implementation, so _bootstrap_flag=True without target/root now fails with the
     Stage 4 precondition error instead of NotImplementedError.
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

verify_bundle = _mod.verify_bundle
atomic_swap = _mod.atomic_swap
HashMismatchError = _mod.HashMismatchError
ManifestError = _mod.ManifestError
AtomicSwapError = _mod.AtomicSwapError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_bundle(*, poison_hash: bool = False) -> str:
    """Create a temporary zip bundle.

    When poison_hash=True the declared sha256 is computed from different bytes
    than the file actually contains, simulating the FM-D fabrication wound.
    """
    real_content = b"kernel payload v0"
    declared_hash = _sha256(b"tampered content") if poison_hash else _sha256(real_content)

    manifest = {
        "id": "test-module",
        "semver": "0.1.0",
        "provides": [],
        "requires": [],
        "files": [
            {
                "path": "tools/test_payload.bin",
                "sha256": declared_hash,
                "size_bytes": len(real_content),
                "protected_class": False,
            }
        ],
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("tools/test_payload.bin", real_content)

    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.write(buf.getvalue())
    tmp.close()
    return tmp.name


class TestFmDFabricationWound(unittest.TestCase):

    def test_verify_bundle_passes_on_good_bundle(self):
        """verify_bundle accepts a correctly-hashed bundle and returns the manifest."""
        path = _build_bundle(poison_hash=False)
        try:
            manifest = verify_bundle(path)
            self.assertEqual(manifest["id"], "test-module")
            self.assertEqual(len(manifest["files"]), 1)
        finally:
            os.unlink(path)

    def test_fm_d_fabrication_wound_detected(self):
        """
        FM-D: verify_bundle MUST raise when declared sha256 != actual file bytes.

        This test is RED if the hash check in verify_bundle() is removed.
        This test is GREEN with the check in place.
        """
        path = _build_bundle(poison_hash=True)
        try:
            with self.assertRaises((HashMismatchError, ManifestError)):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_verify_bundle_rejects_missing_manifest(self):
        """verify_bundle raises ManifestError when manifest.json is absent."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("tools/some_file.txt", b"content")
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.write(buf.getvalue())
        tmp.close()
        try:
            with self.assertRaises(ManifestError):
                verify_bundle(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_verify_bundle_rejects_declared_but_absent_file(self):
        """verify_bundle raises ManifestError when a file listed in manifest is absent from the zip."""
        content = b"present"
        manifest = {
            "id": "m",
            "semver": "0.0.1",
            "provides": [],
            "requires": [],
            "files": [
                {
                    "path": "tools/missing.txt",
                    "sha256": _sha256(content),
                    "size_bytes": len(content),
                    "protected_class": False,
                }
            ],
        }
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            # intentionally omit tools/missing.txt
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.write(buf.getvalue())
        tmp.close()
        try:
            with self.assertRaises(ManifestError):
                verify_bundle(tmp.name)
        finally:
            os.unlink(tmp.name)


class TestAtomicSwapGuard(unittest.TestCase):

    def test_atomic_swap_refuses_without_bootstrap_flag(self):
        """
        atomic_swap must raise NotImplementedError when called without _bootstrap_flag.
        Stage 1 never sets this flag, making live-tree mutation impossible.
        """
        with self.assertRaises(NotImplementedError):
            atomic_swap("/tmp/fake_staging_tree")

    def test_atomic_swap_still_refuses_with_false_flag(self):
        """Explicitly passing False should also refuse."""
        with self.assertRaises(NotImplementedError):
            atomic_swap("/tmp/fake_staging_tree", _bootstrap_flag=False)

    def test_atomic_swap_bootstrap_flag_requires_stage4_target_and_allowed_root(self):
        """Stage 4 allows bootstrap flag only with explicit target_tree and allowed_root."""
        with self.assertRaises(AtomicSwapError):
            atomic_swap("/tmp/fake_staging_tree", _bootstrap_flag=True)


if __name__ == "__main__":
    unittest.main()
