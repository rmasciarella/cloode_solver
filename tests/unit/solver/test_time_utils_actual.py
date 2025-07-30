"""Unit tests for actual time utility functions in time_utils.py."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from ortools.sat.python import cp_model

from src.solver.models.problem import Job, Machine, SchedulingProblem, Task, TaskMode
from src.solver.utils.time_utils import (
    calculate_horizon,
    calculate_latest_start,
    extract_solution,
    print_solution_summary,
)


def create_test_problem(num_jobs=2, due_hours_from_now=24) -> SchedulingProblem:
    """Create a test scheduling problem."""
    machines = [
        Machine(
            resource_id="M1",
            cell_id="cell1",
            name="Machine 1",
            capacity=1,
            cost_per_hour=10,
        ),
        Machine(
            resource_id="M2",
            cell_id="cell1",
            name="Machine 2",
            capacity=1,
            cost_per_hour=15,
        ),
    ]

    jobs = []
    for i in range(num_jobs):
        tasks = [
            Task(
                task_id=f"T{i*2+1}",
                job_id=f"J{i+1}",
                name=f"Task {i*2+1}",
                modes=[
                    TaskMode(
                        task_mode_id="tm_auto",
                        task_id="auto",
                        machine_resource_id="M1",
                        duration_minutes=60,
                    ),
                    TaskMode(
                        task_mode_id="tm_auto",
                        task_id="auto",
                        machine_resource_id="M2",
                        duration_minutes=45,
                    ),
                ],
            ),
            Task(
                task_id=f"T{i*2+2}",
                job_id=f"J{i+1}",
                name=f"Task {i*2+2}",
                modes=[
                    TaskMode(
                        task_mode_id="tm_auto",
                        task_id="auto",
                        machine_resource_id="M1",
                        duration_minutes=90,
                    ),
                    TaskMode(
                        task_mode_id="tm_auto",
                        task_id="auto",
                        machine_resource_id="M2",
                        duration_minutes=75,
                    ),
                ],
            ),
        ]

        job = Job(
            job_id=f"J{i+1}",
            description=f"Job {i+1}",
            tasks=tasks,
            due_date=datetime.now(UTC) + timedelta(hours=due_hours_from_now),
        )
        jobs.append(job)

    return SchedulingProblem(
        jobs=jobs, machines=machines, work_cells=[], precedences=[]
    )


class TestCalculateHorizon:
    """Test horizon calculation function."""

    def test_calculate_horizon_basic(self):
        """Test basic horizon calculation."""
        problem = create_test_problem(num_jobs=2, due_hours_from_now=24)
        horizon = calculate_horizon(problem)

        # Should be based on due date and work content
        assert horizon > 0
        assert isinstance(horizon, int)

    def test_calculate_horizon_far_due_date(self):
        """Test horizon with far future due date."""
        problem = create_test_problem(num_jobs=1, due_hours_from_now=168)  # 1 week
        horizon = calculate_horizon(problem)

        # Should handle far future dates
        assert horizon > 0
        assert horizon < 10000  # Some reasonable upper bound

    def test_calculate_horizon_multiple_jobs(self):
        """Test horizon considers all jobs."""
        problem1 = create_test_problem(num_jobs=1, due_hours_from_now=24)
        problem2 = create_test_problem(num_jobs=5, due_hours_from_now=24)

        horizon1 = calculate_horizon(problem1)
        horizon2 = calculate_horizon(problem2)

        # More jobs = more work = potentially longer horizon
        assert horizon2 >= horizon1


class TestCalculateLatestStart:
    """Test latest start calculation function."""

    def test_calculate_latest_start_basic(self):
        """Test basic latest start calculation."""
        problem = create_test_problem()
        job = problem.jobs[0]
        task = job.tasks[0]
        horizon = 100

        latest_start = calculate_latest_start(task, job, horizon)

        assert isinstance(latest_start, int)
        assert latest_start >= 0
        assert latest_start < horizon

    def test_calculate_latest_start_with_due_date(self):
        """Test latest start respects job due date."""
        problem = create_test_problem(due_hours_from_now=4)  # 4 hours from now
        job = problem.jobs[0]
        task = job.tasks[0]
        horizon = 1000

        latest_start = calculate_latest_start(task, job, horizon)

        # Should be constrained by due date, not just horizon
        assert latest_start < horizon

    def test_calculate_latest_start_task_position(self):
        """Test that task position affects latest start."""
        problem = create_test_problem()
        job = problem.jobs[0]
        task1 = job.tasks[0]  # First task
        task2 = job.tasks[1]  # Second task
        horizon = 100

        latest1 = calculate_latest_start(task1, job, horizon)
        latest2 = calculate_latest_start(task2, job, horizon)

        # First task should have earlier latest start than second
        assert latest1 <= latest2


class TestExtractSolution:
    """Test solution extraction function."""

    def test_extract_solution_optimal(self):
        """Test extracting solution from optimal solve."""
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()

        # Create simple model
        problem = create_test_problem(num_jobs=1)

        # Create variables
        task_starts = {}
        task_ends = {}
        task_assigned = {}

        for job in problem.jobs:
            for task in job.tasks:
                # Start and end variables
                start = model.NewIntVar(0, 100, f"start_{task.task_id}")
                end = model.NewIntVar(0, 100, f"end_{task.task_id}")
                task_starts[(job.job_id, task.task_id)] = start
                task_ends[(job.job_id, task.task_id)] = end

                # Create assignment variables for each machine
                assignments = []
                for machine in problem.machines:
                    assign_var = model.NewBoolVar(
                        f"assign_{task.task_id}_{machine.resource_id}"
                    )
                    task_assigned[(job.job_id, task.task_id, machine.resource_id)] = (
                        assign_var
                    )
                    assignments.append(assign_var)

                # Exactly one machine assignment
                model.AddExactlyOne(assignments)

                # Set duration from first mode (simplified for test)
                if task.modes:
                    duration_units = (task.modes[0].duration_minutes + 14) // 15
                    model.Add(end == start + duration_units)

        # Solve
        solver.Solve(model)

        # Extract solution
        solution = extract_solution(
            solver,
            model,
            problem,
            task_starts,
            task_ends,
            task_assigned,
        )

        assert solution is not None
        assert "schedule" in solution
        assert "makespan" in solution
        assert "solver_stats" in solution

    def test_extract_solution_infeasible(self):
        """Test extracting solution from infeasible solve."""
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()

        # Create infeasible model
        x = model.NewIntVar(0, 10, "x")
        model.Add(x > 10)  # Impossible!

        solver.Solve(model)

        problem = create_test_problem()
        solution = extract_solution(solver, problem, {}, {}, {}, {}, {})

        # Should handle infeasible gracefully
        assert solution is not None
        assert solution.get("status") == "INFEASIBLE" or "schedule" not in solution


class TestPrintSolutionSummary:
    """Test solution summary printing."""

    def test_print_solution_summary_basic(self):
        """Test basic solution summary printing."""
        solution = {
            "schedule": {"J1": {"T1": {"start": 0, "end": 4, "machine": "M1"}}},
            "makespan": 4,
            "solver_stats": {"status": "OPTIMAL", "solve_time": 0.5},
        }

        # Should not raise
        with patch("builtins.print") as mock_print:
            print_solution_summary(solution)

            # Check that something was printed
            assert mock_print.call_count > 0

    def test_print_solution_summary_empty(self):
        """Test printing empty solution."""
        solution = {}

        # Should handle gracefully
        with patch("builtins.print") as mock_print:
            print_solution_summary(solution)

            # Should still print something
            assert mock_print.call_count > 0
