"""Unit tests for solver __main__ module."""

from unittest.mock import MagicMock, patch

import pytest

from src.solver.__main__ import main


class TestMain:
    """Test main entry point function."""

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver", "--time-limit", "60"])
    def test_main_with_time_limit(
        self, mock_solver_class, mock_load, mock_print_summary, _mock_print
    ):
        """Test main with custom time limit."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {"status": "OPTIMAL", "makespan": 10, "schedule": []}
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify
        mock_load.assert_called_once()
        mock_solver_class.assert_called_once_with(mock_problem)
        mock_solver.solve.assert_called_once_with(time_limit=60)
        mock_print_summary.assert_called_once_with(mock_solution)
        assert result == 0  # Success exit code

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver"])
    def test_main_default_time_limit(
        self, mock_solver_class, mock_load, _mock_print_summary, _mock_print
    ):
        """Test main with default time limit."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {"status": "FEASIBLE", "makespan": 20, "schedule": []}
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify default time limit of 30 seconds
        mock_solver.solve.assert_called_once_with(time_limit=30)
        assert result == 0  # Success exit code for FEASIBLE

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver", "--test"])
    def test_main_with_test_flag(
        self, mock_solver_class, mock_load, _mock_print_summary, _mock_print
    ):
        """Test main with --test flag."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {"status": "OPTIMAL", "makespan": 15, "schedule": []}
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify test problem was loaded
        mock_load.assert_called_once()
        assert result == 0

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver"])
    def test_main_infeasible_solution(
        self, mock_solver_class, mock_load, mock_print_summary, mock_print
    ):
        """Test main with infeasible solution returns error code."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {"status": "INFEASIBLE", "makespan": 0, "schedule": []}
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify error exit code for infeasible
        assert result == 1

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver"])
    def test_main_unknown_status(
        self, mock_solver_class, mock_load, mock_print_summary, mock_print
    ):
        """Test main with unknown solver status returns error code."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {"status": "UNKNOWN", "makespan": 0, "schedule": []}
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify error exit code for unknown status
        assert result == 1

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.load_test_problem")
    @patch("sys.argv", ["solver", "--help"])
    def test_main_help(self, mock_load, mock_print):
        """Test main with --help flag."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with 0 for --help
        assert exc_info.value.code == 0
        # Should not load problem when showing help
        mock_load.assert_not_called()

    @patch("src.solver.__main__.print")
    @patch("sys.argv", ["solver", "--invalid-option"])
    def test_main_invalid_args(self, mock_print):
        """Test main with invalid arguments."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        # argparse exits with 2 for invalid arguments
        assert exc_info.value.code == 2

    @patch("src.solver.__main__.print")
    @patch("src.solver.__main__.print_solution_summary")
    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    @patch("sys.argv", ["solver", "--time-limit", "0"])
    def test_main_with_zero_time_limit(
        self, mock_solver_class, mock_load, _mock_print_summary, _mock_print
    ):
        """Test main with zero time limit."""
        # Mock problem
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        # Mock solver
        mock_solver = MagicMock()
        mock_solution = {
            "status": "UNKNOWN",  # Likely status with 0 time limit
            "makespan": 0,
            "schedule": [],
        }
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        result = main()

        # Verify
        mock_solver.solve.assert_called_once_with(time_limit=0)
        assert result == 1  # Error code for non-optimal/feasible


# Test the if __name__ == "__main__" block
@patch("sys.exit")
@patch("src.solver.__main__.main")
def test_main_module_execution(mock_main, _mock_exit):
    """Test that main is called when module is executed."""
    mock_main.return_value = 0

    # Import and execute the module
    import src.solver.__main__

    # Since __name__ != "__main__" during import in tests,
    # we need to manually trigger it
    with (
        patch.object(src.solver.__main__, "__name__", "__main__"),
        open(src.solver.__main__.__file__) as f
    ):
        exec(
            compile(
                f.read(),
                src.solver.__main__.__file__,
                "exec",
            )
        )
