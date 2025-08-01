"""Machine assignment constraints for OR-Tools solver.

Handles task-to-machine assignments and no-overlap constraints.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_machine_assignment_constraints(
    model: cp_model.CpModel,
    task_assigned: dict,
    task_durations: dict,
    problem: SchedulingProblem,
) -> None:
    """Add machine assignment constraints.

    Args:
        model: The CP-SAT model
        task_assigned: Boolean variables for task-machine assignment
        task_durations: Task duration variables
        problem: The scheduling problem

    Constraints Added:
        - Each task must be assigned to exactly one eligible machine
        - Task duration depends on assigned machine

    """
    for job in problem.jobs:
        for task in job.tasks:
            task_key = (job.job_id, task.task_id)

            # Collect assignment variables for this task
            assignment_vars = []
            for mode in task.modes:
                machine_key = (job.job_id, task.task_id, mode.machine_resource_id)
                if machine_key in task_assigned:
                    assignment_vars.append(task_assigned[machine_key])

            # Exactly one machine must be selected
            if assignment_vars:
                model.AddExactlyOne(assignment_vars)

            # Link duration to machine selection
            duration_options = []
            for mode in task.modes:
                machine_key = (job.job_id, task.task_id, mode.machine_resource_id)
                if machine_key in task_assigned:
                    # If this machine is selected, use its duration
                    duration_in_units = mode.duration_time_units
                    duration_options.append(
                        task_assigned[machine_key] * duration_in_units
                    )

            # Sum of all duration options equals actual duration
            if duration_options:
                model.Add(task_durations[task_key] == sum(duration_options))


def add_machine_no_overlap_constraints(
    model: cp_model.CpModel,
    task_intervals: dict,
    task_assigned: dict,
    machine_intervals: dict,
    problem: SchedulingProblem,
) -> None:
    """Add no-overlap constraints for machines.

    Args:
        model: The CP-SAT model
        task_intervals: Dictionary of task interval variables
        task_assigned: Boolean variables for task-machine assignment
        machine_intervals: Lists of intervals per machine
        problem: The scheduling problem

    Constraints Added:
        - Tasks assigned to the same machine cannot overlap

    """
    # Create optional intervals for each task-machine combination
    for job in problem.jobs:
        for task in job.tasks:
            task_key = (job.job_id, task.task_id)
            base_interval = task_intervals[task_key]

            for mode in task.modes:
                machine_id = mode.machine_resource_id
                machine_key = (job.job_id, task.task_id, machine_id)

                if machine_key in task_assigned:
                    # Create optional interval that exists only if assigned
                    optional_interval = model.NewOptionalIntervalVar(
                        base_interval.StartExpr(),
                        base_interval.SizeExpr(),
                        base_interval.EndExpr(),
                        task_assigned[machine_key],
                        f"optional_{job.job_id}_{task.task_id}_{machine_id}",
                    )

                    machine_intervals[machine_id].append(optional_interval)

    # Add no-overlap constraint for each machine
    for machine_id, intervals in machine_intervals.items():
        if intervals:
            # Only add no-overlap for unit capacity machines
            # High-capacity machines use AddCumulative instead
            machine = problem.machine_lookup.get(machine_id)
            if machine and machine.capacity <= 1:
                model.AddNoOverlap(intervals)
