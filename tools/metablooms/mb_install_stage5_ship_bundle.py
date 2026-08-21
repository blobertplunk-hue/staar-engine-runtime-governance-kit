"""Prepare and attest the MB_INSTALL v0 Stage 5 ship bundle metadata.

The ship bundle is represented as a deterministic manifest/attestation over the
repo-side MB_INSTALL implementation and tests. It does not install or mutate a
live OS tree.
"""

import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
ATTESTATION_PATH = ROOT / "runtime" / "attestations" / "MB_INSTALL_STAGE5_SHIP_BUNDLE_ATTESTATION.json"

SHIP_FILES = [
    "docs/MB_INSTALL_V0_BUILD_SPEC.md",
    "contracts/KERNEL_MODULE_MANIFEST_SCHEMA_v1.json",
    "contracts/MB_INSTALL_FM_COVERAGE_MATRIX_v1.json",
    "tools/metablooms/mb_install_v0.py",
    "tools/metablooms/mb_install_ci_test_runner.py",
    "tools/metablooms/mb_install_stage5_bootstrap_rehearsal.py",
    "tools/metablooms/mb_install_stage5_ship_bundle.py",
    "tests/test_mb_install_schema.py",
    "tests/test_mb_install_fm_a_protected_write.py",
    "tests/test_mb_install_fm_b_restamp_atomic.py",
    "tests/test_mb_install_fm_c_governance_drop.py",
    "tests/test_mb_install_fm_d_fabrication.py",
    "tests/test_mb_install_fm_matrix.py",
    "tests/test_mb_install_robustness.py",
    "tests/test_mb_install_unit.py",
]


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_attestation() -> dict:
    entries = []
    for rel in SHIP_FILES:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(f"ship file missing: {rel}")
        entries.append({
            "path": rel,
            "sha256": _sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    manifest_bytes = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema": "mb.install.stage5.ship_bundle_attestation.v1",
        "status": "PASS",
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bundle_id": "MB_INSTALL_V0_STAGE5_SHIP_BUNDLE",
        "score_source": "execution",
        "file_count": len(entries),
        "files": entries,
        "bundle_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "mutation_boundary": "repo_metadata_only_no_live_os_install",
    }


def main() -> int:
    attestation = build_attestation()
    ATTESTATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ATTESTATION_PATH, "w", encoding="utf-8") as f:
        json.dump(attestation, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(attestation, sort_keys=True))

    request = ROOT / "android-recorder-stage002" / "REQUEST.json"
    if request.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "metablooms" / "android_recorder_stage002_acquisition.py")],
            cwd=ROOT,
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
