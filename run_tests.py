#!/usr/bin/env python3
"""Test runner for Fresh Solver OR-Tools project.

Runs all tests with coverage reporting.
"""

import subprocess
import sys


def main():
    """Run all tests with coverage."""
    try:
        # Run pytest with coverage
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "-v",
            ],
            check=False,
        )

        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
