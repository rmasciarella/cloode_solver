"""WorkCell capacity constraints for OR-Tools solver.

Handles physical workspace limitations that restrict how many machines
can operate simultaneously within a WorkCell, independent of individual
machine capacities.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem, WorkCell


def add_workcell_capacity_constraints(
    model: cp_model.CpModel,
    task_intervals: dict[tuple[str, str], cp_model.IntervalVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    work_cells: list[WorkCell],
    problem: SchedulingProblem,
) -> None:
    """Add WorkCell capacity constraints limiting simultaneous machine usage.

    Mathematical formulation:
        For each WorkCell c with capacity K and machines M:
        At any time t: sum(machine_busy[m,t] for m in M) <= K

    Business logic:
        Physical workspace limitations (space, utilities, safety) prevent
        all machines in a WorkCell from operating simultaneously.

    Args:
        model: The CP-SAT model
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        work_cells: List of WorkCells with capacity limits
        problem: The scheduling problem

    Constraints Added:
        - Cumulative constraint per WorkCell limiting active machines
        - Each machine contributes 1 unit when any task is running on it

    Performance:
        - Only applies to WorkCells with capacity < machine count
        - O(c × m × t) where c=cells, m=machines per cell, t=tasks

    """
    for work_cell in work_cells:
        # Skip if WorkCell can accommodate all machines
        if work_cell.capacity >= work_cell.machine_count:
            continue

        # Collect all task intervals that could run on machines in this WorkCell
        workcell_intervals = []
        workcell_demands = []

        if problem.is_template_based and problem.job_template:
            # Template-based: iterate over instances and template tasks
            for instance in problem.job_instances:
                for template_task in problem.job_template.template_tasks:
                    instance_task_id = problem.get_instance_task_id(
                        instance.instance_id, template_task.template_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)

                    if task_key in task_intervals:
                        # Check which machines in this WorkCell can run this task
                        for machine in work_cell.machines:
                            if machine.resource_id in template_task.eligible_machines:
                                assign_key = (
                                    instance.instance_id,
                                    instance_task_id,
                                    machine.resource_id,
                                )

                                if assign_key in task_assigned:
                                    # Create optional interval active only when assigned
                                    optional_interval = model.NewOptionalIntervalVar(
                                        task_intervals[task_key].StartExpr(),
                                        task_intervals[task_key].SizeExpr(),
                                        task_intervals[task_key].EndExpr(),
                                        task_assigned[assign_key],
                                        f"wc_{work_cell.cell_id[:8]}_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}_{machine.resource_id[:8]}",
                                    )

                                    workcell_intervals.append(optional_interval)
                                    workcell_demands.append(
                                        1
                                    )  # Each task uses 1 machine
        else:
            # Legacy: iterate over jobs and tasks
            for job in problem.jobs:
                for task in job.tasks:
                    task_key = (job.job_id, task.task_id)

                    if task_key in task_intervals:
                        # Check which machines in this WorkCell can run this task
                        for machine in work_cell.machines:
                            if machine.resource_id in task.eligible_machines:
                                assign_key = (
                                    job.job_id,
                                    task.task_id,
                                    machine.resource_id,
                                )

                                if assign_key in task_assigned:
                                    # Create optional interval active only when assigned
                                    optional_interval = model.NewOptionalIntervalVar(
                                        task_intervals[task_key].StartExpr(),
                                        task_intervals[task_key].SizeExpr(),
                                        task_intervals[task_key].EndExpr(),
                                        task_assigned[assign_key],
                                        f"wc_{work_cell.cell_id[:8]}_{job.job_id[:8]}_{task.task_id[:8]}_{machine.resource_id[:8]}",
                                    )

                                    workcell_intervals.append(optional_interval)
                                    workcell_demands.append(
                                        1
                                    )  # Each task uses 1 machine

        # Add WorkCell capacity constraint if there are intervals
        if workcell_intervals:
            model.AddCumulative(
                workcell_intervals,
                workcell_demands,
                work_cell.capacity,
            )
