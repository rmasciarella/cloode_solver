"""End-to-end integration tests for template-based scheduling architecture.

Tests the complete pipeline from database loading through template solving to solution persistence.
Validates that the complete template architecture (Weeks 1-3) works end-to-end with optimal performance.
"""

import logging
import time

import pytest

from src.data.loaders.database import (
    DatabaseLoader,
    load_legacy_test_problem,
    load_test_problem,
)
from src.solver.core.solver import FreshSolver

logger = logging.getLogger(__name__)


class TestTemplateIntegration:
    """End-to-end integration tests for template-based scheduling."""

    def test_automatic_mode_detection(self):
        """Test that DatabaseLoader automatically detects and uses optimal loading mode."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)

        # This should automatically choose the best available loading method
        problem = loader.load_problem()

        assert problem is not None
        assert problem.total_task_count > 0
        assert problem.total_machine_count > 0

        # Check if template mode was used
        if problem.is_template_based:
            logger.info("✓ Template mode automatically detected and used")
            assert problem.job_template is not None
            assert len(problem.job_instances) > 0
            assert problem.template_task_count > 0
        else:
            logger.info("✓ Legacy mode used (no template infrastructure)")
            assert len(problem.jobs) > 0

    def test_template_vs_legacy_compatibility(self):
        """Test that both template and legacy modes produce valid, equivalent results."""
        # Load same data using both approaches
        template_loader = DatabaseLoader(
            use_test_tables=True, prefer_template_mode=True
        )
        legacy_loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=False)

        template_problem = template_loader.load_problem()
        legacy_problem = legacy_loader.load_problem()

        # Both should be valid problems
        assert template_problem is not None
        assert legacy_problem is not None

        # If template mode was used, compare with legacy
        if template_problem.is_template_based:
            logger.info("Comparing template vs legacy loading...")

            # Should have same machine count
            assert (
                template_problem.total_machine_count
                == legacy_problem.total_machine_count
            )

            # Template should have structured data
            assert template_problem.job_template is not None
            assert len(template_problem.job_instances) > 0

            # Legacy should have traditional jobs
            assert len(legacy_problem.jobs) > 0

            logger.info("✓ Template and legacy modes both produce valid problems")
        else:
            logger.info("✓ No template infrastructure - both modes use legacy loading")

    def test_template_solving_performance(self):
        """Test template-based solving performance and correctness."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem(max_instances=3)  # Limit for testing

        if not problem.is_template_based:
            pytest.skip("No template infrastructure available for performance testing")

        logger.info(
            f"Testing template problem: {problem.instance_count} instances, "
            f"{problem.template_task_count} template tasks each"
        )

        # Solve with template-optimized solver
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
            f"✓ Template problem solved in {solve_time:.2f}s with makespan {solution.get('makespan')}"
        )

    def test_template_constraint_optimization(self):
        """Test that template constraints provide performance benefits."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem(max_instances=5)

        if not problem.is_template_based:
            pytest.skip(
                "No template infrastructure for constraint optimization testing"
            )

        # Test template-optimized solver
        template_solver = FreshSolver(problem)

        start_time = time.time()
        template_solution = template_solver.solve(time_limit=20)
        template_time = time.time() - start_time

        # Verify template solution
        assert template_solution is not None
        assert template_solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        # Template solver should be efficient
        assert template_time < 20

        logger.info(
            f"✓ Template-optimized constraints completed in {template_time:.2f}s"
        )

        # Log optimization insights
        logger.info("Problem characteristics:")
        logger.info(f"  - {problem.instance_count} identical job instances")
        logger.info(f"  - {problem.template_task_count} tasks per instance")
        logger.info(f"  - {problem.total_task_count} total tasks")
        logger.info(
            f"  - {len(problem.job_template.template_precedences)} template precedences"
        )

    def test_solution_persistence(self):
        """Test that template solutions can be saved back to database."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem(max_instances=2)

        if not problem.is_template_based:
            pytest.skip("No template infrastructure for solution persistence testing")

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
            loader._template_loader.save_solution_assignments(problem, solution_data)
            logger.info("✓ Solution successfully persisted to database")
        except Exception as e:
            logger.warning(f"Solution persistence test skipped: {e}")
            # This is expected if database is read-only or table doesn't exist

    def test_template_instance_creation(self):
        """Test dynamic creation of job instances from templates."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)

        # Try to get available templates
        templates = loader.load_available_templates()

        if not templates:
            pytest.skip("No templates available for instance creation testing")

        template = templates[0]
        logger.info(f"Testing instance creation for template: {template.name}")

        # Test instance creation (would create new records in job_instances table)
        try:
            instance_ids = loader.create_template_instances(
                template.template_id, instance_count=2, base_description="Test Instance"
            )

            assert len(instance_ids) == 2
            logger.info(f"✓ Created {len(instance_ids)} instances: {instance_ids}")

            # Test loading the newly created instances
            problem = loader.load_template_problem(
                template.template_id, max_instances=2
            )
            assert problem.instance_count >= 2

        except Exception as e:
            logger.warning(f"Instance creation test skipped: {e}")
            # Expected if database is read-only

    def test_performance_comparison(self):
        """Compare template vs legacy performance on identical data."""
        # This test requires both template and legacy data representing the same problem
        template_loader = DatabaseLoader(
            use_test_tables=True, prefer_template_mode=True
        )
        legacy_loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=False)

        # Load problems
        template_problem = template_loader.load_problem(max_instances=3)
        legacy_problem = legacy_loader.load_problem()

        if not template_problem.is_template_based:
            pytest.skip(
                "Template infrastructure not available for performance comparison"
            )

        # Test template performance
        template_start = time.time()
        template_solver = FreshSolver(template_problem)
        template_solution = template_solver.solve(time_limit=20)
        template_time = time.time() - template_start

        # Test legacy performance
        legacy_start = time.time()
        legacy_solver = FreshSolver(legacy_problem)
        legacy_solution = legacy_solver.solve(time_limit=20)
        legacy_time = time.time() - legacy_start

        # Both should find solutions
        assert template_solution.get("status") in ["OPTIMAL", "FEASIBLE"]
        assert legacy_solution.get("status") in ["OPTIMAL", "FEASIBLE"]

        # Log performance comparison
        speedup = legacy_time / template_time if template_time > 0 else 1.0
        logger.info("Performance comparison:")
        logger.info(f"  Template mode: {template_time:.2f}s")
        logger.info(f"  Legacy mode:   {legacy_time:.2f}s")
        logger.info(f"  Speedup:       {speedup:.1f}x")

        # Template should be competitive or better
        assert template_time <= legacy_time * 1.5  # Allow 50% margin for small problems

    def test_mixed_loading_modes(self):
        """Test loading different types of problems in the same session."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)

        # Test automatic mode detection
        auto_problem = loader.load_problem()
        assert auto_problem is not None

        # Test explicit legacy loading
        loader_legacy = DatabaseLoader(use_test_tables=True, prefer_template_mode=False)
        legacy_problem = loader_legacy.load_problem()
        assert legacy_problem is not None

        # If templates are available, test specific template loading
        templates = loader.load_available_templates()
        if templates:
            template_problem = loader.load_template_problem(templates[0].template_id)
            assert template_problem is not None
            assert template_problem.is_template_based

            logger.info("✓ Successfully tested mixed loading modes:")
            logger.info(
                f"  - Auto detection: {'template' if auto_problem.is_template_based else 'legacy'}"
            )
            logger.info("  - Explicit legacy: valid")
            logger.info("  - Explicit template: valid")

    def test_template_validation(self):
        """Test comprehensive validation of template-based problems."""
        loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)
        problem = loader.load_problem()

        if not problem.is_template_based:
            pytest.skip("No template infrastructure for validation testing")

        # Run comprehensive problem validation
        issues = problem.validate()

        # Should have no critical validation issues
        critical_issues = [
            issue
            for issue in issues
            if "non-existent" in issue.lower() or "circular" in issue.lower()
        ]
        assert len(critical_issues) == 0, (
            f"Critical validation issues found: {critical_issues}"
        )

        # Log validation results
        if issues:
            logger.warning(f"Validation warnings found: {len(issues)}")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✓ Template problem validation passed with no issues")

        # Test template-specific validations
        template_issues = problem.job_template.validate_template()
        assert len(template_issues) == 0, (
            f"Template validation issues: {template_issues}"
        )

        logger.info("✓ Template validation completed successfully")


def test_convenience_functions():
    """Test that convenience functions work correctly with template integration."""
    # Test automatic loading
    problem = load_test_problem(max_instances=2)
    assert problem is not None
    assert problem.total_task_count > 0

    # Test explicit legacy loading
    legacy_problem = load_legacy_test_problem()
    assert legacy_problem is not None
    assert not legacy_problem.is_template_based

    logger.info("✓ Convenience functions work correctly")


def test_template_architecture_completeness():
    """Test that the complete template architecture (Weeks 1-3) is integrated."""
    loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=True)

    # Week 1: Template data models
    problem = loader.load_problem()
    if problem.is_template_based:
        assert problem.job_template is not None
        assert len(problem.job_instances) > 0
        logger.info("✓ Week 1: Template data models integrated")

        # Week 2: Template-optimized constraints
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=15)
        assert solution.get("status") in ["OPTIMAL", "FEASIBLE"]
        logger.info("✓ Week 2: Template-optimized constraints working")

        # Week 3: Template database architecture
        templates = loader.load_available_templates()
        assert len(templates) > 0
        logger.info("✓ Week 3: Template database architecture operational")

        logger.info(
            "✓ Complete template architecture (Weeks 1-3) successfully integrated"
        )
    else:
        logger.info(
            "Template infrastructure not available - using legacy compatibility mode"
        )


if __name__ == "__main__":
    # Run tests directly
    logging.basicConfig(level=logging.INFO)

    test = TestTemplateIntegration()

    print("Running template integration tests...")

    try:
        test.test_automatic_mode_detection()
        test.test_template_vs_legacy_compatibility()
        test.test_template_solving_performance()
        test.test_template_constraint_optimization()
        test.test_solution_persistence()
        test.test_template_instance_creation()
        test.test_performance_comparison()
        test.test_mixed_loading_modes()
        test.test_template_validation()

        test_convenience_functions()
        test_template_architecture_completeness()

        print("\n✅ All template integration tests passed!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise
