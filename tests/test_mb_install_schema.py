"""Executable schema gate for MB_INSTALL v0 manifests."""

import copy
import json
import pathlib
import unittest

from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "KERNEL_MODULE_MANIFEST_SCHEMA_v1.json"


def _good_manifest() -> dict:
    return {
        "id": "schema-test-module",
        "semver": "1.2.3",
        "provides": ["capability-a"],
        "requires": ["capability-b"],
        "files": [
            {
                "path": "tools/schema_payload.txt",
                "sha256": "a" * 64,
                "size_bytes": 12,
                "protected_class": False,
            }
        ],
    }


class TestKernelModuleManifestSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            cls.schema = json.load(f)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def assert_valid(self, manifest: dict) -> None:
        self.validator.validate(manifest)

    def assert_invalid(self, manifest: dict) -> None:
        errors = list(self.validator.iter_errors(manifest))
        self.assertTrue(errors, "manifest unexpectedly passed schema validation")

    def test_good_manifest_validates(self):
        self.assert_valid(_good_manifest())

    def test_rejects_traversal_path(self):
        manifest = _good_manifest()
        manifest["files"][0]["path"] = "tools/../contracts/evil.txt"
        self.assert_invalid(manifest)

    def test_rejects_absolute_path(self):
        manifest = _good_manifest()
        manifest["files"][0]["path"] = "/etc/passwd"
        self.assert_invalid(manifest)

    def test_rejects_out_of_tree_path(self):
        manifest = _good_manifest()
        manifest["files"][0]["path"] = "home/user/file.txt"
        self.assert_invalid(manifest)

    def test_rejects_backslash_path(self):
        manifest = _good_manifest()
        manifest["files"][0]["path"] = "tools\\evil.txt"
        self.assert_invalid(manifest)

    def test_rejects_bad_sha256(self):
        manifest = _good_manifest()
        manifest["files"][0]["sha256"] = "not-a-sha"
        self.assert_invalid(manifest)

    def test_rejects_bad_semver(self):
        manifest = _good_manifest()
        manifest["semver"] = "v1"
        self.assert_invalid(manifest)

    def test_rejects_exact_duplicate_file_entries(self):
        manifest = _good_manifest()
        manifest["files"].append(copy.deepcopy(manifest["files"][0]))
        self.assert_invalid(manifest)


if __name__ == "__main__":
    unittest.main()
