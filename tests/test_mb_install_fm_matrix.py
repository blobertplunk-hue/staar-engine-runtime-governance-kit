"""
FM coverage matrix completeness gate.

Fails if any FM row is missing from the matrix, if any row lacks
a 'mechanism' or 'fixture' field, or if a live FM fixture points
to a missing test file.
"""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "contracts" / "MB_INSTALL_FM_COVERAGE_MATRIX_v1.json"

EXPECTED_FMS = {"FM-A", "FM-B", "FM-C", "FM-D"}
LIVE_FMS = EXPECTED_FMS
PENDING_FMS = set()


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

    def test_live_fixtures_point_to_real_files(self):
        rows = {row["fm"]: row for row in self.matrix["rows"]}
        for fm in LIVE_FMS:
            fixture = rows[fm]["fixture"]
            self.assertNotIn("PENDING", fixture, f"{fm}: fixture must not be PENDING")
            fixture_file = fixture.split("::")[0]
            fixture_path = ROOT / fixture_file
            self.assertTrue(
                fixture_path.exists(),
                f"{fm}: fixture file not found: {fixture_path}"
            )

    def test_no_pending_rows_remain_after_stage_3(self):
        rows = {row["fm"]: row for row in self.matrix["rows"]}
        for fm in PENDING_FMS:
            fixture = rows[fm]["fixture"]
            self.assertTrue(
                fixture.startswith("PENDING_STAGE_"),
                f"{fm}: expected PENDING_STAGE_N marker, got {fixture!r}"
            )
        for row in self.matrix["rows"]:
            self.assertNotIn("PENDING", row["fixture"], f"{row['fm']}: no PENDING rows after Stage 3")


if __name__ == "__main__":
    unittest.main()
