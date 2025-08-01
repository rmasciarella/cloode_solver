"""Constraints for unattended task scheduling.

Handles dual resource modeling: labor setup during business hours + 24/7 execution.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_business_hours_setup_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add business hours constraints for unattended task setup.

    Mathematical formulation:
        For unattended tasks with setup phase:
        setup_start >= business_hours_start
        setup_end <= business_hours_end
        Where business hours: Mon-Fri 7am-4pm (28-68 time units daily)

    Business logic:
        Unattended tasks require operator setup during business hours only.
        Machine execution can continue 24/7 after setup completion.

    Constraints added:
        - Setup tasks must start/end within business hours windows
        - Business hours: Monday-Friday 7am-4pm (time units 28-68 per day)
        - Weekend setup is prohibited (Saturday-Sunday)

    Performance: O(n) where n = number of unattended tasks with setup
    """
    if problem.is_optimized_mode:
        _add_optimized_business_hours_constraints(
            model, task_starts, task_ends, problem
        )
    else:
        _add_unique_business_hours_constraints(model, task_starts, task_ends, problem)


def _add_optimized_business_hours_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add business hours constraints for optimized mode problems."""
    if not problem.job_optimized_pattern:
        return

    # Business hours: 7am-4pm = time units 28-68 (7*4 to 16*4) per day
    # Daily cycle: 96 time units (24 hours * 4 units/hour)
    business_start_offset = 28  # 7am
    business_end_offset = 68  # 4pm
    daily_cycle = 96  # 24 hours

    for instance in problem.job_instances:
        for optimized_task in problem.job_optimized_pattern.optimized_tasks:
            # Only apply to setup tasks for unattended processes
            if not (optimized_task.is_setup and optimized_task.is_unattended):
                continue

            instance_task_id = problem.get_instance_task_id(
                instance.instance_id, optimized_task.optimized_task_id
            )
            task_key = (instance.instance_id, instance_task_id)

            if task_key not in task_starts:
                continue

            start_var = task_starts[task_key]
            end_var = task_ends[task_key]

            # Create business day choice variables - exactly one must be true
            business_day_choices = []

            for day in range(5):  # Only weekdays (Monday-Friday)
                day_start = day * daily_cycle
                business_day_start = day_start + business_start_offset
                business_day_end = day_start + business_end_offset

                # Boolean variable for whether task is scheduled on this business day
                scheduled_this_day = model.NewBoolVar(
                    f"business_day_{day}_{instance.instance_id}_{optimized_task.optimized_task_id}"
                )
                business_day_choices.append(scheduled_this_day)

                # If scheduled on this day, must be within business hours
                model.Add(start_var >= business_day_start).OnlyEnforceIf(
                    scheduled_this_day
                )
                model.Add(start_var < day_start + daily_cycle).OnlyEnforceIf(
                    scheduled_this_day
                )
                model.Add(end_var <= business_day_end).OnlyEnforceIf(scheduled_this_day)

            # Must be scheduled on exactly one business day
            model.AddExactlyOne(business_day_choices)


def _add_unique_business_hours_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add business hours constraints for unique mode job-based problems."""
    # Business hours: 7am-4pm = time units 28-68 per day
    business_start_offset = 28
    business_end_offset = 68
    daily_cycle = 96

    for job in problem.jobs:
        for task in job.tasks:
            # Only apply to setup tasks for unattended processes
            if not (task.is_setup and task.is_unattended):
                continue

            task_key = (job.job_id, task.task_id)
            if task_key not in task_starts:
                continue

            start_var = task_starts[task_key]
            end_var = task_ends[task_key]

            # Create business day choice variables - exactly one must be true
            business_day_choices = []

            for day in range(5):  # Only weekdays (Monday-Friday)
                day_start = day * daily_cycle
                business_day_start = day_start + business_start_offset
                business_day_end = day_start + business_end_offset

                # Boolean variable for whether task is scheduled on this business day
                scheduled_this_day = model.NewBoolVar(
                    f"business_day_{day}_{job.job_id}_{task.task_id}"
                )
                business_day_choices.append(scheduled_this_day)

                # If scheduled on this day, must be within business hours
                model.Add(start_var >= business_day_start).OnlyEnforceIf(
                    scheduled_this_day
                )
                model.Add(start_var < day_start + daily_cycle).OnlyEnforceIf(
                    scheduled_this_day
                )
                model.Add(end_var <= business_day_end).OnlyEnforceIf(scheduled_this_day)

            # Must be scheduled on exactly one business day
            model.AddExactlyOne(business_day_choices)


def add_unattended_execution_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add 24/7 execution constraints for unattended tasks.

    Mathematical formulation:
        For unattended execution tasks:
        execution_start >= setup_end (dependency constraint)
        No time restrictions on execution (can run 24/7)

    Business logic:
        Machine execution phase can run continuously without operator presence.
        Strategic scheduling of long processes (24+ hours) to utilize weekends.

    Constraints added:
        - Execution tasks can start any time after setup completion
        - No business hours restrictions on machine execution
        - Weekend optimization for long-running processes

    Performance: O(n) where n = number of unattended execution tasks
    """
    if problem.is_optimized_mode:
        _add_optimized_execution_constraints(model, task_starts, task_ends, problem)
    else:
        _add_unique_execution_constraints(model, task_starts, task_ends, problem)


def _add_optimized_execution_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add 24/7 execution constraints for optimized mode problems."""
    if not problem.job_optimized_pattern:
        return

    # Find setup-execution pairs for unattended tasks
    for instance in problem.job_instances:
        setup_tasks = []
        execution_tasks = []

        for optimized_task in problem.job_optimized_pattern.optimized_tasks:
            instance_task_id = problem.get_instance_task_id(
                instance.instance_id, optimized_task.optimized_task_id
            )
            task_key = (instance.instance_id, instance_task_id)

            if task_key not in task_starts:
                continue

            if optimized_task.is_unattended:
                if optimized_task.is_setup:
                    setup_tasks.append((optimized_task, task_key))
                else:
                    execution_tasks.append((optimized_task, task_key))

        # Link setup completion to execution start
        for _setup_task, setup_key in setup_tasks:
            setup_end = task_ends[setup_key]

            # Find corresponding execution tasks (all execution follows setup)
            for _execution_task, execution_key in execution_tasks:
                execution_start = task_starts[execution_key]

                # Execution must start after setup completes
                model.Add(execution_start >= setup_end)


def _add_unique_execution_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
) -> None:
    """Add 24/7 execution constraints for unique mode job-based problems."""
    for job in problem.jobs:
        setup_tasks = []
        execution_tasks = []

        for task in job.tasks:
            task_key = (job.job_id, task.task_id)

            if task_key not in task_starts:
                continue

            if task.is_unattended:
                if task.is_setup:
                    setup_tasks.append((task, task_key))
                else:
                    execution_tasks.append((task, task_key))

        # Link setup completion to execution start
        for _setup_task, setup_key in setup_tasks:
            setup_end = task_ends[setup_key]

            for _execution_task, execution_key in execution_tasks:
                execution_start = task_starts[execution_key]
                model.Add(execution_start >= setup_end)


def add_weekend_optimization_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    _task_durations: dict[tuple[str, str], cp_model.IntVar],
    problem: SchedulingProblem,
    long_task_threshold: int = 96,  # 24 hours in time units
) -> None:
    """Add weekend optimization for long unattended processes.

    Mathematical formulation:
        For tasks with duration >= long_task_threshold:
        Encourage weekend starts to maximize utilization
        weekend_start_bonus = BoolVar for starting on weekend

    Business logic:
        Long unattended processes (24+ hours) should be strategically
        scheduled to start on weekends to maximize equipment utilization.

    Constraints added:
        - Incentivize weekend starts for long processes
        - Bonus scheduling priority for 72-hour processes
        - Maximize weekend utilization without operator dependency

    Performance: O(n) where n = number of long unattended tasks
    """
    weekend_start_day_5 = 5 * 96  # Saturday start
    weekend_start_day_6 = 6 * 96  # Sunday start

    if problem.is_optimized_mode and problem.job_optimized_pattern:
        for instance in problem.job_instances:
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                if not optimized_task.is_unattended or optimized_task.is_setup:
                    continue

                # Check if this is a long-running task
                if (
                    optimized_task.min_duration < long_task_threshold * 15
                ):  # Convert to minutes
                    continue

                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)

                if task_key not in task_starts:
                    continue

                start_var = task_starts[task_key]

                # Create weekend start incentive variables
                weekend_start_sat = model.NewBoolVar(
                    f"weekend_start_sat_{instance.instance_id}_{optimized_task.optimized_task_id}"
                )
                weekend_start_sun = model.NewBoolVar(
                    f"weekend_start_sun_{instance.instance_id}_{optimized_task.optimized_task_id}"
                )

                # Define weekend start conditions
                model.Add(start_var >= weekend_start_day_5).OnlyEnforceIf(
                    weekend_start_sat
                )
                model.Add(start_var < weekend_start_day_5 + 96).OnlyEnforceIf(
                    weekend_start_sat
                )

                model.Add(start_var >= weekend_start_day_6).OnlyEnforceIf(
                    weekend_start_sun
                )
                model.Add(start_var < weekend_start_day_6 + 96).OnlyEnforceIf(
                    weekend_start_sun
                )
