"""Multi-objective optimization constraints for Phase 3.

Implements lexicographical optimization, weighted sum, and epsilon-constraint methods
for production scheduling with multiple competing objectives.
"""

import logging

from ortools.sat.python import cp_model

from src.solver.models.problem import (
    MultiObjectiveConfiguration,
    ObjectiveSolution,
    ObjectiveType,
    OptimizationStrategy,
    SchedulingProblem,
)

logger = logging.getLogger(__name__)


def create_multi_objective_variables(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    _task_starts: dict[tuple[str, str], cp_model.IntVar],
    _task_ends: dict[tuple[str, str], cp_model.IntVar],
    _task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Create decision variables for multi-objective optimization.

    Args:
        model: The CP-SAT model
        problem: The scheduling problem
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        horizon: Planning horizon

    Returns:
        Dictionary of objective variables

    Performance: O(objectives + tasks + machines) complexity

    """
    logger.info("Creating multi-objective variables...")

    objective_vars: dict[str, cp_model.IntVar] = {}

    if not problem.multi_objective_config:
        return objective_vars

    config = problem.multi_objective_config

    # Create variables for each objective type
    for obj_weight in config.objectives:
        obj_type = obj_weight.objective_type

        if obj_type == ObjectiveType.MINIMIZE_MAKESPAN:
            # Makespan: maximum end time across all tasks
            objective_vars["makespan"] = model.NewIntVar(0, horizon, "makespan")

        elif obj_type == ObjectiveType.MINIMIZE_TOTAL_LATENESS:
            # Total lateness: sum of positive differences between completion/due dates
            max_total_lateness = _calculate_max_total_lateness(problem, horizon)
            objective_vars["total_lateness"] = model.NewIntVar(
                0, max_total_lateness, "total_lateness"
            )

        elif obj_type == ObjectiveType.MINIMIZE_MAXIMUM_LATENESS:
            # Maximum lateness: worst lateness across all jobs
            max_lateness = _calculate_max_lateness(problem, horizon)
            objective_vars["maximum_lateness"] = model.NewIntVar(
                -horizon, max_lateness, "maximum_lateness"
            )

        elif obj_type == ObjectiveType.MINIMIZE_TOTAL_COST:
            # Total cost: sum of machine costs and operator costs
            max_total_cost = _calculate_max_total_cost(problem, horizon)
            objective_vars["total_cost"] = model.NewIntVar(
                0, max_total_cost, "total_cost"
            )

        elif obj_type == ObjectiveType.MINIMIZE_TOTAL_TARDINESS:
            # Total tardiness: sum of positive lateness values only
            max_total_tardiness = _calculate_max_total_lateness(problem, horizon)
            objective_vars["total_tardiness"] = model.NewIntVar(
                0, max_total_tardiness, "total_tardiness"
            )

        elif obj_type == ObjectiveType.MINIMIZE_WEIGHTED_COMPLETION_TIME:
            # Weighted completion time: sum of (weight × completion_time) for all jobs
            max_weighted_time = _calculate_max_weighted_completion_time(
                problem, horizon
            )
            objective_vars["weighted_completion_time"] = model.NewIntVar(
                0, max_weighted_time, "weighted_completion_time"
            )

        elif obj_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
            # Machine utilization: percentage of time machines are busy
            objective_vars["machine_utilization"] = model.NewIntVar(
                0,
                10000,
                "machine_utilization",  # Stored as percentage * 100 for integer
            )

        elif obj_type == ObjectiveType.MINIMIZE_SETUP_TIME:
            # Total setup time across all tasks
            max_setup_time = _calculate_max_setup_time(problem, horizon)
            objective_vars["total_setup_time"] = model.NewIntVar(
                0, max_setup_time, "total_setup_time"
            )

    logger.info(f"Created {len(objective_vars)} multi-objective variables")
    return objective_vars


def add_lexicographical_objective_constraints(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    objective_vars: dict[str, cp_model.IntVar],
    horizon: int,
) -> None:
    """Add lexicographical multi-objective constraints.

    Implements hierarchical optimization with objectives optimized in priority order.
    Higher priority objectives are optimized first, with lower priority objectives
    optimized subject to the constraint that higher priority objectives remain optimal.

    Mathematical formulation:
        For objectives O1, O2, O3 with priorities 1, 2, 3:
        1. Minimize O1
        2. Subject to O1 = O1*, minimize O2
        3. Subject to O1 = O1* and O2 = O2*, minimize O3

    Args:
        model: The CP-SAT model
        problem: The scheduling problem with multi-objective configuration
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        objective_vars: Multi-objective decision variables
        horizon: Planning horizon

    Constraints added:
        - Objective value definitions for each objective type
        - Primary objective minimization

    Performance: O(objectives × tasks) for constraint creation

    """
    if not problem.multi_objective_config:
        return

    logger.info("Adding lexicographical multi-objective constraints...")

    config = problem.multi_objective_config
    if config.strategy != OptimizationStrategy.LEXICOGRAPHICAL:
        return

    # Define each objective variable based on its type
    _add_objective_definitions(
        model, problem, task_starts, task_ends, task_assigned, objective_vars, horizon
    )

    # Set primary objective for first optimization phase
    # (Subsequent phases will be handled by the multi-phase solver)
    primary_obj = config.primary_objective
    obj_var_name = _get_objective_variable_name(primary_obj.objective_type)

    if obj_var_name in objective_vars:
        if primary_obj.objective_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
            # Maximization objective
            model.Maximize(objective_vars[obj_var_name])
        else:
            # Minimization objective
            model.Minimize(objective_vars[obj_var_name])

        logger.info(f"Set primary objective: {primary_obj.objective_type.value}")


def add_weighted_sum_objective_constraints(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    objective_vars: dict[str, cp_model.IntVar],
    horizon: int,
) -> None:
    """Add weighted sum multi-objective constraints.

    Combines multiple objectives into single weighted sum for simultaneous optimization.

    Mathematical formulation:
        minimize Σ(weight_i × objective_i) for all i
        where Σ(weight_i) = 1.0

    Args:
        model: The CP-SAT model
        problem: The scheduling problem with multi-objective configuration
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        objective_vars: Multi-objective decision variables
        horizon: Planning horizon

    Constraints added:
        - Objective value definitions for each objective type
        - Weighted sum combination objective

    Performance: O(objectives × tasks) for constraint creation

    """
    if not problem.multi_objective_config:
        return

    logger.info("Adding weighted sum multi-objective constraints...")

    config = problem.multi_objective_config
    if config.strategy != OptimizationStrategy.WEIGHTED_SUM:
        return

    # Define each objective variable based on its type
    _add_objective_definitions(
        model, problem, task_starts, task_ends, task_assigned, objective_vars, horizon
    )

    # Create weighted sum objective
    weighted_terms = []
    scaling_factor = 1000  # Scale weights to integers for CP-SAT

    for obj_weight in config.objectives:
        obj_var_name = _get_objective_variable_name(obj_weight.objective_type)

        if obj_var_name in objective_vars:
            scaled_weight = int(obj_weight.weight * scaling_factor)

            if obj_weight.objective_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
                # For maximization, negate the term
                weighted_terms.append(-scaled_weight * objective_vars[obj_var_name])
            else:
                # For minimization, use positive term
                weighted_terms.append(scaled_weight * objective_vars[obj_var_name])

    if weighted_terms:
        # Create combined objective variable
        max_weighted_sum = _calculate_max_weighted_sum(config, horizon)
        combined_objective = model.NewIntVar(
            -max_weighted_sum, max_weighted_sum, "weighted_sum_objective"
        )

        # Set combined objective equal to weighted sum
        model.Add(combined_objective == sum(weighted_terms))

        # Minimize the weighted sum
        model.Minimize(combined_objective)

        logger.info(f"Created weighted sum objective with {len(weighted_terms)} terms")


def add_epsilon_constraint_objective_constraints(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    objective_vars: dict[str, cp_model.IntVar],
    horizon: int,
) -> None:
    """Add epsilon-constraint multi-objective constraints.

    Optimizes one objective while constraining all others to be within epsilon bounds.

    Mathematical formulation:
        minimize objective_primary
        subject to: objective_i ≤ epsilon_i for all i ≠ primary

    Args:
        model: The CP-SAT model
        problem: The scheduling problem with multi-objective configuration
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        objective_vars: Multi-objective decision variables
        horizon: Planning horizon

    Constraints added:
        - Objective value definitions for each objective type
        - Epsilon bound constraints for constrained objectives
        - Primary objective minimization/maximization

    Performance: O(objectives × tasks) for constraint creation

    """
    if not problem.multi_objective_config:
        return

    logger.info("Adding epsilon-constraint multi-objective constraints...")

    config = problem.multi_objective_config
    if config.strategy != OptimizationStrategy.EPSILON_CONSTRAINT:
        return

    # Define each objective variable based on its type
    _add_objective_definitions(
        model, problem, task_starts, task_ends, task_assigned, objective_vars, horizon
    )

    # Add epsilon constraints for bounded objectives
    primary_obj = config.primary_objective
    constrained_objectives = 0

    for obj_weight in config.objectives:
        if obj_weight.epsilon_bound is not None:
            obj_var_name = _get_objective_variable_name(obj_weight.objective_type)

            if obj_var_name in objective_vars:
                epsilon_bound = int(obj_weight.epsilon_bound)

                if (
                    obj_weight.objective_type
                    == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION
                ):
                    # For maximization objectives, constrain from below
                    model.Add(objective_vars[obj_var_name] >= epsilon_bound)
                else:
                    # For minimization objectives, constrain from above
                    model.Add(objective_vars[obj_var_name] <= epsilon_bound)

                constrained_objectives += 1
                is_maximize = (
                    obj_weight.objective_type
                    == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION
                )
                op_symbol = "≥" if is_maximize else "≤"
                logger.info(
                    f"Added epsilon constraint: {obj_weight.objective_type.value} "
                    f"{op_symbol} {epsilon_bound}"
                )

    # Set primary objective
    primary_var_name = _get_objective_variable_name(primary_obj.objective_type)
    if primary_var_name in objective_vars:
        if primary_obj.objective_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
            model.Maximize(objective_vars[primary_var_name])
        else:
            model.Minimize(objective_vars[primary_var_name])

        logger.info(
            f"Set primary objective: {primary_obj.objective_type.value} "
            f"with {constrained_objectives} epsilon constraints"
        )


def calculate_objective_values(
    solver: cp_model.CpSolver,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    objective_vars: dict[str, cp_model.IntVar],
    horizon: int,
) -> ObjectiveSolution:
    """Calculate all objective values from a solved model.

    Args:
        solver: The solved CP-SAT solver
        problem: The scheduling problem
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_assigned: Task machine assignment variables
        objective_vars: Multi-objective decision variables
        horizon: Planning horizon

    Returns:
        ObjectiveSolution with calculated values for all objectives

    Performance: O(tasks + machines) for value extraction

    """
    logger.info("Calculating objective values...")

    solution = ObjectiveSolution()
    solution.solver_status = solver.StatusName()
    solution.solve_time = solver.WallTime()

    if solver.StatusName() not in ["OPTIMAL", "FEASIBLE"]:
        return solution

    # Extract objective variable values
    for var_name, var in objective_vars.items():
        value = solver.Value(var)

        if var_name == "makespan":
            solution.makespan = value
        elif var_name == "total_lateness":
            solution.total_lateness = value
        elif var_name == "maximum_lateness":
            solution.maximum_lateness = value
        elif var_name == "total_cost":
            solution.total_cost = (
                float(value) / 100.0
            )  # Convert back from scaled integer
        elif var_name == "total_tardiness":
            solution.total_tardiness = value
        elif var_name == "weighted_completion_time":
            solution.weighted_completion_time = float(value) / 100.0
        elif var_name == "machine_utilization":
            solution.machine_utilization = (
                float(value) / 100.0
            )  # Convert from percentage
        elif var_name == "total_setup_time":
            solution.total_setup_time = value

    # Calculate any missing objective values manually
    _calculate_missing_objectives(
        solver, problem, task_starts, task_ends, task_assigned, solution, horizon
    )

    # Set primary objective value
    if problem.multi_objective_config:
        primary_obj = problem.multi_objective_config.primary_objective
        solution.objective_value = solution.get_objective_value(
            primary_obj.objective_type
        )

    logger.info(f"Calculated objective values: {_format_objective_summary(solution)}")
    return solution


# Helper functions


def _add_objective_definitions(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    objective_vars: dict[str, cp_model.IntVar],
    horizon: int,
) -> None:
    """Add constraint definitions for each objective variable."""
    for var_name, var in objective_vars.items():
        if var_name == "makespan":
            _define_makespan_objective(model, task_ends, var)

        elif var_name == "total_lateness":
            _define_total_lateness_objective(model, problem, task_ends, var, horizon)

        elif var_name == "maximum_lateness":
            _define_maximum_lateness_objective(model, problem, task_ends, var, horizon)

        elif var_name == "total_cost":
            _define_total_cost_objective(
                model, problem, task_starts, task_ends, task_assigned, var
            )

        elif var_name == "total_tardiness":
            _define_total_tardiness_objective(model, problem, task_ends, var, horizon)

        elif var_name == "weighted_completion_time":
            _define_weighted_completion_time_objective(model, problem, task_ends, var)

        elif var_name == "machine_utilization":
            _define_machine_utilization_objective(
                model, problem, task_starts, task_ends, task_assigned, var, horizon
            )

        elif var_name == "total_setup_time":
            _define_total_setup_time_objective(model, problem, task_assigned, var)


def _define_makespan_objective(
    model: cp_model.CpModel,
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    makespan_var: cp_model.IntVar,
) -> None:
    """Define makespan as maximum task end time."""
    for end_var in task_ends.values():
        model.Add(makespan_var >= end_var)


def _define_total_lateness_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    total_lateness_var: cp_model.IntVar,
    horizon: int,
) -> None:
    """Define total lateness as sum of job lateness values."""
    lateness_terms = []

    # Calculate lateness for each job
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        # Template-based: calculate lateness for each job instance
        for instance in problem.job_instances:
            # Find last task end time for this instance
            instance_end_times = []
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in task_ends:
                    instance_end_times.append(task_ends[task_key])

            if instance_end_times:
                # Create job completion time variable
                job_completion = model.NewIntVar(
                    0, horizon, f"completion_{instance.instance_id}"
                )
                model.AddMaxEquality(job_completion, instance_end_times)

                # Calculate due date as time units from problem start (relative)
                # Assume problem starts at time 0, so due date is hours * 4 time units
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if instance.due_date is None:
                    continue  # Skip instances without due dates
                due_date_delta = instance.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                # Create lateness variable (can be negative for early completion)
                job_lateness = model.NewIntVar(
                    -horizon, horizon, f"lateness_{instance.instance_id}"
                )
                model.Add(job_lateness == job_completion - due_date_units)

                lateness_terms.append(job_lateness)
    else:
        # Legacy: calculate lateness for each job
        for job in problem.jobs:
            # Find last task end time for this job
            job_end_times = []
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)
                if task_key in task_ends:
                    job_end_times.append(task_ends[task_key])

            if job_end_times:
                # Create job completion time variable
                job_completion = model.NewIntVar(0, horizon, f"completion_{job.job_id}")
                model.AddMaxEquality(job_completion, job_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if job.due_date is None:
                    continue  # Skip jobs without due dates
                due_date_delta = job.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                # Create lateness variable
                job_lateness = model.NewIntVar(
                    -horizon, horizon, f"lateness_{job.job_id}"
                )
                model.Add(job_lateness == job_completion - due_date_units)

                lateness_terms.append(job_lateness)

    if lateness_terms:
        model.Add(total_lateness_var == sum(lateness_terms))


def _define_maximum_lateness_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    max_lateness_var: cp_model.IntVar,
    horizon: int,
) -> None:
    """Define maximum lateness as worst job lateness."""
    lateness_vars = []

    # Same logic as total lateness but take maximum instead of sum
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        for instance in problem.job_instances:
            instance_end_times = []
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in task_ends:
                    instance_end_times.append(task_ends[task_key])

            if instance_end_times:
                job_completion = model.NewIntVar(
                    0, horizon, f"completion_{instance.instance_id}"
                )
                model.AddMaxEquality(job_completion, instance_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if instance.due_date is None:
                    continue  # Skip instances without due dates
                due_date_delta = instance.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                job_lateness = model.NewIntVar(
                    -horizon, horizon, f"lateness_{instance.instance_id}"
                )
                model.Add(job_lateness == job_completion - due_date_units)
                lateness_vars.append(job_lateness)
    else:
        for job in problem.jobs:
            job_end_times = []
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)
                if task_key in task_ends:
                    job_end_times.append(task_ends[task_key])

            if job_end_times:
                job_completion = model.NewIntVar(0, horizon, f"completion_{job.job_id}")
                model.AddMaxEquality(job_completion, job_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if job.due_date is None:
                    continue  # Skip jobs without due dates
                due_date_delta = job.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                job_lateness = model.NewIntVar(
                    -horizon, horizon, f"lateness_{job.job_id}"
                )
                model.Add(job_lateness == job_completion - due_date_units)
                lateness_vars.append(job_lateness)

    if lateness_vars:
        model.AddMaxEquality(max_lateness_var, lateness_vars)


def _define_total_cost_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    total_cost_var: cp_model.IntVar,
) -> None:
    """Define total cost including machine and operator costs."""
    cost_terms = []

    # Machine costs based on usage time
    for machine in problem.machines:
        if machine.cost_per_hour > 0:
            machine_usage_time = model.NewIntVar(
                0, 1000000, f"usage_{machine.resource_id}"
            )

            # Sum usage time for this machine across all assigned tasks
            usage_terms = []
            for task_key, assign_var in task_assigned.items():
                job_id, task_id, machine_id = task_key
                if machine_id == machine.resource_id:
                    task_duration = (
                        task_ends[(job_id, task_id)] - task_starts[(job_id, task_id)]
                    )
                    # Only count duration if task is assigned to this machine
                    usage_contribution = model.NewIntVar(
                        0, 1000000, f"usage_contrib_{job_id}_{task_id}_{machine_id}"
                    )
                    model.Add(usage_contribution == task_duration).OnlyEnforceIf(
                        assign_var
                    )
                    model.Add(usage_contribution == 0).OnlyEnforceIf(assign_var.Not())
                    usage_terms.append(usage_contribution)

            if usage_terms:
                model.Add(machine_usage_time == sum(usage_terms))

                # Convert time units to hours and apply cost rate
                # Scale by 100 to maintain precision with integers
                cost_per_time_unit = int(
                    machine.cost_per_hour * 100 / 4
                )  # 4 time units per hour
                machine_cost = model.NewIntVar(
                    0, 10000000, f"cost_{machine.resource_id}"
                )
                model.Add(machine_cost == machine_usage_time * cost_per_time_unit)
                cost_terms.append(machine_cost)

    # Operator costs (if Phase 2 operators are available)
    # This would be implemented when operator assignment variables are available

    if cost_terms:
        model.Add(total_cost_var == sum(cost_terms))
    else:
        model.Add(total_cost_var == 0)


def _define_total_tardiness_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    total_tardiness_var: cp_model.IntVar,
    horizon: int,
) -> None:
    """Define total tardiness as sum of positive lateness values only."""
    tardiness_terms = []

    # Similar to total lateness but only include positive values
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        for instance in problem.job_instances:
            instance_end_times = []
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in task_ends:
                    instance_end_times.append(task_ends[task_key])

            if instance_end_times:
                job_completion = model.NewIntVar(
                    0, horizon, f"completion_{instance.instance_id}"
                )
                model.AddMaxEquality(job_completion, instance_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if instance.due_date is None:
                    continue  # Skip instances without due dates
                due_date_delta = instance.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                # Tardiness is max(0, completion_time - due_date)
                job_tardiness = model.NewIntVar(
                    0, horizon, f"tardiness_{instance.instance_id}"
                )
                model.Add(job_tardiness >= job_completion - due_date_units)
                model.Add(job_tardiness >= 0)
                tardiness_terms.append(job_tardiness)
    else:
        for job in problem.jobs:
            job_end_times = []
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)
                if task_key in task_ends:
                    job_end_times.append(task_ends[task_key])

            if job_end_times:
                job_completion = model.NewIntVar(0, horizon, f"completion_{job.job_id}")
                model.AddMaxEquality(job_completion, job_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if job.due_date is None:
                    continue  # Skip jobs without due dates
                due_date_delta = job.due_date - problem_start
                due_date_units = max(
                    0, int(due_date_delta.total_seconds() / 900)
                )  # 900 seconds = 15 minutes

                job_tardiness = model.NewIntVar(0, horizon, f"tardiness_{job.job_id}")
                model.Add(job_tardiness >= job_completion - due_date_units)
                model.Add(job_tardiness >= 0)
                tardiness_terms.append(job_tardiness)

    if tardiness_terms:
        model.Add(total_tardiness_var == sum(tardiness_terms))


def _define_weighted_completion_time_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    weighted_completion_var: cp_model.IntVar,
) -> None:
    """Define weighted completion time objective."""
    # For now, use equal weights for all jobs
    # In future, could add job priority weights to the data model
    weighted_terms = []

    if problem.is_optimized_mode and problem.job_optimized_pattern:
        for instance in problem.job_instances:
            instance_end_times = []
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in task_ends:
                    instance_end_times.append(task_ends[task_key])

            if instance_end_times:
                job_completion = model.NewIntVar(
                    0, 100000, f"completion_{instance.instance_id}"
                )
                model.AddMaxEquality(job_completion, instance_end_times)

                # Use weight of 1 for all jobs (could be configurable)
                weighted_terms.append(job_completion)
    else:
        for job in problem.jobs:
            job_end_times = []
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)
                if task_key in task_ends:
                    job_end_times.append(task_ends[task_key])

            if job_end_times:
                job_completion = model.NewIntVar(0, 100000, f"completion_{job.job_id}")
                model.AddMaxEquality(job_completion, job_end_times)
                weighted_terms.append(job_completion)

    if weighted_terms:
        # Scale by 100 to maintain precision
        scaled_completion = model.NewIntVar(0, 10000000, "scaled_weighted_completion")
        model.Add(scaled_completion == sum(weighted_terms) * 100)
        model.Add(weighted_completion_var == scaled_completion)


def _define_machine_utilization_objective(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    utilization_var: cp_model.IntVar,
    horizon: int,
) -> None:
    """Define machine utilization as percentage of time machines are busy."""
    total_machine_time = sum(machine.capacity for machine in problem.machines) * horizon
    total_busy_time_terms = []

    for machine in problem.machines:
        machine_busy_time = model.NewIntVar(
            0, horizon * machine.capacity, f"busy_{machine.resource_id}"
        )

        # Sum busy time for this machine across all assigned tasks
        busy_terms = []
        for task_key, assign_var in task_assigned.items():
            job_id, task_id, machine_id = task_key
            if machine_id == machine.resource_id:
                task_duration = (
                    task_ends[(job_id, task_id)] - task_starts[(job_id, task_id)]
                )
                # Only count duration if task is assigned to this machine
                busy_contribution = model.NewIntVar(
                    0, horizon, f"busy_contrib_{job_id}_{task_id}_{machine_id}"
                )
                model.Add(busy_contribution == task_duration).OnlyEnforceIf(assign_var)
                model.Add(busy_contribution == 0).OnlyEnforceIf(assign_var.Not())
                busy_terms.append(busy_contribution)

        if busy_terms:
            model.Add(machine_busy_time == sum(busy_terms))
            total_busy_time_terms.append(machine_busy_time)

    if total_busy_time_terms and total_machine_time > 0:
        total_busy_time = model.NewIntVar(0, total_machine_time, "total_busy_time")
        model.Add(total_busy_time == sum(total_busy_time_terms))

        # Calculate utilization as percentage * 100 (to use integers)
        # Use regular division since we're working with IntVar expressions
        model.Add(utilization_var * total_machine_time == total_busy_time * 10000)


def _define_total_setup_time_objective(
    model: cp_model.CpModel,
    _problem: SchedulingProblem,
    _task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    setup_time_var: cp_model.IntVar,
) -> None:
    """Define total setup time objective."""
    # This would be implemented when setup times are available in the problem
    # For now, set to 0
    model.Add(setup_time_var == 0)


def _calculate_missing_objectives(
    solver: cp_model.CpSolver,
    _problem: SchedulingProblem,
    _task_starts: dict[tuple[str, str], cp_model.IntVar],
    _task_ends: dict[tuple[str, str], cp_model.IntVar],
    _task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    solution: ObjectiveSolution,
    _horizon: int,
) -> None:
    """Calculate any objective values that weren't captured by variables."""
    # Calculate makespan if not already set
    if solution.makespan is None:
        max_end_time = 0
        for end_var in _task_ends.values():
            end_time = solver.Value(end_var)
            max_end_time = max(max_end_time, end_time)
        solution.makespan = max_end_time

    # Additional calculations could be added here for other objectives


def _get_objective_variable_name(objective_type: ObjectiveType) -> str:
    """Get the variable name for an objective type."""
    mapping = {
        ObjectiveType.MINIMIZE_MAKESPAN: "makespan",
        ObjectiveType.MINIMIZE_TOTAL_LATENESS: "total_lateness",
        ObjectiveType.MINIMIZE_MAXIMUM_LATENESS: "maximum_lateness",
        ObjectiveType.MINIMIZE_TOTAL_COST: "total_cost",
        ObjectiveType.MINIMIZE_TOTAL_TARDINESS: "total_tardiness",
        ObjectiveType.MINIMIZE_WEIGHTED_COMPLETION_TIME: "weighted_completion_time",
        ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION: "machine_utilization",
        ObjectiveType.MINIMIZE_SETUP_TIME: "total_setup_time",
    }
    return mapping.get(objective_type, "unknown")


def _calculate_max_total_lateness(problem: SchedulingProblem, horizon: int) -> int:
    """Calculate maximum possible total lateness."""
    # Pessimistic estimate: all jobs finish at horizon with earliest due dates
    return horizon * (len(problem.jobs) + len(problem.job_instances))


def _calculate_max_lateness(_problem: SchedulingProblem, horizon: int) -> int:
    """Calculate maximum possible lateness for any single job."""
    return horizon


def _calculate_max_total_cost(problem: SchedulingProblem, horizon: int) -> int:
    """Calculate maximum possible total cost."""
    max_cost = 0
    for machine in problem.machines:
        # Assume all machines run at full capacity for entire horizon
        machine_max_cost = int(
            machine.cost_per_hour * horizon * machine.capacity / 4 * 100
        )  # Scale by 100
        max_cost += machine_max_cost
    return max_cost


def _calculate_max_weighted_completion_time(
    problem: SchedulingProblem, horizon: int
) -> int:
    """Calculate maximum possible weighted completion time."""
    # Pessimistic estimate: all jobs complete at horizon
    job_count = len(problem.jobs) + len(problem.job_instances)
    return horizon * job_count * 100  # Scale by 100


def _calculate_max_setup_time(problem: SchedulingProblem, _horizon: int) -> int:
    """Calculate maximum possible setup time."""
    # For now, return a reasonable upper bound
    task_count = problem.total_task_count
    return task_count * 10  # Assume max 10 time units setup per task


def _calculate_max_weighted_sum(
    config: MultiObjectiveConfiguration, horizon: int
) -> int:
    """Calculate maximum possible weighted sum value."""
    # Conservative estimate based on horizon and number of objectives
    return horizon * len(config.objectives) * 1000


def _format_objective_summary(solution: ObjectiveSolution) -> str:
    """Format objective values for logging."""
    parts = []
    if solution.makespan is not None:
        parts.append(f"makespan={solution.makespan}")
    if solution.total_lateness is not None:
        parts.append(f"lateness={solution.total_lateness}")
    if solution.total_cost is not None:
        parts.append(f"cost={solution.total_cost:.2f}")
    return ", ".join(parts)
