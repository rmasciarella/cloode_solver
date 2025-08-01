"""Base interfaces and protocols for constraint functions."""

from typing import Any, Protocol

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


class ConstraintFunction(Protocol):
    """Protocol for constraint functions.

    All constraint functions should follow this signature pattern.
    """

    def __call__(
        self,
        model: cp_model.CpModel,
        variables: dict[str, Any],
        problem: SchedulingProblem,
    ) -> None:
        """Add constraints to the model.

        Args:
            model: The CP-SAT model to add constraints to
            variables: Dictionary of decision variables
            problem: The scheduling problem definition

        """
        ...
