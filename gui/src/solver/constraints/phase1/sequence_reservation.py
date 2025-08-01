"""Sequence resource reservation constraints for OR-Tools solver.

Handles exclusive access to sequence resources where job must complete
all tasks in a sequence before another job can access any sequence resources.
"""

from collections import defaultdict

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem

# Type aliases from TEMPLATES.md
TaskKey = tuple[str, str]  # (job_id, task_id)
InstanceTaskKey = tuple[str, str]  # (instance_id, optimized_task_id)
SequenceKey = str  # Sequence identifier
SequenceJobKey = tuple[SequenceKey, str]  # (sequence_id, job_id or instance_id)
TaskIntervalDict = dict[TaskKey, cp_model.IntervalVar]
InstanceTaskIntervalDict = dict[InstanceTaskKey, cp_model.IntervalVar]
SequenceJobIntervalDict = dict[SequenceJobKey, cp_model.IntervalVar]


def create_sequence_job_intervals(
    model: cp_model.CpModel,
    task_intervals: TaskIntervalDict | InstanceTaskIntervalDict,
    problem: SchedulingProblem,
    horizon: int,
) -> SequenceJobIntervalDict:
    """Create sequence reservation intervals for each (sequence, job) pair.

    Mathematical formulation:
        For each (sequence_id, job_id) with tasks in sequence:
        seq_start = min(task_starts for tasks in sequence)
        seq_end = max(task_ends for tasks in sequence)

    Business logic:
        Creates meta-intervals representing exclusive sequence reservations.
        Each interval spans from first task start to last task end in sequence.

    Args:
        model: The CP-SAT model
        task_intervals: Dictionary of task interval variables (unique or optimized)
        problem: The scheduling problem with sequence information
        horizon: Maximum time horizon

    Returns:
        Dictionary mapping (sequence_id, job_id) to reservation intervals

    Performance: O(tasks) - single pass through tasks to group by sequence

    """
    # Group tasks by (sequence_id, job_id) for tasks with sequences
    sequence_job_tasks: dict[SequenceJobKey, list[TaskKey | InstanceTaskKey]] = (
        defaultdict(list)
    )

    if problem.is_optimized_mode and problem.job_optimized_pattern:
        # Optimized mode: iterate over instances and optimized tasks
        for instance in problem.job_instances:
            for optimized_task in problem.job_optimized_pattern.optimized_tasks:
                if optimized_task.sequence_id:  # Only tasks that belong to sequences
                    sequence_job_key = (
                        optimized_task.sequence_id,
                        instance.instance_id,
                    )
                    instance_task_id = problem.get_instance_task_id(
                        instance.instance_id, optimized_task.optimized_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)
                    sequence_job_tasks[sequence_job_key].append(task_key)
    else:
        # Unique mode: iterate over jobs and tasks
        for job in problem.jobs:
            for task in job.tasks:
                if task.sequence_id:  # Only tasks that belong to sequences
                    sequence_job_key = (task.sequence_id, job.job_id)
                    task_key = (job.job_id, task.task_id)
                    sequence_job_tasks[sequence_job_key].append(task_key)

    sequence_intervals: SequenceJobIntervalDict = {}

    for (seq_id, entity_id), task_keys in sequence_job_tasks.items():
        if not task_keys:
            continue

        # Get task intervals for this sequence-entity combination
        task_interval_vars = [task_intervals[key] for key in task_keys]

        # Create variables for sequence reservation bounds
        # entity_id is either job_id (legacy) or instance_id (template)
        start_var = model.NewIntVar(0, horizon, f"seq_start_{entity_id}_{seq_id}")
        end_var = model.NewIntVar(0, horizon, f"seq_end_{entity_id}_{seq_id}")
        duration_var = model.NewIntVar(0, horizon, f"seq_dur_{entity_id}_{seq_id}")

        # Link reservation to task intervals (spanning constraint)
        model.AddMinEquality(start_var, [iv.StartExpr() for iv in task_interval_vars])
        model.AddMaxEquality(end_var, [iv.EndExpr() for iv in task_interval_vars])

        # Create the sequence reservation interval
        sequence_intervals[(seq_id, entity_id)] = model.NewIntervalVar(
            start_var, duration_var, end_var, f"seq_interval_{entity_id}_{seq_id}"
        )

    return sequence_intervals


def add_sequence_reservation_constraints(
    model: cp_model.CpModel,
    sequence_job_intervals: SequenceJobIntervalDict,
) -> None:
    """Add exclusive sequence resource reservation constraints.

    Mathematical formulation:
        For each sequence S with entities E1, E2, ..., En:
        NoOverlap([seq_interval(S, E1), seq_interval(S, E2), ..., seq_interval(S, En)])

    Business logic:
        Ensures only one entity (job/instance) can access a sequence at a time.
        Once entity starts any task in sequence, it reserves entire sequence
        until all sequence tasks complete. Works for both legacy jobs and templates.

    Args:
        model: The CP-SAT model
        sequence_job_intervals: Dictionary of sequence reservation intervals

    Constraints Added:
        - NoOverlap constraints for each sequence across all entities
        - Ensures exclusive sequence access per the business rule

    Performance: O(sequences × entities_per_sequence) - groups intervals by sequence

    """
    # Group intervals by sequence for NoOverlap constraints
    intervals_by_sequence: dict[SequenceKey, list[cp_model.IntervalVar]] = defaultdict(
        list
    )

    for (seq_id, _entity_id), interval in sequence_job_intervals.items():
        intervals_by_sequence[seq_id].append(interval)

    # Add NoOverlap constraint for each sequence with multiple entities
    for _seq_id, intervals in intervals_by_sequence.items():
        if len(intervals) > 1:  # Only add constraint if multiple entities use sequence
            model.AddNoOverlap(intervals)
