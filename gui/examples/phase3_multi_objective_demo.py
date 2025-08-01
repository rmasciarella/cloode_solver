#!/usr/bin/env python3
"""Phase 3 Multi-Objective Optimization Demonstration.

This script demonstrates the comprehensive multi-objective optimization capabilities
including lexicographical optimization, weighted sum, and Pareto frontier analysis.

Usage:
    uv run python examples/phase3_multi_objective_demo.py
"""

import logging
from datetime import UTC, datetime, timedelta

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    MultiObjectiveConfiguration,
    ObjectiveType,
    ObjectiveWeight,
    OptimizationStrategy,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_demo_problem() -> SchedulingProblem:
    """Create a demonstration scheduling problem for multi-objective optimization."""
    # Create machines with different costs
    machines = [
        Machine(
            resource_id="machine_1",
            cell_id="cell_1",
            name="High-Speed CNC",
            capacity=1,
            cost_per_hour=75.0,
        ),
        Machine(
            resource_id="machine_2",
            cell_id="cell_1",
            name="Standard CNC",
            capacity=1,
            cost_per_hour=50.0,
        ),
        Machine(
            resource_id="machine_3",
            cell_id="cell_2",
            name="Assembly Station",
            capacity=2,
            cost_per_hour=30.0,
        ),
    ]

    # Create work cells
    work_cells = [
        WorkCell(
            cell_id="cell_1", name="Machining Cell", capacity=2, machines=machines[:2]
        ),
        WorkCell(
            cell_id="cell_2", name="Assembly Cell", capacity=3, machines=machines[2:]
        ),
    ]

    # Create jobs with varying due dates to create lateness trade-offs
    base_time = datetime.now(UTC)
    jobs = []

    for i, (due_offset_hours, priority) in enumerate(
        [
            (24, "urgent"),  # Job 1: Due in 24 hours (tight deadline)
            (48, "normal"),  # Job 2: Due in 48 hours (moderate deadline)
            (72, "low"),  # Job 3: Due in 72 hours (loose deadline)
        ]
    ):
        job_id = f"job_{i + 1}"
        due_date = base_time + timedelta(hours=due_offset_hours)

        tasks = []
        for j in range(3):  # 3 tasks per job
            task_id = f"{job_id}_task_{j + 1}"

            # Create different task modes with cost/time trade-offs
            modes = []
            if j == 0:  # Machining task
                modes = [
                    TaskMode(
                        task_mode_id=f"{task_id}_fast",
                        task_id=task_id,
                        machine_resource_id="machine_1",
                        duration_minutes=30,  # Fast but expensive
                    ),
                    TaskMode(
                        task_mode_id=f"{task_id}_slow",
                        task_id=task_id,
                        machine_resource_id="machine_2",
                        duration_minutes=45,  # Slow but cheaper
                    ),
                ]
            elif j == 1:  # Second machining task
                modes = [
                    TaskMode(
                        task_mode_id=f"{task_id}_fast",
                        task_id=task_id,
                        machine_resource_id="machine_1",
                        duration_minutes=60,
                    ),
                    TaskMode(
                        task_mode_id=f"{task_id}_slow",
                        task_id=task_id,
                        machine_resource_id="machine_2",
                        duration_minutes=90,
                    ),
                ]
            else:  # Assembly task
                modes = [
                    TaskMode(
                        task_mode_id=f"{task_id}_assembly",
                        task_id=task_id,
                        machine_resource_id="machine_3",
                        duration_minutes=120,
                    ),
                ]

            task = Task(
                task_id=task_id,
                job_id=job_id,
                name=f"Task {j + 1} ({priority})",
                modes=modes,
            )

            # Set up precedences (linear chain)
            if j > 0:
                task.precedence_predecessors = [f"{job_id}_task_{j}"]
                tasks[j - 1].precedence_successors = [task_id]

            tasks.append(task)

        job = Job(
            job_id=job_id,
            description=f"Job {i + 1} ({priority} priority)",
            due_date=due_date,
            tasks=tasks,
        )
        jobs.append(job)

    # Create scheduling problem
    problem = SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=work_cells,
        precedences=[],  # Precedences are set in tasks
    )

    return problem


def demonstrate_lexicographical_optimization() -> None:
    """Demonstrate lexicographical multi-objective optimization."""
    logger.info("\n" + "=" * 80)
    logger.info("LEXICOGRAPHICAL OPTIMIZATION DEMO")
    logger.info("Priority: Total Lateness > Makespan > Total Cost")
    logger.info("=" * 80)

    problem = create_demo_problem()

    # Configure lexicographical optimization (your preferred approach)
    # Priority 1: Minimize total lateness (most important)
    # Priority 2: Minimize makespan (second priority)
    # Priority 3: Minimize total cost (least important)
    config = MultiObjectiveConfiguration(
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
    )

    problem.multi_objective_config = config

    # Solve with lexicographical optimization
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)

    # Display results
    if solution and "multi_objective" in solution:
        mo = solution["multi_objective"]
        logger.info("✅ Lexicographical Solution Found:")
        logger.info(f"   Total Lateness: {mo['total_lateness']} time units")
        logger.info(f"   Makespan: {mo['makespan']} time units")
        logger.info(f"   Total Cost: ${mo['total_cost']:.2f}")
        logger.info(f"   Machine Utilization: {mo['machine_utilization']:.1f}%")
        logger.info(f"   Strategy: {mo['strategy']}")
    else:
        logger.error("❌ Failed to find lexicographical solution")


def demonstrate_weighted_sum_optimization() -> None:
    """Demonstrate weighted sum multi-objective optimization."""
    logger.info("\n" + "=" * 80)
    logger.info("WEIGHTED SUM OPTIMIZATION DEMO")
    logger.info("Balanced approach with custom weights")
    logger.info("=" * 80)

    problem = create_demo_problem()

    # Configure weighted sum optimization
    # Balanced weights but emphasizing schedule performance over cost
    config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.WEIGHTED_SUM,
        objectives=[
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_MAKESPAN,
                weight=0.4,  # 40% weight on makespan
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_LATENESS,
                weight=0.4,  # 40% weight on lateness
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_COST,
                weight=0.2,  # 20% weight on cost
            ),
        ],
    )

    problem.multi_objective_config = config

    # Solve with weighted sum
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)

    # Display results
    if solution and "multi_objective" in solution:
        mo = solution["multi_objective"]
        logger.info("✅ Weighted Sum Solution Found:")
        logger.info(f"   Makespan: {mo['makespan']} time units (weight: 40%)")
        logger.info(
            f"   Total Lateness: {mo['total_lateness']} time units (weight: 40%)"
        )
        logger.info(f"   Total Cost: ${mo['total_cost']:.2f} (weight: 20%)")
        logger.info(f"   Machine Utilization: {mo['machine_utilization']:.1f}%")
        logger.info(f"   Primary Objective Value: {mo['primary_objective_value']}")
    else:
        logger.error("❌ Failed to find weighted sum solution")


def demonstrate_epsilon_constraint_optimization() -> None:
    """Demonstrate epsilon-constraint multi-objective optimization."""
    logger.info("\n" + "=" * 80)
    logger.info("EPSILON-CONSTRAINT OPTIMIZATION DEMO")
    logger.info("Minimize cost subject to lateness and makespan constraints")
    logger.info("=" * 80)

    problem = create_demo_problem()

    # Configure epsilon-constraint optimization
    # Minimize cost subject to bounds on lateness and makespan
    config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.EPSILON_CONSTRAINT,
        objectives=[
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_COST,
                weight=1.0,
                # No epsilon bound - this is the objective to minimize
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_LATENESS,
                weight=1.0,
                epsilon_bound=50.0,  # Lateness must be ≤ 50 time units
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_MAKESPAN,
                weight=1.0,
                epsilon_bound=200.0,  # Makespan must be ≤ 200 time units
            ),
        ],
    )

    problem.multi_objective_config = config

    # Solve with epsilon-constraint
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)

    # Display results
    if solution and "multi_objective" in solution:
        mo = solution["multi_objective"]
        logger.info("✅ Epsilon-Constraint Solution Found:")
        logger.info(f"   Total Cost: ${mo['total_cost']:.2f} (minimized)")
        logger.info(f"   Total Lateness: {mo['total_lateness']} ≤ 50 time units")
        logger.info(f"   Makespan: {mo['makespan']} ≤ 200 time units")
        logger.info(f"   Machine Utilization: {mo['machine_utilization']:.1f}%")

        # Check constraint satisfaction
        lateness_ok = mo["total_lateness"] <= 50
        makespan_ok = mo["makespan"] <= 200
        logger.info(
            f"   Constraints: Lateness {'✅' if lateness_ok else '❌'}, "
            f"Makespan {'✅' if makespan_ok else '❌'}"
        )
    else:
        logger.error("❌ Failed to find epsilon-constraint solution")


def demonstrate_pareto_frontier_analysis() -> None:
    """Demonstrate Pareto frontier analysis and trade-off visualization."""
    logger.info("\n" + "=" * 80)
    logger.info("PARETO FRONTIER ANALYSIS DEMO")
    logger.info("Finding multiple non-dominated solutions")
    logger.info("=" * 80)

    problem = create_demo_problem()

    # Configure for Pareto analysis with multiple objectives
    config = MultiObjectiveConfiguration(
        strategy=OptimizationStrategy.PARETO_OPTIMAL,
        objectives=[
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_MAKESPAN,
                weight=1.0,
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_LATENESS,
                weight=1.0,
            ),
            ObjectiveWeight(
                objective_type=ObjectiveType.MINIMIZE_TOTAL_COST,
                weight=1.0,
            ),
        ],
        pareto_iterations=8,  # Find 8 Pareto points
    )

    problem.multi_objective_config = config

    # Solve for Pareto frontier
    solver = FreshSolver(problem)
    pareto_results = solver.solve_pareto_optimal(time_limit_per_solve=30)

    # Display results
    if "error" not in pareto_results:
        frontier = pareto_results["pareto_frontier"]
        analysis = pareto_results["trade_off_analysis"]
        recommended = pareto_results["recommended_solution"]

        logger.info("✅ Pareto Frontier Analysis Complete:")
        logger.info(f"   Non-dominated solutions found: {frontier['solution_count']}")
        logger.info(f"   Objectives analyzed: {len(frontier['objective_types'])}")

        # Show trade-off summary
        logger.info("\n📊 Trade-off Analysis:")
        logger.info(f"   Solutions on frontier: {analysis['pareto_solutions_count']}")
        logger.info(f"   Objectives analyzed: {analysis['objectives_analyzed']}")

        if "strongest_correlation" in analysis:
            logger.info(
                f"   Strongest correlation: {analysis['strongest_correlation']:.3f}"
            )
            logger.info(f"   Between: {analysis['strongest_correlation_objectives']}")

        # Show recommended solution
        if recommended:
            rec_obj = recommended["objectives"]
            logger.info("\n🎯 Recommended Balanced Solution:")
            logger.info(f"   Makespan: {rec_obj['makespan']} time units")
            logger.info(f"   Total Lateness: {rec_obj['total_lateness']} time units")
            logger.info(f"   Total Cost: ${rec_obj['total_cost']:.2f}")
            logger.info(
                f"   Machine Utilization: {rec_obj['machine_utilization']:.1f}%"
            )

        # Show extreme solutions for comparison
        logger.info("\n🔄 Trade-off Examples from Pareto Frontier:")
        for i, solution in enumerate(frontier["solutions"][:3]):  # Show first 3
            obj = solution["objectives"]
            logger.info(
                f"   Solution {i + 1}: Makespan={obj['makespan']}, "
                f"Lateness={obj['total_lateness']}, Cost=${obj['total_cost']:.2f}"
            )
    else:
        logger.error(f"❌ Pareto analysis failed: {pareto_results['error']}")


def demonstrate_trade_off_insights() -> None:
    """Demonstrate trade-off insights and recommendations."""
    logger.info("\n" + "=" * 80)
    logger.info("TRADE-OFF INSIGHTS & RECOMMENDATIONS")
    logger.info("=" * 80)

    logger.info("🎯 Key Insights from Multi-Objective Optimization:")
    logger.info("")

    logger.info("1. LEXICOGRAPHICAL APPROACH (Recommended):")
    logger.info("   ✅ Best for clear priority hierarchy")
    logger.info("   ✅ Guarantees primary objective is optimized first")
    logger.info("   ✅ Easy to understand and explain to stakeholders")
    logger.info("   ⚠️  May miss good compromise solutions")
    logger.info("")

    logger.info("2. WEIGHTED SUM APPROACH:")
    logger.info("   ✅ Good for balanced optimization")
    logger.info("   ✅ Single solve - faster than multi-phase")
    logger.info("   ⚠️  Requires careful weight tuning")
    logger.info("   ⚠️  May not find solutions on non-convex Pareto frontiers")
    logger.info("")

    logger.info("3. EPSILON-CONSTRAINT APPROACH:")
    logger.info("   ✅ Good when constraints are more important than optimization")
    logger.info("   ✅ Can find non-convex Pareto points")
    logger.info("   ⚠️  Requires knowledge of reasonable epsilon bounds")
    logger.info("")

    logger.info("4. PARETO FRONTIER ANALYSIS:")
    logger.info("   ✅ Shows all trade-off options")
    logger.info("   ✅ Identifies correlations between objectives")
    logger.info("   ✅ Provides decision support with multiple alternatives")
    logger.info("   ⚠️  Computationally expensive (multiple solves)")
    logger.info("")

    logger.info("💡 PRODUCTION RECOMMENDATIONS:")
    logger.info("   • Use LEXICOGRAPHICAL for daily production scheduling")
    logger.info("   • Use PARETO ANALYSIS for strategic planning & what-if scenarios")
    logger.info(
        "   • Use WEIGHTED SUM for real-time optimization with tight time limits"
    )
    logger.info("   • Use EPSILON-CONSTRAINT when regulatory constraints are critical")


def main() -> None:
    """Run the complete Phase 3 multi-objective optimization demonstration."""
    logger.info("🚀 Starting Phase 3 Multi-Objective Optimization Demonstration")
    logger.info(
        "This demo showcases advanced production planning with competing objectives"
    )

    try:
        # Demonstrate each optimization strategy
        demonstrate_lexicographical_optimization()
        demonstrate_weighted_sum_optimization()
        demonstrate_epsilon_constraint_optimization()
        demonstrate_pareto_frontier_analysis()
        demonstrate_trade_off_insights()

        logger.info("\n" + "=" * 80)
        logger.info("✅ PHASE 3 MULTI-OBJECTIVE OPTIMIZATION DEMO COMPLETE")
        logger.info("=" * 80)
        logger.info("🎯 Key Capabilities Demonstrated:")
        logger.info(
            "   ✅ Lexicographical optimization (total lateness > makespan > cost)"
        )
        logger.info("   ✅ Configurable weighted objectives")
        logger.info("   ✅ Epsilon-constraint method")
        logger.info("   ✅ Pareto-optimal solution finding")
        logger.info("   ✅ Trade-off analysis and visualization")
        logger.info("   ✅ Automatic solution recommendation")
        logger.info("")
        logger.info("🏭 Production Planning Benefits:")
        logger.info("   • Balance schedule performance vs. costs")
        logger.info("   • Meet delivery commitments while controlling expenses")
        logger.info("   • Explore what-if scenarios with trade-off analysis")
        logger.info("   • Support data-driven decision making")
        logger.info("")
        logger.info("Ready for production use! 🎉")

    except Exception as e:
        logger.error(f"❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
