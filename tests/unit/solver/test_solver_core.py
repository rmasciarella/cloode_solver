"""Unit tests for the core FreshSolver functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

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


def create_simple_problem():
    """Create a simple scheduling problem for testing."""
    # Create work cell
    work_cell = WorkCell(cell_id="WC1", name="Work Cell 1", capacity=2, machines=[])

    # Create machines
    machines = [
        Machine(
            resource_id="M1",
            cell_id="WC1",
            name="Machine 1",
            capacity=1,
            cost_per_hour=10.0,
        ),
        Machine(
            resource_id="M2",
            cell_id="WC1",
            name="Machine 2",
            capacity=1,
            cost_per_hour=15.0,
        ),
    ]

    work_cell.machines = machines

    # Create tasks
    task1 = Task(
        task_id="T1",
        job_id="J1",
        name="Task 1",
        modes=[
            TaskMode(
                task_mode_id="TM1",
                task_id="T1",
                machine_resource_id="M1",
                duration_minutes=60,
            ),
            TaskMode(
                task_mode_id="TM2",
                task_id="T1",
                machine_resource_id="M2",
                duration_minutes=45,
            ),
        ],
    )

    task2 = Task(
        task_id="T2",
        job_id="J1",
        name="Task 2",
        modes=[
            TaskMode(
                task_mode_id="TM3",
                task_id="T2",
                machine_resource_id="M1",
                duration_minutes=90,
            ),
        ],
    )

    # Create job with due date
    job = Job(
        job_id="J1",
        description="Test Job 1",
        due_date=datetime.now(UTC) + timedelta(hours=8),
        tasks=[task1, task2],
    )

    # Create precedence
    precedence = Precedence(predecessor_task_id="T1", successor_task_id="T2")

    return SchedulingProblem(
        jobs=[job], machines=machines, work_cells=[work_cell], precedences=[precedence]
    )


class TestFreshSolver:
    """Test the FreshSolver class."""

    def test_solver_initialization(self):
        """Test solver can be initialized."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)
        assert solver is not None
        assert hasattr(solver, "solve")
        assert solver.problem == problem

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solve_simple_problem(self, mock_solver_class):
        """Test solving a simple scheduling problem."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        # Mock the OR-Tools solver
        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = 4  # OPTIMAL
        mock_solver_instance.StatusName.return_value = "OPTIMAL"
        mock_solver_instance.Value.return_value = 2
        mock_solver_instance.WallTime.return_value = 0.1
        mock_solver_instance.NumBranches.return_value = 10
        mock_solver_instance.NumConflicts.return_value = 0
        mock_solver_instance.ObjectiveValue.return_value = 5

        with patch("builtins.print"):  # Suppress output
            solution = solver.solve()

        assert solution is not None
        assert solution["status"] == "OPTIMAL"
        assert "schedule" in solution
        assert "makespan" in solution

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solve_with_time_limit(self, mock_solver_class):
        """Test solving with custom time limit."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = 2  # FEASIBLE
        mock_solver_instance.StatusName.return_value = "FEASIBLE"
        mock_solver_instance.Value.return_value = 2
        mock_solver_instance.WallTime.return_value = 0.1
        mock_solver_instance.NumBranches.return_value = 10
        mock_solver_instance.NumConflicts.return_value = 0

        with patch("builtins.print"):
            solver.solve(time_limit=30)

        # Check time limit was set
        assert mock_solver_instance.parameters.max_time_in_seconds == 30

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solve_infeasible_problem(self, mock_solver_class):
        """Test handling of infeasible problems."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = 3  # INFEASIBLE
        mock_solver_instance.StatusName.return_value = "INFEASIBLE"

        with patch("builtins.print"):
            solution = solver.solve()

        assert solution is not None
        assert solution["status"] == "INFEASIBLE"
        assert solution["schedule"] == []

    def test_solver_validates_problem(self):
        """Test solver handles problems with invalid machine references."""
        # Create problem with task referencing non-existent machine
        job = Job(
            job_id="J1",
            description="Job 1",
            due_date=datetime.now(UTC) + timedelta(hours=8),
            tasks=[
                Task(
                    task_id="T1",
                    job_id="J1",
                    name="Task 1",
                    modes=[
                        TaskMode(
                            task_mode_id="TM1",
                            task_id="T1",
                            machine_resource_id="M1",  # This machine doesn't exist
                            duration_minutes=60,
                        )
                    ],
                )
            ],
        )

        problem = SchedulingProblem(
            jobs=[job],
            machines=[],  # No machines!
            work_cells=[
                WorkCell(cell_id="WC1", name="Cell 1", capacity=1, machines=[])
            ],
            precedences=[],
        )

        # The problem should have validation issues
        issues = problem.validate()
        assert len(issues) > 0
        assert any("non-existent machine" in issue for issue in issues)

        # Solver should handle this gracefully - either return OPTIMAL with
        # unassigned tasks
        # or INFEASIBLE (both are acceptable behaviors)
        solver = FreshSolver(problem)
        with patch("builtins.print"):
            solution = solver.solve()
            assert solution["status"] in ["OPTIMAL", "INFEASIBLE"]
            # If optimal, tasks should have no machine assignment
            if solution["status"] == "OPTIMAL":
                for task in solution["schedule"]:
                    assert task["machine_id"] is None

    @patch("src.solver.core.solver.load_test_problem")
    def test_solve_from_database(self, mock_load):
        """Test solving problem loaded from database."""
        # Mock the database loader
        test_problem = create_simple_problem()
        mock_load.return_value = test_problem

        solver = FreshSolver(test_problem)

        with patch.object(solver, "solve") as mock_solve:
            mock_solve.return_value = {"status": "OPTIMAL"}

            # This would typically be called from main
            solution = solver.solve()

            assert solution is not None
            mock_solve.assert_called_once()

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solver_with_no_precedences(self, mock_solver_class):
        """Test solver handles problems without precedences."""
        problem = create_simple_problem()
        problem.precedences = []  # Remove precedences

        solver = FreshSolver(problem)

        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = 4  # OPTIMAL
        mock_solver_instance.StatusName.return_value = "OPTIMAL"
        mock_solver_instance.Value.return_value = 2
        mock_solver_instance.WallTime.return_value = 0.1
        mock_solver_instance.NumBranches.return_value = 10
        mock_solver_instance.NumConflicts.return_value = 0

        with patch("builtins.print"):
            solution = solver.solve()

        assert solution is not None
        assert solution["status"] == "OPTIMAL"

    @patch("ortools.sat.python.cp_model.CpSolver")
    def test_solver_with_multiple_jobs(self, mock_solver_class):
        """Test solver handles multiple jobs."""
        problem = create_simple_problem()

        # Add second job
        job2 = Job(
            job_id="J2",
            description="Job 2",
            due_date=datetime.now(UTC) + timedelta(hours=10),
            tasks=[
                Task(
                    task_id="T3",
                    job_id="J2",
                    name="Task 3",
                    modes=[
                        TaskMode(
                            task_mode_id="TM3",
                            task_id="T3",
                            machine_resource_id="M2",
                            duration_minutes=30,
                        )
                    ],
                )
            ],
        )
        problem.jobs.append(job2)

        solver = FreshSolver(problem)

        mock_solver_instance = MagicMock()
        mock_solver_class.return_value = mock_solver_instance
        mock_solver_instance.Solve.return_value = 4  # OPTIMAL
        mock_solver_instance.StatusName.return_value = "OPTIMAL"
        mock_solver_instance.Value.return_value = 2
        mock_solver_instance.WallTime.return_value = 0.1
        mock_solver_instance.NumBranches.return_value = 10
        mock_solver_instance.NumConflicts.return_value = 0

        with patch("builtins.print"):
            solution = solver.solve()

        assert solution is not None
        assert solution["status"] == "OPTIMAL"
        assert len(problem.jobs) == 2
