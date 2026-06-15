"""Unit tests for mb_install_v0.py — verify_bundle, check_protected_writes, restamp_sidecars."""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
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
check_protected_writes = _mod.check_protected_writes
stage_to_tmp = _mod.stage_to_tmp
restamp_sidecars = _mod.restamp_sidecars
write_receipt = _mod.write_receipt
HashMismatchError = _mod.HashMismatchError
ManifestError = _mod.ManifestError
ProtectedWriteError = _mod.ProtectedWriteError
PathViolationError = _mod.PathViolationError
DuplicatePathError = _mod.DuplicatePathError
UndeclaredPayloadError = _mod.UndeclaredPayloadError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bundle(manifest: dict, payloads: list[tuple[str, bytes]]) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        for path, content in payloads:
            zf.writestr(path, content)
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp.write(buf.getvalue())
    tmp.close()
    return tmp.name


def _good_bundle(files: list[tuple[str, bytes]] | None = None) -> tuple[str, dict]:
    """Build a well-formed bundle zip. Returns (zip_path, manifest)."""
    if files is None:
        files = [("tools/hello.txt", b"hello"), ("contracts/mod.json", b"{}")]

    entries = []
    for path, content in files:
        entries.append({
            "path": path,
            "sha256": _sha256(content),
            "size_bytes": len(content),
            "protected_class": False,
        })

    manifest = {
        "id": "unit-test-module",
        "semver": "1.2.3",
        "provides": ["thing-a"],
        "requires": ["thing-b"],
        "files": entries,
    }

    return _write_bundle(manifest, files), manifest


class TestVerifyBundle(unittest.TestCase):

    def test_good_bundle_returns_manifest(self):
        path, expected = _good_bundle()
        try:
            manifest = verify_bundle(path)
            self.assertEqual(manifest["id"], "unit-test-module")
            self.assertEqual(manifest["semver"], "1.2.3")
            self.assertEqual(len(manifest["files"]), 2)
        finally:
            os.unlink(path)

    def test_rejects_traversal_path(self):
        files = [("tools/../contracts/evil.txt", b"bad")]
        path, _ = _good_bundle(files)
        try:
            with self.assertRaises((PathViolationError, ManifestError)):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_absolute_path(self):
        content = b"bad"
        manifest = {
            "id": "x", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "/etc/passwd", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False}],
        }
        path = _write_bundle(manifest, [])
        try:
            with self.assertRaises((PathViolationError, ManifestError)):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_out_of_tree_path(self):
        files = [("home/user/.bashrc", b"bad")]
        path, _ = _good_bundle(files)
        try:
            with self.assertRaises((PathViolationError, ManifestError)):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_backslash_path(self):
        content = b"bad"
        manifest = {
            "id": "x", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "tools\\evil.txt", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False}],
        }
        path = _write_bundle(manifest, [("tools\\evil.txt", content)])
        try:
            with self.assertRaises(PathViolationError):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_duplicate_manifest_paths(self):
        content = b"same"
        manifest = {
            "id": "dup", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [
                {"path": "tools/dup.txt", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False},
                {"path": "tools/dup.txt", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False},
            ],
        }
        path = _write_bundle(manifest, [("tools/dup.txt", content)])
        try:
            with self.assertRaises(DuplicatePathError):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_duplicate_zip_members(self):
        content = b"same"
        manifest = {
            "id": "dupzip", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "tools/dup.txt", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False}],
        }
        path = _write_bundle(manifest, [("tools/dup.txt", content), ("tools/dup.txt", content)])
        try:
            with self.assertRaises(DuplicatePathError):
                verify_bundle(path)
        finally:
            os.unlink(path)

    def test_rejects_undeclared_zip_payload(self):
        content = b"declared"
        manifest = {
            "id": "extra", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "tools/declared.txt", "sha256": _sha256(content), "size_bytes": len(content), "protected_class": False}],
        }
        path = _write_bundle(manifest, [("tools/declared.txt", content), ("tools/extra.txt", b"extra")])
        try:
            with self.assertRaises(UndeclaredPayloadError):
                verify_bundle(path)
        finally:
            os.unlink(path)


class TestCheckProtectedWrites(unittest.TestCase):

    def _manifest_with_protected(self, protected: bool) -> dict:
        return {
            "id": "m", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "tools/f.txt", "sha256": "a" * 64, "size_bytes": 0, "protected_class": protected}],
        }

    def test_no_protected_files_always_passes(self):
        manifest = self._manifest_with_protected(False)
        check_protected_writes(manifest, "")
        check_protected_writes(manifest, "some-token")

    def test_protected_file_with_valid_token_passes(self):
        manifest = self._manifest_with_protected(True)
        check_protected_writes(manifest, "robert-auth-token-xyz")

    def test_protected_file_with_empty_token_raises(self):
        manifest = self._manifest_with_protected(True)
        with self.assertRaises(ProtectedWriteError):
            check_protected_writes(manifest, "")

    def test_protected_file_with_whitespace_only_token_raises(self):
        manifest = self._manifest_with_protected(True)
        with self.assertRaises(ProtectedWriteError):
            check_protected_writes(manifest, "   ")


class TestRestamp(unittest.TestCase):

    def test_restamp_creates_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = os.path.join(tmp, "payload.bin")
            with open(payload, "wb") as f:
                f.write(b"important data")
            result = restamp_sidecars([payload])
            sidecar = payload + ".sha256"
            self.assertTrue(os.path.exists(sidecar))
            expected_hash = _sha256(b"important data")
            self.assertEqual(result[payload], expected_hash)
            with open(sidecar) as f:
                self.assertEqual(f.read().strip(), expected_hash)

    def test_restamp_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, content in enumerate([b"alpha", b"beta", b"gamma"]):
                p = os.path.join(tmp, f"file{i}.bin")
                with open(p, "wb") as f:
                    f.write(content)
                paths.append(p)
            result = restamp_sidecars(paths)
            self.assertEqual(len(result), 3)
            for p, content in zip(paths, [b"alpha", b"beta", b"gamma"]):
                self.assertEqual(result[p], _sha256(content))
                self.assertTrue(os.path.exists(p + ".sha256"))

    def test_restamp_updates_sidecar_when_content_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "file.bin")
            with open(p, "wb") as f:
                f.write(b"v1")
            restamp_sidecars([p])
            with open(p, "wb") as f:
                f.write(b"v2")
            result = restamp_sidecars([p])
            self.assertEqual(result[p], _sha256(b"v2"))


class TestStageToTmp(unittest.TestCase):

    def test_stages_files_correctly(self):
        import shutil
        zip_path, manifest = _good_bundle([("tools/a.txt", b"file-a"), ("contracts/b.json", b"{}")])
        try:
            tmp_dir = stage_to_tmp(manifest, zip_path)
            try:
                self.assertTrue(os.path.exists(os.path.join(tmp_dir, "tools/a.txt")))
                self.assertTrue(os.path.exists(os.path.join(tmp_dir, "contracts/b.json")))
                with open(os.path.join(tmp_dir, "tools/a.txt"), "rb") as f:
                    self.assertEqual(f.read(), b"file-a")
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        finally:
            os.unlink(zip_path)


class TestWriteReceipt(unittest.TestCase):

    def test_receipt_shape(self):
        manifest = {
            "id": "mod-x", "semver": "2.0.0", "provides": [], "requires": [],
            "files": [{"path": "tools/f.txt", "sha256": "a" * 64, "size_bytes": 0, "protected_class": False}],
        }
        receipt = write_receipt(manifest, install_id="run-001")
        self.assertEqual(receipt["module_id"], "mod-x")
        self.assertEqual(receipt["semver"], "2.0.0")
        self.assertEqual(receipt["score_source"], "execution")
        self.assertEqual(receipt["install_id"], "run-001")
        self.assertIn("tools/f.txt", receipt["files_installed"])

    def test_receipt_is_deterministic(self):
        manifest = {
            "id": "mod-y", "semver": "0.0.1", "provides": [], "requires": [],
            "files": [{"path": "tools/x.txt", "sha256": "b" * 64, "size_bytes": 1, "protected_class": False}],
        }
        r1 = write_receipt(manifest, install_id="abc")
        r2 = write_receipt(manifest, install_id="abc")
        self.assertEqual(r1, r2)

    def test_receipt_sorts_files_for_equivalent_manifests(self):
        files_a = [
            {"path": "tools/b.txt", "sha256": "b" * 64, "size_bytes": 1, "protected_class": False},
            {"path": "tools/a.txt", "sha256": "a" * 64, "size_bytes": 1, "protected_class": False},
        ]
        files_b = list(reversed(files_a))
        manifest_a = {"id": "mod-z", "semver": "0.0.1", "provides": [], "requires": [], "files": files_a}
        manifest_b = {"id": "mod-z", "semver": "0.0.1", "provides": [], "requires": [], "files": files_b}
        self.assertEqual(write_receipt(manifest_a, "abc"), write_receipt(manifest_b, "abc"))
        self.assertEqual(write_receipt(manifest_a, "abc")["files_installed"], ["tools/a.txt", "tools/b.txt"])


if __name__ == "__main__":
    unittest.main()
