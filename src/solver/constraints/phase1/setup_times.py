"""Setup time constraints for OR-Tools solver.

Handles sequence-dependent setup times between tasks on the same machine.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_setup_time_constraints(
    model: cp_model.CpModel,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    setup_times: dict[tuple[str, str, str], int],
    _problem: SchedulingProblem,  # Interface requirement, not used in
    # current implementation
) -> None:
    """Add sequence-dependent setup time constraints between tasks on same machine.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        task_assigned: Dictionary of task assignment variables
        setup_times: Dictionary mapping (task1_id, task2_id, machine_id) to setup time
        problem: The scheduling problem

    Constraints Added:
        - If task2 follows task1 on same machine: task2.start >= task1.end + setup_time
        - Uses big-M method with conditional constraints

    Performance:
        - O(n² × m) where n = tasks, m = machines (worst case)
        - Can be reduced by only considering feasible task sequences

    """
    # Group tasks by machine to reduce iterations
    machine_tasks: dict[str, list[tuple[str, str]]] = {}
    for (job_id, task_id, machine_id), _assigned in task_assigned.items():
        if machine_id not in machine_tasks:
            machine_tasks[machine_id] = []
        machine_tasks[machine_id].append((job_id, task_id))

    # For each machine, add setup constraints between task pairs
    for machine_id, tasks in machine_tasks.items():
        for i, (job1, task1) in enumerate(tasks):
            for j, (job2, task2) in enumerate(tasks):
                if i == j:  # Skip same task
                    continue

                # Get setup time for this sequence (default to 0)
                setup_key = (task1, task2, machine_id)
                setup_time = setup_times.get(setup_key, 0)

                if setup_time > 0:
                    # Create boolean for "task1 before task2 on this machine"
                    before = model.NewBoolVar(f"before_{task1}_{task2}_{machine_id}")

                    # If both assigned to machine AND task1 before task2
                    both_assigned = model.NewBoolVar(
                        f"both_{task1}_{task2}_{machine_id}"
                    )
                    model.Add(
                        task_assigned[(job1, task1, machine_id)] >= 1
                    ).OnlyEnforceIf(both_assigned)
                    model.Add(
                        task_assigned[(job2, task2, machine_id)] >= 1
                    ).OnlyEnforceIf(both_assigned)

                    # If both assigned and task1 before task2, enforce setup time
                    model.Add(
                        task_starts[(job2, task2)]
                        >= task_ends[(job1, task1)] + setup_time
                    ).OnlyEnforceIf([both_assigned, before])
