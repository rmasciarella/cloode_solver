#!/usr/bin/env python3
"""Quick performance benchmark for Phase 0 validation."""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ortools.sat.python import cp_model

from scripts.benchmark import BenchmarkDataGenerator
from src.solver.core.solver import FreshSolver


def run_quick_benchmark():
    """Run quick benchmarks for Phase 0."""
    generator = BenchmarkDataGenerator()

    print("OR-Tools Scheduling Solver - Quick Performance Check")
    print("=" * 50)

    scenarios = [
        ("Tiny", 2, 5, 3),
        ("Small", 5, 10, 5),
        ("Medium", 20, 25, 10),
    ]

    for name, jobs, tasks, machines in scenarios:
        print(f"\nBenchmark: {name}")
        print(f"  Jobs: {jobs}, Tasks per job: {tasks}, Machines: {machines}")

        # Generate problem
        problem = generator.generate_problem(jobs, tasks, machines)
        total_tasks = sum(len(job.tasks) for job in problem.jobs)
        print(f"  Total tasks: {total_tasks}")

        # Solve
        start_time = time.time()
        solver = FreshSolver(problem)

        # Configure solver to suppress output
        solver.solver = cp_model.CpSolver()
        solver.solver.parameters.log_search_progress = False
        solver.solver.parameters.max_time_in_seconds = 60

        solution = solver.solve(time_limit=60)
        solve_time = time.time() - start_time

        # Report results
        print(f"  Status: {solution['status']}")
        print(f"  Solve time: {solve_time:.3f}s")
        if solution["makespan"]:
            print(f"  Makespan: {solution['makespan']}")

        # Check against targets
        if name == "Small" and solve_time < 10:
            print("  ✓ Meets target (<10s)")
        elif name == "Medium" and solve_time < 60:
            print("  ✓ Meets target (<60s)")


if __name__ == "__main__":
    run_quick_benchmark()
