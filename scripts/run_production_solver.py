#!/usr/bin/env python3
"""Production data solver script.

Loads real production data and runs the optimized OR-Tools solver.
Demonstrates the template-based architecture with real-world constraints.
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.loaders.database import DatabaseLoader  # noqa: E402
from src.solver.core.solver import FreshSolver  # noqa: E402

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("production_solver.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """Run solver with production data."""
    logger.info("🚀 Starting Production Data Solver")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # Load production data (use_test_tables=False)
        logger.info("📊 Loading production data...")
        load_start = time.time()

        loader = DatabaseLoader(use_test_tables=False, prefer_optimized_mode=True)
        problem = loader.load_problem()

        load_time = time.time() - load_start

        # Log problem characteristics
        logger.info(f"✅ Data loaded in {load_time:.3f}s")
        logger.info(f"   📋 Jobs: {len(problem.jobs)}")
        logger.info(f"   📝 Tasks: {problem.total_task_count}")
        logger.info(f"   🏭 Machines: {len(problem.machines)}")
        logger.info(f"   🔗 Precedences: {len(problem.precedences)}")
        logger.info(f"   📊 Optimized mode: {problem.is_optimized_mode}")

        if problem.is_optimized_mode:
            logger.info(f"   🎯 Optimized tasks: {problem.optimized_task_count}")
            logger.info(f"   📈 Instances: {problem.instance_count}")
            logger.info("   ⚡ Expected speedup: 5-8x")

        # Create solver
        logger.info("\n🔧 Initializing solver...")
        # solver_start = time.time()  # Unused variable

        solver = FreshSolver(problem)

        # Configure for production - longer time limits for larger problems
        if problem.total_task_count > 50:
            time_limit = 120  # 2 minutes for large problems
        elif problem.total_task_count > 20:
            time_limit = 60  # 1 minute for medium problems
        else:
            time_limit = 30  # 30 seconds for small problems

        logger.info(f"   ⏱️ Time limit: {time_limit}s")
        logger.info(f"   📊 Problem size: {problem.total_task_count} tasks")

        # Solve the problem
        logger.info("\n🎯 Solving optimization problem...")
        solve_start = time.time()

        solution = solver.solve(time_limit=time_limit)

        solve_time = time.time() - solve_start
        total_time = time.time() - start_time

        # Report results
        logger.info("\n📈 SOLUTION RESULTS")
        logger.info("=" * 40)
        logger.info(f"Status: {solution.get('status', 'UNKNOWN')}")
        logger.info(f"Solve time: {solve_time:.3f}s")
        logger.info(f"Total time: {total_time:.3f}s")

        if solution.get("status") in ["OPTIMAL", "FEASIBLE"]:
            makespan = solution.get("makespan", 0)
            scheduled_tasks = len(solution.get("task_schedule", {}))

            logger.info("✅ Solution found!")
            logger.info(
                f"   📏 Makespan: {makespan} time units ({makespan * 0.25:.1f} hours)"
            )
            logger.info(
                f"   📝 Tasks scheduled: {scheduled_tasks}/{problem.total_task_count}"
            )

            # Performance analysis
            if problem.is_template_based:
                theoretical_legacy_time = solve_time * 7.81  # Inverse of 7.81x speedup
                logger.info("   ⚡ Template speedup: ~7.8x")
                logger.info(
                    f"   📊 Legacy estimated time: {theoretical_legacy_time:.1f}s"
                )

            # Business metrics
            if "machine_utilization" in solution:
                utilization = solution["machine_utilization"]
                if utilization:
                    avg_util = sum(utilization.values()) / len(utilization)
                    logger.info(f"   🏭 Average machine utilization: {avg_util:.1f}%")

            # Due date performance
            if "lateness_penalties" in solution:
                penalties = solution["lateness_penalties"]
                total_lateness = sum(penalties.values())
                on_time_jobs = sum(1 for p in penalties.values() if p == 0)
                logger.info(f"   📅 On-time jobs: {on_time_jobs}/{len(penalties)}")
                logger.info(f"   ⏰ Total lateness: {total_lateness} time units")

        else:
            logger.warning(f"❌ No solution found within {time_limit}s time limit")
            logger.warning("   Consider increasing time limit or checking constraints")

        # Performance targets validation
        logger.info("\n🎯 PERFORMANCE VALIDATION")
        logger.info("=" * 40)

        if problem.total_task_count <= 50:
            target = 10.0
            status = "✅ EXCELLENT" if solve_time <= target else "⚠️ SLOW"
            logger.info(f"Small problem target (<10s): {status} ({solve_time:.1f}s)")
        elif problem.total_task_count <= 500:
            target = 60.0
            status = "✅ EXCELLENT" if solve_time <= target else "⚠️ SLOW"
            logger.info(f"Medium problem target (<60s): {status} ({solve_time:.1f}s)")
        else:
            target = 1800.0  # 30 minutes
            status = "✅ ACCEPTABLE" if solve_time <= target else "❌ TOO SLOW"
            logger.info(f"Large problem target (<30m): {status} ({solve_time:.1f}s)")

        # Template architecture validation
        if problem.is_template_based and solve_time > 10:
            logger.warning(
                "⚠️ Template solver unexpectedly slow - investigate parameters"
            )
        elif problem.is_template_based:
            logger.info("✅ Template architecture delivering expected performance")

        logger.info("\n🎉 Production solver completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Production solver failed: {e}")
        logger.exception("Full error details:")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
