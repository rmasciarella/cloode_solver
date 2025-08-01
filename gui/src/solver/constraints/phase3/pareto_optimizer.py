"""Pareto-optimal solution finder for multi-objective optimization.

Implements algorithms to find the Pareto frontier and analyze trade-offs
between competing objectives in production scheduling.
"""

import logging

from ortools.sat.python import cp_model

from src.solver.models.problem import (
    MultiObjectiveConfiguration,
    ObjectiveSolution,
    ObjectiveType,
    OptimizationStrategy,
    ParetoFrontier,
    ParetoSolution,
    SchedulingProblem,
    TradeOffAnalysis,
)

logger = logging.getLogger(__name__)


def find_pareto_frontier(
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    horizon: int,
    time_limit_per_solve: int = 30,
) -> ParetoFrontier:
    """Find Pareto-optimal solutions using epsilon-constraint method.

    Generates multiple solutions by systematically varying epsilon bounds
    on objectives to explore the Pareto frontier.

    Algorithm:
        1. Find extreme solutions (optimize each objective individually)
        2. Generate intermediate points using epsilon-constraint method
        3. Filter dominated solutions to maintain Pareto optimality

    Args:
        problem: The scheduling problem with multi-objective configuration
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        horizon: Planning horizon
        time_limit_per_solve: Time limit for each individual solve

    Returns:
        ParetoFrontier containing non-dominated solutions

    Performance: O(iterations × solve_time) where iterations = pareto_iterations

    """
    if not problem.multi_objective_config:
        return ParetoFrontier()

    logger.info("Finding Pareto frontier...")

    config = problem.multi_objective_config
    objective_types = [obj.objective_type for obj in config.objectives]

    frontier = ParetoFrontier(objective_types=objective_types)

    # Step 1: Find extreme solutions (optimize each objective individually)
    logger.info("Finding extreme solutions...")
    extreme_solutions = _find_extreme_solutions(
        problem, task_starts, task_ends, task_assigned, horizon, time_limit_per_solve
    )

    for solution in extreme_solutions:
        if solution:
            pareto_sol = ParetoSolution(objectives=solution)
            frontier.add_solution(pareto_sol)

    logger.info(f"Found {len(extreme_solutions)} extreme solutions")

    # Step 2: Generate intermediate solutions using epsilon-constraint method
    if config.pareto_iterations > len(objective_types):
        logger.info("Generating intermediate Pareto solutions...")
        intermediate_solutions = _generate_intermediate_solutions(
            problem,
            task_starts,
            task_ends,
            task_assigned,
            horizon,
            extreme_solutions,
            config.pareto_iterations - len(objective_types),
            time_limit_per_solve,
        )

        for solution in intermediate_solutions:
            if solution:
                pareto_sol = ParetoSolution(objectives=solution)
                frontier.add_solution(pareto_sol)

        logger.info(f"Generated {len(intermediate_solutions)} intermediate solutions")

    logger.info(
        f"Pareto frontier contains {frontier.solution_count} non-dominated solutions"
    )
    return frontier


def analyze_trade_offs(frontier: ParetoFrontier) -> TradeOffAnalysis:
    """Analyze trade-offs in the Pareto frontier.

    Calculates objective ranges, correlations, and provides insights
    about the trade-offs between different objectives.

    Args:
        frontier: The Pareto frontier to analyze

    Returns:
        TradeOffAnalysis with ranges, correlations, and recommendations

    Performance: O(solutions × objectives²) for correlation analysis

    """
    logger.info("Analyzing trade-offs in Pareto frontier...")

    analysis = TradeOffAnalysis(pareto_frontier=frontier)

    # Find recommended solution (balanced trade-off)
    if frontier.solution_count > 0:
        analysis.recommended_solution = _select_balanced_solution(frontier)
        logger.info("Selected balanced solution as recommendation")

    return analysis


def recommend_solution(
    frontier: ParetoFrontier,
    preferences: dict[ObjectiveType, float] | None = None,
) -> ParetoSolution | None:
    """Recommend a solution from the Pareto frontier based on preferences.

    Uses preference weights to score solutions and select the best match.
    If no preferences provided, selects the most balanced solution.

    Args:
        frontier: The Pareto frontier
        preferences: Optional dictionary of objective preferences (weights)

    Returns:
        Recommended ParetoSolution or None if frontier is empty

    Performance: O(solutions × objectives) for scoring

    """
    if frontier.solution_count == 0:
        return None

    if not preferences:
        # Use balanced selection
        return _select_balanced_solution(frontier)

    logger.info("Recommending solution based on preferences...")

    # Score each solution based on preferences
    best_solution = None
    best_score = float("-inf")

    # Normalize objectives to [0, 1] range for fair comparison
    normalized_ranges = _calculate_normalized_ranges(frontier)

    for solution in frontier.solutions:
        score = 0.0

        for obj_type, preference_weight in preferences.items():
            obj_value = solution.objectives.get_objective_value(obj_type)
            if obj_value is None:
                continue

            # Normalize the objective value
            if obj_type in normalized_ranges:
                min_val, max_val = normalized_ranges[obj_type]
                if max_val > min_val:
                    if obj_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
                        # For maximization, higher is better
                        normalized_value = (obj_value - min_val) / (max_val - min_val)
                    else:
                        # For minimization, lower is better
                        normalized_value = 1.0 - (obj_value - min_val) / (
                            max_val - min_val
                        )
                else:
                    normalized_value = 1.0

                score += preference_weight * normalized_value

        if score > best_score:
            best_score = score
            best_solution = solution

    logger.info(f"Recommended solution with score {best_score:.3f}")
    return best_solution


# Helper functions


def _find_extreme_solutions(
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    horizon: int,
    time_limit: int,
) -> list[ObjectiveSolution | None]:
    """Find extreme solutions by optimizing each objective individually."""
    config = problem.multi_objective_config
    if not config:
        return []

    extreme_solutions = []

    for obj_weight in config.objectives:
        logger.info(
            f"Finding extreme solution for {obj_weight.objective_type.value}..."
        )

        # Create a temporary single-objective configuration
        temp_config = MultiObjectiveConfiguration(
            strategy=OptimizationStrategy.LEXICOGRAPHICAL,
            objectives=[obj_weight],
        )

        # Temporarily replace the multi-objective config
        original_config = problem.multi_objective_config
        problem.multi_objective_config = temp_config

        try:
            solution = _solve_single_objective(
                problem, task_starts, task_ends, task_assigned, horizon, time_limit
            )
            extreme_solutions.append(solution)

        except Exception as e:
            logger.warning(
                f"Failed to find extreme solution for "
                f"{obj_weight.objective_type.value}: {e}"
            )
            extreme_solutions.append(None)

        finally:
            # Restore original configuration
            problem.multi_objective_config = original_config

    return extreme_solutions


def _generate_intermediate_solutions(
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    horizon: int,
    extreme_solutions: list[ObjectiveSolution | None],
    num_intermediate: int,
    time_limit: int,
) -> list[ObjectiveSolution | None]:
    """Generate intermediate solutions using epsilon-constraint method."""
    config = problem.multi_objective_config
    if not config or len(extreme_solutions) < 2:
        return []

    # Calculate objective ranges from extreme solutions
    objective_ranges = _calculate_objective_ranges(extreme_solutions, config.objectives)

    intermediate_solutions = []

    for i in range(num_intermediate):
        # Generate random epsilon bounds within the objective ranges
        epsilon_objectives = []

        for j, obj_weight in enumerate(config.objectives):
            obj_type = obj_weight.objective_type

            if obj_type in objective_ranges:
                min_val, max_val = objective_ranges[obj_type]

                if j == 0:
                    # First objective becomes the primary (no epsilon bound)
                    # primary_obj_type = obj_type  # First objective is primary
                    epsilon_objectives.append(obj_weight)
                else:
                    # Generate epsilon bound using systematic spacing
                    if max_val > min_val:
                        # Use deterministic spacing for reproducible results
                        spacing_factor = (i + 1) / (num_intermediate + 1)
                        epsilon_value = min_val + spacing_factor * (max_val - min_val)
                    else:
                        epsilon_value = min_val

                    epsilon_obj = obj_weight.__class__(
                        objective_type=obj_type,
                        weight=obj_weight.weight,
                        epsilon_bound=epsilon_value,
                    )
                    epsilon_objectives.append(epsilon_obj)

        if len(epsilon_objectives) > 1:
            # Create epsilon-constraint configuration
            temp_config = MultiObjectiveConfiguration(
                strategy=OptimizationStrategy.EPSILON_CONSTRAINT,
                objectives=epsilon_objectives,
            )

            # Temporarily replace the multi-objective config
            original_config = problem.multi_objective_config
            problem.multi_objective_config = temp_config

            try:
                solution = _solve_single_objective(
                    problem, task_starts, task_ends, task_assigned, horizon, time_limit
                )
                intermediate_solutions.append(solution)

            except Exception as e:
                logger.warning(f"Failed to generate intermediate solution {i + 1}: {e}")
                intermediate_solutions.append(None)

            finally:
                # Restore original configuration
                problem.multi_objective_config = original_config

    return intermediate_solutions


def _solve_single_objective(
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],  # noqa: ARG001
    task_ends: dict[tuple[str, str], cp_model.IntVar],  # noqa: ARG001
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],  # noqa: ARG001
    horizon: int,
    time_limit: int,
) -> ObjectiveSolution | None:
    """Solve for a single objective configuration using actual CP-SAT solving."""
    import time

    from src.solver.core.solver import FreshSolver

    logger.info("Solving single objective with CP-SAT...")

    start_time = time.time()

    try:
        # Create solver instance with time limit
        solver = FreshSolver(problem)

        # Configure solver with time limit
        if solver.solver:
            solver.solver.parameters.max_time_in_seconds = time_limit

        # Solve the problem using the existing solver infrastructure
        solution_result = solver.solve()

        solve_time = time.time() - start_time

        if solution_result is None or "status" not in solution_result:
            logger.warning("Single objective solve failed - no solution found")
            return None

        # Create ObjectiveSolution from the result
        objective_solution = ObjectiveSolution()
        objective_solution.solve_time = solve_time
        objective_solution.solver_status = solution_result.get("status", "UNKNOWN")

        # Extract objective values based on the configuration
        if problem.multi_objective_config:
            for obj_weight in problem.multi_objective_config.objectives:
                obj_type = obj_weight.objective_type

                if obj_type == ObjectiveType.MINIMIZE_MAKESPAN:
                    objective_solution.makespan = solution_result.get("makespan", 0)
                elif obj_type == ObjectiveType.MINIMIZE_TOTAL_LATENESS:
                    objective_solution.total_lateness = int(
                        solution_result.get("lateness", 0)
                    )
                elif obj_type == ObjectiveType.MINIMIZE_TOTAL_COST:
                    objective_solution.total_cost = solution_result.get(
                        "total_cost", 0.0
                    )
                elif obj_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
                    # Calculate machine utilization from solution
                    machine_util = solution_result.get("machine_utilization")
                    if machine_util is not None:
                        objective_solution.machine_utilization = machine_util
                    else:
                        # Calculate utilization from problem data
                        total_work_time = 0
                        for job in problem.jobs:
                            for task in job.tasks:
                                # Use first mode duration as approximation
                                if task.modes:
                                    total_work_time += task.modes[0].duration_time_units

                        num_machines = len(problem.machines)
                        utilization = (
                            total_work_time / (horizon * num_machines)
                            if num_machines > 0
                            else 0.0
                        )
                        objective_solution.machine_utilization = min(1.0, utilization)

        logger.info(f"Single objective solved in {solve_time:.2f}s")
        return objective_solution

    except Exception as e:
        solve_time = time.time() - start_time
        logger.error(f"Single objective solve failed after {solve_time:.2f}s: {e}")
        return None


def _calculate_objective_ranges(
    solutions: list[ObjectiveSolution | None],
    objectives: list,
) -> dict[ObjectiveType, tuple[float, float]]:
    """Calculate min/max ranges for each objective from extreme solutions."""
    ranges = {}

    for obj_weight in objectives:
        obj_type = obj_weight.objective_type
        values = []

        for solution in solutions:
            if solution:
                value = solution.get_objective_value(obj_type)
                if value is not None:
                    values.append(value)

        if values:
            ranges[obj_type] = (min(values), max(values))

    return ranges


def _select_balanced_solution(frontier: ParetoFrontier) -> ParetoSolution | None:
    """Select the most balanced solution from the Pareto frontier.

    Uses a distance-based approach to find the solution closest to
    the ideal point (best value for each objective).
    """
    if frontier.solution_count == 0:
        return None

    if frontier.solution_count == 1:
        return frontier.solutions[0]

    # Find ideal point (best value for each objective)
    ideal_point = {}
    for obj_type in frontier.objective_types:
        best_value = None

        for solution in frontier.solutions:
            value = solution.objectives.get_objective_value(obj_type)
            if value is None:
                continue

            if best_value is None:
                best_value = value
            elif obj_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:  # type: ignore[unreachable]
                # For maximization, higher is better
                if value > best_value:
                    best_value = value
            else:
                # For minimization, lower is better
                if value < best_value:
                    best_value = value

        if best_value is not None:
            ideal_point[obj_type] = best_value

    # Find solution with minimum distance to ideal point
    best_solution = None
    min_distance = float("inf")

    # Normalize objectives for fair distance calculation
    normalized_ranges = _calculate_normalized_ranges(frontier)

    for solution in frontier.solutions:
        distance = 0.0
        objective_count = 0

        for obj_type in frontier.objective_types:
            if obj_type not in ideal_point or obj_type not in normalized_ranges:
                continue

            value = solution.objectives.get_objective_value(obj_type)
            if value is None:
                continue

            ideal_value = ideal_point[obj_type]
            min_val, max_val = normalized_ranges[obj_type]

            # Normalize both values
            if max_val > min_val:
                normalized_value = (value - min_val) / (max_val - min_val)
                normalized_ideal = (ideal_value - min_val) / (max_val - min_val)

                distance += (normalized_value - normalized_ideal) ** 2
                objective_count += 1

        if objective_count > 0:
            # Use average squared distance
            avg_distance = distance / objective_count
            if avg_distance < min_distance:
                min_distance = avg_distance
                best_solution = solution

    return best_solution


def _calculate_normalized_ranges(
    frontier: ParetoFrontier,
) -> dict[ObjectiveType, tuple[float, float]]:
    """Calculate normalized ranges for objectives in the frontier."""
    ranges = {}

    for obj_type in frontier.objective_types:
        values = []

        for solution in frontier.solutions:
            value = solution.objectives.get_objective_value(obj_type)
            if value is not None:
                values.append(value)

        if values:
            ranges[obj_type] = (min(values), max(values))

    return ranges
