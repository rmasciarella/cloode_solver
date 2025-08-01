#!/usr/bin/env python3
"""Performance benchmark script for OR-Tools scheduling solver.

Measures solve time, memory usage, and solution quality across different dataset sizes.
"""

import json
import os
import sys
import time
import tracemalloc
from datetime import UTC, datetime, timedelta

from ortools.sat.python import cp_model

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


class BenchmarkDataGenerator:
    """Generate test data of varying sizes."""

    @staticmethod
    def generate_problem(
        num_jobs: int, tasks_per_job: int, num_machines: int
    ) -> SchedulingProblem:
        """Generate a scheduling problem of specified size."""
        # Create machines
        machines = []
        cells = []

        # Create work cells (one per 2 machines)
        num_cells = (num_machines + 1) // 2
        for i in range(num_cells):
            cell = WorkCell(cell_id=f"cell_{i}", name=f"Cell {i}", capacity=2)
            cells.append(cell)

        # Create machines
        for i in range(num_machines):
            cell_idx = i // 2
            machine = Machine(
                resource_id=f"machine_{i}",
                cell_id=f"cell_{cell_idx}",
                name=f"Machine {i}",
                capacity=1,
                cost_per_hour=100 + i * 10,
            )
            machines.append(machine)

        # Create jobs with tasks
        jobs = []
        for j in range(num_jobs):
            tasks = []

            for t in range(tasks_per_job):
                task_id = f"job_{j}_task_{t}"

                # Create modes (each task can run on 2-3 machines)
                modes = []
                for m in range(min(3, num_machines)):
                    machine_idx = (j + t + m) % num_machines
                    duration = (
                        30 + (t * 15) + (m * 10)
                    )  # Vary duration by task and machine

                    mode = TaskMode(
                        task_mode_id=f"mode_{j}_{t}_{m}",
                        task_id=task_id,
                        machine_resource_id=f"machine_{machine_idx}",
                        duration_minutes=duration,
                    )
                    modes.append(mode)

                task = Task(
                    task_id=task_id,
                    job_id=f"job_{j}",
                    name=f"Job {j} Task {t}",
                    department_id=f"dept_{j % 3}",
                    modes=modes,
                    is_setup=(t == 0),  # First task is setup
                    is_unattended=(t == tasks_per_job - 1),  # Last task is unattended
                )
                tasks.append(task)

            # Set job due date based on total task time
            total_duration = sum(30 + (t * 15) for t in range(tasks_per_job))
            due_date = datetime.now(UTC) + timedelta(minutes=total_duration * 2)

            job = Job(
                job_id=f"job_{j}",
                description=f"Job {j}",
                due_date=due_date,
                tasks=tasks,
            )
            jobs.append(job)

        # Create precedences (linear within each job)
        precedences = []
        for job in jobs:
            for i in range(len(job.tasks) - 1):
                precedence = Precedence(
                    predecessor_task_id=job.tasks[i].task_id,
                    successor_task_id=job.tasks[i + 1].task_id,
                )
                precedences.append(precedence)

        return SchedulingProblem(
            jobs=jobs, machines=machines, work_cells=cells, precedences=precedences
        )


class BenchmarkRunner:
    """Run benchmarks and collect metrics."""

    def __init__(self):
        """Initialize benchmark runner with empty results."""
        self.results = []

    def run_benchmark(
        self, problem_name: str, problem: SchedulingProblem, time_limit: int = 60
    ) -> dict:
        """Run a single benchmark and return metrics."""
        print(f"\nRunning benchmark: {problem_name}")
        print(f"  Jobs: {len(problem.jobs)}")
        print(f"  Total tasks: {sum(len(job.tasks) for job in problem.jobs)}")
        print(f"  Machines: {len(problem.machines)}")
        print(f"  Precedences: {len(problem.precedences)}")

        # Start memory tracking
        tracemalloc.start()
        start_time = time.time()

        # Create and solve
        try:
            solver = FreshSolver(problem)
            # Suppress solver output
            solver.solver = cp_model.CpSolver()
            solver.solver.parameters.log_search_progress = False
            solution = solver.solve(time_limit=time_limit)

            # End timing
            solve_time = time.time() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Extract metrics
            result = {
                "name": problem_name,
                "num_jobs": len(problem.jobs),
                "num_tasks": sum(len(job.tasks) for job in problem.jobs),
                "num_machines": len(problem.machines),
                "num_precedences": len(problem.precedences),
                "solve_time": round(solve_time, 3),
                "memory_mb": round(peak / 1024 / 1024, 2),
                "status": solution["status"],
                "makespan": solution.get("makespan", None),
                "solver_stats": solution.get("statistics", {}),
            }

        except Exception as e:
            tracemalloc.stop()
            result = {
                "name": problem_name,
                "num_jobs": len(problem.jobs),
                "num_tasks": sum(len(job.tasks) for job in problem.jobs),
                "num_machines": len(problem.machines),
                "num_precedences": len(problem.precedences),
                "solve_time": None,
                "memory_mb": None,
                "status": "ERROR",
                "error": str(e),
            }

        self.results.append(result)
        return result

    def run_all_benchmarks(self):
        """Run all benchmark scenarios."""
        generator = BenchmarkDataGenerator()

        # Define benchmark scenarios
        scenarios = [
            # (name, num_jobs, tasks_per_job, num_machines, time_limit)
            ("Tiny", 2, 5, 3, 10),
            ("Small", 5, 10, 5, 30),
            ("Medium", 20, 25, 10, 60),
            ("Large", 50, 50, 20, 300),
        ]

        for name, jobs, tasks, machines, time_limit in scenarios:
            problem = generator.generate_problem(jobs, tasks, machines)
            self.run_benchmark(name, problem, time_limit)

    def print_results(self):
        """Print benchmark results in a table format."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        header = (
            f"{'Name':<10} {'Jobs':<6} {'Tasks':<7} {'Time(s)':<10} "
            f"{'Memory(MB)':<12} {'Status':<10} {'Makespan':<10}"
        )
        print(header)
        print("-" * 80)

        for r in self.results:
            time_str = f"{r['solve_time']:.3f}" if r["solve_time"] else "N/A"
            mem_str = f"{r['memory_mb']:.1f}" if r["memory_mb"] else "N/A"
            makespan_str = str(r["makespan"]) if r["makespan"] else "N/A"

            print(
                f"{r['name']:<10} {r['num_jobs']:<6} {r['num_tasks']:<7} "
                f"{time_str:<10} {mem_str:<12} {r['status']:<10} {makespan_str:<10}"
            )

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save results to JSON file."""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {filepath}")


def main():
    """Run all benchmarks."""
    print("OR-Tools Scheduling Solver - Performance Benchmarks")
    print("=" * 50)

    runner = BenchmarkRunner()
    runner.run_all_benchmarks()
    runner.print_results()
    runner.save_results()

    # Check performance targets
    print("\nPerformance Target Check:")
    for r in runner.results:
        if r["status"] == "OPTIMAL" and r["solve_time"]:
            if r["name"] == "Small" and r["solve_time"] < 10:
                print(f"✓ {r['name']}: {r['solve_time']}s < 10s target")
            elif r["name"] == "Medium" and r["solve_time"] < 60:
                print(f"✓ {r['name']}: {r['solve_time']}s < 60s target")
            else:
                print(f"✗ {r['name']}: {r['solve_time']}s")


if __name__ == "__main__":
    main()
