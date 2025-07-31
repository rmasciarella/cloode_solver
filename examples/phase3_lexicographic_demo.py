#!/usr/bin/env python3
"""Phase 3 Lexicographic Multi-Objective Optimization Demo.

This example demonstrates the enhanced lexicographic optimization:
minimize total lateness > makespan > cost

The solver optimizes each objective in priority order, ensuring that
higher priority objectives remain at their optimal values.
"""

import logging
import os
import sys
from datetime import UTC, datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    MultiObjectiveConfiguration,
    ObjectiveType,
    ObjectiveWeight,
    OptimizationStrategy,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)

# Configure detailed logging to see the optimization phases
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_lexicographic_demo_problem() -> SchedulingProblem:
    """Create a demo problem designed to show clear trade-offs between objectives."""
    # Create machines with different costs
    machines = [
        Machine(
            resource_id="machine_1",
            cell_id="cell_1",
            name="Fast Expensive Machine",
            capacity=1,
            cost_per_hour=100.0,  # Expensive but fast
        ),
        Machine(
            resource_id="machine_2",
            cell_id="cell_1",
            name="Slow Cheap Machine",
            capacity=1,
            cost_per_hour=50.0,  # Cheap but slow
        ),
        Machine(
            resource_id="machine_3",
            cell_id="cell_2",
            name="Medium Machine",
            capacity=1,
            cost_per_hour=75.0,  # Medium cost and speed
        ),
    ]

    # Create jobs with different due dates to create lateness trade-offs
    now = datetime.now(UTC)
    jobs = []

    # Job 1: Tight deadline (will likely be late)
    job1_due = now + timedelta(hours=2)
    job1_tasks = [
        Task(
            task_id="j1_t1",
            job_id="job_1",
            name="Job 1 Task 1",
            modes=[
                TaskMode(
                    "j1_t1_m1", "j1_t1", "machine_1", 60
                ),  # 1 hour on fast machine
                TaskMode(
                    "j1_t1_m2", "j1_t1", "machine_2", 120
                ),  # 2 hours on slow machine
                TaskMode(
                    "j1_t1_m3", "j1_t1", "machine_3", 90
                ),  # 1.5 hours on medium machine
            ],
        ),
        Task(
            task_id="j1_t2",
            job_id="job_1",
            name="Job 1 Task 2",
            precedence_predecessors=["j1_t1"],
            modes=[
                TaskMode(
                    "j1_t2_m1", "j1_t2", "machine_1", 45
                ),  # 45 min on fast machine
                TaskMode(
                    "j1_t2_m2", "j1_t2", "machine_2", 90
                ),  # 1.5 hours on slow machine
                TaskMode(
                    "j1_t2_m3", "j1_t2", "machine_3", 75
                ),  # 1.25 hours on medium machine
            ],
        ),
    ]

    jobs.append(
        Job(
            job_id="job_1",
            description="Urgent Job - Tight Deadline",
            due_date=job1_due,
            tasks=job1_tasks,
        )
    )

    # Job 2: Medium deadline
    job2_due = now + timedelta(hours=4)
    job2_tasks = [
        Task(
            task_id="j2_t1",
            job_id="job_2",
            name="Job 2 Task 1",
            modes=[
                TaskMode(
                    "j2_t1_m1", "j2_t1", "machine_1", 90
                ),  # 1.5 hours on fast machine
                TaskMode(
                    "j2_t1_m2", "j2_t1", "machine_2", 150
                ),  # 2.5 hours on slow machine
                TaskMode(
                    "j2_t1_m3", "j2_t1", "machine_3", 120
                ),  # 2 hours on medium machine
            ],
        ),
    ]

    jobs.append(
        Job(
            job_id="job_2",
            description="Medium Priority Job",
            due_date=job2_due,
            tasks=job2_tasks,
        )
    )

    # Job 3: Relaxed deadline
    job3_due = now + timedelta(hours=6)
    job3_tasks = [
        Task(
            task_id="j3_t1",
            job_id="job_3",
            name="Job 3 Task 1",
            modes=[
                TaskMode(
                    "j3_t1_m1", "j3_t1", "machine_1", 75
                ),  # 1.25 hours on fast machine
                TaskMode(
                    "j3_t1_m2", "j3_t1", "machine_2", 135
                ),  # 2.25 hours on slow machine
                TaskMode(
                    "j3_t1_m3", "j3_t1", "machine_3", 105
                ),  # 1.75 hours on medium machine
            ],
        ),
        Task(
            task_id="j3_t2",
            job_id="job_3",
            name="Job 3 Task 2",
            precedence_predecessors=["j3_t1"],
            modes=[
                TaskMode(
                    "j3_t2_m1", "j3_t2", "machine_1", 60
                ),  # 1 hour on fast machine
                TaskMode(
                    "j3_t2_m2", "j3_t2", "machine_2", 120
                ),  # 2 hours on slow machine
                TaskMode(
                    "j3_t2_m3", "j3_t2", "machine_3", 90
                ),  # 1.5 hours on medium machine
            ],
        ),
    ]

    jobs.append(
        Job(
            job_id="job_3",
            description="Low Priority Job - Flexible Deadline",
            due_date=job3_due,
            tasks=job3_tasks,
        )
    )

    # Create work cells containing machines
    work_cells = [
        WorkCell(
            cell_id="cell_1",
            name="Main Production Cell",
            capacity=2,  # Can handle 2 machines
            machines=[machines[0], machines[1]],  # Fast and slow machines
        ),
        WorkCell(
            cell_id="cell_2",
            name="Secondary Cell",
            capacity=1,
            machines=[machines[2]],  # Medium machine
        ),
    ]

    # Create precedence constraints from task definitions
    precedences = []
    for job in jobs:
        for task in job.tasks:
            for pred_task_id in task.precedence_predecessors:
                precedences.append(
                    Precedence(
                        predecessor_task_id=pred_task_id, successor_task_id=task.task_id
                    )
                )

    # Configure lexicographic multi-objective optimization
    # Priority order: minimize total lateness > makespan > cost
    multi_objective_config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.LEXICOGRAPHICAL,
        objectives=[
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_LATENESS,
                weight=1.0,
                priority=1,  # Highest priority
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_MAKESPAN,
                weight=1.0,
                priority=2,  # Second priority
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_COST,
                weight=1.0,
                priority=3,  # Third priority
            ),
        ],
        lexicographical_tolerance=0.01,
    )

    return SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=work_cells,
        precedences=precedences,
        multi_objective_config=multi_objective_config,
    )


def demonstrate_different_strategies():
    """Compare lexicographic optimization with other strategies."""
    logger.info("=== Phase 3 Multi-Objective Optimization Comparison ===")

    # Create the base problem (used for all demonstrations)
    # Note: Each demo creates its own problem instance

    # 1. Test Lexicographic Optimization (our main focus)
    logger.info(
        "\n1. LEXICOGRAPHIC OPTIMIZATION (Priority: Lateness > Makespan > Cost)"
    )
    lexicographic_problem = create_lexicographic_demo_problem()
    lexicographic_problem.multi_objective_config.strategy = (
        OptimizationStrategy.LEXICOGRAPHICAL
    )

    solver = FreshSolver(lexicographic_problem)
    lexicographic_result = solver.solve_lexicographic(time_limit_per_phase=60)

    if "error" not in lexicographic_result:
        logger.info("Lexicographic Optimization Results:")
        multi_obj = lexicographic_result.get("multi_objective", {})
        logger.info(f"  Total Lateness: {multi_obj.get('total_lateness')}")
        logger.info(f"  Makespan: {multi_obj.get('makespan')}")
        cost_value = multi_obj.get("total_cost", 0)
        cost_str = f"${cost_value:.2f}" if cost_value is not None else "$0.00"
        logger.info(f"  Total Cost: {cost_str}")
        logger.info(f"  Strategy: {multi_obj.get('strategy')}")

        # Show phase-by-phase results
        phase_results = multi_obj.get("phase_results", [])
        for phase_result in phase_results:
            logger.info(
                f"  Phase {phase_result['phase']} ({phase_result['objective']}): "
                f"{phase_result['optimal_value']} "
                f"(solved in {phase_result['solve_time']:.2f}s)"
            )
    else:
        logger.error(
            f"Lexicographic optimization failed: {lexicographic_result.get('error')}"
        )

    # 2. Test Weighted Sum for comparison
    logger.info("\n2. WEIGHTED SUM OPTIMIZATION (Equal weights)")
    weighted_problem = create_lexicographic_demo_problem()
    weighted_problem.multi_objective_config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.WEIGHTED_SUM,
        objectives=[
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_LATENESS,
                weight=0.5,  # 50% weight
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_MAKESPAN,
                weight=0.3,  # 30% weight
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_COST,
                weight=0.2,  # 20% weight
            ),
        ],
    )

    solver = FreshSolver(weighted_problem)
    weighted_result = solver.solve(time_limit=60)

    if "multi_objective" in weighted_result:
        logger.info("Weighted Sum Optimization Results:")
        multi_obj = weighted_result["multi_objective"]
        logger.info(f"  Total Lateness: {multi_obj.get('total_lateness')}")
        logger.info(f"  Makespan: {multi_obj.get('makespan')}")
        cost_value = multi_obj.get("total_cost", 0)
        cost_str = f"${cost_value:.2f}" if cost_value is not None else "$0.00"
        logger.info(f"  Total Cost: {cost_str}")
        logger.info(f"  Strategy: {multi_obj.get('strategy')}")

    # 3. Test Pareto Optimization
    logger.info("\n3. PARETO OPTIMIZATION (Multiple trade-off solutions)")
    pareto_problem = create_lexicographic_demo_problem()
    pareto_problem.multi_objective_config.strategy = OptimizationStrategy.PARETO_OPTIMAL

    solver = FreshSolver(pareto_problem)
    pareto_result = solver.solve_pareto_optimal(time_limit_per_solve=30)

    if "pareto_frontier" in pareto_result:
        frontier = pareto_result["pareto_frontier"]
        logger.info(f"Pareto Frontier found {frontier['solution_count']} solutions:")

        for i, solution in enumerate(
            frontier["solutions"][:3]
        ):  # Show first 3 solutions
            obj = solution["objectives"]
            logger.info(f"  Solution {i + 1}:")
            logger.info(f"    Total Lateness: {obj.get('total_lateness')}")
            logger.info(f"    Makespan: {obj.get('makespan')}")
            cost_value = obj.get("total_cost", 0)
            cost_str = f"${cost_value:.2f}" if cost_value is not None else "$0.00"
            logger.info(f"    Total Cost: {cost_str}")

        if len(frontier["solutions"]) > 3:
            logger.info(f"    ... and {len(frontier['solutions']) - 3} more solutions")

        # Show recommended solution
        if pareto_result.get("recommended_solution"):
            rec_obj = pareto_result["recommended_solution"]["objectives"]
            logger.info("  Recommended Solution:")
            logger.info(f"    Total Lateness: {rec_obj.get('total_lateness')}")
            logger.info(f"    Makespan: {rec_obj.get('makespan')}")
            cost_value = rec_obj.get("total_cost", 0)
            cost_str = f"${cost_value:.2f}" if cost_value is not None else "$0.00"
            logger.info(f"    Total Cost: {cost_str}")

    return {
        "lexicographic": lexicographic_result,
        "weighted_sum": weighted_result,
        "pareto": pareto_result,
    }


def analyze_trade_offs(results: dict):
    """Analyze the trade-offs between different optimization strategies."""
    logger.info("\n=== TRADE-OFF ANALYSIS ===")

    # Use the visualization utility for comprehensive trade-off analysis
    from src.solver.visualization.trade_off_visualizer import (
        visualize_optimization_results,
    )

    # Create comprehensive visualization
    visualization_report = visualize_optimization_results(
        results=results, include_pareto=True, include_charts=True
    )

    # Print the visualization report line by line using logger
    for line in visualization_report.split("\n"):
        logger.info(line)


def main():
    """Execute the Phase 3 lexicographic multi-objective optimization demonstration."""
    logger.info("Starting Phase 3 Lexicographic Multi-Objective Optimization Demo")
    logger.info("=" * 70)

    try:
        # Run the comparison
        results = demonstrate_different_strategies()

        # Analyze trade-offs
        analyze_trade_offs(results)

        logger.info("\n" + "=" * 70)
        logger.info("Demo completed successfully!")
        logger.info("\nLexicographic optimization provides a principled way to handle")
        logger.info(
            "multiple competing objectives by optimizing them in priority order."
        )
        logger.info("This ensures that the most important objective (total lateness)")
        logger.info("is optimized first, with subsequent objectives optimized subject")
        logger.info("to maintaining optimality of higher-priority objectives.")

    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
