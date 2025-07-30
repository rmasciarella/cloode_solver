#!/usr/bin/env python3
"""Quick test to validate template solver implementation works."""

import logging
from datetime import UTC, datetime, timedelta

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import JobInstance, SchedulingProblem
from src.solver.models.template_generator import (
    create_manufacturing_job_template,
    create_test_machines,
    create_test_work_cells,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Quick validation test for the template solver."""
    logger.info("Running quick template solver validation...")

    # Create template and instances
    template = create_manufacturing_job_template()
    machines = create_test_machines()
    work_cells = create_test_work_cells()

    # Create job instances
    now = datetime.now(UTC)
    job_instances = [
        JobInstance(
            instance_id="instance_001",
            template_id=template.template_id,
            description="Test Job Instance 1",
            due_date=now + timedelta(hours=4),
        ),
        JobInstance(
            instance_id="instance_002",
            template_id=template.template_id,
            description="Test Job Instance 2",
            due_date=now + timedelta(hours=6),
        ),
    ]

    # Create template-based scheduling problem
    problem = SchedulingProblem.create_from_template(
        job_template=template,
        job_instances=job_instances,
        machines=machines,
        work_cells=work_cells,
    )

    logger.info(
        f"Created problem: {problem.instance_count} instances, "
        f"{problem.template_task_count} template tasks"
    )
    logger.info(f"Total tasks: {problem.total_task_count}")
    logger.info(f"Is template-based: {problem.is_template_based}")

    # Create and test solver
    solver = FreshSolver(problem)
    logger.info("FreshSolver created successfully")

    # Test variable creation
    solver.create_variables()
    logger.info(
        f"Variables created: {len(solver.task_starts)} start vars, "
        f"{len(solver.task_assigned)} assignment vars"
    )

    # Test constraint addition
    solver.add_constraints()
    logger.info("Constraints added successfully")

    # Test objective setting
    solver.set_objective()
    logger.info("Objective set successfully")

    # Test search strategy
    solver.add_search_strategy()
    logger.info("Search strategy added successfully")

    logger.info("✅ All template solver components validated successfully!")
    logger.info(
        "🎉 Week 2 Template Architecture Implementation is ready for full testing!"
    )


if __name__ == "__main__":
    main()
