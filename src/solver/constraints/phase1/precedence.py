"""Precedence constraints for OR-Tools solver.

Handles task ordering and dependencies.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem


def add_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    task_ends: dict,
    problem: SchedulingProblem,
) -> None:
    """Add precedence constraints between tasks.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        problem: The scheduling problem

    Constraints Added:
        - successor must start after predecessor ends

    """
    for precedence in problem.precedences:
        # Find the job IDs for each task
        pred_task = problem.get_task(precedence.predecessor_task_id)
        succ_task = problem.get_task(precedence.successor_task_id)

        if pred_task and succ_task:
            pred_key = (pred_task.job_id, pred_task.task_id)
            succ_key = (succ_task.job_id, succ_task.task_id)

            model.Add(task_starts[succ_key] >= task_ends[pred_key])


def add_redundant_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: dict,
    task_ends: dict,
    problem: SchedulingProblem,
) -> None:
    """Add redundant transitive precedence constraints to help solver.

    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        problem: The scheduling problem

    Constraints Added:
        - If A->B and B->C, add A->C constraint

    """
    # Build adjacency lists for precedence graph
    successors: dict[str, list[str]] = {}
    for prec in problem.precedences:
        if prec.predecessor_task_id not in successors:
            successors[prec.predecessor_task_id] = []
        successors[prec.predecessor_task_id].append(prec.successor_task_id)

    # Find transitive relationships (limited depth to avoid explosion)
    for task_a_id in successors:
        task_a = problem.get_task(task_a_id)
        if not task_a:
            continue

        for task_b_id in successors.get(task_a_id, []):
            task_b = problem.get_task(task_b_id)
            if not task_b:
                continue

            for task_c_id in successors.get(task_b_id, []):
                task_c = problem.get_task(task_c_id)
                if not task_c:
                    continue

                # Add transitive constraint A -> C
                key_a = (task_a.job_id, task_a.task_id)
                key_c = (task_c.job_id, task_c.task_id)

                model.Add(task_starts[key_c] >= task_ends[key_a])
