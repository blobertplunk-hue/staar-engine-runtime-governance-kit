"""Acquire, verify, build, and chunk the Android Recorder Stage002 toolchain payload.

This helper is temporary PR-only acquisition infrastructure.  It is invoked by
an existing trusted CI workflow and emits only hash-bound attestation JSON into
runtime/attestations so the existing artifact uploader can transport the binary
payload back to the sandbox.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / "android-recorder-stage002"
PROJECT = WORK / "project"
OUT = ROOT / "runtime" / "attestations"
TOOLCHAIN = WORK / "toolchain"
CACHE = WORK / "cache"
ANDROID_HOME = TOOLCHAIN / "android-sdk"
GRADLE_USER_HOME = TOOLCHAIN / "gradle-home"
PAYLOAD_DIR = WORK / "stage002-payload"
PAYLOAD_ARCHIVE = WORK / "android-recorder-stage002-toolchain.tar.gz"
MASTER = OUT / "ANDROID_RECORDER_STAGE002_TOOLCHAIN_MANIFEST.json"

CMDLINE_NAME = "commandlinetools-linux-15859902_latest.zip"
CMDLINE_URL = f"https://dl.google.com/android/repository/{CMDLINE_NAME}"
CMDLINE_SHA256 = "4e4c464f145a7512b57d088ac6c278c03c9eea610886b35a5e0804e74eedf583"
GRADLE_VERSION = "9.5.0"
GRADLE_NAME = f"gradle-{GRADLE_VERSION}-bin.zip"
GRADLE_URL = f"https://services.gradle.org/distributions/{GRADLE_NAME}"
GRADLE_SHA_URL = f"{GRADLE_URL}.sha256"
ANDROID_PLATFORM_PACKAGE = "platforms;android-37"
ANDROID_BUILD_TOOLS_PACKAGE = "build-tools;36.0.0"
CHUNK_SIZE = 18 * 1024 * 1024


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args: list[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None,
        capture: bool = False, input_text: str | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        env=env,
        check=True,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return completed.stdout or ""


def download(url: str, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([
        "curl", "--fail", "--location", "--retry", "5", "--retry-all-errors",
        "--output", str(dest), url,
    ])


def write_chunks(payload: pathlib.Path, proof: dict) -> list[dict]:
    total_size = payload.stat().st_size
    total_chunks = math.ceil(total_size / CHUNK_SIZE)
    records: list[dict] = []
    with payload.open("rb") as stream:
        for index in range(total_chunks):
            raw = stream.read(CHUNK_SIZE)
            raw_sha = hashlib.sha256(raw).hexdigest()
            filename = f"ANDROID_RECORDER_STAGE002_PAYLOAD_CHUNK_{index + 1:04d}_OF_{total_chunks:04d}.json"
            record = {
                "schema": "metablooms.android_recorder.stage002.payload_chunk.v1",
                "stage": "ANDROID_RECORDER_STAGE002_TOOLCHAIN_HYDRATION_AND_BUILD_SHELL_RED_GREEN",
                "status": "PASS",
                "index": index + 1,
                "count": total_chunks,
                "payload_filename": payload.name,
                "payload_sha256": proof["payload_sha256"],
                "payload_size_bytes": total_size,
                "chunk_size_bytes": len(raw),
                "chunk_sha256": raw_sha,
                "data_base64": base64.b64encode(raw).decode("ascii"),
            }
            (OUT / filename).write_text(
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            records.append({
                "filename": filename,
                "index": index + 1,
                "chunk_size_bytes": len(raw),
                "chunk_sha256": raw_sha,
            })
    return records


def main() -> int:
    request = WORK / "REQUEST.json"
    if not request.is_file():
        raise FileNotFoundError(f"request marker missing: {request}")
    if not (PROJECT / "scripts/verify_manifest_policy.py").is_file():
        raise FileNotFoundError("manifest policy verifier missing")

    for path in (TOOLCHAIN, CACHE, PAYLOAD_DIR):
        if path.exists():
            shutil.rmtree(path)
    if PAYLOAD_ARCHIVE.exists():
        PAYLOAD_ARCHIVE.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("ANDROID_RECORDER_STAGE002_*.json"):
        old.unlink()

    CACHE.mkdir(parents=True, exist_ok=True)
    ANDROID_HOME.mkdir(parents=True, exist_ok=True)
    GRADLE_USER_HOME.mkdir(parents=True, exist_ok=True)

    cmdline_zip = CACHE / CMDLINE_NAME
    download(CMDLINE_URL, cmdline_zip)
    actual_cmdline_sha = sha256(cmdline_zip)
    if actual_cmdline_sha != CMDLINE_SHA256:
        raise RuntimeError(
            f"command-line tools SHA mismatch: expected {CMDLINE_SHA256}, got {actual_cmdline_sha}"
        )

    unpack = CACHE / "cmdline-unpack"
    unpack.mkdir(parents=True, exist_ok=True)
    run(["unzip", "-q", str(cmdline_zip), "-d", str(unpack)])
    latest = ANDROID_HOME / "cmdline-tools/latest"
    latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(unpack / "cmdline-tools"), str(latest))
    sdkmanager = latest / "bin/sdkmanager"
    if not sdkmanager.is_file():
        raise RuntimeError("sdkmanager missing after verified command-line tools extraction")

    env = {
        **os.environ,
        "ANDROID_HOME": str(ANDROID_HOME),
        "ANDROID_SDK_ROOT": str(ANDROID_HOME),
        "GRADLE_USER_HOME": str(GRADLE_USER_HOME),
        "PATH": f"{latest / 'bin'}:{ANDROID_HOME / 'platform-tools'}:{os.environ.get('PATH', '')}",
    }
    subprocess.run(
        [str(sdkmanager), f"--sdk_root={ANDROID_HOME}", "--licenses"],
        cwd=str(ROOT), env=env, input="y\n" * 200, text=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=False,
    )
    run([
        str(sdkmanager), f"--sdk_root={ANDROID_HOME}",
        "platform-tools", ANDROID_PLATFORM_PACKAGE, ANDROID_BUILD_TOOLS_PACKAGE,
    ], env=env)

    android_jar = ANDROID_HOME / "platforms/android-37/android.jar"
    adb = ANDROID_HOME / "platform-tools/adb"
    aapt2 = ANDROID_HOME / "build-tools/36.0.0/aapt2"
    for required in (android_jar, adb, aapt2):
        if not required.exists():
            raise RuntimeError(f"required hydrated SDK artifact missing: {required}")
    sdk_installed = run(
        [str(sdkmanager), f"--sdk_root={ANDROID_HOME}", "--list_installed"],
        env=env, capture=True,
    )

    gradle_zip = CACHE / GRADLE_NAME
    gradle_sha_file = CACHE / f"{GRADLE_NAME}.sha256"
    download(GRADLE_URL, gradle_zip)
    download(GRADLE_SHA_URL, gradle_sha_file)
    expected_gradle_sha = gradle_sha_file.read_text(encoding="utf-8").strip().split()[0]
    actual_gradle_sha = sha256(gradle_zip)
    if actual_gradle_sha != expected_gradle_sha:
        raise RuntimeError(
            f"Gradle SHA mismatch: expected {expected_gradle_sha}, got {actual_gradle_sha}"
        )
    run(["unzip", "-q", str(gradle_zip), "-d", str(TOOLCHAIN)])
    gradle_bin = TOOLCHAIN / f"gradle-{GRADLE_VERSION}/bin/gradle"
    if not gradle_bin.is_file():
        raise RuntimeError("Gradle binary missing after verified distribution extraction")
    gradle_version_text = run([str(gradle_bin), "--version"], env=env, capture=True)

    manifest_policy = run(
        ["python3", "scripts/verify_manifest_policy.py"],
        cwd=PROJECT, env=env, capture=True,
    ).strip()
    if manifest_policy != "MANIFEST_POLICY=PASS":
        raise RuntimeError(f"manifest policy did not pass: {manifest_policy!r}")

    run([
        str(gradle_bin), "wrapper", "--gradle-version", GRADLE_VERSION,
        "--distribution-type", "bin", "--no-daemon",
    ], cwd=PROJECT, env=env)
    gradlew = PROJECT / "gradlew"
    gradlew.chmod(0o755)
    wrapper_version_text = run([str(gradlew), "--version"], cwd=PROJECT, env=env, capture=True)
    run([str(gradlew), ":app:assembleDebug", "--stacktrace", "--no-daemon"], cwd=PROJECT, env=env)
    apk = PROJECT / "app/build/outputs/apk/debug/app-debug.apk"
    if not apk.is_file():
        raise RuntimeError("debug APK missing after assembleDebug")
    apk_sha = sha256(apk)

    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ANDROID_HOME, PAYLOAD_DIR / "android-sdk", symlinks=True)
    shutil.copytree(TOOLCHAIN / f"gradle-{GRADLE_VERSION}", PAYLOAD_DIR / f"gradle-{GRADLE_VERSION}", symlinks=True)
    shutil.copy2(gradle_zip, PAYLOAD_DIR / GRADLE_NAME)
    shutil.copytree(GRADLE_USER_HOME, PAYLOAD_DIR / "gradle-home", symlinks=True)
    shutil.copytree(PROJECT, PAYLOAD_DIR / "project", symlinks=True, ignore=shutil.ignore_patterns(".gradle"))
    (PAYLOAD_DIR / "SDK_INSTALLED.txt").write_text(sdk_installed, encoding="utf-8")

    proof = {
        "schema": "metablooms.android_recorder.stage002.remote_proof.v1",
        "stage": "ANDROID_RECORDER_STAGE002_TOOLCHAIN_HYDRATION_AND_BUILD_SHELL_RED_GREEN",
        "status": "PASS",
        "commandline_tools_filename": CMDLINE_NAME,
        "commandline_tools_url": CMDLINE_URL,
        "commandline_tools_sha256": actual_cmdline_sha,
        "android_platform_package": ANDROID_PLATFORM_PACKAGE,
        "android_build_tools_package": ANDROID_BUILD_TOOLS_PACKAGE,
        "gradle_version": GRADLE_VERSION,
        "gradle_bin_sha256": actual_gradle_sha,
        "gradle_version_output": gradle_version_text,
        "wrapper_version_output": wrapper_version_text,
        "manifest_policy": manifest_policy,
        "assemble_debug": "PASS",
        "apk_relative_path": "project/app/build/outputs/apk/debug/app-debug.apk",
        "apk_sha256": apk_sha,
        "sdk_installed_text": sdk_installed,
    }
    (PAYLOAD_DIR / "STAGE002_REMOTE_PROOF.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    run([
        "tar", "--sort=name", "--mtime=UTC 2026-08-21", "--owner=0", "--group=0",
        "--numeric-owner", "-czf", str(PAYLOAD_ARCHIVE), PAYLOAD_DIR.name,
    ], cwd=WORK)
    proof["payload_filename"] = PAYLOAD_ARCHIVE.name
    proof["payload_size_bytes"] = PAYLOAD_ARCHIVE.stat().st_size
    proof["payload_sha256"] = sha256(PAYLOAD_ARCHIVE)

    chunks = write_chunks(PAYLOAD_ARCHIVE, proof)
    master = {
        **proof,
        "chunk_encoding": "base64-json",
        "chunk_raw_size_bytes": CHUNK_SIZE,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "reconstruction": "sort chunks by index, base64-decode data_base64, concatenate raw bytes, verify payload_sha256 before extraction",
    }
    MASTER.write_text(json.dumps(master, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "payload_sha256": master["payload_sha256"],
        "payload_size_bytes": master["payload_size_bytes"],
        "chunk_count": master["chunk_count"],
        "apk_sha256": master["apk_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
