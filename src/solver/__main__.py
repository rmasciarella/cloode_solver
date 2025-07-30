#!/usr/bin/env python3
"""Main entry point for the Fresh OR-Tools Solver."""

import argparse
import logging
import sys

from src.data.loaders.database import load_test_problem
from src.solver.core.solver import FreshSolver
from src.solver.utils.time_utils import print_solution_summary

logger = logging.getLogger(__name__)


def main() -> int:
    """Execute the solver command-line interface."""
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

    args = parser.parse_args()

    # Load problem
    logger.info("Loading problem from database...")
    problem = load_test_problem()

    # Create and run solver
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=args.time_limit)

    # Print results
    print_solution_summary(solution)

    return 0 if solution["status"] in ["OPTIMAL", "FEASIBLE"] else 1


if __name__ == "__main__":
    sys.exit(main())
