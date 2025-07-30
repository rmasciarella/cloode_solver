"""Performance regression tests for the Fresh Solver."""

import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

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


class PerformanceMetrics:
    """Store and compare performance metrics."""

    def __init__(self, baseline_file: str = "tests/performance/baseline_metrics.json"):
        self.baseline_file = Path(baseline_file)
        self.current_metrics: dict[str, float] = {}
        self.baseline_metrics: dict[str, float] = {}
        self._load_baseline()

    def _load_baseline(self):
        """Load baseline metrics from file."""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                self.baseline_metrics = json.load(f)

    def save_baseline(self):
        """Save current metrics as new baseline."""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, "w") as f:
            json.dump(self.current_metrics, f, indent=2)

    def record_metric(self, name: str, value: float):
        """Record a performance metric."""
        self.current_metrics[name] = value

    def check_regression(self, name: str, tolerance: float = 0.2) -> bool:
        """Check if there's a performance regression.

        Args:
            name: Metric name
            tolerance: Acceptable performance degradation (0.2 = 20% slower)

        Returns:
            True if performance is acceptable, False if regression detected

        """
        if name not in self.baseline_metrics:
            return True  # No baseline to compare against

        baseline = self.baseline_metrics[name]
        current = self.current_metrics.get(name, float("inf"))

        # Check if current is within tolerance
        return current <= baseline * (1 + tolerance)


def create_test_problem(
    num_jobs: int, tasks_per_job: int, num_machines: int
) -> SchedulingProblem:
    """Create a test problem with specified dimensions."""
    machines = []
    for i in range(num_machines):
        machines.append(
            Machine(
                resource_id=f"M{i + 1}",
                cell_id="WC1",
                name=f"Machine {i + 1}",
                capacity=1,
                cost_per_hour=10.0,
            )
        )

    jobs = []
    task_counter = 1

    for job_idx in range(num_jobs):
        tasks = []

        for task_idx in range(tasks_per_job):
            # Create modes for each machine
            modes = []
            for machine_idx in range(
                min(3, num_machines)
            ):  # Each task can use up to 3 machines
                modes.append(
                    TaskMode(
                        task_mode_id=f"TM{task_counter}_{machine_idx}",
                        task_id=f"T{task_counter}",
                        machine_resource_id=machines[machine_idx].resource_id,
                        duration_minutes=60 + (task_idx * 15),  # 60-120 minutes
                    )
                )

            task = Task(
                task_id=f"T{task_counter}",
                job_id=f"J{job_idx + 1}",
                name=f"Task {task_counter}",
                modes=modes,
            )
            tasks.append(task)
            task_counter += 1

        job = Job(
            job_id=f"J{job_idx + 1}",
            description=f"Job {job_idx + 1}",
            due_date=datetime.now(UTC) + timedelta(hours=24),
            tasks=tasks,
        )
        jobs.append(job)

    # Add precedences within each job
    precedences = []
    for job in jobs:
        for i in range(len(job.tasks) - 1):
            precedences.append(
                Precedence(
                    predecessor_task_id=job.tasks[i].task_id,
                    successor_task_id=job.tasks[i + 1].task_id,
                )
            )

    # Create a work cell containing all machines
    work_cell = WorkCell(
        cell_id="WC1", name="Work Cell 1", capacity=len(machines), machines=machines
    )

    return SchedulingProblem(
        jobs=jobs, machines=machines, work_cells=[work_cell], precedences=precedences
    )


class TestPerformanceRegression:
    """Test suite for performance regression."""

    @pytest.fixture
    def metrics(self):
        """Create performance metrics tracker."""
        return PerformanceMetrics()

    def test_tiny_dataset_performance(self, metrics):
        """Test performance on tiny dataset (2 jobs, 10 tasks total)."""
        problem = create_test_problem(num_jobs=2, tasks_per_job=5, num_machines=3)

        solver = FreshSolver(problem)
        start_time = time.time()
        solution = solver.solve(time_limit=60)
        solve_time = time.time() - start_time

        assert solution is not None, "Failed to find solution for tiny dataset"

        metrics.record_metric("tiny_dataset_solve_time", solve_time)
        assert solve_time < 1.0, f"Tiny dataset took {solve_time:.2f}s, expected < 1s"

        # Check regression
        assert metrics.check_regression(
            "tiny_dataset_solve_time"
        ), f"Performance regression detected: {solve_time:.2f}s vs baseline"

    def test_small_dataset_performance(self, metrics):
        """Test performance on small dataset (5 jobs, 50 tasks total)."""
        problem = create_test_problem(num_jobs=5, tasks_per_job=10, num_machines=5)

        solver = FreshSolver(problem)
        start_time = time.time()
        solution = solver.solve(time_limit=60)
        solve_time = time.time() - start_time

        assert solution is not None, "Failed to find solution for small dataset"

        metrics.record_metric("small_dataset_solve_time", solve_time)
        assert (
            solve_time < 10.0
        ), f"Small dataset took {solve_time:.2f}s, expected < 10s"

        # Check regression
        assert metrics.check_regression(
            "small_dataset_solve_time"
        ), f"Performance regression detected: {solve_time:.2f}s vs baseline"

    @pytest.mark.slow
    def test_medium_dataset_performance(self, metrics):
        """Test performance on medium dataset (20 jobs, 200 tasks total)."""
        problem = create_test_problem(num_jobs=20, tasks_per_job=10, num_machines=10)

        solver = FreshSolver(problem)
        start_time = time.time()
        solution = solver.solve(time_limit=120)
        solve_time = time.time() - start_time

        assert solution is not None, "Failed to find solution for medium dataset"

        metrics.record_metric("medium_dataset_solve_time", solve_time)
        assert (
            solve_time < 60.0
        ), f"Medium dataset took {solve_time:.2f}s, expected < 60s"

        # Check regression
        assert metrics.check_regression(
            "medium_dataset_solve_time"
        ), f"Performance regression detected: {solve_time:.2f}s vs baseline"

    @pytest.mark.skip(reason="psutil not installed")
    def test_solver_memory_usage(self, metrics):
        """Test solver memory usage doesn't grow excessively."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Solve multiple problems
        for _i in range(5):
            problem = create_test_problem(num_jobs=10, tasks_per_job=5, num_machines=5)
            solver = FreshSolver()
            solver.solve(problem, time_limit_seconds=30)

        # Check memory after solving
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        metrics.record_metric("memory_increase_mb", memory_increase)

        # Memory shouldn't increase by more than 100MB
        assert (
            memory_increase < 100
        ), f"Memory increased by {memory_increase:.2f}MB, expected < 100MB"

    def test_constraint_scaling(self, metrics):
        """Test how constraint addition time scales with problem size."""
        sizes = [10, 20, 50]
        times = []

        for size in sizes:
            problem = create_test_problem(
                num_jobs=size, tasks_per_job=5, num_machines=5
            )
            solver = FreshSolver(problem)

            # Time constraint creation (we'll time the variable and constraint creation)
            start_time = time.time()
            solver.create_variables()
            solver.add_constraints()
            constraint_time = time.time() - start_time

            times.append(constraint_time)

        # Check that constraint time doesn't grow quadratically
        # If it doubles when size doubles, that's linear (good)
        # If it quadruples, that's quadratic (bad)
        growth_rate = times[2] / times[0]  # 50 tasks vs 10 tasks (5x)

        metrics.record_metric("constraint_scaling_factor", growth_rate)

        # Should be less than quadratic growth (25x)
        assert (
            growth_rate < 15
        ), f"Constraint creation time grew by {growth_rate:.2f}x for 5x problem size"


@pytest.mark.parametrize("save_baseline", [False])
def test_update_baseline(save_baseline):
    """Run all performance tests and optionally save as new baseline.

    To update baseline: pytest -k test_update_baseline --save-baseline
    """
    if save_baseline or os.environ.get("SAVE_BASELINE") == "1":
        metrics = PerformanceMetrics()

        # Run all tests to collect metrics
        test_suite = TestPerformanceRegression()
        test_suite.test_tiny_dataset_performance(metrics)
        test_suite.test_small_dataset_performance(metrics)
        test_suite.test_medium_dataset_performance(metrics)
        test_suite.test_solver_memory_usage(metrics)
        test_suite.test_constraint_scaling(metrics)

        # Save as new baseline
        metrics.save_baseline()
        print(f"Saved new baseline metrics to {metrics.baseline_file}")
        print("Current metrics:", json.dumps(metrics.current_metrics, indent=2))
