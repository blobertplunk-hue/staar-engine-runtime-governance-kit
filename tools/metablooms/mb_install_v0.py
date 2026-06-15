"""MB_INSTALL v0 — staged-shadow-apply install primitive.

Stage 1: skeleton with FM-D (verify_bundle), FM-A (check_protected_writes),
FM-B (restamp_sidecars) implemented. atomic_swap is guarded NotImplemented
and will not run without the explicit bootstrap flag (set only in stage 4+).
"""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

_ALLOWED_PREFIXES = ("0_kernel/", "tools/", "contracts/", "schemas/")


class ManifestError(Exception):
    pass


class HashMismatchError(ManifestError):
    pass


class ProtectedWriteError(ManifestError):
    pass


class PathViolationError(ManifestError):
    pass


def _validate_path(path: str) -> None:
    if os.path.isabs(path):
        raise PathViolationError(f"Absolute path forbidden: {path!r}")
    parts = Path(path).parts
    if ".." in parts:
        raise PathViolationError(f"Path traversal forbidden: {path!r}")
    if not any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
        raise PathViolationError(
            f"Path outside allowed trees {_ALLOWED_PREFIXES}: {path!r}"
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_bundle(zip_path: str) -> dict[str, Any]:
    """Open zip, load manifest, hash every listed file's bytes; fail on any mismatch (FM-D)."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        try:
            manifest_bytes = zf.read("manifest.json")
        except KeyError:
            raise ManifestError("Bundle missing manifest.json")

        try:
            manifest: dict[str, Any] = json.loads(manifest_bytes)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"manifest.json is not valid JSON: {exc}") from exc

        for entry in manifest.get("files", []):
            path = entry["path"]
            _validate_path(path)

            try:
                actual_bytes = zf.read(path)
            except KeyError:
                raise ManifestError(
                    f"Manifest declares {path!r} but file is absent from the bundle"
                )

            actual_hash = _sha256_bytes(actual_bytes)
            declared_hash = entry["sha256"]
            if actual_hash != declared_hash:
                raise HashMismatchError(
                    f"Hash mismatch for {path!r}: "
                    f"declared={declared_hash!r} actual={actual_hash!r}"
                )

            actual_size = len(actual_bytes)
            declared_size = entry["size_bytes"]
            if actual_size != declared_size:
                raise ManifestError(
                    f"Size mismatch for {path!r}: "
                    f"declared={declared_size} actual={actual_size}"
                )

    return manifest


def check_protected_writes(manifest: dict[str, Any], authorize_token: str) -> None:
    """Fail closed if any protected_class file is present without a non-empty token (FM-A)."""
    protected = [e for e in manifest.get("files", []) if e.get("protected_class")]
    if protected and not (authorize_token and authorize_token.strip()):
        raise ProtectedWriteError(
            f"Bundle contains {len(protected)} protected file(s) "
            "but no authorization token was provided"
        )


def stage_to_tmp(manifest: dict[str, Any], zip_path: str) -> str:
    """Copy bundle files into a fresh tmp staging dir; re-verify staged bytes against manifest."""
    tmp_dir = tempfile.mkdtemp(prefix="mb_install_stage_")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for entry in manifest.get("files", []):
                path = entry["path"]
                _validate_path(path)
                data = zf.read(path)
                staged_hash = _sha256_bytes(data)
                if staged_hash != entry["sha256"]:
                    raise HashMismatchError(
                        f"Staging hash mismatch for {path!r} — bundle may have been modified"
                    )
                dest = os.path.join(tmp_dir, path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    return tmp_dir


def atomic_swap(tmp_tree: str, *, _bootstrap_flag: bool = False) -> None:
    """Live-tree swap.

    Stage 1 guard: raises NotImplementedError unless _bootstrap_flag=True.
    The flag is set only by the bootstrap harness introduced in stage 4.
    Tests in stages 1–3 never set it, making live-tree mutation impossible.
    """
    if not _bootstrap_flag:
        raise NotImplementedError(
            "atomic_swap is disabled in stage 1. "
            "Pass _bootstrap_flag=True only from the bootstrap harness (stage 4+)."
        )
    # Real implementation lands in stage 4.
    raise NotImplementedError("atomic_swap real implementation not yet built (stage 4+)")


def restamp_sidecars(touched_files: list[str]) -> dict[str, str]:
    """Recompute and write .sha256 sidecar for every file in the same call (FM-B).

    Returns a mapping of filepath → hex digest.
    """
    results: dict[str, str] = {}
    for filepath in touched_files:
        filepath = os.fspath(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        digest = _sha256_bytes(data)
        sidecar_path = filepath + ".sha256"
        with open(sidecar_path, "w", encoding="utf-8") as f:
            f.write(digest + "\n")
        results[filepath] = digest
    return results


def write_receipt(
    manifest: dict[str, Any],
    install_id: str,
    *,
    score_source: str = "execution",
) -> dict[str, Any]:
    """Return a deterministic install receipt dict.

    score_source must be 'execution' for real installs (FM-C invariant).
    """
    return {
        "install_id": install_id,
        "module_id": manifest.get("id"),
        "semver": manifest.get("semver"),
        "score_source": score_source,
        "files_installed": [e["path"] for e in manifest.get("files", [])],
    }
