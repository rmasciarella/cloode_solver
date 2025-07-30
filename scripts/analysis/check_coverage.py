#!/usr/bin/env python3
"""Check test coverage for Fresh Solver project."""

import subprocess
import sys


def run_coverage():
    """Run tests with coverage report."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
    ]

    print("Running tests with coverage...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode


if __name__ == "__main__":
    exit_code = run_coverage()
    sys.exit(exit_code)
