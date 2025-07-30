"""Unit tests for data loader base class."""

from typing import Any

import pytest

from src.data.loaders.base import DataLoader
from src.solver.models.problem import Job, Machine, SchedulingProblem, Task, TaskMode


class MockDataLoader(DataLoader):
    """Mock implementation of DataLoader for testing."""

    def __init__(self, mock_data: dict[str, Any] = None):
        self.mock_data = mock_data or {}
        self.load_problem_called = False
        self.save_solution_called = False
        self.saved_solutions = {}

    def load_problem(self, problem_id: str | None = None) -> SchedulingProblem:
        """Mock load_problem implementation."""
        self.load_problem_called = True

        if "error" in self.mock_data:
            raise ValueError(self.mock_data["error"])

        if "connection_error" in self.mock_data:
            raise ConnectionError(self.mock_data["connection_error"])

        # Return mock problem based on problem_id
        if problem_id == "empty":
            return SchedulingProblem(
                jobs=[], machines=[], work_cells=[], precedences=[]
            )

        # Default problem
        machines = [
            Machine(
                resource_id="M1",
                cell_id="cell1",
                name="Machine 1",
                capacity=1,
                cost_per_hour=10,
            )
        ]

        tasks = [
            Task(
                task_id="T1",
                job_id="J1",
                name="Task 1",
                modes=[
                    TaskMode(
                        task_mode_id="tm_auto",
                        task_id="auto",
                        machine_resource_id="M1",
                        duration_minutes=60,
                    )
                ],
            )
        ]

        from datetime import UTC, datetime, timedelta

        jobs = [
            Job(
                job_id="J1",
                description="Job 1",
                tasks=tasks,
                due_date=datetime.now(UTC) + timedelta(hours=24),
            )
        ]

        return SchedulingProblem(
            jobs=jobs, machines=machines, work_cells=[], precedences=[]
        )

    def save_solution(self, problem_id: str, solution: dict) -> None:
        """Mock save_solution implementation."""
        self.save_solution_called = True

        if "save_error" in self.mock_data:
            raise ValueError(self.mock_data["save_error"])

        if "save_connection_error" in self.mock_data:
            raise ConnectionError(self.mock_data["save_connection_error"])

        self.saved_solutions[problem_id] = solution


class TestDataLoader:
    """Test DataLoader abstract base class."""

    def test_loader_instantiation(self):
        """Test that loader can be instantiated through mock."""
        loader = MockDataLoader()
        assert loader is not None
        assert hasattr(loader, "load_problem")
        assert hasattr(loader, "save_solution")

    def test_load_problem_method(self):
        """Test load_problem method."""
        loader = MockDataLoader()

        # Load without problem_id
        problem = loader.load_problem()
        assert loader.load_problem_called
        assert isinstance(problem, SchedulingProblem)
        assert len(problem.jobs) == 1
        assert len(problem.machines) == 1

        # Load with problem_id
        problem = loader.load_problem("test_problem")
        assert isinstance(problem, SchedulingProblem)

    def test_load_problem_empty(self):
        """Test loading empty problem."""
        loader = MockDataLoader()
        problem = loader.load_problem("empty")

        assert isinstance(problem, SchedulingProblem)
        assert len(problem.jobs) == 0
        assert len(problem.machines) == 0

    def test_save_solution_method(self):
        """Test save_solution method."""
        loader = MockDataLoader()

        solution = {"schedule": {"J1": {"T1": {"start": 0, "end": 4}}}, "makespan": 4}

        loader.save_solution("problem1", solution)

        assert loader.save_solution_called
        assert "problem1" in loader.saved_solutions
        assert loader.saved_solutions["problem1"] == solution

    def test_load_problem_error_handling(self):
        """Test error handling in load_problem."""
        # Test ValueError
        loader = MockDataLoader(mock_data={"error": "Problem not found"})
        with pytest.raises(ValueError, match="Problem not found"):
            loader.load_problem("missing")

        # Test ConnectionError
        loader = MockDataLoader(mock_data={"connection_error": "Database unavailable"})
        with pytest.raises(ConnectionError, match="Database unavailable"):
            loader.load_problem()

    def test_save_solution_error_handling(self):
        """Test error handling in save_solution."""
        # Test ValueError
        loader = MockDataLoader(mock_data={"save_error": "Invalid problem ID"})
        with pytest.raises(ValueError, match="Invalid problem ID"):
            loader.save_solution("bad_id", {})

        # Test ConnectionError
        loader = MockDataLoader(mock_data={"save_connection_error": "Network error"})
        with pytest.raises(ConnectionError, match="Network error"):
            loader.save_solution("problem1", {})

    def test_loader_interface_contract(self):
        """Test that DataLoader enforces interface contract."""
        loader = MockDataLoader()

        # load_problem should accept optional problem_id
        problem1 = loader.load_problem()
        problem2 = loader.load_problem("specific_id")

        assert isinstance(problem1, SchedulingProblem)
        assert isinstance(problem2, SchedulingProblem)

        # save_solution should require problem_id and solution
        loader.save_solution("id", {"solution": "data"})

        # Should have saved
        assert loader.saved_solutions["id"]["solution"] == "data"

    def test_abstract_base_class(self):
        """Test that DataLoader is abstract and can't be instantiated directly."""
        # This would fail if DataLoader wasn't abstract
        with pytest.raises(TypeError):
            DataLoader()  # Can't instantiate abstract class
