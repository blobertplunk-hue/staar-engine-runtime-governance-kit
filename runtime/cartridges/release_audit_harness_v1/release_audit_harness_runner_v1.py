#!/usr/bin/env python3
"""Remote-safe MetaBlooms release audit harness runner.

Stdlib-first CI-safe release auditor for ZIP, ZIP.ZST, and TAR.ZST
MetaBlooms artifacts. It emits an audit result/report/packet and bounded
self-tests for regression coverage.
"""
from __future__ import annotations

import argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tarfile, tempfile, time, zipfile
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from collections import Counter

SCHEMA = "metablooms.release_audit_harness.remote_runner.v1"
VERSION = "1.3.0-stage001-tar-zst"
DEFAULT_ROOT = "Metablooms_OS"
REQUIRED = [
    "{root}/scripts/mpp/mpp.sh",
    "{root}/METABLOOMS_PREBOOT_RESCUE_v1.sh",
    "{root}/scripts/boot/METABLOOMS_PREBOOT_RESCUE_v1.sh",
]


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def sidecar_hash(path: Path) -> str | None:
    side = Path(str(path) + ".sha256")
    if not side.exists():
        return None
    parts = side.read_text(errors="replace").split()
    first = parts[0] if parts else ""
    return first.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", first) else None


def run_text(cmd: list[str], cwd: Path | None = None, timeout: int = 120):
    started = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
        return {"cmd": cmd, "cwd": str(cwd) if cwd else None, "returncode": p.returncode, "elapsed": round(time.time()-started, 3), "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:]}
    except subprocess.TimeoutExpired as e:
        return {"cmd": cmd, "cwd": str(cwd) if cwd else None, "returncode": "TIMEOUT", "elapsed": round(time.time()-started, 3), "stdout_tail": str(e.stdout or "")[-3000:], "stderr_tail": str(e.stderr or "")[-3000:]}


def run_binary_to_file(cmd: list[str], target: Path, timeout: int = 180):
    started = time.time()
    try:
        with target.open("wb") as f:
            p = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=timeout)
        stderr_tail = (p.stderr or b"")[-3000:].decode("utf-8", errors="replace")
        if p.returncode != 0 and target.exists():
            target.unlink(missing_ok=True)
        return {"cmd": cmd, "target": str(target), "returncode": p.returncode, "elapsed": round(time.time()-started, 3), "stderr_tail": stderr_tail, "size_bytes": target.stat().st_size if target.exists() else 0, "partial_removed": p.returncode != 0}
    except subprocess.TimeoutExpired as e:
        if target.exists():
            target.unlink(missing_ok=True)
        stderr_tail = (e.stderr or b"")[-3000:].decode("utf-8", errors="replace") if isinstance(e.stderr, (bytes, bytearray)) else str(e.stderr or "")[-3000:]
        return {"cmd": cmd, "target": str(target), "returncode": "TIMEOUT", "elapsed": round(time.time()-started, 3), "stderr_tail": stderr_tail, "size_bytes": 0, "partial_removed": True}


def path_meta(names: list[str], required: list[str]):
    counts = Counter(names)
    duplicates = [n for n, c in counts.items() if c > 1]
    traversal, absolute, winabs, overlong = [], [], [], []
    for n in names:
        p = PurePosixPath(n)
        if ".." in p.parts: traversal.append(n)
        if n.startswith(("/", "\\")): absolute.append(n)
        if re.match(r"^[A-Za-z]:", n): winabs.append(n)
        if len(n.encode()) > 240: overlong.append(n)
    missing = [r for r in required if r not in names]
    return duplicates, traversal, absolute, winabs, overlong, missing


def check_zip(zip_path: Path, root: str):
    checks, meta = [], {"zip_path": str(zip_path)}
    try:
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            names = z.namelist()
            required = [r.format(root=root) for r in REQUIRED]
            duplicates, traversal, absolute, winabs, overlong, missing = path_meta(names, required)
            hard_unsafe = len(traversal) + len(absolute) + len(winabs)
            meta.update({"testzip": bad or "PASS", "member_count": len(names), "duplicate_member_count": len(duplicates), "unsafe_path_counts": {"traversal": len(traversal), "absolute": len(absolute), "windows_absolute": len(winabs), "overlong_gt240": len(overlong)}, "required_missing": missing})
            checks.append(["zip_testzip", "PASS" if not bad else "FAIL", bad or "PASS"])
            checks.append(["zip_duplicate_members", "PASS" if not duplicates else "FAIL", len(duplicates)])
            checks.append(["zip_unsafe_paths", "PASS" if hard_unsafe == 0 else "FAIL", meta["unsafe_path_counts"]])
            checks.append(["path_length_over_240", "WARN" if overlong else "PASS", len(overlong)])
            checks.append(["required_boot_members", "PASS" if not missing else "FAIL", missing])
    except Exception as e:
        checks.append(["zip_open", "FAIL", f"{type(e).__name__}: {e}"])
        meta["exception"] = f"{type(e).__name__}: {e}"
    return checks, meta


def check_tar(tar_path: Path, root: str):
    checks, meta = [], {"tar_path": str(tar_path)}
    try:
        with tarfile.open(tar_path, "r:*") as t:
            members = t.getmembers()
            names = [m.name for m in members]
            required = [r.format(root=root) for r in REQUIRED]
            duplicates, traversal, absolute, winabs, overlong, missing = path_meta(names, required)
            unsafe_links = [m.name for m in members if m.issym() or m.islnk() or m.isdev()]
            hard_unsafe = len(traversal) + len(absolute) + len(winabs) + len(unsafe_links)
            meta.update({"member_count": len(names), "duplicate_member_count": len(duplicates), "unsafe_path_counts": {"traversal": len(traversal), "absolute": len(absolute), "windows_absolute": len(winabs), "overlong_gt240": len(overlong), "unsafe_link_or_device": len(unsafe_links)}, "required_missing": missing})
            checks.append(["tar_open", "PASS", len(names)])
            checks.append(["tar_duplicate_members", "PASS" if not duplicates else "FAIL", len(duplicates)])
            checks.append(["tar_unsafe_paths", "PASS" if hard_unsafe == 0 else "FAIL", meta["unsafe_path_counts"]])
            checks.append(["path_length_over_240", "WARN" if overlong else "PASS", len(overlong)])
            checks.append(["required_boot_members", "PASS" if not missing else "FAIL", missing])
    except Exception as e:
        checks.append(["tar_open", "FAIL", f"{type(e).__name__}: {e}"])
        meta["exception"] = f"{type(e).__name__}: {e}"
    return checks, meta


def materialize(artifact: Path, out: Path):
    if artifact.suffix == ".zip":
        return artifact, "zip", []
    if artifact.name.endswith(".zip.zst") or artifact.name.endswith(".tar.zst"):
        zstd = shutil.which("zstd")
        if not zstd:
            return None, None, [["zstd_available", "BLOCKED", "zstd missing"]]
        frame = run_text([zstd, "-q", "-t", str(artifact)], timeout=120)
        checks = [["zstd_frame", "PASS" if frame["returncode"] == 0 else "FAIL", frame]]
        if frame["returncode"] != 0:
            return None, None, checks
        target = out / artifact.name[:-4]
        kind = "zip" if target.suffix == ".zip" else "tar" if target.suffix == ".tar" else None
        if kind is None:
            return None, None, [["artifact_extension", "BLOCKED", "expected .zip, .zip.zst, or .tar.zst"]]
        dec = run_binary_to_file([zstd, "-q", "-dc", str(artifact)], target, timeout=240)
        checks.append([f"zst_materialize_{kind}", "PASS" if dec["returncode"] == 0 and target.exists() and target.stat().st_size > 0 else "FAIL", dec])
        return (target if dec["returncode"] == 0 and target.exists() and target.stat().st_size > 0 else None), kind, checks
    if artifact.suffix == ".tar":
        return artifact, "tar", []
    return None, None, [["artifact_extension", "BLOCKED", "expected .zip, .zip.zst, or .tar.zst"]]


def audit(args):
    out = Path(args.out_dir)
    if args.clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    artifact = Path(args.artifact).resolve()
    checks = []
    meta = {"schema": SCHEMA, "runner_version": VERSION, "created_utc": utc(), "artifact": str(artifact), "expected_root": args.expected_root}
    if not artifact.exists():
        checks.append(["artifact_present", "BLOCKED", "artifact missing"])
    else:
        exp = sidecar_hash(artifact)
        actual = sha256(artifact)
        checks.append(["artifact_sha_sidecar", "PASS" if exp == actual else ("BLOCKED" if exp is None else "FAIL"), {"actual": actual, "expected": exp}])
        path, kind, mat_checks = materialize(artifact, out)
        checks.extend(mat_checks)
        if path:
            if kind == "zip":
                zchecks, zmeta = check_zip(path, args.expected_root)
                checks.extend(zchecks); meta["zip"] = zmeta
            elif kind == "tar":
                tchecks, tmeta = check_tar(path, args.expected_root)
                checks.extend(tchecks); meta["tar"] = tmeta
    hard_bad = [c for c in checks if c[1] in {"FAIL", "BLOCKED"}]
    warns = [c for c in checks if c[1] == "WARN"]
    verdict = "PASS_WITH_FINDINGS" if warns and not hard_bad else "PASS" if not hard_bad else ("BLOCKED" if any(c[1] == "BLOCKED" for c in hard_bad) else "FAIL")
    result = {"schema": SCHEMA, "runner_version": VERSION, "created_utc": utc(), "verdict": verdict, "checks": [{"check_id": c[0], "decision": c[1], "details": c[2]} for c in checks], "metadata": meta}
    write_json(out / "audit_result.json", result)
    lines = ["# MetaBlooms Remote Release Audit", "", f"Verdict: {verdict}", "", "| Check | Decision |", "|---|---:|"]
    for c in checks: lines.append(f"| {c[0]} | {c[1]} |")
    (out / "audit_report.md").write_text("\n".join(lines) + "\n")
    with zipfile.ZipFile(out / "audit_packet.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out / "audit_result.json", "audit_result.json")
        z.write(out / "audit_report.md", "audit_report.md")
    (out / "audit_packet.zip.sha256").write_text(f"{sha256(out/'audit_packet.zip')}  audit_packet.zip\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if verdict in {"PASS", "PASS_WITH_FINDINGS"} else 1


def make_zip(path: Path, root=DEFAULT_ROOT, missing_mpp=False, traversal=False, wrong_sidecar=False, malformed_sidecar=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if traversal: z.writestr("../evil.txt", "bad")
        z.writestr(f"{root}/METABLOOMS_PREBOOT_RESCUE_v1.sh", "#!/usr/bin/env bash\necho rescue\n")
        z.writestr(f"{root}/scripts/boot/METABLOOMS_PREBOOT_RESCUE_v1.sh", "#!/usr/bin/env bash\necho rescue\n")
        if not missing_mpp: z.writestr(f"{root}/scripts/mpp/mpp.sh", "#!/usr/bin/env bash\necho PASS\n")
    if malformed_sidecar:
        side = "not-a-sha256  " + path.name + "\n"
    elif wrong_sidecar:
        side = "0" * 64 + "  " + path.name + "\n"
    else:
        side = f"{sha256(path)}  {path.name}\n"
    Path(str(path)+".sha256").write_text(side)


def make_tar_zst(path: Path, root=DEFAULT_ROOT, missing_mpp=False, traversal=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.with_suffix("")
    with tarfile.open(raw, "w") as t:
        entries = {
            f"{root}/METABLOOMS_PREBOOT_RESCUE_v1.sh": b"#!/usr/bin/env bash\necho rescue\n",
            f"{root}/scripts/boot/METABLOOMS_PREBOOT_RESCUE_v1.sh": b"#!/usr/bin/env bash\necho rescue\n",
        }
        if not missing_mpp: entries[f"{root}/scripts/mpp/mpp.sh"] = b"#!/usr/bin/env bash\necho PASS\n"
        if traversal: entries["../evil.txt"] = b"bad"
        for name, data in entries.items():
            info = tarfile.TarInfo(name); info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    zstd = shutil.which("zstd")
    if not zstd: raise RuntimeError("zstd required for tar.zst fixture")
    p = subprocess.run([zstd, "-q", "-f", str(raw), "-o", str(path)], text=True, capture_output=True)
    if p.returncode != 0: raise RuntimeError(p.stderr[-1000:])
    raw.unlink(missing_ok=True)
    Path(str(path)+".sha256").write_text(f"{sha256(path)}  {path.name}\n")


def self_test(args):
    out = Path(args.out_dir)
    if args.clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    cases = [
        ("positive", "zip", {}, "PASS"),
        ("missing_mpp", "zip", {"missing_mpp": True}, "FAIL"),
        ("traversal", "zip", {"traversal": True}, "FAIL"),
        ("sidecar_wrong_hash", "zip", {"wrong_sidecar": True}, "FAIL"),
        ("sidecar_malformed", "zip", {"malformed_sidecar": True}, "BLOCKED"),
        ("positive_tar_zst", "tar.zst", {}, "PASS"),
        ("tar_zst_traversal", "tar.zst", {"traversal": True}, "FAIL"),
    ]
    results = []
    for name, kind, opts, expected in cases:
        art = out / "fixtures" / (f"{name}.tar.zst" if kind == "tar.zst" else f"{name}.zip")
        if kind == "tar.zst": make_tar_zst(art, **opts)
        else: make_zip(art, **opts)
        ns = argparse.Namespace(artifact=str(art), out_dir=str(out/name), expected_root=DEFAULT_ROOT, clean=True)
        rc = audit(ns)
        actual = json.loads((out/name/"audit_result.json").read_text())["verdict"]
        passed = (expected == actual) or (expected == "PASS" and actual in {"PASS", "PASS_WITH_FINDINGS"}) or (expected == "FAIL" and actual in {"FAIL", "BLOCKED"}) or (expected == "BLOCKED" and actual == "BLOCKED")
        results.append({"case": name, "expected": expected, "actual": actual, "pass": passed})
    summary = {"schema":"metablooms.release_audit_harness.remote_self_test.v1", "created_utc":utc(), "runner_version":VERSION, "decision":"PASS" if all(r["pass"] for r in results) else "FAIL", "cases":results}
    write_json(out / "self_test_result.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["decision"] == "PASS" else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact")
    p.add_argument("--out-dir", default="remote_audit_out")
    p.add_argument("--expected-root", default=DEFAULT_ROOT)
    p.add_argument("--clean", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test: return self_test(args)
    if not args.artifact: p.error("--artifact required unless --self-test")
    return audit(args)

if __name__ == "__main__":
    raise SystemExit(main())
