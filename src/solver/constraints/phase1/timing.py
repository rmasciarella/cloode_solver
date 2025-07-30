"""Timing constraints for OR-Tools solver.

Handles task duration and time-based constraints.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_task_duration_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    task_ends: dict,
    _task_intervals: dict,  # Not used in current implementation, kept for
    # interface compatibility
    task_durations: dict,
    problem: SchedulingProblem,
) -> None:
    """Add duration constraints linking start, end, and duration variables.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        task_intervals: Dictionary of task interval variables
        task_durations: Dictionary of task duration variables
        problem: The scheduling problem

    Constraints Added:
        - end = start + duration for each task
        - interval variable spans from start to end with duration

    """
    if problem.is_template_based and problem.job_template:
        # Template-based: iterate over instances and template tasks
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)

                # Link start, duration, and end for template task instance
                if (
                    task_key in task_starts
                    and task_key in task_ends
                    and task_key in task_durations
                ):
                    model.Add(
                        task_ends[task_key]
                        == task_starts[task_key] + task_durations[task_key]
                    )
    else:
        # Legacy: iterate over jobs and tasks
        for job in problem.jobs:
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)

                # Link start, duration, and end
                model.Add(
                    task_ends[task_key]
                    == task_starts[task_key] + task_durations[task_key]
                )
