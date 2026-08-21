"""PR-only Android Recorder Stage002 toolchain acquisition and attestation."""
from __future__ import annotations

import base64, hashlib, json, math, os, pathlib, shutil, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / "android-recorder-stage002"
PROJECT = WORK / "project"
REQUEST = WORK / "REQUEST.json"
OUT = ROOT / "runtime/attestations"
TOOLCHAIN = WORK / "toolchain"
CACHE = WORK / "cache"
PAYLOAD = WORK / "stage002-payload"
ARCHIVE = WORK / "android-recorder-stage002-toolchain.tar.gz"
CHUNK_SIZE = 18 * 1024 * 1024
CMDLINE_NAME = "commandlinetools-linux-15859902_latest.zip"
CMDLINE_URL = f"https://dl.google.com/android/repository/{CMDLINE_NAME}"
CMDLINE_SHA = "4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"
GRADLE_VERSION = "9.5.0"


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(*args: str, cwd: pathlib.Path = ROOT, env=None, capture=False) -> str:
    cp = subprocess.run(
        list(args), cwd=cwd, env=env, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return cp.stdout or ""


def fetch(url: str, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run("curl", "--fail", "--location", "--retry", "5", "--retry-all-errors", "--output", str(dest), url)


def main() -> int:
    req = json.loads(REQUEST.read_text(encoding="utf-8"))
    platform_pkg = req["android_platform_package"]
    build_tools_pkg = req["android_build_tools_package"]
    platform_suffix = platform_pkg.split(";", 1)[1]
    build_tools_suffix = build_tools_pkg.split(";", 1)[1]

    for p in (TOOLCHAIN, CACHE, PAYLOAD):
        if p.exists(): shutil.rmtree(p)
    if ARCHIVE.exists(): ARCHIVE.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("ANDROID_RECORDER_STAGE002_*.json"): p.unlink()

    android_home = TOOLCHAIN / "android-sdk"
    gradle_user_home = TOOLCHAIN / "gradle-home"
    android_home.mkdir(parents=True)
    gradle_user_home.mkdir(parents=True)
    CACHE.mkdir(parents=True)

    cmd_zip = CACHE / CMDLINE_NAME
    fetch(CMDLINE_URL, cmd_zip)
    if digest(cmd_zip) != CMDLINE_SHA:
        raise RuntimeError("verified command-line-tools SHA-256 mismatch")
    unpack = CACHE / "cmdline-unpack"
    run("unzip", "-q", str(cmd_zip), "-d", str(unpack))
    latest = android_home / "cmdline-tools/latest"
    latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(unpack / "cmdline-tools"), str(latest))
    sdkmanager = latest / "bin/sdkmanager"
    env = {
        **os.environ,
        "ANDROID_HOME": str(android_home),
        "ANDROID_SDK_ROOT": str(android_home),
        "GRADLE_USER_HOME": str(gradle_user_home),
        "PATH": f"{latest / 'bin'}:{android_home / 'platform-tools'}:{os.environ.get('PATH','')}",
    }
    subprocess.run(
        [str(sdkmanager), f"--sdk_root={android_home}", "--licenses"],
        cwd=ROOT, env=env, input="y\n" * 200, text=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False,
    )
    run(str(sdkmanager), f"--sdk_root={android_home}", "platform-tools", platform_pkg, build_tools_pkg, env=env)
    sdk_list = run(str(sdkmanager), f"--sdk_root={android_home}", "--list_installed", env=env, capture=True)
    required = [
        android_home / f"platforms/{platform_suffix}/android.jar",
        android_home / "platform-tools/adb",
        android_home / f"build-tools/{build_tools_suffix}/aapt2",
    ]
    for p in required:
        if not p.exists(): raise RuntimeError(f"hydrated SDK artifact missing: {p}")

    gradle_name = f"gradle-{GRADLE_VERSION}-bin.zip"
    gradle_zip = CACHE / gradle_name
    gradle_sha = CACHE / f"{gradle_name}.sha256"
    gradle_url = f"https://services.gradle.org/distributions/{gradle_name}"
    fetch(gradle_url, gradle_zip)
    fetch(f"{gradle_url}.sha256", gradle_sha)
    expected_gradle = gradle_sha.read_text(encoding="utf-8").strip().split()[0]
    if digest(gradle_zip) != expected_gradle: raise RuntimeError("Gradle SHA-256 mismatch")
    run("unzip", "-q", str(gradle_zip), "-d", str(TOOLCHAIN))
    gradle_bin = TOOLCHAIN / f"gradle-{GRADLE_VERSION}/bin/gradle"
    gradle_version = run(str(gradle_bin), "--version", env=env, capture=True)

    policy = run("python3", "scripts/verify_manifest_policy.py", cwd=PROJECT, env=env, capture=True).strip()
    if policy != "MANIFEST_POLICY=PASS": raise RuntimeError(policy)
    run(str(gradle_bin), "wrapper", "--gradle-version", GRADLE_VERSION, "--distribution-type", "bin", "--no-daemon", cwd=PROJECT, env=env)
    gradlew = PROJECT / "gradlew"
    gradlew.chmod(0o755)
    wrapper_version = run(str(gradlew), "--version", cwd=PROJECT, env=env, capture=True)
    run(str(gradlew), ":app:assembleDebug", "--stacktrace", "--no-daemon", cwd=PROJECT, env=env)
    apk = PROJECT / "app/build/outputs/apk/debug/app-debug.apk"
    if not apk.exists(): raise RuntimeError("assembleDebug did not produce APK")

    PAYLOAD.mkdir(parents=True)
    shutil.copytree(android_home, PAYLOAD / "android-sdk", symlinks=True)
    shutil.copytree(TOOLCHAIN / f"gradle-{GRADLE_VERSION}", PAYLOAD / f"gradle-{GRADLE_VERSION}", symlinks=True)
    shutil.copy2(gradle_zip, PAYLOAD / gradle_name)
    shutil.copytree(gradle_user_home, PAYLOAD / "gradle-home", symlinks=True)
    shutil.copytree(PROJECT, PAYLOAD / "project", symlinks=True, ignore=shutil.ignore_patterns(".gradle"))
    (PAYLOAD / "SDK_INSTALLED.txt").write_text(sdk_list, encoding="utf-8")
    proof = {
        "schema": "metablooms.android_recorder.stage002.remote_proof.v1",
        "stage": req["stage"], "status": "PASS",
        "commandline_tools_filename": CMDLINE_NAME, "commandline_tools_url": CMDLINE_URL,
        "commandline_tools_sha256": digest(cmd_zip),
        "android_platform_package": platform_pkg, "android_build_tools_package": build_tools_pkg,
        "gradle_version": GRADLE_VERSION, "gradle_bin_sha256": digest(gradle_zip),
        "manifest_policy": policy, "assemble_debug": "PASS", "apk_sha256": digest(apk),
        "gradle_version_output": gradle_version, "wrapper_version_output": wrapper_version,
        "sdk_installed_text": sdk_list,
    }
    (PAYLOAD / "STAGE002_REMOTE_PROOF.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run("tar", "--sort=name", "--mtime=UTC 2026-08-21", "--owner=0", "--group=0", "--numeric-owner", "-czf", str(ARCHIVE), PAYLOAD.name, cwd=WORK)
    proof.update(payload_filename=ARCHIVE.name, payload_size_bytes=ARCHIVE.stat().st_size, payload_sha256=digest(ARCHIVE))

    count = math.ceil(ARCHIVE.stat().st_size / CHUNK_SIZE)
    chunks = []
    with ARCHIVE.open("rb") as f:
        for i in range(1, count + 1):
            raw = f.read(CHUNK_SIZE)
            chunk_sha = hashlib.sha256(raw).hexdigest()
            name = f"ANDROID_RECORDER_STAGE002_PAYLOAD_CHUNK_{i:04d}_OF_{count:04d}.json"
            data = {
                "schema": "metablooms.android_recorder.stage002.payload_chunk.v1", "stage": req["stage"], "status": "PASS",
                "index": i, "count": count, "payload_filename": ARCHIVE.name,
                "payload_sha256": proof["payload_sha256"], "payload_size_bytes": proof["payload_size_bytes"],
                "chunk_size_bytes": len(raw), "chunk_sha256": chunk_sha,
                "data_base64": base64.b64encode(raw).decode("ascii"),
            }
            (OUT / name).write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            chunks.append({"filename": name, "index": i, "chunk_size_bytes": len(raw), "chunk_sha256": chunk_sha})
    master = {**proof, "chunk_encoding": "base64-json", "chunk_count": count, "chunk_raw_size_bytes": CHUNK_SIZE, "chunks": chunks}
    (OUT / "ANDROID_RECORDER_STAGE002_TOOLCHAIN_MANIFEST.json").write_text(json.dumps(master, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status":"PASS", "payload_sha256":proof["payload_sha256"], "chunk_count":count, "apk_sha256":proof["apk_sha256"]}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
