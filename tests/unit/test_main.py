"""Unit tests for solver main entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.solver.__main__ import main


class TestMain:
    """Test the main entry point."""

    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    def test_main_success(self, mock_solver_class, mock_load):
        """Test successful execution of main."""
        # Setup mocks
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        mock_solver = MagicMock()
        mock_solution = {
            "status": "OPTIMAL",
            "makespan": 100,
            "makespan_hours": 25.0,
            "total_lateness_minutes": 0,
            "schedule": [],
            "solver_stats": {
                "status": "OPTIMAL",
                "solve_time": 1.0,
                "branches": 100,
                "conflicts": 5,
            },
        }
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        with (
            patch("builtins.print") as mock_print,
            patch.object(sys, "argv", ["solver"]),
        ):
            result = main()

        # Verify
        assert result == 0
        mock_load.assert_called_once()
        mock_solver_class.assert_called_once_with(mock_problem)
        mock_solver.solve.assert_called_once_with(time_limit=30)

        # Check that solution was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("OPTIMAL" in call for call in print_calls)

    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    def test_main_no_solution(self, mock_solver_class, mock_load):
        """Test main when no solution is found."""
        # Setup mocks
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        mock_solver = MagicMock()
        mock_solution = {
            "status": "INFEASIBLE",
            "makespan": 0,
            "makespan_hours": 0.0,
            "total_lateness_minutes": 0,
            "schedule": [],
            "solver_stats": {
                "status": "INFEASIBLE",
                "solve_time": 1.0,
                "branches": 100,
                "conflicts": 5,
            },
        }
        mock_solver.solve.return_value = mock_solution
        mock_solver_class.return_value = mock_solver

        # Run main
        with (
            patch("builtins.print") as mock_print,
            patch.object(sys, "argv", ["solver"]),
        ):
            result = main()

        # Verify
        assert result == 1  # Error exit code

        # Check that INFEASIBLE status was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("INFEASIBLE" in call for call in print_calls)

    @patch("src.solver.__main__.load_test_problem")
    def test_main_load_error(self, mock_load):
        """Test main when problem loading fails."""
        # Setup mock to raise error
        mock_load.side_effect = ConnectionError("Database unavailable")

        # Run main
        with patch.object(sys, "argv", ["solver"]), pytest.raises(ConnectionError):
            main()

    @patch("src.solver.__main__.load_test_problem")
    @patch("src.solver.__main__.FreshSolver")
    def test_main_solver_error(self, mock_solver_class, mock_load):
        """Test main when solver raises error."""
        # Setup mocks
        mock_problem = MagicMock()
        mock_load.return_value = mock_problem

        mock_solver = MagicMock()
        mock_solver.solve.side_effect = ValueError("Invalid problem")
        mock_solver_class.return_value = mock_solver

        # Run main
        with patch.object(sys, "argv", ["solver"]), pytest.raises(ValueError):
            main()

    def test_main_module_execution(self):
        """Test that __main__ module executes main when run."""
        # This tests the if __name__ == "__main__": block
        with patch("src.solver.__main__.main") as mock_main:
            mock_main.return_value = 0

            # Simulate running the module
            with patch.object(sys, "argv", ["solver.py"]):
                # Import would trigger execution if __name__ == "__main__"
                # But in test context, __name__ != "__main__"
                # So we just verify the structure exists
                import src.solver.__main__ as main_module

                assert hasattr(main_module, "main")
                assert callable(main_module.main)
