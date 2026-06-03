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


    def test_checkout_proof_files_excluded_from_manifest_when_excluded(self):
        """Verifies --exclude github_checkout_head.txt and --exclude github_checkout_status.txt
        keep proof files out of the TSV while still leaving them available for upload."""
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "repo_file.txt").write_text("tracked", encoding="utf-8")
            (root / "github_checkout_head.txt").write_text("abc123\n", encoding="utf-8")
            (root / "github_checkout_status.txt").write_text("", encoding="utf-8")
            out = root / "github_main_manifest.tsv"
            receipt = root / "github_manifest_receipt.json"
            excludes = list(mod.DEFAULT_EXCLUDES) + [
                "github_checkout_head.txt",
                "github_checkout_status.txt",
            ]
            result = mod.write_manifest(root, out, receipt, excludes)
            self.assertEqual(result["decision"], "PASS")
            self.assertEqual(result["file_count"], 1)
            text = out.read_text(encoding="utf-8")
            self.assertIn("repo_file.txt", text)
            self.assertNotIn("github_checkout_head.txt", text)
            self.assertNotIn("github_checkout_status.txt", text)
            # Proof files still exist on disk for artifact upload
            self.assertTrue((root / "github_checkout_head.txt").is_file())
            self.assertTrue((root / "github_checkout_status.txt").is_file())


if __name__ == "__main__":
    unittest.main()
