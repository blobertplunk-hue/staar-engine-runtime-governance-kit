"""MB_INSTALL v0 — staged-shadow-apply install primitive.

Stage 4: FM-D (verify_bundle), FM-A (check_protected_writes), FM-B
(atomic sidecar restamp helper), FM-C (receipt validation helper), and a
throwaway-target-only atomic_swap implementation are present. Stage 5 bootstrap
rehearsal and ship bundle remain pending.
"""

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Optional

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


class ReceiptValidationError(ManifestError):
    pass


class AtomicSwapError(ManifestError):
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


def stage_to_tmp(
    manifest: dict[str, Any],
    zip_path: str,
    *,
    staging_root: Optional[str] = None,
) -> str:
    """Copy bundle files into a fresh tmp staging dir; re-verify staged bytes.

    staging_root is optional. When supplied by a controlled rehearsal harness,
    the temporary staging tree is created inside that root so later containment
    gates can prove both staged and target trees share the same throwaway root.
    """
    verify_bundle(zip_path)
    tmp_dir = tempfile.mkdtemp(prefix="mb_install_stage_", dir=staging_root)
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


def _assert_within_directory(candidate: str, root: str) -> None:
    candidate_path = Path(candidate).resolve()
    root_path = Path(root).resolve()
    if candidate_path == root_path:
        return
    try:
        candidate_path.relative_to(root_path)
    except ValueError as exc:
        raise AtomicSwapError(
            f"Atomic swap target {candidate_path} is outside allowed throwaway root {root_path}"
        ) from exc


def atomic_swap(
    tmp_tree: str,
    target_tree: Optional[str] = None,
    *,
    allowed_root: Optional[str] = None,
    _bootstrap_flag: bool = False,
) -> None:
    """Swap a staged tree into an explicitly allowed throwaway target.

    Stage 4 still refuses by default. A caller must provide _bootstrap_flag=True,
    a target_tree, and an allowed_root. The target must resolve inside allowed_root.
    This is intentionally suitable only for CI/bootstrap rehearsal throwaway trees.
    """
    if not _bootstrap_flag:
        raise NotImplementedError(
            "atomic_swap is disabled unless _bootstrap_flag=True is supplied by "
            "the controlled bootstrap/CI harness."
        )
    if target_tree is None or allowed_root is None:
        raise AtomicSwapError("atomic_swap requires target_tree and allowed_root")
    if not os.path.isdir(tmp_tree):
        raise AtomicSwapError(f"tmp_tree must be an existing directory: {tmp_tree!r}")

    tmp_path = str(Path(tmp_tree).resolve())
    target_path = str(Path(target_tree).resolve())
    allowed_path = str(Path(allowed_root).resolve())
    _assert_within_directory(target_path, allowed_path)
    _assert_within_directory(tmp_path, allowed_path)

    backup_path = target_path + ".mb_install_backup"
    if os.path.exists(backup_path):
        raise AtomicSwapError(f"Backup path already exists: {backup_path!r}")

    backup_created = False
    try:
        if os.path.exists(target_path):
            os.replace(target_path, backup_path)
            backup_created = True
        os.replace(tmp_path, target_path)
    except Exception:
        if backup_created and not os.path.exists(target_path) and os.path.exists(backup_path):
            os.replace(backup_path, target_path)
        raise
    else:
        if backup_created:
            shutil.rmtree(backup_path)


def restamp_sidecars(touched_files: list[str]) -> dict[str, str]:
    """Recompute .sha256 sidecars using same-directory temp files and os.replace (FM-B)."""
    results: dict[str, str] = {}
    for filepath in touched_files:
        filepath = os.fspath(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        digest = _sha256_bytes(data)
        sidecar_path = filepath + ".sha256"
        sidecar_dir = os.path.dirname(sidecar_path) or "."
        fd, tmp_path = tempfile.mkstemp(
            prefix=os.path.basename(sidecar_path) + ".",
            suffix=".tmp",
            dir=sidecar_dir,
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(digest + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, sidecar_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            raise
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
    File paths and governance contracts are sorted so equivalent manifests produce
    the same receipt shape.
    """
    if score_source != "execution":
        raise ReceiptValidationError(
            f"Install receipts must use score_source='execution', got {score_source!r}"
        )
    return {
        "install_id": install_id,
        "module_id": manifest.get("id"),
        "semver": manifest.get("semver"),
        "score_source": score_source,
        "files_installed": sorted(e["path"] for e in manifest.get("files", [])),
        "governance_contracts": sorted(manifest.get("governance_contracts", [])),
    }


def validate_receipt(receipt: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Validate receipt completeness for governance-drop detection (FM-C)."""
    required_keys = {"install_id", "module_id", "semver", "score_source", "files_installed"}
    missing = required_keys - set(receipt)
    if missing:
        raise ReceiptValidationError(f"Receipt missing required key(s): {sorted(missing)!r}")
    if receipt["score_source"] != "execution":
        raise ReceiptValidationError("Receipt score_source must be 'execution'")
    expected_files = sorted(e["path"] for e in manifest.get("files", []))
    if receipt["files_installed"] != expected_files:
        raise ReceiptValidationError("Receipt files_installed does not match manifest")
    expected_contracts = sorted(manifest.get("governance_contracts", []))
    if expected_contracts and receipt.get("governance_contracts") != expected_contracts:
        raise ReceiptValidationError("Receipt governance_contracts does not match manifest")
