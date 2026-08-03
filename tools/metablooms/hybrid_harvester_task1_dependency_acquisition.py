"""Acquire and attest the exact Hybrid Resource Harvester Task 1 npm graph.

This helper is temporary PR-only acquisition infrastructure. It writes one JSON
attestation into runtime/attestations so the repository's existing artifact
uploader returns the lockfile and deterministic node_modules archive.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / "dependency-acquisition"
OUT = ROOT / "runtime" / "attestations" / "HYBRID_RESOURCE_HARVESTER_TASK1_DEPENDENCIES.json"
ARCHIVE = WORK / "node_modules.tgz"
EXPECTED = {
    "playwright": "1.61.1",
    "fast-xml-parser": "5.10.1",
    "parse5": "8.0.1",
    "pdfjs-dist": "6.1.200",
    "yauzl": "3.4.0",
    "file-type": "22.0.1",
    "minisearch": "7.2.0",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        list(args),
        cwd=WORK,
        env={**os.environ, "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1"},
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return completed.stdout or ""


def main() -> int:
    run("npm", "install", "--ignore-scripts", "--omit=optional", "--no-audit", "--no-fund")
    npm_ls_text = run("npm", "ls", "--depth=0", capture=True)
    npm_ls_json = json.loads(run("npm", "ls", "--depth=0", "--json", capture=True))

    import_probe = run(
        "node",
        "--input-type=module",
        "-e",
        """
import { readFile } from 'node:fs/promises';
const expected = {
  playwright: '1.61.1',
  'fast-xml-parser': '5.10.1',
  parse5: '8.0.1',
  'pdfjs-dist': '6.1.200',
  yauzl: '3.4.0',
  'file-type': '22.0.1',
  minisearch: '7.2.0'
};
for (const [name, version] of Object.entries(expected)) {
  const pkg = JSON.parse(await readFile(`node_modules/${name}/package.json`, 'utf8'));
  if (pkg.version !== version) throw new Error(`${name}: expected ${version}, got ${pkg.version}`);
}
await import('playwright');
await import('fast-xml-parser');
await import('parse5');
await import('pdfjs-dist/legacy/build/pdf.mjs');
await import('yauzl');
await import('file-type');
await import('minisearch');
console.log('IMPORT_PROBE=PASS');
""",
        capture=True,
    )

    run(
        "tar",
        "--sort=name",
        "--mtime=UTC 2026-08-03",
        "--owner=0",
        "--group=0",
        "--numeric-owner",
        "-czf",
        str(ARCHIVE),
        "node_modules",
    )

    lockfile = WORK / "package-lock.json"
    package_json = WORK / "package.json"
    direct = {
        name: json.loads((WORK / "node_modules" / name / "package.json").read_text(encoding="utf-8"))["version"]
        for name in EXPECTED
    }
    if direct != EXPECTED:
        raise RuntimeError(f"direct dependency mismatch: {direct!r}")

    attestation = {
        "schema": "mb.hybrid_resource_harvester.task1.dependencies.v1",
        "status": "PASS",
        "node_version": run("node", "--version", capture=True).strip(),
        "npm_version": run("npm", "--version", capture=True).strip(),
        "install_command": "npm install --ignore-scripts --omit=optional --no-audit --no-fund",
        "direct_dependencies": direct,
        "npm_ls": npm_ls_json,
        "npm_ls_text": npm_ls_text,
        "import_probe": import_probe,
        "package_json_sha256": sha256(package_json),
        "package_lock_sha256": sha256(lockfile),
        "node_modules_tgz_sha256": sha256(ARCHIVE),
        "package_lock_text": lockfile.read_text(encoding="utf-8"),
        "node_modules_tgz_base64": base64.b64encode(ARCHIVE.read_bytes()).decode("ascii"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(attestation, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in attestation.items() if not key.endswith("_base64") and key != "package_lock_text"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
