"""Unit tests for solver utilities.

Tests time calculations, horizon computation, and solution extraction.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from ortools.sat.python import cp_model

from src.solver.models.problem import Job, Machine, SchedulingProblem, Task, TaskMode
from src.solver.utils.time_utils import (
    calculate_horizon,
    calculate_latest_start,
    extract_solution,
    print_solution_summary,
)


class TestCalculateHorizon:
    """Test horizon calculation."""

    def test_calculate_horizon_normal(self):
        """Test horizon calculation with normal data."""
        # GIVEN: Jobs with tasks and due dates
        now = datetime.now(UTC)

        task1 = Task(
            "t1",
            "j1",
            "Task 1",
            modes=[TaskMode("m1", "t1", "machine-1", 30)],  # 30 minutes
        )
        task2 = Task(
            "t2",
            "j1",
            "Task 2",
            modes=[TaskMode("m2", "t2", "machine-1", 45)],  # 45 minutes
        )

        job1 = Job(
            job_id="j1",
            description="Job 1",
            due_date=now + timedelta(hours=6),
            tasks=[task1, task2],
        )
        job2 = Job(
            job_id="j2",
            description="Job 2",
            due_date=now + timedelta(hours=8),
            tasks=[],
        )

        problem = SchedulingProblem([job1, job2], [], [], [])

        # WHEN: Calculating horizon
        with patch("builtins.print"):  # Suppress print output
            horizon = calculate_horizon(problem)

        # THEN: Horizon is reasonable
        # Total work: 75 minutes = 5 time units
        # Time to latest due: 8 hours = 32 time units
        # Should use max(32, 5*2) * 1.2 = 38.4 -> 38
        assert horizon >= 38
        assert horizon >= 100  # Minimum horizon

    def test_calculate_horizon_minimum_enforced(self):
        """Test that minimum horizon is enforced."""
        # GIVEN: Very short problem
        now = datetime.now(UTC)
        task = Task(
            "t1",
            "j1",
            "Task",
            modes=[TaskMode("m1", "t1", "machine-1", 15)],  # 1 time unit
        )
        job = Job(
            job_id="j1",
            description="Job",
            due_date=now + timedelta(hours=1),
            tasks=[task],
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Calculating horizon
        with patch("builtins.print"):
            horizon = calculate_horizon(problem)

        # THEN: Minimum horizon applied
        assert horizon >= 100  # MIN_HORIZON

    def test_calculate_horizon_large_workload(self):
        """Test horizon with large workload."""
        # GIVEN: Many tasks
        now = datetime.now(UTC)
        tasks = []
        for i in range(20):
            task = Task(
                f"t{i}",
                "j1",
                f"Task {i}",
                modes=[TaskMode(f"m{i}", f"t{i}", "machine-1", 60)],  # 1 hour each
            )
            tasks.append(task)

        job = Job(
            job_id="j1",
            description="Big Job",
            due_date=now + timedelta(days=2),
            tasks=tasks,
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Calculating horizon
        with patch("builtins.print"):
            horizon = calculate_horizon(problem)

        # THEN: Horizon accommodates workload
        # 20 hours of work = 80 time units
        # Should use at least 80 * 2 * 1.2 = 192
        assert horizon >= 192


class TestCalculateLatestStart:
    """Test latest start time calculation."""

    def test_calculate_latest_start_normal(self):
        """Test latest start calculation within bounds."""
        # GIVEN: Task and job with future due date
        now = datetime.now(UTC)
        task = Task(
            "t1",
            "j1",
            "Task",
            modes=[TaskMode("m1", "t1", "machine-1", 30)],  # 2 time units
        )
        job = Job(
            job_id="j1",
            description="Job",
            due_date=now + timedelta(hours=6),
            tasks=[task],
        )
        horizon = 100

        # WHEN: Calculating latest start
        latest = calculate_latest_start(task, job, horizon)

        # THEN: Latest start is due date minus duration
        # 6 hours = 24 time units
        # Latest = 24 - 2 = 22 (but might be 21 due to rounding)
        assert latest in [21, 22]  # Allow for minor rounding differences

    def test_calculate_latest_start_negative_prevention(self):
        """Test that latest start is never negative."""
        # GIVEN: Task with past due date
        now = datetime.now(UTC)
        task = Task(
            "t1",
            "j1",
            "Task",
            modes=[TaskMode("m1", "t1", "machine-1", 120)],  # 8 time units
        )
        job = Job(
            job_id="j1",
            description="Job",
            due_date=now - timedelta(hours=1),
            tasks=[task],
        )  # Past due
        horizon = 100

        # WHEN: Calculating latest start
        latest = calculate_latest_start(task, job, horizon)

        # THEN: Latest start is 0 (not negative)
        assert latest == 0

    def test_calculate_latest_start_horizon_capping(self):
        """Test that latest start respects horizon."""
        # GIVEN: Task with very far due date
        now = datetime.now(UTC)
        task = Task(
            "t1",
            "j1",
            "Task",
            modes=[TaskMode("m1", "t1", "machine-1", 30)],  # 2 time units
        )
        job = Job(
            job_id="j1",
            description="Job",
            due_date=now + timedelta(days=10),
            tasks=[task],
        )
        horizon = 50  # Small horizon

        # WHEN: Calculating latest start
        latest = calculate_latest_start(task, job, horizon)

        # THEN: Latest start is capped by horizon
        assert latest == 48  # horizon - duration


class TestExtractSolution:
    """Test solution extraction from solved model."""

    def test_extract_solution_optimal(self):
        """Test extracting optimal solution."""
        # GIVEN: Solved model with optimal status
        solver = MagicMock(spec=cp_model.CpSolver)
        solver.StatusName.return_value = "OPTIMAL"
        solver.WallTime.return_value = 1.5
        solver.NumBranches.return_value = 100
        solver.NumConflicts.return_value = 50
        solver.ObjectiveValue.return_value = 42

        # Mock variable values
        solver.Value.side_effect = lambda var: {
            "start_j1_t1": 0,
            "end_j1_t1": 2,
            "start_j1_t2": 2,
            "end_j1_t2": 6,
            "assigned_j1_t1_m1": 1,
            "assigned_j1_t2_m1": 1,
        }.get(str(var), 0)

        model = MagicMock()

        # Create test problem
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "m1", 30)])
        task2 = Task("t2", "j1", "Task 2", modes=[TaskMode("m2", "t2", "m1", 60)])
        job = Job(
            "j1", "Job 1", datetime.now(UTC) + timedelta(hours=2), tasks=[task1, task2]
        )
        machine = Machine("m1", "c1", "Machine 1")
        problem = SchedulingProblem([job], [machine], [], [])

        # Create variables
        task_starts = {
            ("j1", "t1"): MagicMock(__str__=lambda _: "start_j1_t1"),
            ("j1", "t2"): MagicMock(__str__=lambda _: "start_j1_t2"),
        }
        task_ends = {
            ("j1", "t1"): MagicMock(__str__=lambda _: "end_j1_t1"),
            ("j1", "t2"): MagicMock(__str__=lambda _: "end_j1_t2"),
        }
        task_assigned = {
            ("j1", "t1", "m1"): MagicMock(__str__=lambda _: "assigned_j1_t1_m1"),
            ("j1", "t2", "m1"): MagicMock(__str__=lambda _: "assigned_j1_t2_m1"),
        }

        # WHEN: Extracting solution
        solution = extract_solution(
            solver, model, problem, task_starts, task_ends, task_assigned
        )

        # THEN: Solution extracted correctly
        assert solution["status"] == "OPTIMAL"
        assert len(solution["schedule"]) == 2
        assert solution["schedule"][0]["task_id"] == "t1"
        assert solution["schedule"][0]["start_time"] == 0
        assert solution["schedule"][0]["end_time"] == 2
        assert solution["schedule"][0]["machine_id"] == "m1"
        assert solution["makespan"] == 6
        assert solution["solver_stats"]["solve_time"] == 1.5

    def test_extract_solution_infeasible(self):
        """Test extracting infeasible solution."""
        # GIVEN: Infeasible solver status
        solver = MagicMock()
        solver.StatusName.return_value = "INFEASIBLE"
        solver.WallTime.return_value = 0.5
        solver.NumBranches.return_value = 10
        solver.NumConflicts.return_value = 5

        model = MagicMock()
        problem = SchedulingProblem([], [], [], [])

        # WHEN: Extracting solution
        solution = extract_solution(solver, model, problem, {}, {}, {})

        # THEN: Empty solution with status
        assert solution["status"] == "INFEASIBLE"
        assert solution["schedule"] == []
        assert solution["makespan"] == 0
        assert solution["lateness"] == 0

    def test_extract_solution_lateness_calculation(self):
        """Test that lateness is calculated correctly."""
        # GIVEN: Job that finishes late
        solver = MagicMock()
        solver.StatusName.return_value = "OPTIMAL"
        solver.Value.side_effect = lambda var: {
            "start_j1_t1": 0,
            "end_j1_t1": 20,  # Ends at time 20 (5 hours)
            "assigned_j1_t1_m1": 1,
        }.get(str(var), 0)

        model = MagicMock()

        # Job due in 2 hours but task takes 5 hours
        now = datetime.now(UTC)
        task = Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "m1", 300)])
        job = Job(
            job_id="j1",
            description="Job 1",
            due_date=now + timedelta(hours=2),
            tasks=[task],
        )
        machine = Machine("m1", "c1", "Machine 1")
        problem = SchedulingProblem([job], [machine], [], [])

        task_starts = {("j1", "t1"): MagicMock(__str__=lambda _: "start_j1_t1")}
        task_ends = {("j1", "t1"): MagicMock(__str__=lambda _: "end_j1_t1")}
        task_assigned = {
            ("j1", "t1", "m1"): MagicMock(__str__=lambda _: "assigned_j1_t1_m1")
        }

        # WHEN: Extracting solution
        solution = extract_solution(
            solver, model, problem, task_starts, task_ends, task_assigned
        )

        # THEN: Lateness calculated
        # Task ends at 5 hours, due at 2 hours = 3 hours late = 180 minutes
        # Allow for minor floating point differences
        assert abs(solution["total_lateness_minutes"] - 180) < 0.001

    @patch("builtins.hasattr")
    def test_extract_solution_no_objective(self, mock_hasattr):
        """Test extraction when solver has no objective value."""
        # GIVEN: Solver without objective
        solver = MagicMock()
        solver.StatusName.return_value = "FEASIBLE"
        solver.WallTime.return_value = 1.0
        solver.NumBranches.return_value = 50
        solver.NumConflicts.return_value = 25
        mock_hasattr.return_value = False  # No ObjectiveValue attribute

        model = MagicMock()
        problem = SchedulingProblem([], [], [], [])

        # WHEN: Extracting solution
        solution = extract_solution(solver, model, problem, {}, {}, {})

        # THEN: Objective value is None
        assert solution["solver_stats"]["objective_value"] is None


class TestPrintSolutionSummary:
    """Test solution summary printing."""

    @patch("builtins.print")
    def test_print_solution_summary(self, mock_print):
        """Test printing solution summary."""
        # GIVEN: Solution data
        solution = {
            "status": "OPTIMAL",
            "makespan": 10,
            "makespan_hours": 2.5,
            "total_lateness_minutes": 30.5,
            "solver_stats": {"solve_time": 1.234, "branches": 1000, "conflicts": 500},
            "schedule": [
                {
                    "task_name": "Task 1",
                    "start_time": 0,
                    "end_time": 4,
                    "duration_minutes": 60,
                    "machine_name": "Machine 1",
                },
                {
                    "task_name": "Task 2",
                    "start_time": 4,
                    "end_time": 10,
                    "duration_minutes": 90,
                    "machine_name": "Machine 2",
                },
            ],
        }

        # WHEN: Printing summary
        print_solution_summary(solution)

        # THEN: Summary printed with correct format
        printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        assert "OPTIMAL" in printed_text
        assert "2.5 hours" in printed_text
        assert "30.5 minutes" in printed_text
        assert "1.23 seconds" in printed_text
        assert "1,000" in printed_text  # Formatted number
        assert "Task 1" in printed_text
        assert "Task 2" in printed_text

    @patch("builtins.print")
    def test_print_solution_summary_truncation(self, mock_print):
        """Test that long schedules are truncated."""
        # GIVEN: Solution with many tasks
        tasks = []
        for i in range(15):
            tasks.append(
                {
                    "task_name": f"Task {i}",
                    "start_time": i * 2,
                    "end_time": (i + 1) * 2,
                    "duration_minutes": 30,
                    "machine_name": "Machine 1",
                }
            )

        solution = {
            "status": "FEASIBLE",
            "makespan": 30,
            "makespan_hours": 7.5,
            "total_lateness_minutes": 0,
            "solver_stats": {"solve_time": 2.0, "branches": 5000, "conflicts": 2500},
            "schedule": tasks,
        }

        # WHEN: Printing summary
        print_solution_summary(solution)

        # THEN: Only first 10 tasks shown
        printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        assert "Task 9" in printed_text  # Last of first 10
        assert "Task 10" not in printed_text  # 11th task not shown
        assert "and 5 more tasks" in printed_text
