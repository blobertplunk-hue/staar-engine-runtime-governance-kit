"""MB_INSTALL v0 Stage 5 bootstrap rehearsal against a throwaway target tree.

This script intentionally uses only temporary directories. It builds a small valid
bundle, verifies it, stages it, swaps it into a throwaway target under an explicit
allowed_root, restamps sidecars, emits and validates a receipt, and writes an
attestation JSON.
"""

import hashlib
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import zipfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

verify_bundle = _mod.verify_bundle
check_protected_writes = _mod.check_protected_writes
stage_to_tmp = _mod.stage_to_tmp
atomic_swap = _mod.atomic_swap
restamp_sidecars = _mod.restamp_sidecars
write_receipt = _mod.write_receipt
validate_receipt = _mod.validate_receipt

ATTESTATION_PATH = ROOT / "runtime" / "attestations" / "MB_INSTALL_STAGE5_BOOTSTRAP_REHEARSAL_ATTESTATION.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_rehearsal_bundle(path: str) -> dict:
    payloads = {
        "tools/stage5_payload.txt": b"stage5 throwaway payload\n",
        "contracts/stage5_governance_contract.json": b'{"contract":"stage5"}\n',
    }
    manifest = {
        "id": "mb-install-stage5-rehearsal",
        "semver": "0.5.0",
        "provides": ["mb_install.stage5.rehearsal"],
        "requires": [],
        "governance_contracts": ["contracts/stage5_governance_contract.json"],
        "files": [
            {
                "path": name,
                "sha256": _sha256(content),
                "size_bytes": len(content),
                "protected_class": False,
            }
            for name, content in sorted(payloads.items())
        ],
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
        for name, content in sorted(payloads.items()):
            zf.writestr(name, content)
    return manifest


def run_rehearsal() -> dict:
    with tempfile.TemporaryDirectory(prefix="mb_install_stage5_allowed_") as allowed_root:
        bundle_path = os.path.join(allowed_root, "bundle.zip")
        expected_manifest = _write_rehearsal_bundle(bundle_path)
        manifest = verify_bundle(bundle_path)
        if manifest != expected_manifest:
            raise AssertionError("Verified manifest changed during bundle read")
        check_protected_writes(manifest, "")

        tmp_tree = stage_to_tmp(manifest, bundle_path, staging_root=allowed_root)
        target_tree = os.path.join(allowed_root, "target")
        os.makedirs(target_tree, exist_ok=True)
        with open(os.path.join(target_tree, "old.txt"), "w", encoding="utf-8") as f:
            f.write("old target content\n")

        atomic_swap(tmp_tree, target_tree, allowed_root=allowed_root, _bootstrap_flag=True)

        touched_files = []
        for entry in manifest["files"]:
            touched_files.append(os.path.join(target_tree, *pathlib.PurePosixPath(entry["path"]).parts))
        sidecars = restamp_sidecars(touched_files)
        receipt = write_receipt(manifest, install_id="stage5-bootstrap-rehearsal")
        validate_receipt(receipt, manifest)

        for path in touched_files:
            if not os.path.exists(path):
                raise AssertionError(f"Expected staged payload missing: {path}")
            if not os.path.exists(path + ".sha256"):
                raise AssertionError(f"Expected sidecar missing: {path}.sha256")

        return {
            "schema": "mb.install.stage5.bootstrap_rehearsal.v1",
            "status": "PASS",
            "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "allowed_root_basename": os.path.basename(allowed_root),
            "target_tree_basename": os.path.basename(target_tree),
            "module_id": manifest["id"],
            "files_installed": receipt["files_installed"],
            "governance_contracts": receipt["governance_contracts"],
            "sidecars_restamped": sorted(os.path.relpath(path, target_tree) for path in sidecars),
            "mutation_boundary": "temporary_directory_only",
        }


def main() -> int:
    attestation = run_rehearsal()
    ATTESTATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ATTESTATION_PATH, "w", encoding="utf-8") as f:
        json.dump(attestation, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(attestation, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
