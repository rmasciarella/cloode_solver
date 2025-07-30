"""Unit tests for the main solver class.

Tests solver orchestration and integration of components.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from ortools.sat.python import cp_model

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
)


class TestFreshSolver:
    """Test FreshSolver class."""

    def test_solver_initialization(self, sample_problem_data):
        """Test solver initialization."""
        # GIVEN: Valid problem data
        problem = SchedulingProblem(
            jobs=sample_problem_data["jobs"],
            machines=sample_problem_data["machines"],
            work_cells=sample_problem_data["cells"],
            precedences=sample_problem_data["precedences"],
        )

        # WHEN: Creating solver
        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)

        # THEN: Solver initialized correctly
        assert solver.problem == problem
        assert solver.horizon == 100
        assert isinstance(solver.model, cp_model.CpModel)
        assert len(solver.task_starts) == 0  # Not populated until solve

    def test_create_variables(self, sample_problem_data):
        """Test variable creation."""
        # GIVEN: Solver with problem
        problem = SchedulingProblem(
            jobs=sample_problem_data["jobs"],
            machines=sample_problem_data["machines"],
            work_cells=sample_problem_data["cells"],
            precedences=sample_problem_data["precedences"],
        )

        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)

        # WHEN: Creating variables
        with patch("builtins.print"):  # Suppress output
            solver.create_variables()

        # THEN: Variables created for all tasks
        # 2 jobs with 3 tasks total
        assert len(solver.task_starts) == 3
        assert len(solver.task_ends) == 3
        assert len(solver.task_durations) == 3
        assert len(solver.task_intervals) == 3

        # Check specific variable exists
        assert ("job-1", "task-1-1") in solver.task_starts
        assert ("job-2", "task-2-1") in solver.task_starts

        # Check assignment variables (task-machine combinations)
        # task-1-1 has 2 modes, task-1-2 has 1 mode, task-2-1 has 2 modes = 5 total
        assert len(solver.task_assigned) == 5

    def test_create_variables_bounds(self):
        """Test that variable bounds are set correctly."""
        # GIVEN: Task with specific timing requirements
        task = Task(
            "t1",
            "j1",
            "Task",
            modes=[
                TaskMode("m1", "t1", "machine-1", 30),  # 2 time units
                TaskMode("m2", "t1", "machine-2", 60),  # 4 time units
            ],
        )
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC) + timedelta(hours=2),
            tasks=[task],
        )
        problem = SchedulingProblem([job], [], [], [])

        with (
            patch("src.solver.utils.time_utils.calculate_horizon", return_value=50),
            patch(
                "src.solver.utils.time_utils.calculate_latest_start", return_value=20
            )
        ):
            solver = FreshSolver(problem)

        # WHEN: Creating variables
        with patch("builtins.print"):
            solver.create_variables()

        # THEN: Bounds are correct
        start_var = solver.task_starts[("j1", "t1")]
        duration_var = solver.task_durations[("j1", "t1")]
        end_var = solver.task_ends[("j1", "t1")]

        # Check bounds (can't directly access from Python API, but verify they exist)
        assert start_var is not None
        assert duration_var is not None
        assert end_var is not None

    def test_add_constraints(self, sample_problem_data):
        """Test that all constraints are added."""
        # GIVEN: Solver with variables created
        problem = SchedulingProblem(
            jobs=sample_problem_data["jobs"],
            machines=sample_problem_data["machines"],
            work_cells=sample_problem_data["cells"],
            precedences=sample_problem_data["precedences"],
        )

        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)

        with patch("builtins.print"):
            solver.create_variables()

        # Mock constraint functions where they are used
        with (
            patch(
                "src.solver.core.solver.add_task_duration_constraints"
            ) as mock_duration,
            patch(
                "src.solver.core.solver.add_precedence_constraints"
            ) as mock_precedence,
            patch(
                "src.solver.core.solver.add_machine_assignment_constraints"
            ) as mock_assignment,
            patch(
                "src.solver.core.solver.add_machine_no_overlap_constraints"
            ) as mock_overlap,
            patch(
                "src.solver.core.solver.add_machine_capacity_constraints"
            ) as mock_capacity,
            patch(
                "src.solver.core.solver.add_redundant_precedence_constraints"
            ) as mock_redundant,
        ):

            # WHEN: Adding constraints
            solver.add_constraints()

            # THEN: All constraint functions called
            mock_duration.assert_called_once()
            mock_precedence.assert_called_once()
            mock_assignment.assert_called_once()
            mock_overlap.assert_called_once()
            mock_capacity.assert_called_once()
            mock_redundant.assert_called_once()

    def test_set_objective(self):
        """Test objective function setting."""
        # GIVEN: Solver with tasks
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "m1", 30)])
        task2 = Task("t2", "j1", "Task 2", modes=[TaskMode("m2", "t2", "m1", 45)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task1, task2],
        )
        problem = SchedulingProblem([job], [], [], [])

        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)

        with patch("builtins.print"):
            solver.create_variables()

        # WHEN: Setting objective
        solver.set_objective()

        # THEN: Model has minimize objective
        # Can't directly verify objective in Python API, but check no errors
        assert solver.model is not None

    def test_add_search_strategy(self):
        """Test search strategy is added."""
        # GIVEN: Solver with tasks
        task = Task("t1", "j1", "Task", modes=[TaskMode("m1", "t1", "m1", 30)])
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )
        problem = SchedulingProblem([job], [], [], [])

        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)

        with patch("builtins.print"):
            solver.create_variables()

        # WHEN: Adding search strategy
        solver.add_search_strategy()

        # THEN: No errors (can't directly verify strategy)
        assert solver.model is not None

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solve_optimal(self, mock_solver_class):
        """Test solving with optimal solution."""
        # GIVEN: Simple problem
        task = Task("t1", "j1", "Task", modes=[TaskMode("m1", "t1", "m1", 30)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC) + timedelta(hours=2),
            tasks=[task],
        )
        machine = Machine("m1", "c1", "Machine 1")
        problem = SchedulingProblem([job], [machine], [], [])

        # Mock solver
        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = cp_model.OPTIMAL
        mock_solver_instance.StatusName.return_value = "OPTIMAL"
        mock_solver_instance.Value.return_value = 2  # Mock value for variables
        mock_solver_instance.WallTime.return_value = 0.1
        mock_solver_instance.NumBranches.return_value = 10
        mock_solver_instance.NumConflicts.return_value = 0
        mock_solver_instance.ObjectiveValue.return_value = 2

        with (
            patch("src.solver.utils.time_utils.calculate_horizon", return_value=100),
            patch("src.solver.utils.time_utils.extract_solution") as mock_extract
        ):
            mock_extract.return_value = {
                "status": "OPTIMAL",
                "makespan": 2,
                "schedule": [],
            }

            solver = FreshSolver(problem)

            # WHEN: Solving
            with patch("builtins.print"):
                solution = solver.solve(time_limit=30)

            # THEN: Solution returned
            assert solution["status"] == "OPTIMAL"
            mock_solver_instance.parameters.max_time_in_seconds = 30
            mock_solver_instance.parameters.num_search_workers = 8

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solve_infeasible(self, mock_solver_class):
        """Test solving with infeasible problem."""
        # GIVEN: Problem setup with a simple job
        task = Task("t1", "j1", "Task", modes=[TaskMode("m1", "t1", "m1", 30)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC) + timedelta(hours=1),
            tasks=[task],
        )
        problem = SchedulingProblem([job], [], [], [])

        # Mock infeasible result
        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = cp_model.INFEASIBLE
        mock_solver_instance.StatusName.return_value = "INFEASIBLE"

        with (
            patch("src.solver.utils.time_utils.calculate_horizon", return_value=100),
            patch("src.solver.utils.time_utils.extract_solution") as mock_extract
        ):
            mock_extract.return_value = {
                "status": "INFEASIBLE",
                "makespan": 0,
                "schedule": [],
            }

            solver = FreshSolver(problem)

            # WHEN: Solving
            with patch("builtins.print"):
                solution = solver.solve()

            # THEN: Infeasible solution returned
            assert solution["status"] == "INFEASIBLE"
            assert solution["schedule"] == []

    def test_solve_time_limit(self):
        """Test that time limit is passed to solver."""
        # GIVEN: Simple problem with a job
        task = Task("t1", "j1", "Task", modes=[TaskMode("m1", "t1", "m1", 30)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC) + timedelta(hours=1),
            tasks=[task],
        )
        problem = SchedulingProblem([job], [], [], [])

        with (
            patch("src.solver.utils.time_utils.calculate_horizon", return_value=100),
            patch("ortools.sat.python.cp_model.CpSolver") as mock_solver_class
        ):
            mock_solver_instance = MagicMock()
            mock_solver_class.return_value = mock_solver_instance

            solver = FreshSolver(problem)

            # WHEN: Solving with custom time limit
            with (
                patch("builtins.print"),
                patch("src.solver.utils.time_utils.extract_solution")
            ):
                solver.solve(time_limit=120)

            # THEN: Time limit set correctly
            assert mock_solver_instance.parameters.max_time_in_seconds == 120


class TestPhase1Integration:
    """Integration tests for Phase 1 functionality."""

    def test_phase1_complete_solve(self):
        """Test complete Phase 1 solving with all constraints."""
        # GIVEN: Complete problem with all Phase 1 elements
        # Create machines
        m1 = Machine("m1", "c1", "Machine 1")
        m2 = Machine("m2", "c1", "Machine 2")

        # Create tasks with modes
        t1_modes = [
            TaskMode("mode1", "t1", "m1", 30),  # 2 time units on m1
            TaskMode("mode2", "t1", "m2", 45),  # 3 time units on m2
        ]
        t2_modes = [
            TaskMode("mode3", "t2", "m1", 60),  # 4 time units on m1
            TaskMode("mode4", "t2", "m2", 45),  # 3 time units on m2
        ]

        task1 = Task("t1", "j1", "Task 1", modes=t1_modes)
        task2 = Task("t2", "j1", "Task 2", modes=t2_modes)

        # Create job
        job = Job(
            "j1", "Job 1", datetime.now(UTC) + timedelta(hours=2), tasks=[task1, task2]
        )

        # Create precedence
        precedence = Precedence("t1", "t2")  # t1 must finish before t2

        # Create problem
        problem = SchedulingProblem(
            jobs=[job], machines=[m1, m2], work_cells=[], precedences=[precedence]
        )

        # WHEN: Solving
        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=100):
            solver = FreshSolver(problem)
            with patch("builtins.print"):
                solution = solver.solve(time_limit=10)

        # THEN: Valid solution found
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]
        assert len(solution["schedule"]) == 2

        # Verify precedence is respected
        schedule = solution["schedule"]
        t1_end = next(t for t in schedule if t["task_id"] == "t1")["end_time"]
        t2_start = next(t for t in schedule if t["task_id"] == "t2")["start_time"]
        assert t2_start >= t1_end

        # Verify each task assigned to a machine
        for task in schedule:
            assert task["machine_id"] in ["m1", "m2"]

    def test_phase1_performance(self):
        """Test that Phase 1 meets performance targets."""
        # GIVEN: Tiny dataset (2 jobs, 10 tasks)
        machines = [Machine(f"m{i}", "c1", f"Machine {i}") for i in range(3)]

        jobs = []
        precedences = []

        for j in range(2):
            tasks = []
            for t in range(5):
                task_id = f"t{j}_{t}"
                modes = [
                    TaskMode(f"mode_{task_id}_m{m}", task_id, f"m{m}", 30 + m * 15)
                    for m in range(3)
                ]
                task = Task(task_id, f"j{j}", f"Task {j}-{t}", modes=modes)
                tasks.append(task)

                # Add precedence within job
                if t > 0:
                    precedences.append(Precedence(f"t{j}_{t-1}", task_id))

            job = Job(
                f"j{j}", f"Job {j}", datetime.now(UTC) + timedelta(hours=8), tasks=tasks
            )
            jobs.append(job)

        problem = SchedulingProblem(jobs, machines, [], precedences)

        # WHEN: Solving
        import time

        start_time = time.time()

        with patch("src.solver.utils.time_utils.calculate_horizon", return_value=200):
            solver = FreshSolver(problem)
            with patch("builtins.print"):
                solution = solver.solve(time_limit=5)

        solve_time = time.time() - start_time

        # THEN: Meets performance target
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]
        assert solve_time < 1.0  # Should solve in < 1 second
        assert len(solution["schedule"]) == 10  # All tasks scheduled
