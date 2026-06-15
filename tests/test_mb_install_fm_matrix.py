"""
FM coverage matrix completeness gate.

Fails if any FM row is missing from the matrix, or if any row lacks
a 'mechanism' or 'fixture' field (even if PENDING). This ensures no
failure-mode wound can be silently dropped from the matrix.
"""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "contracts" / "MB_INSTALL_FM_COVERAGE_MATRIX_v1.json"

EXPECTED_FMS = {"FM-A", "FM-B", "FM-C", "FM-D"}


class TestFmMatrixCompleteness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(MATRIX_PATH, encoding="utf-8") as f:
            cls.matrix = json.load(f)

    def test_matrix_file_loads(self):
        self.assertIn("rows", self.matrix)

    def test_all_four_fm_rows_present(self):
        fms_found = {row.get("fm") for row in self.matrix["rows"]}
        missing = EXPECTED_FMS - fms_found
        self.assertEqual(missing, set(), f"Missing FM rows: {missing}")

    def test_every_row_has_mechanism(self):
        for row in self.matrix["rows"]:
            fm = row.get("fm", "?")
            self.assertIn("mechanism", row, f"{fm}: missing 'mechanism' field")
            self.assertTrue(row["mechanism"], f"{fm}: 'mechanism' must not be empty")

    def test_every_row_has_fixture(self):
        for row in self.matrix["rows"]:
            fm = row.get("fm", "?")
            self.assertIn("fixture", row, f"{fm}: missing 'fixture' field")
            self.assertTrue(row["fixture"], f"{fm}: 'fixture' must not be empty")

    def test_fm_d_fixture_points_to_real_file(self):
        rows = {row["fm"]: row for row in self.matrix["rows"]}
        fm_d = rows["FM-D"]
        fixture = fm_d["fixture"]
        self.assertNotIn("PENDING", fixture, "FM-D fixture must not be PENDING")
        # Extract the file path portion (before ::)
        fixture_file = fixture.split("::")[0]
        fixture_path = ROOT / fixture_file
        self.assertTrue(
            fixture_path.exists(),
            f"FM-D fixture file not found: {fixture_path}"
        )

    def test_pending_rows_are_correctly_marked(self):
        rows = {row["fm"]: row for row in self.matrix["rows"]}
        for fm in ("FM-A", "FM-B", "FM-C"):
            fixture = rows[fm]["fixture"]
            self.assertTrue(
                fixture.startswith("PENDING_STAGE_"),
                f"{fm}: expected PENDING_STAGE_N marker, got {fixture!r}"
            )


if __name__ == "__main__":
    unittest.main()
