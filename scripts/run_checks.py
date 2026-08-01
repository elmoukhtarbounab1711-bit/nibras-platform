"""
Local CI gate for Nibras.

Usage:  python scripts/run_checks.py

Runs lint then the full test suite and returns a non-zero exit code on any
failure — matching the CI gate standard in Testing Strategy §6 and
Deployment/DevOps §3: "lint + full test suite must pass before merge".
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

STEPS = [
    ("lint (ruff)", [PYTHON, "-m", "ruff", "check", "."]),
    ("tests (pytest)", [PYTHON, "-m", "pytest", "-q"]),
]


def main():
    failed = False
    for name, cmd in STEPS:
        print(f"\n== {name} ==", flush=True)
        result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            failed = True
            print(f"!! FAILED: {name}", flush=True)
    if failed:
        print("\nCI gate failed.", file=sys.stderr)
        sys.exit(1)
    print("\nCI gate passed: lint + tests.")


if __name__ == "__main__":
    main()
