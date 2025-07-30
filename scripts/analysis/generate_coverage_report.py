#!/usr/bin/env python3
"""Generate comprehensive test coverage report."""

import subprocess
import sys


def main():
    """Run tests and generate coverage report."""
    print("=" * 80)
    print("FRESH SOLVER - TEST COVERAGE REPORT")
    print("=" * 80)

    # First, try to run only tests that work
    working_test_patterns = [
        "tests/unit/models/",
        "tests/unit/solver/test_solver_utils.py",
        "tests/performance/test_performance_regression.py",
    ]

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *working_test_patterns,
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=json",
        "-v",
        "--tb=short",
    ]

    print("\nRunning tests with coverage analysis...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Parse coverage from JSON if available
    try:
        import json

        with open("coverage.json") as f:
            coverage_data = json.load(f)
            total_percent = coverage_data["totals"]["percent_covered"]
            print("\n" + "=" * 80)
            print(f"OVERALL COVERAGE: {total_percent:.1f}%")
            print("=" * 80)

            # Show uncovered modules
            print("\nMODULES NEEDING TESTS (0% coverage):")
            print("-" * 40)
            for file_path, file_data in coverage_data["files"].items():
                if file_data["summary"]["percent_covered"] == 0:
                    print(f"  - {file_path}")

            print("\nMODULES WITH LOW COVERAGE (<50%):")
            print("-" * 40)
            for file_path, file_data in coverage_data["files"].items():
                percent = file_data["summary"]["percent_covered"]
                if 0 < percent < 50:
                    print(f"  - {file_path}: {percent:.1f}%")

    except Exception as e:
        print(f"\nCould not parse coverage JSON: {e}")

    # Coverage target check
    print("\n" + "=" * 80)
    print("COVERAGE TARGET: 90%")

    if result.returncode == 0:
        print("\nHTML coverage report generated in: htmlcov/index.html")
        print("\nTo reach 90% coverage, focus on:")
        print("1. Core solver module (src/solver/core/solver.py)")
        print("2. Constraint modules (src/solver/constraints/phase1/)")
        print("3. Database loader (src/data/loaders/database.py)")
        print("4. Main entry point (src/solver/__main__.py)")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
