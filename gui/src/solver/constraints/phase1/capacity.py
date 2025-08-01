"""Machine capacity constraints for OR-Tools solver.

Handles cumulative resource constraints for machines that can run multiple tasks.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import Machine, SchedulingProblem


def add_machine_capacity_constraints(
    model: cp_model.CpModel,
    task_intervals: dict[tuple[str, str], cp_model.IntervalVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    machines: list[Machine],
    problem: SchedulingProblem,
) -> None:
    """Add cumulative capacity constraints for machines that can handle multiple tasks.

    Args:
        model: The CP-SAT model
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        machines: List of machines with capacities
        problem: The scheduling problem

    Constraints Added:
        - CumulativeConstraint for machines with capacity > 1
        - Only applied to high-capacity machines (capacity=1 uses no-overlap)

    Performance:
        - No-overlap is used for capacity=1 (more efficient)
        - AddCumulative only for capacity > 1 (necessary for parallel tasks)
        - O(n × m) where n = tasks, m = high-capacity machines

    """
    for machine in machines:
        if machine.capacity <= 1:
            # Skip unit capacity - no-overlap constraint is more efficient
            continue

        # Collect intervals and demands for this machine
        intervals = []
        demands = []

        if problem.is_optimized_mode and problem.job_optimized_pattern:
            # Optimized mode: iterate over instances and optimized tasks
            for instance in problem.job_instances:
                for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                    # Check if optimized task can run on this machine
                    if machine.resource_id in optimized_task.eligible_machines:
                        instance_task_id = problem.get_instance_task_id(
                            instance.instance_id, optimized_task.optimized_task_id
                        )
                        task_key = (instance.instance_id, instance_task_id)
                        assign_key = (
                            instance.instance_id,
                            instance_task_id,
                            machine.resource_id,
                        )

                        if task_key in task_intervals and assign_key in task_assigned:
                            # Create optional interval based on assignment
                            optional_interval = model.NewOptionalIntervalVar(
                                task_intervals[task_key].StartExpr(),
                                task_intervals[task_key].SizeExpr(),
                                task_intervals[task_key].EndExpr(),
                                task_assigned[assign_key],
                                f"optional_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}_{machine.resource_id[:8]}",
                            )

                            intervals.append(optional_interval)
                            demands.append(1)  # Each task consumes 1 unit of capacity
        else:
            # Unique mode: iterate over jobs and tasks
            for job in problem.jobs:
                for task in job.tasks:
                    # Check if task can run on this machine
                    if machine.resource_id in task.eligible_machines:
                        task_key = (job.job_id, task.task_id)
                        assign_key = (job.job_id, task.task_id, machine.resource_id)

                        # Create optional interval based on assignment
                        optional_interval = model.NewOptionalIntervalVar(
                            task_intervals[task_key].StartExpr(),
                            task_intervals[task_key].SizeExpr(),
                            task_intervals[task_key].EndExpr(),
                            task_assigned[assign_key],
                            f"optional_{job.job_id[:8]}_{task.task_id[:8]}_{machine.resource_id[:8]}",
                        )

                        intervals.append(optional_interval)
                        demands.append(1)  # Each task consumes 1 unit of capacity

        # Add cumulative constraint if machine has tasks
        if intervals:
            model.AddCumulative(intervals, demands, machine.capacity)
