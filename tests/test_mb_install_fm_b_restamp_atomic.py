"""FM-B sidecar atomic restamp fixture for MB_INSTALL v0 Stage 3."""

import hashlib
import importlib.util
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

restamp_sidecars = _mod.restamp_sidecars


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestFmBRestampAtomic(unittest.TestCase):

    def test_restamp_writes_expected_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = os.path.join(tmp, "payload.txt")
            with open(payload, "wb") as f:
                f.write(b"payload-v1")

            result = restamp_sidecars([payload])
            expected = _sha256(b"payload-v1")
            self.assertEqual(result[payload], expected)
            with open(payload + ".sha256", encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), expected)

    def test_failed_replace_preserves_existing_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = os.path.join(tmp, "payload.txt")
            sidecar = payload + ".sha256"
            with open(payload, "wb") as f:
                f.write(b"payload-v2")
            with open(sidecar, "w", encoding="utf-8") as f:
                f.write("old-sidecar\n")

            with mock.patch.object(_mod.os, "replace", side_effect=OSError("simulated replace failure")):
                with self.assertRaises(OSError):
                    restamp_sidecars([payload])

            with open(sidecar, encoding="utf-8") as f:
                self.assertEqual(f.read(), "old-sidecar\n")
            leftovers = [name for name in os.listdir(tmp) if name.endswith(".tmp")]
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
