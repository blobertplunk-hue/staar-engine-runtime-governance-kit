"""
Tests for CHAT790_OS_REPAIRS_STAGE_A — tool routing policy.

Proves:
  1. Mounted /mnt/data artifact work must not route to file_search.
  2. Direct filesystem, Python, and archive reads are the preferred route
     for mounted artifacts.

Tests validate the machine-readable policy document; they do not require
live mounted paths or running processes.
"""
import json
import os
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_POLICY_PATH = os.path.join(_REPO_ROOT, "governance", "tool_routing", "TOOL_ROUTING_POLICY_v1.json")
_BAN_DOC_PATH = os.path.join(
    _REPO_ROOT, "governance", "tool_routing", "FILE_SEARCH_BAN_FOR_MOUNTED_ARTIFACTS_v1.md"
)


def _load_policy():
    with open(_POLICY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _mounted_route(policy):
    """Return the route object for mounted_mnt_data_os_artifact_truth, or None."""
    for route in policy.get("routes", []):
        if route.get("id") == "mounted_mnt_data_os_artifact_truth":
            return route
    return None


class TestPolicyDocumentExists(unittest.TestCase):

    def test_policy_json_exists(self):
        self.assertTrue(os.path.isfile(_POLICY_PATH),
                        f"TOOL_ROUTING_POLICY_v1.json not found at {_POLICY_PATH}")

    def test_policy_is_valid_json(self):
        policy = _load_policy()
        self.assertIsInstance(policy, dict)

    def test_policy_has_policy_id(self):
        policy = _load_policy()
        self.assertEqual(policy.get("policy_id"), "TOOL_ROUTING_POLICY_v1")

    def test_policy_has_routes(self):
        policy = _load_policy()
        self.assertIn("routes", policy)
        self.assertIsInstance(policy["routes"], list)
        self.assertGreater(len(policy["routes"]), 0)

    def test_ban_doc_exists(self):
        self.assertTrue(os.path.isfile(_BAN_DOC_PATH),
                        f"FILE_SEARCH_BAN_FOR_MOUNTED_ARTIFACTS_v1.md not found at {_BAN_DOC_PATH}")


class TestMountedArtifactRoutePresent(unittest.TestCase):

    def test_mounted_route_exists(self):
        """Policy must contain a route for mounted_mnt_data_os_artifact_truth."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route,
            "Policy must contain route id='mounted_mnt_data_os_artifact_truth'")

    def test_mounted_route_matches_mnt_data(self):
        """The mounted route must match on /mnt/data."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        targets = route.get("match", {}).get("target_contains_any", [])
        self.assertIn("/mnt/data", targets,
            "Route match.target_contains_any must include '/mnt/data'")

    def test_mounted_route_matches_metablooms_os(self):
        """The mounted route must match on Metablooms_OS."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        targets = route.get("match", {}).get("target_contains_any", [])
        self.assertIn("Metablooms_OS", targets,
            "Route match.target_contains_any must include 'Metablooms_OS'")


class TestFilesearchForbiddenForMountedArtifacts(unittest.TestCase):
    """
    PROVES: mounted /mnt/data artifact work must not route to file_search.
    """

    def test_file_search_in_forbidden_tools(self):
        """file_search must be listed in forbidden_tools for the mounted artifact route."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        forbidden = route.get("forbidden_tools", [])
        self.assertIn("file_search", forbidden,
            "file_search must be in forbidden_tools for mounted_mnt_data_os_artifact_truth")

    def test_decision_is_blocking(self):
        """The mounted route decision must indicate a block, not a pass."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        decision = route.get("decision", "")
        self.assertIn("BLOCK", decision.upper(),
            f"Decision '{decision}' must contain BLOCK for the mounted artifact route")

    def test_file_search_not_in_preferred_tools_for_mounted_route(self):
        """file_search must not appear in preferred_tools for the mounted route."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        preferred = route.get("preferred_tools", [])
        self.assertNotIn("file_search", preferred,
            "file_search must NOT be a preferred tool for mounted artifact work")

    def test_global_rule_bans_file_search(self):
        """A global rule must exist that bans file_search for mounted truth."""
        policy = _load_policy()
        global_rules = policy.get("global_rules", [])
        ban_rule = next(
            (r for r in global_rules if r.get("id") == "no_file_search_for_mounted_truth"),
            None
        )
        self.assertIsNotNone(ban_rule,
            "global_rules must include id='no_file_search_for_mounted_truth'")
        self.assertEqual(ban_rule.get("severity"), "BLOCKER",
            "no_file_search_for_mounted_truth global rule must have severity=BLOCKER")


class TestPreferredToolsForMountedArtifacts(unittest.TestCase):
    """
    PROVES: direct filesystem, Python, and archive reads are the preferred
    route for mounted OS artifacts.
    """

    def test_preferred_methods_present(self):
        """The mounted route must list preferred_methods."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        methods = route.get("preferred_methods", [])
        self.assertGreater(len(methods), 0,
            "preferred_methods must be non-empty for mounted artifact route")

    def test_direct_filesystem_read_is_preferred(self):
        """A direct filesystem read method must be listed."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        methods_lower = [m.lower() for m in route.get("preferred_methods", [])]
        self.assertTrue(
            any("filesystem" in m or "direct" in m for m in methods_lower),
            f"preferred_methods must include a direct filesystem read. Got: {methods_lower}"
        )

    def test_python_read_is_preferred(self):
        """Python read must be listed as a preferred method."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        methods_lower = [m.lower() for m in route.get("preferred_methods", [])]
        self.assertTrue(
            any("python" in m for m in methods_lower),
            f"preferred_methods must include Python read. Got: {methods_lower}"
        )

    def test_archive_read_is_preferred(self):
        """Archive read (zip or tar) must be listed as a preferred method."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        methods_lower = [m.lower() for m in route.get("preferred_methods", [])]
        self.assertTrue(
            any("zip" in m or "tar" in m or "archive" in m for m in methods_lower),
            f"preferred_methods must include archive (zip/tar) read. Got: {methods_lower}"
        )

    def test_preferred_tools_include_bash_or_read(self):
        """Bash or Read must be listed as preferred tools for the mounted route."""
        policy = _load_policy()
        route = _mounted_route(policy)
        self.assertIsNotNone(route)
        preferred = route.get("preferred_tools", [])
        self.assertTrue(
            "Bash" in preferred or "Read" in preferred,
            f"preferred_tools must include Bash or Read. Got: {preferred}"
        )


class TestBanDocumentContent(unittest.TestCase):

    def _read_ban_doc(self):
        with open(_BAN_DOC_PATH, encoding="utf-8") as f:
            return f.read()

    def test_ban_doc_mentions_file_search(self):
        content = self._read_ban_doc()
        self.assertIn("file_search", content,
            "Ban document must mention 'file_search'")

    def test_ban_doc_mentions_mnt_data(self):
        content = self._read_ban_doc()
        self.assertIn("/mnt/data", content,
            "Ban document must mention '/mnt/data'")

    def test_ban_doc_mentions_preferred_alternatives(self):
        content = self._read_ban_doc()
        self.assertTrue(
            "Python" in content or "filesystem" in content.lower() or "zip" in content.lower(),
            "Ban document must mention preferred alternatives to file_search"
        )

    def test_ban_doc_mentions_forbidden_status(self):
        content = self._read_ban_doc()
        self.assertTrue(
            "FORBIDDEN" in content or "forbidden" in content or "banned" in content.lower(),
            "Ban document must state that file_search is forbidden"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
