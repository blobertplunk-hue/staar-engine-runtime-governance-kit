#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "metablooms" / "github_repo_manifest_generator_v1.py"
spec = importlib.util.spec_from_file_location("github_repo_manifest_generator_v1", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestGitHubRepoManifestGenerator(unittest.TestCase):
    def test_manifest_generation_hashes_files_and_excludes_git(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "ignored").write_text("ignore", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.txt").write_text("beta", encoding="utf-8")
            out = root / "github_main_manifest.tsv"
            receipt = root / "github_manifest_receipt.json"
            result = mod.write_manifest(root, out, receipt, list(mod.DEFAULT_EXCLUDES))
            self.assertEqual(result["decision"], "PASS")
            self.assertEqual(result["file_count"], 2)
            text = out.read_text(encoding="utf-8")
            self.assertIn("a.txt", text)
            self.assertIn("nested/b.txt", text)
            self.assertNotIn(".git/ignored", text)
            self.assertTrue(out.with_name(out.name + ".sha256").is_file())
            receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt_data["manifest_sha256"], result["manifest_sha256"])


if __name__ == "__main__":
    unittest.main()
