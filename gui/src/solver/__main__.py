#!/usr/bin/env python3
"""Main entry point for the Fresh OR-Tools Solver with structured logging."""

import argparse
import sys

from src.data.loaders.database import load_test_problem
from src.solver.core.solver import FreshSolver
from src.solver.utils.logging_config import get_solver_logger, setup_logging
from src.solver.utils.time_utils import log_solution_summary


def main() -> int:
    """Execute the solver command-line interface with structured logging."""
    parser = argparse.ArgumentParser(
        description="Fresh OR-Tools CP-SAT Solver for job-shop scheduling"
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=30,
        help="Time limit for solver in seconds (default: 30)",
    )
    parser.add_argument(
        "--test", action="store_true", help="Load test problem from database"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        action="store_true",
        help="Enable file logging (default: console only)",
    )
    parser.add_argument(
        "--performance-log",
        action="store_true",
        help="Enable detailed performance logging",
    )

    args = parser.parse_args()

    # Setup centralized logging
    setup_logging(
        level=args.log_level,
        enable_file_logging=args.log_file,
        enable_performance_logging=args.performance_log,
    )

    logger = get_solver_logger("main")
    logger.info("Fresh OR-Tools Solver starting")
    logger.info(
        "Configuration: time_limit=%ds, log_level=%s", args.time_limit, args.log_level
    )

    try:
        # Load problem
        logger.info("Loading problem from database...")
        problem = load_test_problem()
        logger.info(
            "Problem loaded: %d jobs, %d tasks, %d machines",
            len(problem.jobs),
            problem.total_task_count,
            len(problem.machines),
        )

        # Create and run solver
        logger.info("Initializing solver...")
        solver = FreshSolver(problem)

        logger.info("Starting solve with %d second time limit", args.time_limit)
        solution = solver.solve(time_limit=args.time_limit)

        # Log structured solution summary
        log_solution_summary(solution, logger)

        # Provide console feedback
        status = solution.get("status", "UNKNOWN")
        if status in ["OPTIMAL", "FEASIBLE"]:
            print(f"✅ Solver completed successfully: {status}")
            if "makespan" in solution:
                makespan_hours = solution.get(
                    "makespan_hours", solution["makespan"] * 15 / 60
                )
                makespan_units = solution["makespan"]
                print(
                    f"📅 Makespan: {makespan_units} time units "
                    f"({makespan_hours:.1f} hours)"
                )
            logger.info("Solver completed successfully")
            return 0
        else:
            print(f"❌ Solver failed: {status}")
            logger.error("Solver failed with status: %s", status)
            return 1

    except Exception as e:
        logger.error("Solver execution failed: %s", str(e), exc_info=True)
        print(f"❌ Solver execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
