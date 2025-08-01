#!/usr/bin/env python
"""Run all tests for Phase 1 components."""

import subprocess
import sys


def run_tests():
    """Run pytest with coverage."""
    print("Running Phase 1 unit tests...\n")

    # Run tests with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v",
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
