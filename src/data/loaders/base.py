"""Base interface for data loaders."""

from abc import ABC, abstractmethod

from src.solver.models.problem import SchedulingProblem


class DataLoader(ABC):
    """Abstract base class for data loaders.

    All data loaders should implement this interface to ensure
    consistency across different data sources.
    """

    @abstractmethod
    def load_problem(self, problem_id: str | None = None) -> SchedulingProblem:
        """Load a scheduling problem from the data source.

        Args:
            problem_id: Optional identifier for a specific problem.
                       If None, loads a default or test problem.

        Returns:
            A fully populated SchedulingProblem instance

        Raises:
            ValueError: If problem_id is not found
            ConnectionError: If data source is unavailable

        """
        pass

    @abstractmethod
    def save_solution(self, problem_id: str, solution: dict) -> None:
        """Save a solution back to the data source.

        Args:
            problem_id: The problem identifier
            solution: Solution dictionary from the solver

        Raises:
            ValueError: If problem_id is not found
            ConnectionError: If data source is unavailable

        """
        pass
