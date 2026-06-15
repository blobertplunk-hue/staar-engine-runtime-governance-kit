"""Run MB_INSTALL unittest suite and persist full output for CI diagnostics."""

import os
import subprocess
import sys

LOG_PATH = os.path.join("runtime", "test-logs", "mb-install-tests.log")


def main() -> int:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_mb_install_*.py",
        "-v",
    ]
    result = subprocess.run(cmd, text=True, capture_output=True)
    output = result.stdout + result.stderr
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(output)
    print(output, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
