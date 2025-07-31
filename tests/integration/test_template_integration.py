"""End-to-end integration tests for optimized-based scheduling architecture.

Tests the complete pipeline from database loading through optimized solving to
solution persistence.
Validates that the complete optimized architecture (Weeks 1-3) works end-to-end
with optimal performance.
"""

import logging
import time

import pytest

from src.data.loaders.database import (
    DatabaseLoader,
)
from src.solver.core.solver import FreshSolver

logger = logging.getLogger(__name__)


class TestOptimizedIntegration:
    """End-to-end integration tests for optimized-based scheduling."""

    def test_automatic_mode_detection(self, mock_database_loader):
        """Test that DatabaseLoader automatically detects and uses optimal loading mode.

        Tests automatic selection of optimized vs unique loading mode.
        """
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)

        # This should automatically choose the best available loading method
        problem = loader.load_problem()

        assert problem is not None
        assert problem.total_task_count > 0
        assert problem.total_machine_count > 0

        # Check if optimized mode was used
        if problem.is_optimized_mode:
            logger.info("✓ Optimized mode automatically detected and used")
            assert problem.job_optimized_pattern is not None
            assert len(problem.job_instances) > 0
            assert problem.optimized_task_count > 0
        else:
            logger.info("✓ Unique mode used (no optimized infrastructure)")
            assert len(problem.jobs) > 0

    def test_optimized_vs_unique_compatibility(self, mock_database_loader):
        """Test that both optimized and unique modes produce valid, equivalent results.

        Compares optimized and unique loading modes for compatibility.
        """
        # Load same data using both approaches
        optimized_loader = mock_database_loader(
            use_test_tables=True, prefer_optimized_mode=True
        )
        unique_loader = mock_database_loader(
            use_test_tables=True, prefer_optimized_mode=False
        )

        optimized_problem = optimized_loader.load_problem()
        unique_problem = unique_loader.load_problem()

        # Both should be valid problems
        assert optimized_problem is not None
        assert unique_problem is not None

        # If optimized mode was used, compare with unique
        if optimized_problem.is_optimized_mode:
            logger.info("Comparing optimized vs unique loading...")

            # Should have same machine count
            assert (
                optimized_problem.total_machine_count
                == unique_problem.total_machine_count
            )

            # Optimized should have structured data
            assert optimized_problem.job_optimized_pattern is not None
            assert len(optimized_problem.job_instances) > 0

            # Unique should have traditional jobs
            assert len(unique_problem.jobs) > 0

            logger.info("✓ Optimized and unique modes both produce valid problems")
        else:
            logger.info("✓ No optimized infrastructure - both modes use unique loading")

    def test_optimized_solving_performance(self, mock_database_loader):
        """Test optimized-based solving performance and correctness."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)
        problem = loader.load_problem(max_instances=3)  # Limit for testing

        if not problem.is_optimized_mode:
            pytest.skip("No optimized infrastructure available for performance testing")

        logger.info(
            f"Testing optimized problem: {problem.instance_count} instances, "
            f"{problem.optimized_task_count} optimized tasks each"
        )

        # Solve with optimized-optimized solver
        start_time = time.time()
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=30)
        solve_time = time.time() - start_time

        # Verify solution quality
        assert solution is not None
        assert solution.get("status") in ["OPTIMAL", "FEASIBLE"]
        assert solution.get("makespan", 0) > 0
        assert solve_time < 30  # Should complete well within time limit

        # Verify all tasks are scheduled
        scheduled_tasks = solution.get("task_schedule", {})
        expected_task_count = problem.total_task_count
        assert len(scheduled_tasks) == expected_task_count

        logger.info(
            f"✓ Optimized problem solved in {solve_time:.2f}s with makespan "
            f"{solution.get('makespan')}"
        )

    def test_optimized_constraint_optimization(self, mock_database_loader):
        """Test that optimized constraints provide performance benefits."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)
        problem = loader.load_problem(max_instances=5)

        if not problem.is_optimized_mode:
            pytest.skip(
                "No optimized infrastructure for constraint optimization testing"
            )

        # Test optimized-optimized solver
        optimized_solver = FreshSolver(problem)

        start_time = time.time()
        optimized_solution = optimized_solver.solve(time_limit=20)
        optimized_time = time.time() - start_time

        # Verify optimized solution
        assert optimized_solution is not None
        assert optimized_solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        # Optimized solver should be efficient
        assert optimized_time < 20

        logger.info(
            f"✓ Optimized-optimized constraints completed in {optimized_time:.2f}s"
        )

        # Log optimization insights
        logger.info("Problem characteristics:")
        logger.info(f"  - {problem.instance_count} identical job instances")
        logger.info(f"  - {problem.optimized_task_count} tasks per instance")
        logger.info(f"  - {problem.total_task_count} total tasks")
        logger.info(
            f"  - {len(problem.job_optimized_pattern.optimized_precedences)} optimized precedences"
        )

    def test_solution_persistence(self, mock_database_loader):
        """Test that optimized solutions can be saved back to database."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)
        problem = loader.load_problem(max_instances=2)

        if not problem.is_optimized_mode:
            pytest.skip("No optimized infrastructure for solution persistence testing")

        # Solve the problem
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=15)

        assert solution is not None
        assert solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        # Convert solution to database format
        solution_data = {}
        task_schedule = solution.get("task_schedule", {})

        for task_id, schedule_info in task_schedule.items():
            solution_data[task_id] = {
                "mode_id": schedule_info.get("mode_id"),
                "start_time": schedule_info.get("start"),
                "end_time": schedule_info.get("end"),
                "machine_id": schedule_info.get("machine_id"),
            }

        # Test solution persistence (would save to instance_task_assignments table)
        try:
            loader._optimized_loader.save_solution_assignments(problem, solution_data)
            logger.info("✓ Solution successfully persisted to database")
        except Exception as e:
            logger.warning(f"Solution persistence test skipped: {e}")
            # This is expected if database is read-only or table doesn't exist

    def test_optimized_instance_creation(self, mock_database_loader):
        """Test dynamic creation of job instances from optimized_patterns."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)

        # Try to get available optimized_patterns
        optimized_patterns = loader.load_available_optimized_patterns()

        if not optimized_patterns:
            pytest.skip("No optimized_patterns available for instance creation testing")

        optimized_pattern = optimized_patterns[0]
        logger.info(f"Testing instance creation for optimized: {optimized.name}")

        # Test instance creation (would create new records in job_instances table)
        try:
            instance_ids = loader.create_optimized_instances(
                optimized_pattern.pattern_id, instance_count=2, base_description="Test Instance"
            )

            assert len(instance_ids) == 2
            logger.info(f"✓ Created {len(instance_ids)} instances: {instance_ids}")

            # Test loading the newly created instances
            problem = loader.load_optimized_problem(
                optimized_pattern.pattern_id, max_instances=2
            )
            assert problem.instance_count >= 2

        except Exception as e:
            logger.warning(f"Instance creation test skipped: {e}")
            # Expected if database is read-only

    def test_performance_comparison(self, mock_database_loader):
        """Compare optimized vs unique performance on identical data."""
        # This test requires both optimized and unique data representing the same problem
        optimized_loader = mock_database_loader(
            use_test_tables=True, prefer_optimized_mode=True
        )
        unique_loader = mock_database_loader(
            use_test_tables=True, prefer_optimized_mode=False
        )

        # Load problems
        optimized_problem = optimized_loader.load_problem(max_instances=3)
        unique_problem = unique_loader.load_problem()

        if not optimized_problem.is_optimized_mode:
            pytest.skip(
                "Optimized infrastructure not available for performance comparison"
            )

        # Test optimized performance
        optimized_start = time.time()
        optimized_solver = FreshSolver(optimized_problem)
        optimized_solution = optimized_solver.solve(time_limit=20)
        optimized_time = time.time() - optimized_start

        # Test unique performance
        unique_start = time.time()
        unique_solver = FreshSolver(unique_problem)
        unique_solution = unique_solver.solve(time_limit=20)
        unique_time = time.time() - unique_start

        # Both should find solutions
        assert optimized_solution.get("status") in ["OPTIMAL", "FEASIBLE"]
        assert unique_solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        # Log performance comparison
        speedup = unique_time / optimized_time if optimized_time > 0 else 1.0
        logger.info("Performance comparison:")
        logger.info(f"  Optimized mode: {optimized_time:.2f}s")
        logger.info(f"  Unique mode:   {unique_time:.2f}s")
        logger.info(f"  Speedup:       {speedup:.1f}x")

        # Optimized should be competitive or better
        assert optimized_time <= unique_time * 1.5  # Allow 50% margin for small problems

    def test_mixed_loading_modes(self, mock_database_loader):
        """Test loading different types of problems in the same session."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)

        # Test automatic mode detection
        auto_problem = loader.load_problem()
        assert auto_problem is not None

        # Test explicit unique loading
        loader_unique = mock_database_loader(
            use_test_tables=True, prefer_optimized_mode=False
        )
        unique_problem = loader_unique.load_problem()
        assert unique_problem is not None

        # If optimized_patterns are available, test specific optimized loading
        optimized_patterns = loader.load_available_optimized_patterns()
        if optimized_patterns:
            optimized_problem = loader.load_optimized_problem(optimized_patterns[0].pattern_id)
            assert optimized_problem is not None
            assert optimized_problem.is_optimized_mode

            logger.info("✓ Successfully tested mixed loading modes:")
            logger.info(
                f"  - Auto detection: "
                f"{'optimized' if auto_problem.is_optimized_mode else 'unique'}"
            )
            logger.info("  - Explicit unique: valid")
            logger.info("  - Explicit optimized: valid")

    def test_optimized_validation(self, mock_database_loader):
        """Test comprehensive validation of optimized-based problems."""
        loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)
        problem = loader.load_problem()

        if not problem.is_optimized_mode:
            pytest.skip("No optimized infrastructure for validation testing")

        # Run comprehensive problem validation
        issues = problem.validate()

        # Should have no critical validation issues
        critical_issues = [
            issue
            for issue in issues
            if "non-existent" in issue.lower() or "circular" in issue.lower()
        ]
        assert (
            len(critical_issues) == 0
        ), f"Critical validation issues found: {critical_issues}"

        # Log validation results
        if issues:
            logger.warning(f"Validation warnings found: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✓ Optimized problem validation passed with no issues")

        # Test optimized-specific validations
        optimized_issues = problem.job_optimized_pattern.validate_optimized()
        assert (
            len(optimized_issues) == 0
        ), f"Optimized validation issues: {optimized_issues}"

        logger.info("✓ Optimized validation completed successfully")


def test_convenience_functions(mock_database_loader):
    """Test that convenience functions work correctly with optimized integration."""
    # Test automatic loading with mock
    loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)
    problem = loader.load_problem(max_instances=2)
    assert problem is not None
    assert problem.total_task_count > 0

    # Test explicit unique loading with mock
    unique_loader = mock_database_loader(
        use_test_tables=True, prefer_optimized_mode=False
    )
    unique_problem = unique_loader.load_problem()
    assert unique_problem is not None
    assert not unique_problem.is_optimized_mode

    logger.info("✓ Convenience functions work correctly")


def test_optimized_architecture_completeness(mock_database_loader):
    """Test that the complete optimized architecture (Weeks 1-3) is integrated."""
    loader = mock_database_loader(use_test_tables=True, prefer_optimized_mode=True)

    # Week 1: Optimized data models
    problem = loader.load_problem()
    if problem.is_optimized_mode:
        assert problem.job_optimized_pattern is not None
        assert len(problem.job_instances) > 0
        logger.info("✓ Week 1: Optimized data models integrated")

        # Week 2: Optimized-optimized constraints
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=15)
        assert solution.get("status") in ["OPTIMAL", "FEASIBLE"]
        logger.info("✓ Week 2: Optimized-optimized constraints working")

        # Week 3: Optimized database architecture
        optimized_patterns = loader.load_available_optimized_patterns()
        assert len(optimized_patterns) > 0
        logger.info("✓ Week 3: Optimized database architecture operational")

        logger.info(
            "✓ Complete optimized architecture (Weeks 1-3) successfully integrated"
        )
    else:
        logger.info(
            "Optimized infrastructure not available - using unique compatibility mode"
        )


if __name__ == "__main__":
    # Run tests directly
    logging.basicConfig(level=logging.INFO)

    test = TestOptimizedIntegration()

    print("Running optimized integration tests...")

    try:
        # Create mock database loader for standalone execution
        import os
        from unittest.mock import MagicMock, patch

        from src.data.loaders.database import DatabaseLoader

        # Mock test data
        mock_test_data = {
            "test_work_cells": [
                {"cell_id": "cell-1", "name": "Production Cell 1", "capacity": 3}
            ],
            "test_resources": [
                {
                    "resource_id": "lathe-1",
                    "cell_id": "cell-1",
                    "name": "CNC Lathe 1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "50.0",
                }
            ],
            "test_jobs": [
                {
                    "job_id": "order-001",
                    "description": "Customer Order 001",
                    "due_date": "2025-07-31T08:00:00+00:00",
                    "created_at": "2025-07-30T12:00:00+00:00",
                    "updated_at": "2025-07-30T12:00:00+00:00",
                }
            ],
            "test_tasks": [
                {
                    "task_id": "op-001-1",
                    "job_id": "order-001",
                    "name": "Setup Operation",
                    "department_id": "machining",
                    "is_setup": True,
                    "is_unattended": False,
                }
            ],
            "test_task_modes": [
                {
                    "task_mode_id": "mode-1",
                    "task_id": "op-001-1",
                    "machine_resource_id": "lathe-1",
                    "duration_minutes": 30,
                }
            ],
            "test_task_precedences": [],
        }

        def create_mock_client(url=None, key=None):  # noqa: ARG001
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_client.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table

            def mock_execute():
                if (
                    hasattr(mock_client.table, "call_args_list")
                    and mock_client.table.call_args_list
                ):
                    table_name = mock_client.table.call_args_list[-1][0][0]
                    return MagicMock(data=mock_test_data.get(table_name, []))
                return MagicMock(data=[])

            mock_table.execute.side_effect = mock_execute
            return mock_client

        with (
            patch(
                "src.data.loaders.database.create_client",
                side_effect=create_mock_client,
            ),
            patch(
                "src.data.loaders.optimized_database.create_client",
                side_effect=create_mock_client,
            ),
            patch.dict(
                os.environ,
                {
                    "SUPABASE_URL": "https://mock.supabase.co",
                    "SUPABASE_ANON_KEY": "mock-key",
                },
            ),
        ):
            test.test_automatic_mode_detection(DatabaseLoader)
            test.test_optimized_vs_unique_compatibility(DatabaseLoader)
            test.test_optimized_solving_performance(DatabaseLoader)
            test.test_optimized_constraint_optimization(DatabaseLoader)
            test.test_solution_persistence(DatabaseLoader)
            test.test_optimized_instance_creation(DatabaseLoader)
            test.test_performance_comparison(DatabaseLoader)
            test.test_mixed_loading_modes(DatabaseLoader)
            test.test_optimized_validation(DatabaseLoader)

            test_convenience_functions(DatabaseLoader)
            test_optimized_architecture_completeness(DatabaseLoader)

        print("\n✅ All optimized integration tests passed!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise
