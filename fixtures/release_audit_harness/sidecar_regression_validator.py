#!/usr/bin/env python3
"""Sidecar regression validator for MetaBlooms release audit harness.

Covers the three runner self-test gaps identified in FIND-01, FIND-02, FIND-09:
  1. sidecar_wrong_hash  — sidecar present with wrong (but valid 64-hex) hash -> FAIL
  2. sidecar_malformed   — sidecar present with non-hex content              -> BLOCKED
  3. tar_zst_artifact    — artifact extension is .tar.zst (unsupported)       -> BLOCKED

Runs the existing release_audit_harness_runner_v1.py via subprocess so the runner
itself is not modified.  Pass --runner <path> if the runner is not at the default
relative location.

Exit code: 0 if all cases match expected decisions, 1 otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


RUNNER_DEFAULT = Path(__file__).resolve().parents[2] / (
    "runtime/cartridges/release_audit_harness_v1/release_audit_harness_runner_v1.py"
)

DEFAULT_ROOT = "Metablooms_OS"
REQUIRED_MEMBERS = [
    f"{DEFAULT_ROOT}/scripts/mpp/mpp.sh",
    f"{DEFAULT_ROOT}/METABLOOMS_PREBOOT_RESCUE_v1.sh",
    f"{DEFAULT_ROOT}/scripts/boot/METABLOOMS_PREBOOT_RESCUE_v1.sh",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_valid_zip(path: Path) -> str:
    """Create a minimal valid ZIP with all required members. Returns actual SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for member in REQUIRED_MEMBERS:
            z.writestr(member, "# fixture\n")
    digest = sha256_bytes(path.read_bytes())
    return digest


def run_runner(runner: Path, artifact: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-S", str(runner),
         "--artifact", str(artifact),
         "--out-dir", str(out_dir),
         "--expected-root", DEFAULT_ROOT,
         "--clean"],
        capture_output=True,
        text=True,
    )
    result_file = out_dir / "audit_result.json"
    if result_file.exists():
        return json.loads(result_file.read_text())
    return {"verdict": "RUNNER_ERROR", "runner_stderr": result.stderr[-2000:]}


def case_sidecar_wrong_hash(runner: Path, tmp: Path) -> tuple[bool, str]:
    """FIND-01: sidecar present with wrong (valid 64-hex) hash -> artifact_sha_sidecar FAIL."""
    artifact = tmp / "wrong_sidecar.zip"
    actual_sha = make_valid_zip(artifact)
    wrong_sha = "a" * 64  # valid 64-hex, definitely not the real digest
    sidecar = Path(str(artifact) + ".sha256")
    sidecar.write_text(f"{wrong_sha}  wrong_sidecar.zip\n")

    result = run_runner(runner, artifact, tmp / "wrong_sidecar_out")
    verdict = result.get("verdict", "")
    checks = {c["check_id"]: c["decision"] for c in result.get("checks", [])}
    sidecar_decision = checks.get("artifact_sha_sidecar", "MISSING")

    ok = verdict in {"FAIL", "BLOCKED"} and sidecar_decision == "FAIL"
    note = (
        f"verdict={verdict} artifact_sha_sidecar={sidecar_decision} "
        f"(actual={actual_sha[:8]}... wrong={wrong_sha[:8]}...)"
    )
    return ok, note


def case_sidecar_malformed(runner: Path, tmp: Path) -> tuple[bool, str]:
    """FIND-02: sidecar present with non-hex content -> artifact_sha_sidecar BLOCKED."""
    artifact = tmp / "malformed_sidecar.zip"
    make_valid_zip(artifact)
    sidecar = Path(str(artifact) + ".sha256")
    sidecar.write_text("not-a-valid-hash\n")

    result = run_runner(runner, artifact, tmp / "malformed_sidecar_out")
    verdict = result.get("verdict", "")
    checks = {c["check_id"]: c["decision"] for c in result.get("checks", [])}
    sidecar_decision = checks.get("artifact_sha_sidecar", "MISSING")

    ok = verdict in {"FAIL", "BLOCKED"} and sidecar_decision == "BLOCKED"
    note = f"verdict={verdict} artifact_sha_sidecar={sidecar_decision}"
    return ok, note


def case_tar_zst_blocked(runner: Path, tmp: Path) -> tuple[bool, str]:
    """FIND-06/09: artifact extension is .tar.zst -> artifact_extension BLOCKED.

    Note: FIND-05 (partial archive on timeout) is not exercised here because it
    requires mocking subprocess timeout.  It is documented in the audit report.
    """
    artifact = tmp / "fixture.tar.zst"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"\x28\xb5\x2f\xfd\x04\x00")  # minimal zstd magic header

    result = run_runner(runner, artifact, tmp / "tar_zst_out")
    verdict = result.get("verdict", "")
    checks = {c["check_id"]: c["decision"] for c in result.get("checks", [])}
    ext_decision = checks.get("artifact_extension", "MISSING")

    ok = verdict in {"FAIL", "BLOCKED"} and ext_decision == "BLOCKED"
    note = f"verdict={verdict} artifact_extension={ext_decision}"
    return ok, note


CASES = [
    ("sidecar_wrong_hash",  case_sidecar_wrong_hash,  "FIND-01"),
    ("sidecar_malformed",   case_sidecar_malformed,    "FIND-02"),
    ("tar_zst_blocked",     case_tar_zst_blocked,      "FIND-06/09"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", type=Path, default=RUNNER_DEFAULT,
                    help="Path to release_audit_harness_runner_v1.py")
    args = ap.parse_args()

    runner = args.runner.resolve()
    if not runner.exists():
        print(f"RUNNER_NOT_FOUND: {runner}", file=sys.stderr)
        print("Pass --runner <path> if the harness runner is not at the default location.")
        return 2

    results = []
    with tempfile.TemporaryDirectory(prefix="mb_sidecar_regression_") as td:
        tmp = Path(td)
        for name, fn, find_id in CASES:
            ok, note = fn(runner, tmp / name)
            status = "PASS" if ok else "FAIL"
            results.append({"case": name, "find_id": find_id, "status": status, "note": note})
            print(f"[{status}] {name} ({find_id}): {note}")

    summary = {
        "schema": "mb.fixtures.sidecar_regression_validator.result.v1",
        "runner": str(runner),
        "decision": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
        "cases": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
