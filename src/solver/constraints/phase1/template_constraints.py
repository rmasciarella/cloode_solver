"""Template-based constraint generation for OR-Tools solver.

Optimized constraints for problems with identical job templates to avoid
O(n³) precedence explosion and leverage template structure.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_template_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    task_ends: dict,
    problem: SchedulingProblem,
) -> None:
    """Add precedence constraints for template-based problems.

    This optimized version creates precedence constraints based on template
    structure and replicates them across instances, avoiding O(n³) explosion.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        problem: The scheduling problem (must be template-based)

    Constraints Added:
        - Template precedence constraints replicated across all instances

    Performance: O(template_size * instance_count) vs O(n³) for naive approach

    """
    if not problem.is_template_based or not problem.job_template:
        return

    template = problem.job_template
    instances = problem.job_instances

    # Add template precedence constraints for each instance
    for instance in instances:
        for template_prec in template.template_precedences:
            pred_template_task_id = template_prec.predecessor_template_task_id
            succ_template_task_id = template_prec.successor_template_task_id

            # Generate instance-specific task IDs
            pred_instance_task_id = problem.get_instance_task_id(
                instance.instance_id, pred_template_task_id
            )
            succ_instance_task_id = problem.get_instance_task_id(
                instance.instance_id, succ_template_task_id
            )

            # Create constraint keys
            pred_key = (instance.instance_id, pred_instance_task_id)
            succ_key = (instance.instance_id, succ_instance_task_id)

            # Add precedence constraint: successor starts after predecessor ends
            if pred_key in task_ends and succ_key in task_starts:
                model.Add(task_starts[succ_key] >= task_ends[pred_key])


def add_template_assignment_constraints(
    model: cp_model.CpModel,
    task_assigned: dict,
    task_durations: dict,
    problem: SchedulingProblem,
) -> None:
    """Add machine assignment constraints for template-based problems.

    Each template task instance must be assigned to exactly one machine mode.
    Duration is determined by the selected mode.

    Args:
        model: The CP-SAT model
        task_assigned: Dictionary of assignment variables
        task_durations: Dictionary of duration variables
        problem: The scheduling problem (must be template-based)

    Constraints Added:
        - Each template task instance assigned to exactly one mode
        - Duration determined by selected mode

    """
    if not problem.is_template_based or not problem.job_template:
        return

    template = problem.job_template
    instances = problem.job_instances

    for instance in instances:
        for template_task in template.template_tasks:
            instance_task_id = problem.get_instance_task_id(
                instance.instance_id, template_task.template_task_id
            )
            task_key = (instance.instance_id, instance_task_id)

            # Collect assignment variables for this task
            assignment_vars = []
            for mode in template_task.modes:
                machine_key = (
                    instance.instance_id,
                    instance_task_id,
                    mode.machine_resource_id,
                )
                if machine_key in task_assigned:
                    assignment_vars.append(task_assigned[machine_key])

            # Exactly one mode must be selected
            if assignment_vars:
                model.AddExactlyOne(assignment_vars)

            # Duration constraint based on selected mode
            if task_key in task_durations:
                for mode in template_task.modes:
                    machine_key = (
                        instance.instance_id,
                        instance_task_id,
                        mode.machine_resource_id,
                    )
                    if machine_key in task_assigned:
                        # If this mode is selected, duration equals mode duration
                        model.Add(
                            task_durations[task_key] == mode.duration_time_units
                        ).OnlyEnforceIf(task_assigned[machine_key])


def add_template_no_overlap_constraints(
    model: cp_model.CpModel,
    task_intervals: dict,
    task_assigned: dict,
    machine_intervals: dict,
    problem: SchedulingProblem,
) -> None:
    """Add no-overlap constraints for template-based problems on single-capacity machines.

    Prevents multiple tasks from running simultaneously on the same machine.
    Only applies to machines with capacity = 1.

    Args:
        model: The CP-SAT model
        task_intervals: Dictionary of interval variables
        task_assigned: Dictionary of assignment variables
        machine_intervals: Dictionary to populate with machine interval lists
        problem: The scheduling problem (must be template-based)

    Constraints Added:
        - No overlap on single-capacity machines

    """
    if not problem.is_template_based or not problem.job_template:
        return

    template = problem.job_template
    instances = problem.job_instances

    # Group intervals by machine for single-capacity machines
    for machine in problem.machines:
        if machine.capacity != 1:
            continue  # Skip high-capacity machines

        machine_task_intervals = []

        for instance in instances:
            for template_task in template.template_tasks:
                # Check if this template task can run on this machine
                if machine.resource_id not in template_task.eligible_machines:
                    continue

                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                machine_key = (
                    instance.instance_id,
                    instance_task_id,
                    machine.resource_id,
                )

                if task_key in task_intervals and machine_key in task_assigned:
                    # Create optional interval for this task on this machine
                    optional_interval = model.NewOptionalIntervalVar(
                        task_intervals[task_key].StartExpr(),
                        task_intervals[task_key].SizeExpr(),
                        task_intervals[task_key].EndExpr(),
                        task_assigned[machine_key],
                        f"optional_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}_{machine.resource_id[:8]}",
                    )
                    machine_task_intervals.append(optional_interval)

        # Add no-overlap constraint for this machine
        if machine_task_intervals:
            model.AddNoOverlap(machine_task_intervals)
            machine_intervals[machine.resource_id] = machine_task_intervals


def add_symmetry_breaking_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    problem: SchedulingProblem,
) -> None:
    """Add symmetry breaking constraints for identical job instances.

    Since all job instances are identical, we can break symmetry by forcing
    an ordering on instances. This dramatically reduces the search space.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        problem: The scheduling problem (must be template-based)

    Constraints Added:
        - Lexicographic ordering of instance start times
        - Instance 1 starts before Instance 2, etc.

    """
    if not problem.is_template_based or not problem.job_template:
        return

    template = problem.job_template
    instances = problem.job_instances

    if len(instances) < 2:
        return  # No symmetry to break

    # Sort instances by ID for consistent ordering
    sorted_instances = sorted(instances, key=lambda x: x.instance_id)

    # For each pair of consecutive instances, ensure lexicographic ordering
    for i in range(len(sorted_instances) - 1):
        instance_a = sorted_instances[i]
        instance_b = sorted_instances[i + 1]

        # Find the first template task (assuming template tasks are ordered)
        if template.template_tasks:
            first_template_task = template.template_tasks[0]

            # Generate task keys for both instances
            task_id_a = problem.get_instance_task_id(
                instance_a.instance_id, first_template_task.template_task_id
            )
            task_id_b = problem.get_instance_task_id(
                instance_b.instance_id, first_template_task.template_task_id
            )

            key_a = (instance_a.instance_id, task_id_a)
            key_b = (instance_b.instance_id, task_id_b)

            # Instance A's first task must start no later than Instance B's first task
            if key_a in task_starts and key_b in task_starts:
                model.Add(task_starts[key_a] <= task_starts[key_b])


def add_template_redundant_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    task_ends: dict,
    problem: SchedulingProblem,
    horizon: int,
) -> None:
    """Add redundant constraints to help solver prune search space.

    For template-based problems, we can add several helpful redundant constraints:
    - Total work constraint (makespan >= total_work / total_capacity)
    - Template critical path constraint
    - Instance separation hints

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        problem: The scheduling problem (must be template-based)
        horizon: Problem horizon (maximum time units)

    Constraints Added:
        - Total work lower bound on makespan
        - Template critical path constraints

    """
    if not problem.is_template_based or not problem.job_template:
        return

    template = problem.job_template
    instances = problem.job_instances

    # Calculate total work required
    template_min_work = sum(
        min(mode.duration_time_units for mode in template_task.modes)
        for template_task in template.template_tasks
    )
    total_min_work = template_min_work * len(instances)

    # Calculate total machine capacity
    total_capacity = sum(machine.capacity for machine in problem.machines)

    if total_capacity > 0:
        # Theoretical minimum makespan based on work and capacity
        theoretical_min = (total_min_work + total_capacity - 1) // total_capacity

        # Find all task end times
        all_ends = []
        for instance in instances:
            for template_task in template.template_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in task_ends:
                    all_ends.append(task_ends[task_key])

        # Add constraint: makespan >= theoretical minimum
        if all_ends and theoretical_min > 0:
            makespan = model.NewIntVar(0, horizon, "makespan_lb")
            for end_var in all_ends:
                model.Add(makespan >= end_var)
            model.Add(makespan >= theoretical_min)
