#!/usr/bin/env python3
"""Direct validation of template integration without external dependencies."""

import logging
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data.loaders.database import DatabaseLoader, load_test_problem
from solver.core.solver import FreshSolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_automatic_mode_detection():
    """Test automatic template detection and loading."""
    print("1. Testing automatic mode detection...")

    try:
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem()

        assert problem is not None
        assert problem.total_task_count > 0
        assert problem.total_machine_count > 0

        if problem.is_template_based:
            print("   ✅ Template mode automatically detected and used")
            assert problem.job_template is not None
            assert len(problem.job_instances) > 0
        else:
            print("   ✅ Legacy mode used (no template infrastructure)")
            assert len(problem.jobs) > 0

        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_template_vs_legacy_compatibility():
    """Test that both modes produce valid results."""
    print("2. Testing template vs legacy compatibility...")

    try:
        # Template mode
        template_loader = DatabaseLoader(
            use_test_tables=True, prefer_template_mode=True
        )
        template_problem = template_loader.load_problem()

        # Legacy mode
        legacy_loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=False)
        legacy_problem = legacy_loader.load_problem()

        assert template_problem is not None
        assert legacy_problem is not None

        # Should have same machine count
        assert (
            template_problem.total_machine_count == legacy_problem.total_machine_count
        )

        print("   ✅ Both template and legacy modes produce valid problems")
        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_template_solving():
    """Test template-based solving."""
    print("3. Testing template-based solving...")

    try:
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem(max_instances=2)

        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=15)

        assert solution is not None
        assert solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        if problem.is_template_based:
            print("   ✅ Template-based solving successful")
        else:
            print("   ✅ Legacy solving successful")

        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def test_convenience_functions():
    """Test convenience functions."""
    print("4. Testing convenience functions...")

    try:
        problem = load_test_problem(max_instances=2)
        assert problem is not None
        assert problem.total_task_count > 0

        print("   ✅ Convenience functions work correctly")
        return True

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


def main():
    """Run integration validation."""
    print("=== TEMPLATE INTEGRATION VALIDATION ===")

    tests = [
        test_automatic_mode_detection,
        test_template_vs_legacy_compatibility,
        test_template_solving,
        test_convenience_functions,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    print("\n=== RESULTS ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("Template architecture is ready for production!")
        return True
    else:
        print("⚠️ Some tests failed - check implementation")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
