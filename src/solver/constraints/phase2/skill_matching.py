"""Phase 2.1a: Basic skill matching constraints for operator-task assignment.

Implements skill-based operator assignment with proficiency matching.
"""

import logging
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem

if TYPE_CHECKING:
    from src.solver.models.task import Task
    from src.solver.models.template_task import TemplateTask

logger = logging.getLogger(__name__)

# Type aliases for OR-Tools variables following TEMPLATES.md
TaskKey = tuple[str, str]  # (job_id, task_id)
OperatorKey = str
OperatorAssignmentKey = tuple[str, str, str]  # (job_id, task_id, operator_id)
TaskOperatorAssignmentDict = dict[OperatorAssignmentKey, cp_model.IntVar]


def add_skill_requirement_constraints(
    model: cp_model.CpModel,
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> None:
    """Add skill requirement constraints ensuring operators have required skills.

    Mathematical formulation:
        For each task t with skill requirements S:
        ∑_{o ∈ qualified_operators(t)} task_operator_assigned[t,o] = 1

    Business logic:
        Only operators with the required skills and proficiency levels
        can be assigned to tasks.

    Args:
        model: The CP-SAT model to add constraints to
        task_operator_assigned: Assignment variables (job_id, task_id, operator_id)
            -> BoolVar
        problem: The scheduling problem containing skill requirements

    Constraints added:
        - Task assignment restricted to qualified operators only
        - Exactly one operator per task (1:1 assignment)

    Performance considerations:
        - Pre-filters operators by skill requirements to reduce variable count
        - O(tasks × qualified_operators) complexity

    """
    logger.info("Adding skill requirement constraints...")

    constraints_added = 0

    # Get all tasks that need operator assignment
    task_ids = set()
    if problem.is_template_based and problem.job_template:
        # Template-based tasks
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_ids.add(task_id)
    else:
        # Legacy tasks
        for job in problem.jobs:
            for task in job.tasks:
                task_ids.add(task.task_id)

    for task_id in task_ids:
        # Get qualified operators for this task
        qualified_operators = problem.get_qualified_operators(task_id)

        if not qualified_operators:
            # No qualified operators - this will make the problem infeasible
            logger.warning(f"Task {task_id} has no qualified operators")
            continue

        # Create assignment variables for qualified operators only
        assignment_vars = []
        for operator in qualified_operators:
            # Find the job_id for this task
            job_id = None
            if problem.is_template_based:
                # Parse instance task ID
                parsed = problem.parse_instance_task_id(task_id)
                if parsed:
                    job_id = parsed[0]  # instance_id acts as job_id
            else:
                # Find job containing this task
                for job in problem.jobs:
                    if any(task.task_id == task_id for task in job.tasks):
                        job_id = job.job_id
                        break

            if job_id:
                assignment_key = (job_id, task_id, operator.operator_id)
                if assignment_key in task_operator_assigned:
                    assignment_vars.append(task_operator_assigned[assignment_key])

        if assignment_vars:
            # For single-operator tasks, exactly one operator must be assigned
            # For multi-operator tasks, handled by multi_operator_task_constraints

            # Check if this is a multi-operator task
            is_multi_operator = False
            if problem.is_template_based:
                parsed = problem.parse_instance_task_id(task_id)
                if parsed:
                    template_task_result = problem.get_template_task(parsed[1])
                    is_multi_operator = (
                        template_task_result is not None
                        and template_task_result.max_operators > 1
                    )
            else:
                task_result = problem.get_task(task_id)
                is_multi_operator = (
                    task_result is not None and task_result.max_operators > 1
                )

            if not is_multi_operator:
                # Single-operator task: exactly one operator assigned
                model.AddExactlyOne(assignment_vars)
                constraints_added += 1
            else:
                # Multi-operator task: at least one operator (min/max elsewhere)
                model.Add(sum(assignment_vars) >= 1)
                constraints_added += 1

    logger.info(f"Added {constraints_added} skill requirement constraints")


def add_operator_capacity_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
) -> None:
    """Add operator capacity constraints preventing overlapping assignments.

    Mathematical formulation:
        For each operator o and overlapping tasks t1, t2:
        task_operator_assigned[t1,o] + task_operator_assigned[t2,o] ≤ 1
        OR use NoOverlap constraint with optional intervals

    Business logic:
        Operators can only work on one task at a time.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables

    Constraints added:
        - Operator cannot work on overlapping tasks
        - One task per operator at any given time

    Performance considerations:
        - Uses interval variables for efficient no-overlap constraints
        - O(operators × tasks) complexity

    """
    logger.info("Adding operator capacity constraints...")

    constraints_added = 0

    # Group assignments by operator
    operator_intervals: dict[str, list[cp_model.IntervalVar]] = {}

    for (
        job_id,
        task_id,
        operator_id,
    ), assignment_var in task_operator_assigned.items():
        if operator_id not in operator_intervals:
            operator_intervals[operator_id] = []

        # Create optional interval for this operator-task assignment
        task_key = (job_id, task_id)
        if task_key in task_starts and task_key in task_ends:
            # Create a duration variable for this interval
            duration_var = model.NewIntVar(
                1, 100, f"op_duration_{operator_id}_{job_id}_{task_id}"
            )
            # Constrain duration to match task duration
            model.Add(duration_var == task_ends[task_key] - task_starts[task_key])

            interval = model.NewOptionalIntervalVar(
                task_starts[task_key],
                duration_var,
                task_ends[task_key],
                assignment_var,
                f"operator_interval_{operator_id}_{job_id}_{task_id}",
            )
            operator_intervals[operator_id].append(interval)

    # Add no-overlap constraints for each operator
    for intervals in operator_intervals.values():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)
            constraints_added += 1

    logger.info(f"Added {constraints_added} operator capacity constraints")


def add_multi_operator_task_constraints(
    model: cp_model.CpModel,
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> None:
    """Add constraints for tasks requiring multiple operators.

    Mathematical formulation:
        For each task t with min_operators m and max_operators M:
        m ≤ ∑_{o ∈ qualified_operators(t)} task_operator_assigned[t,o] ≤ M

    Business logic:
        Tasks can require multiple operators working simultaneously.
        Minimum and maximum operator counts must be respected.

    Args:
        model: The CP-SAT model to add constraints to
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    Constraints added:
        - Minimum operator count per task
        - Maximum operator count per task
        - Multi-skill requirement coverage

    Performance considerations:
        - O(tasks × operators) complexity
        - Pre-filters by qualified operators

    """
    logger.info("Adding multi-operator task constraints...")

    constraints_added = 0

    # Get all tasks that need multi-operator support
    task_ids = set()
    task_definitions: dict[str, Task | TemplateTask] = {}  # task_id -> task object

    if problem.is_template_based and problem.job_template:
        # Template-based tasks
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_ids.add(task_id)
                task_definitions[task_id] = template_task
    else:
        # Legacy tasks
        for job in problem.jobs:
            for task in job.tasks:
                task_ids.add(task.task_id)
                task_definitions[task.task_id] = task

    for task_id in task_ids:
        task_def = task_definitions[task_id]

        # Get all operator assignment variables for this task
        assignment_vars = []
        for assignment_key, assignment_var in task_operator_assigned.items():
            if assignment_key[1] == task_id:  # (job_id, task_id, operator_id)
                assignment_vars.append(assignment_var)

        if assignment_vars:
            # Add minimum operator constraint
            model.Add(sum(assignment_vars) >= task_def.min_operators)
            constraints_added += 1

            # Add maximum operator constraint
            model.Add(sum(assignment_vars) <= task_def.max_operators)
            constraints_added += 1

    logger.info(f"Added {constraints_added} multi-operator task constraints")


def add_skill_proficiency_optimization(
    model: cp_model.CpModel,
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> dict[str, cp_model.IntVar]:
    """Add skill proficiency optimization variables and constraints.

    Creates efficiency variables based on operator skill proficiency
    and task requirements for optimization objectives.

    Args:
        model: The CP-SAT model to add constraints to
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    Returns:
        Dictionary mapping task_id to efficiency variables

    Constraints added:
        - Task efficiency calculation based on assigned operators
        - Skill proficiency matching bonus/penalty

    """
    logger.info("Adding skill proficiency optimization...")

    task_efficiency_vars = {}
    constraints_added = 0

    # Get all tasks
    task_ids = set()
    if problem.is_template_based and problem.job_template:
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_ids.add(task_id)
    else:
        for job in problem.jobs:
            for task in job.tasks:
                task_ids.add(task.task_id)

    for task_id in task_ids:
        # Create efficiency variable for this task
        task_efficiency_vars[task_id] = model.NewIntVar(
            0,
            500,  # 0% to 500% efficiency (5x with expert operators)
            f"task_efficiency_{task_id[:12]}",
        )

        # Calculate efficiency based on assigned operators
        efficiency_terms = []
        for assignment_key, assignment_var in task_operator_assigned.items():
            if assignment_key[1] == task_id:  # (job_id, task_id, operator_id)
                operator_id = assignment_key[2]

                # Get operator efficiency for this task
                efficiency = problem.calculate_operator_task_efficiency(
                    operator_id, task_id
                )
                efficiency_scaled = int(efficiency * 100)  # Scale to integer percentage

                # Add efficiency contribution if operator is assigned
                efficiency_terms.append(assignment_var * efficiency_scaled)

        if efficiency_terms:
            # Task efficiency = sum of assigned operator efficiencies
            model.Add(task_efficiency_vars[task_id] == sum(efficiency_terms))
            constraints_added += 1

    logger.info(f"Added {constraints_added} skill proficiency optimization constraints")
    return task_efficiency_vars


def add_basic_skill_matching_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> None:
    """Add all basic skill matching constraints for Phase 2.1a.

    Combines skill requirement and operator capacity constraints
    for complete skill-based assignment functionality.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    """
    logger.info("Adding basic skill matching constraints...")

    # Add skill requirement constraints
    add_skill_requirement_constraints(model, task_operator_assigned, problem)

    # Add operator capacity constraints
    add_operator_capacity_constraints(
        model, task_starts, task_ends, task_operator_assigned
    )

    logger.info("Basic skill matching constraints added successfully")


def add_advanced_skill_matching_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> dict[str, cp_model.IntVar]:
    """Add all advanced skill matching constraints for Phase 2.1b.

    Combines basic constraints with multi-operator support and
    skill proficiency optimization.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    Returns:
        Dictionary mapping task_id to efficiency variables for objective

    """
    logger.info("Adding advanced skill matching constraints...")

    # Add basic constraints first
    add_basic_skill_matching_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # Add multi-operator task support
    add_multi_operator_task_constraints(model, task_operator_assigned, problem)

    # Add skill proficiency optimization
    task_efficiency_vars = add_skill_proficiency_optimization(
        model, task_operator_assigned, problem
    )

    logger.info("Advanced skill matching constraints added successfully")
    return task_efficiency_vars
