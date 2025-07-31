"""Phase 3 Multi-Objective Optimization Constraints.

This module provides constraints and solvers for multi-objective optimization
including lexicographical optimization, weighted sum, and Pareto-optimal solutions.
"""

from .multi_objective_constraints import (
    add_epsilon_constraint_objective_constraints,
    add_lexicographical_objective_constraints,
    add_weighted_sum_objective_constraints,
    calculate_objective_values,
    create_multi_objective_variables,
)
from .pareto_optimizer import (
    analyze_trade_offs,
    find_pareto_frontier,
    recommend_solution,
)

__all__ = [
    "add_lexicographical_objective_constraints",
    "add_weighted_sum_objective_constraints",
    "add_epsilon_constraint_objective_constraints",
    "calculate_objective_values",
    "create_multi_objective_variables",
    "find_pareto_frontier",
    "analyze_trade_offs",
    "recommend_solution",
]
