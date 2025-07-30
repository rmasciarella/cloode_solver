#!/usr/bin/env python3
"""Test runner for Fresh Solver OR-Tools project.

Runs all tests with coverage reporting and structured logging.
"""

import logging
import subprocess
import sys
from pathlib import Path

# Add project root to path for logging config import
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Setup basic logging for test runner
log_format = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)


def main():
    """Run all tests with coverage and structured logging."""
    logger.info("Starting test run with coverage reporting")

    try:
        # Run pytest with coverage
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v",
        ]

        logger.info("Executing command: %s", " ".join(cmd))

        result = subprocess.run(cmd, check=False)

        if result.returncode == 0:
            logger.info("All tests passed successfully")
            print("✅ All tests passed")
        else:
            logger.warning(
                "Some tests failed or were skipped (exit code: %d)", result.returncode
            )
            print(f"⚠️ Tests completed with exit code: {result.returncode}")

        return result.returncode

    except KeyboardInterrupt:
        logger.info("Test run interrupted by user")
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        logger.error("Error running tests: %s", str(e))
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
