#!/usr/bin/env python3
"""Remote-safe MetaBlooms release audit harness runner.

Repo-control-plane runner for GitHub Actions. This intentionally lives outside
runtime/ so the OS runtime copy can remain OS-authoritative.
"""
from __future__ import annotations

import argparse, hashlib, io, json, re, shutil, subprocess, tarfile, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SCHEMA = "metablooms.release_audit_harness.remote_runner.v1"
VERSION = "1.3.0-stage0u-r2-repo-control"
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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sidecar_hash(path: Path) -> str | None:
    side = Path(str(path) + ".sha256")
    if not side.exists():
        return None
    first = (side.read_text(errors="replace").split() or [""])[0]
    return first.lower() if re.fullmatch(r"[0-9a-fA-F]{64}", first) else None


def run_text(cmd: list[str], timeout: int = 120):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {"cmd": cmd, "returncode": p.returncode, "stdout_tail": p.stdout[-3000:], "stderr_tail": p.stderr[-3000:]}
    except subprocess.TimeoutExpired as e:
        return {"cmd": cmd, "returncode": "TIMEOUT", "stdout_tail": str(e.stdout or "")[-3000:], "stderr_tail": str(e.stderr or "")[-3000:]}


def run_binary_to_file(cmd: list[str], target: Path, timeout: int = 240):
    try:
        with target.open("wb") as f:
            p = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=timeout)
        if p.returncode != 0:
            target.unlink(missing_ok=True)
        return {"cmd": cmd, "returncode": p.returncode, "size_bytes": target.stat().st_size if target.exists() else 0}
    except subprocess.TimeoutExpired:
        target.unlink(missing_ok=True)
        return {"cmd": cmd, "returncode": "TIMEOUT", "size_bytes": 0}


def path_meta(names: list[str], required: list[str]):
    counts = Counter(names)
    duplicates = [n for n, c in counts.items() if c > 1]
    traversal, absolute, winabs, overlong, unsafe_links = [], [], [], [], []
    for n in names:
        p = PurePosixPath(n)
        if ".." in p.parts: traversal.append(n)
        if n.startswith(("/", "\\")): absolute.append(n)
        if re.match(r"^[A-Za-z]:", n): winabs.append(n)
        if len(n.encode()) > 240: overlong.append(n)
    missing = [r for r in required if r not in names]
    return duplicates, traversal, absolute, winabs, overlong, unsafe_links, missing


def check_zip(zip_path: Path, root: str):
    checks, meta = [], {"zip_path": str(zip_path)}
    try:
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            names = z.namelist()
            required = [r.format(root=root) for r in REQUIRED]
            duplicates, traversal, absolute, winabs, overlong, unsafe_links, missing = path_meta(names, required)
            hard_unsafe = len(traversal) + len(absolute) + len(winabs)
            meta.update({"testzip": bad or "PASS", "member_count": len(names), "duplicate_member_count": len(duplicates), "unsafe_path_counts": {"traversal": len(traversal), "absolute": len(absolute), "windows_absolute": len(winabs), "overlong_gt240": len(overlong)}, "required_missing": missing})
            checks += [["zip_testzip", "PASS" if not bad else "FAIL", bad or "PASS"], ["zip_duplicate_members", "PASS" if not duplicates else "FAIL", len(duplicates)], ["zip_unsafe_paths", "PASS" if hard_unsafe == 0 else "FAIL", meta["unsafe_path_counts"]], ["path_length_over_240", "WARN" if overlong else "PASS", len(overlong)], ["required_boot_members", "PASS" if not missing else "FAIL", missing]]
    except Exception as e:
        checks.append(["zip_open", "FAIL", f"{type(e).__name__}: {e}"])
    return checks, meta


def check_tar(tar_path: Path, root: str):
    checks, meta = [], {"tar_path": str(tar_path)}
    try:
        with tarfile.open(tar_path, "r:*") as t:
            members = t.getmembers(); names = [m.name for m in members]
            required = [r.format(root=root) for r in REQUIRED]
            duplicates, traversal, absolute, winabs, overlong, _, missing = path_meta(names, required)
            unsafe_links = [m.name for m in members if m.issym() or m.islnk() or m.isdev()]
            hard_unsafe = len(traversal) + len(absolute) + len(winabs) + len(unsafe_links)
            meta.update({"member_count": len(names), "duplicate_member_count": len(duplicates), "unsafe_path_counts": {"traversal": len(traversal), "absolute": len(absolute), "windows_absolute": len(winabs), "overlong_gt240": len(overlong), "unsafe_link_or_device": len(unsafe_links)}, "required_missing": missing})
            checks += [["tar_open", "PASS", len(names)], ["tar_duplicate_members", "PASS" if not duplicates else "FAIL", len(duplicates)], ["tar_unsafe_paths", "PASS" if hard_unsafe == 0 else "FAIL", meta["unsafe_path_counts"]], ["path_length_over_240", "WARN" if overlong else "PASS", len(overlong)], ["required_boot_members", "PASS" if not missing else "FAIL", missing]]
    except Exception as e:
        checks.append(["tar_open", "FAIL", f"{type(e).__name__}: {e}"])
    return checks, meta


def materialize(artifact: Path, out: Path):
    if artifact.suffix == ".zip":
        return artifact, "zip", []
    if artifact.name.endswith((".zip.zst", ".tar.zst")):
        zstd = shutil.which("zstd")
        if not zstd: return None, None, [["zstd_available", "BLOCKED", "zstd missing"]]
        frame = run_text([zstd, "-q", "-t", str(artifact)])
        checks = [["zstd_frame", "PASS" if frame["returncode"] == 0 else "FAIL", frame]]
        if frame["returncode"] != 0: return None, None, checks
        target = out / artifact.name[:-4]
        kind = "zip" if target.suffix == ".zip" else "tar" if target.suffix == ".tar" else None
        if not kind: return None, None, [["artifact_extension", "BLOCKED", "expected .zip, .zip.zst, or .tar.zst"]]
        dec = run_binary_to_file([zstd, "-q", "-dc", str(artifact)], target)
        checks.append([f"zst_materialize_{kind}", "PASS" if dec["returncode"] == 0 and target.exists() and target.stat().st_size > 0 else "FAIL", dec])
        return (target if dec["returncode"] == 0 and target.exists() and target.stat().st_size > 0 else None), kind, checks
    if artifact.suffix == ".tar": return artifact, "tar", []
    return None, None, [["artifact_extension", "BLOCKED", "expected .zip, .zip.zst, or .tar.zst"]]


def audit(args):
    out = Path(args.out_dir)
    if args.clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    artifact = Path(args.artifact).resolve(); checks = []
    meta = {"schema": SCHEMA, "runner_version": VERSION, "created_utc": utc(), "artifact": str(artifact), "expected_root": args.expected_root}
    if not artifact.exists(): checks.append(["artifact_present", "BLOCKED", "artifact missing"])
    else:
        exp, actual = sidecar_hash(artifact), sha256(artifact)
        checks.append(["artifact_sha_sidecar", "PASS" if exp == actual else ("BLOCKED" if exp is None else "FAIL"), {"actual": actual, "expected": exp}])
        path, kind, mat_checks = materialize(artifact, out); checks.extend(mat_checks)
        if path:
            if kind == "zip": zchecks, zmeta = check_zip(path, args.expected_root); checks.extend(zchecks); meta["zip"] = zmeta
            elif kind == "tar": tchecks, tmeta = check_tar(path, args.expected_root); checks.extend(tchecks); meta["tar"] = tmeta
    hard_bad = [c for c in checks if c[1] in {"FAIL", "BLOCKED"}]; warns = [c for c in checks if c[1] == "WARN"]
    verdict = "PASS_WITH_FINDINGS" if warns and not hard_bad else "PASS" if not hard_bad else ("BLOCKED" if any(c[1] == "BLOCKED" for c in hard_bad) else "FAIL")
    result = {"schema": SCHEMA, "runner_version": VERSION, "created_utc": utc(), "verdict": verdict, "checks": [{"check_id": c[0], "decision": c[1], "details": c[2]} for c in checks], "metadata": meta}
    write_json(out / "audit_result.json", result)
    (out / "audit_report.md").write_text("# MetaBlooms Remote Release Audit\n\nVerdict: " + verdict + "\n", encoding="utf-8")
    with zipfile.ZipFile(out / "audit_packet.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out / "audit_result.json", "audit_result.json"); z.write(out / "audit_report.md", "audit_report.md")
    (out / "audit_packet.zip.sha256").write_text(f"{sha256(out/'audit_packet.zip')}  audit_packet.zip\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True)); return 0 if verdict in {"PASS", "PASS_WITH_FINDINGS"} else 1


def make_zip(path: Path, root=DEFAULT_ROOT, missing_mpp=False, traversal=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        if traversal: z.writestr("../evil.txt", "bad")
        z.writestr(f"{root}/METABLOOMS_PREBOOT_RESCUE_v1.sh", "#!/usr/bin/env bash\necho rescue\n")
        z.writestr(f"{root}/scripts/boot/METABLOOMS_PREBOOT_RESCUE_v1.sh", "#!/usr/bin/env bash\necho rescue\n")
        if not missing_mpp: z.writestr(f"{root}/scripts/mpp/mpp.sh", "#!/usr/bin/env bash\necho PASS\n")
    Path(str(path)+".sha256").write_text(f"{sha256(path)}  {path.name}\n", encoding="utf-8")


def self_test(args):
    out = Path(args.out_dir)
    if args.clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    cases = [("positive", {}, "PASS"), ("missing_mpp", {"missing_mpp": True}, "FAIL"), ("traversal", {"traversal": True}, "FAIL")]
    results = []
    for name, opts, expected in cases:
        art = out / "fixtures" / f"{name}.zip"; make_zip(art, **opts)
        rc = audit(argparse.Namespace(artifact=str(art), out_dir=str(out/name), expected_root=DEFAULT_ROOT, clean=True))
        actual = json.loads((out/name/"audit_result.json").read_text(encoding="utf-8"))["verdict"]
        results.append({"case": name, "expected": expected, "actual": actual, "pass": (expected == actual) or (expected == "FAIL" and actual in {"FAIL", "BLOCKED"})})
    summary = {"schema":"metablooms.release_audit_harness.remote_self_test.v1", "created_utc":utc(), "runner_version":VERSION, "decision":"PASS" if all(r["pass"] for r in results) else "FAIL", "cases":results}
    write_json(out / "self_test_result.json", summary); print(json.dumps(summary, indent=2, sort_keys=True)); return 0 if summary["decision"] == "PASS" else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact"); p.add_argument("--out-dir", default="remote_audit_out"); p.add_argument("--expected-root", default=DEFAULT_ROOT); p.add_argument("--clean", action="store_true"); p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test: return self_test(args)
    if not args.artifact: p.error("--artifact required unless --self-test")
    return audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
