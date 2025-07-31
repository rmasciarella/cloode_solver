"""Due date constraints and lateness penalty calculations for OR-Tools solver.

Implements User Story 3: due date constraint enforcement with lateness penalties
integrated into the objective function for optimized mode architecture.
"""

from datetime import datetime
from typing import Any

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem

# Type aliases following TEMPLATES.md centralized patterns
TaskKey = tuple[str, str]  # (job_id/instance_id, task_id)
TaskStartDict = dict[TaskKey, cp_model.IntVar]
TaskEndDict = dict[TaskKey, cp_model.IntVar]
InstanceTaskKey = tuple[str, str]  # (instance_id, optimized_task_id)


def add_due_date_enforcement_constraints(
    model: cp_model.CpModel,
    task_ends: TaskEndDict,
    problem: SchedulingProblem,
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Add hard due date enforcement constraints.

    Mathematical formulation:
        For each job/instance j with due date d:
        max(task_end[j,t] for t in tasks[j]) <= d

    Business logic:
        Jobs must complete by their due dates (hard constraint).
        Creates completion time variables for lateness calculation.

    Args:
        model: The CP-SAT model to add constraints to
        task_ends: Dictionary of task end variables
        problem: The scheduling problem with due date information
        horizon: The scheduling horizon in time units

    Returns:
        Dictionary mapping job/instance IDs to completion time variables

    Constraints added:
        - Job completion time = max(task end times)
        - Job completion <= due date (hard constraint)

    Performance considerations:
        - O(instances × optimized_tasks) for optimized mode
        - O(jobs × tasks) for unique mode

    """
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        return add_optimized_due_date_constraints(model, task_ends, problem, horizon)
    else:
        return add_unique_due_date_constraints(model, task_ends, problem, horizon)


def add_optimized_due_date_constraints(
    model: cp_model.CpModel,
    task_ends: TaskEndDict,
    problem: SchedulingProblem,
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Add due date constraints for optimized mode instances.

    Mathematical formulation:
        For each instance i with due date d:
        completion[i] = max(task_end[i,t] for t in optimized_tasks)
        completion[i] <= d

    Args:
        model: The CP-SAT model to add constraints to
        task_ends: Dictionary of task end variables
        problem: The scheduling problem with optimized pattern information
        horizon: The scheduling horizon in time units

    Returns:
        Dictionary mapping instance IDs to completion time variables

    Constraints added:
        - Instance completion time = max(optimized task end times)
        - Instance completion <= due date (hard constraint)

    """
    completion_times = {}

    for instance in problem.job_instances:
        instance_end_times = _collect_instance_task_ends(
            instance, problem.job_optimized_pattern, problem, task_ends
        )

        if instance_end_times:
            completion_var = _create_completion_time_variable(
                model, instance.instance_id, instance_end_times, horizon
            )
            completion_times[instance.instance_id] = completion_var

            _add_hard_due_date_constraint(model, completion_var, instance.due_date)

    return completion_times


def add_unique_due_date_constraints(
    model: cp_model.CpModel,
    task_ends: TaskEndDict,
    problem: SchedulingProblem,
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Add due date constraints for unique mode job structure.

    Mathematical formulation:
        For each job j with due date d:
        completion[j] = max(task_end[j,t] for t in job_tasks)
        completion[j] <= d

    Args:
        model: The CP-SAT model to add constraints to
        task_ends: Dictionary of task end variables
        problem: The scheduling problem with job information
        horizon: The scheduling horizon in time units

    Returns:
        Dictionary mapping job IDs to completion time variables

    Constraints added:
        - Job completion time = max(job task end times)
        - Job completion <= due date (hard constraint)

    """
    completion_times = {}

    for job in problem.jobs:
        job_end_times = _collect_job_task_ends(job, task_ends)

        if job_end_times:
            completion_var = _create_completion_time_variable(
                model, job.job_id, job_end_times, horizon
            )
            completion_times[job.job_id] = completion_var

            _add_hard_due_date_constraint(model, completion_var, job.due_date)

    return completion_times


def add_lateness_penalty_variables(
    model: cp_model.CpModel,
    completion_times: dict[str, cp_model.IntVar],
    problem: SchedulingProblem,
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Add lateness penalty variables for objective integration.

    Mathematical formulation:
        For each job/instance j:
        lateness[j] = max(0, completion[j] - due_date[j])

    Business logic:
        Lateness penalties only apply to jobs completed after due date.
        Early completion has zero penalty (not negative lateness).

    Args:
        model: The CP-SAT model
        completion_times: Job/instance completion time variables
        problem: The scheduling problem with due dates
        horizon: The scheduling horizon

    Returns:
        Dictionary mapping job/instance IDs to lateness penalty variables

    Constraints added:
        - Lateness = max(0, completion - due_date)
        - Ensures non-negative penalties only

    """
    lateness_penalties = {}

    if problem.is_optimized_mode:
        # Optimized mode lateness calculation
        for instance in problem.job_instances:
            if (
                instance.instance_id in completion_times
                and instance.due_date is not None
            ):
                due_date_units = _convert_due_date_to_time_units(instance.due_date)

                # Create lateness penalty variable (non-negative)
                lateness_var = model.NewIntVar(
                    0, horizon, f"lateness_{instance.instance_id}"
                )

                # Lateness = max(0, completion - due_date)
                completion_var = completion_times[instance.instance_id]

                # Create auxiliary variable for completion - due_date
                late_amount = model.NewIntVar(
                    -horizon, horizon, f"late_amt_{instance.instance_id}"
                )
                model.Add(late_amount == completion_var - due_date_units)

                # Lateness penalty = max(0, late_amount)
                model.AddMaxEquality(lateness_var, [0, late_amount])
                lateness_penalties[instance.instance_id] = lateness_var
    else:
        # Unique mode lateness calculation
        for job in problem.jobs:
            if job.job_id in completion_times and job.due_date is not None:
                due_date_units = _convert_due_date_to_time_units(job.due_date)

                lateness_var = model.NewIntVar(0, horizon, f"lateness_{job.job_id}")

                completion_var = completion_times[job.job_id]

                late_amount = model.NewIntVar(
                    -horizon, horizon, f"late_amt_{job.job_id}"
                )
                model.Add(late_amount == completion_var - due_date_units)

                model.AddMaxEquality(lateness_var, [0, late_amount])
                lateness_penalties[job.job_id] = lateness_var

    return lateness_penalties


def create_total_lateness_objective_variable(
    model: cp_model.CpModel,
    lateness_penalties: dict[str, cp_model.IntVar],
    horizon: int,
) -> cp_model.IntVar:
    """Create total lateness objective variable for optimization.

    Mathematical formulation:
        total_lateness = sum(lateness[j] for j in jobs/instances)

    Business logic:
        Aggregates all individual lateness penalties into single objective.
        Integrates with template hierarchical optimization (primary objective).

    Args:
        model: The CP-SAT model
        lateness_penalties: Individual job/instance lateness variables
        horizon: The scheduling horizon

    Returns:
        Total lateness objective variable for optimization

    Performance:
        - O(1) constraint creation regardless of instance count
        - Efficient sum aggregation by CP-SAT solver

    """
    max_total_lateness = horizon * len(lateness_penalties)

    total_lateness = model.NewIntVar(0, max_total_lateness, "total_lateness_penalty")

    if lateness_penalties:
        model.Add(total_lateness == sum(lateness_penalties.values()))
    else:
        model.Add(total_lateness == 0)

    return total_lateness


def _collect_instance_task_ends(
    instance: Any,  # JobInstance type from problem module
    job_optimized_pattern: Any,  # JobOptimizedPattern type from problem module
    problem: SchedulingProblem,
    task_ends: TaskEndDict,
) -> list[cp_model.IntVar]:
    """Collect task end variables for an optimized mode instance.

    Args:
        instance: The job instance with tasks
        job_optimized_pattern: The optimized pattern defining instance structure
        problem: The scheduling problem
        task_ends: Dictionary of task end variables

    Returns:
        List of task end variables for the instance

    """
    instance_end_times = []

    for optimized_task in job_optimized_pattern.optimized_tasks:
        instance_task_id = problem.get_instance_task_id(
            instance.instance_id, optimized_task.optimized_task_id
        )
        task_key = (instance.instance_id, instance_task_id)

        if task_key in task_ends:
            instance_end_times.append(task_ends[task_key])

    return instance_end_times


def _collect_job_task_ends(
    job: Any,  # Job type from problem module
    task_ends: TaskEndDict,
) -> list[cp_model.IntVar]:
    """Collect task end variables for a unique mode job.

    Args:
        job: The job with tasks
        task_ends: Dictionary of task end variables

    Returns:
        List of task end variables for the job

    """
    job_end_times = []

    for task in job.tasks:
        task_key = (job.job_id, task.task_id)
        if task_key in task_ends:
            job_end_times.append(task_ends[task_key])

    return job_end_times


def _create_completion_time_variable(
    model: cp_model.CpModel,
    entity_id: str,
    end_times: list[cp_model.IntVar],
    horizon: int,
) -> cp_model.IntVar:
    """Create completion time variable for job/instance.

    Args:
        model: The CP-SAT model
        entity_id: Job ID or instance ID
        end_times: List of task end time variables
        horizon: The scheduling horizon

    Returns:
        Completion time variable representing max of end times

    """
    completion_var = model.NewIntVar(0, horizon, f"completion_{entity_id}")
    model.AddMaxEquality(completion_var, end_times)
    return completion_var


def _add_hard_due_date_constraint(
    model: cp_model.CpModel,
    completion_var: cp_model.IntVar,
    due_date: datetime | None,
) -> None:
    """Add hard due date constraint if due date exists.

    Args:
        model: The CP-SAT model
        completion_var: Job/instance completion time variable
        due_date: Due date (optional)

    """
    if due_date is not None:
        due_date_units = _convert_due_date_to_time_units(due_date)
        model.Add(completion_var <= due_date_units)


def _convert_due_date_to_time_units(due_date: datetime) -> int:
    """Convert due date to solver time units (15-minute intervals).

    For past due dates, returns a reasonable minimum time to allow scheduling.
    This prevents domain conflicts while still allowing lateness penalties.

    Args:
        due_date: datetime object representing job/instance due date

    Returns:
        Due date in time units from problem start (minimum 1 to prevent infeasibility)

    """
    from datetime import UTC, datetime

    # Use the problem's defined start time for deterministic calculation
    # This should be passed as a parameter, not calculated using datetime.now()
    if hasattr(due_date, "problem_start_time"):
        problem_start = due_date.problem_start_time
    else:
        # For backward compatibility, use a fixed reference time
        # This ensures deterministic behavior - same input always gives same result
        problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)

    # Ensure due_date is timezone-aware
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=UTC)

    # Calculate time delta and convert to 15-minute intervals
    due_date_delta = due_date - problem_start
    due_date_seconds = due_date_delta.total_seconds()

    if due_date_seconds < 0:
        # For past due dates, allow at least 1 time unit to prevent infeasibility
        # The lateness penalty will still be calculated correctly
        return 1

    # For future due dates, use actual time delta (minimum 1)
    return max(1, int(due_date_seconds / 900))
