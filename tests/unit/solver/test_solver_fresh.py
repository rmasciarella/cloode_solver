"""Unit tests for FreshSolver core functionality."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from ortools.sat.python import cp_model

from src.solver.core.solver import FreshSolver, main
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
    """Create a simple test problem."""
    now = datetime.now(UTC)
    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Machine 1", capacity=1),
        Machine(resource_id="m2", cell_id="cell1", name="Machine 2", capacity=2),
    ]

    tasks = [
        Task(
            task_id="t1",
            job_id="j1",
            name="Task 1",
            modes=[
                TaskMode("mode1", "t1", "m1", 30),
                TaskMode("mode2", "t1", "m2", 45),
            ],
        ),
        Task(
            task_id="t2",
            job_id="j1",
            name="Task 2",
            modes=[TaskMode("mode3", "t2", "m1", 60)],
        ),
    ]

    job = Job(
        job_id="j1", description="Job 1", due_date=now + timedelta(hours=4), tasks=tasks
    )
    precedences = [Precedence("t1", "t2")]

    return SchedulingProblem(
        jobs=[job],
        machines=machines,
        work_cells=[WorkCell("cell1", "Cell 1", 2, machines)],
        precedences=precedences,
    )


class TestFreshSolver:
    """Test FreshSolver class."""

    def test_init(self):
        """Test solver initialization."""
        problem = create_simple_problem()
        setup_times = {("t1", "t2", "m1"): 2}

        solver = FreshSolver(problem, setup_times)

        assert solver.problem == problem
        assert solver.setup_times == setup_times
        assert isinstance(solver.model, cp_model.CpModel)
        assert solver.horizon > 0
        assert solver.solver is None

    def test_init_no_setup_times(self):
        """Test solver initialization without setup times."""
        problem = create_simple_problem()

        solver = FreshSolver(problem)

        assert solver.setup_times == {}

    @patch("src.solver.core.solver.calculate_horizon")
    def test_horizon_calculation(self, mock_calc_horizon):
        """Test that horizon is calculated during init."""
        mock_calc_horizon.return_value = 100
        problem = create_simple_problem()

        solver = FreshSolver(problem)

        assert solver.horizon == 100
        mock_calc_horizon.assert_called_once_with(problem)

    @patch("builtins.print")
    def test_create_variables(self, _mock_print):
        """Test decision variable creation."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        solver.create_variables()

        # Check task timing variables
        assert ("j1", "t1") in solver.task_starts
        assert ("j1", "t2") in solver.task_starts
        assert ("j1", "t1") in solver.task_ends
        assert ("j1", "t2") in solver.task_ends
        assert ("j1", "t1") in solver.task_durations
        assert ("j1", "t2") in solver.task_durations
        assert ("j1", "t1") in solver.task_intervals
        assert ("j1", "t2") in solver.task_intervals

        # Check assignment variables
        assert ("j1", "t1", "m1") in solver.task_assigned
        assert ("j1", "t1", "m2") in solver.task_assigned
        assert ("j1", "t2", "m1") in solver.task_assigned

        # Verify variable types
        # Check it's an IntVar by checking OR-Tools methods
        var = solver.task_starts[("j1", "t1")]
        assert hasattr(var, "Proto")  # IntVar has Proto() method
        assert hasattr(
            solver.task_intervals[("j1", "t1")], "StartExpr"
        )  # IntervalVar method

    @patch("builtins.print")
    @patch("src.solver.core.solver.add_task_duration_constraints")
    @patch("src.solver.core.solver.add_precedence_constraints")
    @patch("src.solver.core.solver.add_machine_assignment_constraints")
    @patch("src.solver.core.solver.add_machine_no_overlap_constraints")
    @patch("src.solver.core.solver.add_machine_capacity_constraints")
    @patch("src.solver.core.solver.add_redundant_precedence_constraints")
    def test_add_constraints_no_setup(
        self,
        mock_redundant,
        mock_capacity,
        mock_no_overlap,
        mock_assignment,
        mock_precedence,
        mock_duration,
        _mock_print,
    ):
        """Test constraint addition without setup times."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)
        solver.create_variables()

        solver.add_constraints()

        # Verify all constraint functions were called
        mock_duration.assert_called_once()
        mock_precedence.assert_called_once()
        mock_assignment.assert_called_once()
        mock_no_overlap.assert_called_once()
        mock_capacity.assert_called_once()
        mock_redundant.assert_called_once()

    @patch("builtins.print")
    @patch("src.solver.core.solver.add_setup_time_constraints")
    def test_add_constraints_with_setup(self, mock_setup, _mock_print):
        """Test that setup time constraints are added when setup times exist."""
        problem = create_simple_problem()
        setup_times = {("t1", "t2", "m1"): 2}
        solver = FreshSolver(problem, setup_times)
        solver.create_variables()

        solver.add_constraints()

        # Verify setup time constraints were called
        mock_setup.assert_called_once_with(
            solver.model,
            solver.task_starts,
            solver.task_ends,
            solver.task_assigned,
            setup_times,
            problem,
        )

    @patch("builtins.print")
    def test_set_objective(self, _mock_print):
        """Test objective function setup."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)
        solver.create_variables()

        # Count constraints before
        constraints_before = len(solver.model.Proto().constraints)

        solver.set_objective()

        # Should have added constraints for makespan
        constraints_after = len(solver.model.Proto().constraints)
        assert constraints_after > constraints_before

        # Should have objective
        assert solver.model.Proto().HasField("objective")

    def test_add_search_strategy(self):
        """Test search strategy addition."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)
        solver.create_variables()

        # Should not raise
        solver.add_search_strategy()

        # Verify search strategy was added
        assert len(solver.model.Proto().search_strategy) > 0

    @patch("builtins.print")
    @patch("src.solver.core.solver.extract_solution")
    def test_solve_optimal(self, mock_extract, _mock_print):
        """Test solving with optimal solution."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        # Mock solution
        mock_solution = {"status": "OPTIMAL", "makespan": 10, "schedule": []}
        mock_extract.return_value = mock_solution

        # Mock solver to return OPTIMAL
        with patch.object(cp_model.CpSolver, "Solve", return_value=cp_model.OPTIMAL):
            solution = solver.solve(time_limit=10)

        assert solution == mock_solution
        assert solver.solver is not None
        mock_extract.assert_called_once()

    @patch("builtins.print")
    @patch("src.solver.core.solver.extract_solution")
    def test_solve_infeasible(self, mock_extract, _mock_print):
        """Test solving with infeasible problem."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        # Mock solution
        mock_solution = {"status": "INFEASIBLE", "makespan": 0, "schedule": []}
        mock_extract.return_value = mock_solution

        # Mock solver to return INFEASIBLE
        with patch.object(cp_model.CpSolver, "Solve", return_value=cp_model.INFEASIBLE):
            solution = solver.solve(time_limit=10)

        assert solution["status"] == "INFEASIBLE"

    @patch("builtins.print")
    def test_solve_with_time_limit(self, _mock_print):
        """Test that time limit is properly set."""
        problem = create_simple_problem()
        solver = FreshSolver(problem)

        # Mock the solver methods needed by extract_solution
        with (
            patch.object(cp_model.CpSolver, "Solve", return_value=cp_model.OPTIMAL),
            patch.object(cp_model.CpSolver, "StatusName", return_value="OPTIMAL"),
            patch.object(cp_model.CpSolver, "Value", return_value=10),
            patch.object(cp_model.CpSolver, "WallTime", return_value=1.0),
            patch.object(cp_model.CpSolver, "ObjectiveValue", return_value=20),
            patch.object(cp_model.CpSolver, "NumBranches", return_value=100),
            patch.object(cp_model.CpSolver, "NumConflicts", return_value=5),
        ):
            solver.solve(time_limit=30)

        assert solver.solver.parameters.max_time_in_seconds == 30


class TestMain:
    """Test main function."""

    @patch("builtins.print")
    @patch("src.solver.core.solver.print_solution_summary")
    @patch("src.solver.core.solver.load_test_problem")
    @patch.object(FreshSolver, "solve")
    def test_main(self, mock_solve, mock_load, mock_print_summary, _mock_print):
        """Test main function execution."""
        # Mock problem loading
        test_problem = create_simple_problem()
        mock_load.return_value = test_problem

        # Mock solver solution
        mock_solution = {"status": "OPTIMAL", "makespan": 10, "schedule": []}
        mock_solve.return_value = mock_solution

        # Run main
        result = main()

        # Verify calls
        mock_load.assert_called_once()
        mock_solve.assert_called_once_with(time_limit=30)
        mock_print_summary.assert_called_once_with(mock_solution)
        assert result == mock_solution

    @patch("builtins.print")
    @patch("src.solver.core.solver.load_test_problem")
    def test_main_with_custom_setup_times(self, mock_load, _mock_print):
        """Test that main can handle custom setup times."""
        test_problem = create_simple_problem()
        mock_load.return_value = test_problem

        with patch.object(FreshSolver, "__init__", return_value=None) as mock_init:
            mock_solution = {
                "status": "OPTIMAL",
                "schedule": [],
                "makespan": 10,
                "makespan_hours": 2.5,
                "total_lateness_minutes": 0,
                "solver_stats": {
                    "status": "OPTIMAL",
                    "solve_time": 1.0,
                    "branches": 100,
                    "conflicts": 5,
                    "objective_value": 10,
                },
            }
            with patch.object(FreshSolver, "solve", return_value=mock_solution):
                main()

            # Verify solver was created with setup_times parameter
            mock_init.assert_called_once()
            _, kwargs = mock_init.call_args
            assert "setup_times" in kwargs
            assert isinstance(kwargs["setup_times"], dict)
