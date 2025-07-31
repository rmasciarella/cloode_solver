#!/usr/bin/env python3
"""Trade-off Visualization Demo.

This example demonstrates the trade-off visualization utilities
for comparing different multi-objective optimization strategies.
"""

import logging
import os
import sys
from datetime import UTC, datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from src.solver.visualization.trade_off_visualizer import (
    create_objective_bar_chart,
    create_strategy_comparison_table,
    visualize_optimization_results,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple format for cleaner output
)
logger = logging.getLogger(__name__)


def create_demo_problem() -> SchedulingProblem:
    """Create a simple demo problem for visualization testing."""
    # Create machines
    machines = [
        Machine("m1", "cell1", "Fast Machine", 1, 120.0),
        Machine("m2", "cell1", "Slow Machine", 1, 60.0),
    ]

    # Create a simple job
    now = datetime.now(UTC)
    job_due = now + timedelta(hours=3)

    tasks = [
        Task(
            task_id="t1",
            job_id="j1",
            name="Task 1",
            modes=[
                TaskMode("t1_m1", "t1", "m1", 60),  # 1 hour on fast machine
                TaskMode("t1_m2", "t1", "m2", 120),  # 2 hours on slow machine
            ],
        ),
        Task(
            task_id="t2",
            job_id="j1",
            name="Task 2",
            precedence_predecessors=["t1"],
            modes=[
                TaskMode("t2_m1", "t2", "m1", 45),  # 45 min on fast machine
                TaskMode("t2_m2", "t2", "m2", 90),  # 1.5 hours on slow machine
            ],
        ),
    ]

    job = Job("j1", "Demo Job", job_due, tasks)

    work_cell = WorkCell("cell1", "Demo Cell", 2, machines)

    precedences = [Precedence("t1", "t2")]

    multi_objective_config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.LEXICOGRAPHICAL,
        objectives=[
            ObjectiveWeight(ObjectiveType.MINIMIZE_TOTAL_LATENESS, 1.0, priority=1),
            ObjectiveWeight(ObjectiveType.MINIMIZE_MAKESPAN, 1.0, priority=2),
            ObjectiveWeight(ObjectiveType.MINIMIZE_TOTAL_COST, 1.0, priority=3),
        ],
    )

    return SchedulingProblem(
        jobs=[job],
        machines=machines,
        work_cells=[work_cell],
        precedences=precedences,
        multi_objective_config=multi_objective_config,
    )


def create_mock_results() -> dict:
    """Create mock optimization results for visualization demo."""
    # Mock results that would come from actual solver runs
    results = {
        "lexicographic": {
            "multi_objective": {
                "total_lateness": 0,
                "makespan": 18,
                "total_cost": 543.75,
                "strategy": "LEXICOGRAPHICAL",
            },
            "solve_time": 1.2,
        },
        "weighted_sum": {
            "multi_objective": {
                "total_lateness": 5,
                "makespan": 15,
                "total_cost": 620.50,
                "strategy": "WEIGHTED_SUM",
            },
            "solve_time": 0.8,
        },
        "pareto": {
            "recommended_solution": {
                "objectives": MockObjectiveSolution(
                    total_lateness=2, makespan=16, total_cost=580.25
                )
            },
            "solve_time": 3.5,
        },
    }

    return results


class MockObjectiveSolution:
    """Mock objective solution for demo purposes."""

    def __init__(self, total_lateness=0, makespan=0, total_cost=0):
        """Initialize mock objective solution with default values."""
        self.total_lateness = total_lateness
        self.makespan = makespan
        self.total_cost = total_cost

    def get_objective_value(self, objective_type: ObjectiveType):
        """Get objective value by type."""
        if objective_type == ObjectiveType.MINIMIZE_TOTAL_LATENESS:
            return self.total_lateness
        elif objective_type == ObjectiveType.MINIMIZE_MAKESPAN:
            return self.makespan
        elif objective_type == ObjectiveType.MINIMIZE_TOTAL_COST:
            return self.total_cost
        return None


def main():
    """Execute the trade-off visualization demonstration."""
    logger.info("=" * 80)
    logger.info("TRADE-OFF VISUALIZATION DEMO")
    logger.info("=" * 80)
    logger.info("")

    logger.info("This demo showcases the visualization utilities for comparing")
    logger.info("different multi-objective optimization strategies.")
    logger.info("")

    # Create mock results (in real usage, these would come from solver runs)
    results = create_mock_results()

    logger.info("Sample optimization results created:")
    logger.info("• Lexicographic: 0 lateness, 18 makespan, $543.75 cost")
    logger.info("• Weighted Sum: 5 lateness, 15 makespan, $620.50 cost")
    logger.info("• Pareto: 2 lateness, 16 makespan, $580.25 cost")
    logger.info("")

    # 1. Demo: Strategy Comparison Table
    logger.info("1. STRATEGY COMPARISON TABLE")
    logger.info("=" * 50)
    table = create_strategy_comparison_table(results)
    logger.info(table)
    logger.info("")

    # 2. Demo: Objective Bar Charts
    logger.info("2. OBJECTIVE BAR CHARTS")
    logger.info("=" * 50)
    charts = create_objective_bar_chart(results, objective="all")
    logger.info(charts)
    logger.info("")

    # 3. Demo: Comprehensive Visualization
    logger.info("3. COMPREHENSIVE VISUALIZATION REPORT")
    logger.info("=" * 50)
    comprehensive = visualize_optimization_results(
        results=results,
        include_pareto=False,  # Skip Pareto plot since we have mock data
        include_charts=True,
    )
    logger.info(comprehensive)
    logger.info("")

    # 4. Demo: Individual Objective Charts
    logger.info("4. INDIVIDUAL OBJECTIVE DEMONSTRATIONS")
    logger.info("=" * 50)

    logger.info("\nLateness Chart:")
    logger.info("-" * 30)
    lateness_chart = create_objective_bar_chart(results, objective="lateness")
    logger.info(lateness_chart)

    logger.info("\nMakespan Chart:")
    logger.info("-" * 30)
    makespan_chart = create_objective_bar_chart(results, objective="makespan")
    logger.info(makespan_chart)

    logger.info("\nCost Chart:")
    logger.info("-" * 30)
    cost_chart = create_objective_bar_chart(results, objective="cost")
    logger.info(cost_chart)

    logger.info("")
    logger.info("=" * 80)
    logger.info("DEMO COMPLETED")
    logger.info("=" * 80)
    logger.info("")
    logger.info("The visualization utilities provide:")
    logger.info("• Clear comparison tables for strategy performance")
    logger.info("• ASCII bar charts for objective comparisons")
    logger.info("• Comprehensive reports with recommendations")
    logger.info("• Modular components for custom analysis")
    logger.info("")
    logger.info("Use these tools in your optimization workflow to:")
    logger.info("• Compare different optimization strategies")
    logger.info("• Understand trade-offs between objectives")
    logger.info("• Make informed decisions about strategy selection")


if __name__ == "__main__":
    main()
