#!/usr/bin/env python3
"""Generate a deterministic TSV manifest for a GitHub repository checkout.

This is intentionally dependency-free so it can run in GitHub Actions and in the
ChatGPT sandbox. It does not mutate the repository. It walks a checkout,
excludes VCS/output artifacts, hashes files, and writes a manifest plus receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, List

DEFAULT_EXCLUDES = (
    ".git/",
    "github_main_manifest.tsv",
    "github_main_manifest.tsv.sha256",
    "github_manifest_receipt.json",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_excluded(rel: str, excludes: Iterable[str]) -> bool:
    rel_norm = rel.replace(os.sep, "/")
    for ex in excludes:
        ex_norm = ex.replace(os.sep, "/")
        if ex_norm.endswith("/") and rel_norm.startswith(ex_norm):
            return True
        if rel_norm == ex_norm:
            return True
    return False


def iter_files(root: Path, excludes: Iterable[str]) -> Iterable[Path]:
    root = root.resolve()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        if is_excluded(rel, excludes):
            if path.is_dir():
                # rglob cannot be pruned directly; children are filtered by prefix.
                pass
            continue
        if path.is_file() and not path.is_symlink():
            yield path


def write_manifest(root: Path, output: Path, receipt: Path, excludes: List[str]) -> dict:
    root = root.resolve()
    output = output.resolve()
    receipt = receipt.resolve()
    rows = []
    for path in iter_files(root, excludes):
        rel = path.relative_to(root).as_posix()
        st = path.stat()
        executable = "1" if (st.st_mode & 0o111) else "0"
        rows.append((rel, str(st.st_size), sha256_file(path), executable))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("path\tsize\tsha256\texecutable_bit\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")
    manifest_sha = sha256_file(output)
    sha_path = output.with_name(output.name + ".sha256")
    sha_path.write_text(f"{manifest_sha}  {output.name}\n", encoding="utf-8")
    result = {
        "schema": "mb.github_os_sync.github_repo_manifest_receipt.v1",
        "decision": "PASS",
        "root": str(root),
        "manifest": str(output),
        "manifest_sha256": manifest_sha,
        "file_count": len(rows),
        "columns": ["path", "size", "sha256", "executable_bit"],
        "excludes": excludes,
        "github_ref": os.environ.get("GITHUB_REF", ""),
        "github_sha": os.environ.get("GITHUB_SHA", ""),
        "github_repository": os.environ.get("GITHUB_REPOSITORY", ""),
    }
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate GitHub checkout manifest TSV")
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="github_main_manifest.tsv")
    ap.add_argument("--receipt", default="github_manifest_receipt.json")
    ap.add_argument("--exclude", action="append", default=[])
    args = ap.parse_args()
    excludes = list(DEFAULT_EXCLUDES) + list(args.exclude)
    result = write_manifest(Path(args.root), Path(args.output), Path(args.receipt), excludes)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
