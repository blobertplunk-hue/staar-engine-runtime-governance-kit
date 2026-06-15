"""FM-C governance-drop receipt fixture for MB_INSTALL v0 Stage 3."""

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

write_receipt = _mod.write_receipt
validate_receipt = _mod.validate_receipt
ReceiptValidationError = _mod.ReceiptValidationError


def _manifest() -> dict:
    return {
        "id": "fm-c-test-module",
        "semver": "0.3.0",
        "provides": [],
        "requires": [],
        "governance_contracts": ["contracts/governance/fm-c-contract.json"],
        "files": [
            {
                "path": "contracts/fm_c_payload.json",
                "sha256": "a" * 64,
                "size_bytes": 2,
                "protected_class": False,
            }
        ],
    }


class TestFmCGovernanceDrop(unittest.TestCase):

    def test_receipt_preserves_governance_contracts(self):
        manifest = _manifest()
        receipt = write_receipt(manifest, install_id="run-fm-c")
        self.assertEqual(receipt["governance_contracts"], manifest["governance_contracts"])
        validate_receipt(receipt, manifest)

    def test_validate_receipt_rejects_governance_contract_drop(self):
        manifest = _manifest()
        receipt = write_receipt(manifest, install_id="run-fm-c")
        del receipt["governance_contracts"]
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(receipt, manifest)

    def test_validate_receipt_rejects_inferred_score_source(self):
        manifest = _manifest()
        receipt = write_receipt(manifest, install_id="run-fm-c")
        receipt["score_source"] = "inferred"
        with self.assertRaises(ReceiptValidationError):
            validate_receipt(receipt, manifest)

    def test_write_receipt_rejects_non_execution_score_source(self):
        with self.assertRaises(ReceiptValidationError):
            write_receipt(_manifest(), install_id="run-fm-c", score_source="inferred")


if __name__ == "__main__":
    unittest.main()
