#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "metablooms" / "github_os_sync_gate_v1.py"
spec = importlib.util.spec_from_file_location("github_os_sync_gate_v1", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestGitHubOsSyncGate(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run([sys.executable, "-S", str(TOOL), *args], cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_contracts_pass(self):
        result = self.run_tool("validate-contracts")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_and_private_precedence(self):
        data = mod.classify(["runtime/generated/METABLOOMS_FULL_OS_20260603.tar.zst", "runtime/state/contains_token_example.txt"])
        rows = {row["path"]: row["class"] for row in data["paths"]}
        self.assertEqual(rows["runtime/generated/METABLOOMS_FULL_OS_20260603.tar.zst"], "release_asset_only")
        self.assertEqual(rows["runtime/state/contains_token_example.txt"], "private_excluded")

    def test_github_manifest_sample_classifies(self):
        sample = [
            "AGENTS.md",
            "AUTHORITY_MAP.md",
            "audits/inventory/_inventory.jsonl",
            "contracts/engine_contracts/PROMOTION_GATE_v1.json",
            "externalization/sticky_full_os_exports/20260601T2326Z/README_STICKY_DURABLE_FLOOR_IMPORTED_20260601T2326Z.md",
            "source_materials/raw_import/STAAR_ENGINE_SOP.md",
            ".github/workflows/metablooms-repo-manifest.yml",
            "governance/tool_routing/TOOL_ROUTING_POLICY_v1.json",
        ]
        data = mod.classify(sample)
        self.assertEqual(data["decision"], "PASS")
        self.assertFalse([row for row in data["paths"] if row["class"] == "UNCLASSIFIED_BLOCK_MOVEMENT"])

    def test_unknown_nested_path_blocks(self):
        result = self.run_tool("classify-paths", "unknown/new/file.xyz")
        self.assertEqual(result.returncode, 2)

    def test_authority_map_blocks_over_threshold_unclassifiables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "map.json"
            path.write_text(json.dumps({
                "path_authorities": [{"path": "governance/github_os_sync/SYNC_AUTHORITY_MAP_v1.json", "authority_class": "os_authoritative_with_github_pr_proposal_path"}],
                "divergence_summary": {"unclassifiable_split_brain_paths": "101"},
            }))
            result = self.run_tool("validate-authority-map", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("101 > 100", result.stdout)

    def test_bidirectional_conflict_requires_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "map.json"
            path.write_text(json.dumps({
                "path_authorities": [
                    {"path": "governance/github_os_sync/SYNC_AUTHORITY_MAP_v1.json", "authority_class": "os_authoritative_with_github_pr_proposal_path"},
                    {"path": "x", "authority_class": "bidirectional_source", "diverged": True},
                ],
                "divergence_summary": {"unclassifiable_split_brain_paths": 0},
            }))
            result = self.run_tool("validate-authority-map", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertIn("human merge receipt", result.stdout)


if __name__ == "__main__":
    unittest.main()
