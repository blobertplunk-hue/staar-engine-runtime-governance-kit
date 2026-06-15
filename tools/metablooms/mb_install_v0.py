"""MB_INSTALL v0 — staged-shadow-apply install primitive.

Stage 1: skeleton with FM-D (verify_bundle), FM-A (check_protected_writes),
FM-B (restamp_sidecars helper) implemented. atomic_swap is guarded
NotImplemented and will not run without the explicit bootstrap flag (set only
in stage 4+).
"""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import PurePosixPath
from typing import Any

_ALLOWED_PREFIXES = ("0_kernel/", "tools/", "contracts/", "schemas/")
_MANIFEST_NAME = "manifest.json"


class ManifestError(Exception):
    pass


class HashMismatchError(ManifestError):
    pass


class ProtectedWriteError(ManifestError):
    pass


class PathViolationError(ManifestError):
    pass


class DuplicatePathError(ManifestError):
    pass


class UndeclaredPayloadError(ManifestError):
    pass


def _validate_path(path: str) -> None:
    if not isinstance(path, str) or not path:
        raise PathViolationError(f"Path must be a non-empty string: {path!r}")
    if "\\" in path:
        raise PathViolationError(f"Backslash path separators forbidden: {path!r}")
    if path.startswith("/") or os.path.isabs(path):
        raise PathViolationError(f"Absolute path forbidden: {path!r}")
    if path.startswith("./") or "/./" in path or path.endswith("/."):
        raise PathViolationError(f"Dot path segment forbidden: {path!r}")
    if "//" in path:
        raise PathViolationError(f"Empty path segment forbidden: {path!r}")

    pure = PurePosixPath(path)
    if ".." in pure.parts:
        raise PathViolationError(f"Path traversal forbidden: {path!r}")
    if not any(path.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
        raise PathViolationError(
            f"Path outside allowed trees {_ALLOWED_PREFIXES}: {path!r}"
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0o170000
    return mode == 0o120000


def _payload_names(zf: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for info in zf.infolist():
        name = info.filename
        if name in seen:
            raise DuplicatePathError(f"Duplicate zip member forbidden: {name!r}")
        seen.add(name)
        if name == _MANIFEST_NAME or info.is_dir():
            continue
        if _zip_member_is_symlink(info):
            raise PathViolationError(f"Symlink zip member forbidden: {name!r}")
        _validate_path(name)
        names.append(name)
    return names


def _declared_paths(manifest: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for entry in manifest.get("files", []):
        path = entry["path"]
        _validate_path(path)
        if path in seen:
            raise DuplicatePathError(f"Duplicate manifest file path forbidden: {path!r}")
        seen.add(path)
        paths.append(path)
    return paths


def verify_bundle(zip_path: str) -> dict[str, Any]:
    """Open zip, load manifest, hash every listed file's bytes; fail on any mismatch (FM-D)."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        try:
            manifest_bytes = zf.read(_MANIFEST_NAME)
        except KeyError:
            raise ManifestError("Bundle missing manifest.json")

        try:
            manifest: dict[str, Any] = json.loads(manifest_bytes)
        except json.JSONDecodeError as exc:
            raise ManifestError(f"manifest.json is not valid JSON: {exc}") from exc

        declared = _declared_paths(manifest)
        actual_payloads = _payload_names(zf)
        declared_set = set(declared)
        actual_set = set(actual_payloads)
        extra = actual_set - declared_set
        missing = declared_set - actual_set
        if extra:
            raise UndeclaredPayloadError(
                f"Bundle contains undeclared payload file(s): {sorted(extra)!r}"
            )
        if missing:
            raise ManifestError(
                f"Manifest declares absent payload file(s): {sorted(missing)!r}"
            )

        for entry in manifest.get("files", []):
            path = entry["path"]
            actual_bytes = zf.read(path)

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
    verify_bundle(zip_path)
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
                dest = os.path.join(tmp_dir, *PurePosixPath(path).parts)
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
    """Recompute and write .sha256 sidecars for every file in this helper call (FM-B skeleton).

    Stage 1 provides the helper and unit coverage. The stronger FM-B atomic-write fixture
    and any temp+replace behavior land in Stage 3.
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
    File paths are sorted so equivalent manifests produce the same receipt shape.
    """
    return {
        "install_id": install_id,
        "module_id": manifest.get("id"),
        "semver": manifest.get("semver"),
        "score_source": score_source,
        "files_installed": sorted(e["path"] for e in manifest.get("files", [])),
    }
