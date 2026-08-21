#!/usr/bin/env python3
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"

def fail(message: str) -> int:
    print(f"MANIFEST_POLICY=FAIL {message}", file=sys.stderr)
    return 1

def main() -> int:
    if not MANIFEST.is_file():
        return fail(f"missing:{MANIFEST.relative_to(ROOT)}")
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "android.permission.RECORD_AUDIO",
        "android.permission.FOREGROUND_SERVICE",
        "android.permission.FOREGROUND_SERVICE_MICROPHONE",
    ]
    for permission in required:
        if permission not in text:
            return fail(f"missing_permission:{permission}")
    if "android.permission.INTERNET" in text:
        return fail("forbidden_permission:android.permission.INTERNET")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return fail(f"invalid_xml:{exc}")
    services = root.findall("./application/service")
    if not any(
        service.attrib.get(ANDROID + "foregroundServiceType") == "microphone"
        and service.attrib.get(ANDROID + "exported") == "false"
        for service in services
    ):
        return fail("missing_nonexported_microphone_foreground_service")
    providers = root.findall("./application/provider")
    if not any(
        provider.attrib.get(ANDROID + "name") == "androidx.core.content.FileProvider"
        and provider.attrib.get(ANDROID + "exported") == "false"
        and provider.attrib.get(ANDROID + "grantUriPermissions") == "true"
        for provider in providers
    ):
        return fail("missing_secure_fileprovider")
    print("MANIFEST_POLICY=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
