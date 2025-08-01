"""Phase 2.1b: Shift calendar integration for operator availability.

Implements operator shift schedule constraints and availability windows.
"""

import logging
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem

if TYPE_CHECKING:
    from src.solver.models.operator_shift import OperatorShift

logger = logging.getLogger(__name__)

# Type aliases for OR-Tools variables following TEMPLATES.md
TaskKey = tuple[str, str]  # (job_id, task_id)
OperatorAssignmentKey = tuple[str, str, str]  # (job_id, task_id, operator_id)
TaskOperatorAssignmentDict = dict[OperatorAssignmentKey, cp_model.IntVar]


def add_operator_shift_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> None:
    """Add constraints ensuring operators only work during their shifts.

    Mathematical formulation:
        For each operator o, task t, and shift s:
        If task_operator_assigned[t,o] = 1 then:
        shift_start[s] ≤ task_start[t] AND task_end[t] ≤ shift_end[s]

    Business logic:
        Operators can only be assigned to tasks that fall within their
        scheduled work shifts. Tasks cannot span across shift boundaries.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables
        problem: The scheduling problem containing shift data

    Constraints added:
        - Task start must be after operator shift start
        - Task end must be before operator shift end
        - Only applies when operator is assigned to task

    Performance considerations:
        - O(operators × tasks × shifts) complexity
        - Uses conditional constraints for efficiency

    """
    logger.info("Adding operator shift constraints...")

    if not problem.operator_shifts:
        logger.info("No operator shifts defined, skipping shift constraints")
        return

    constraints_added = 0

    # Group shifts by operator for efficient lookup
    operator_shifts: dict[str, list[OperatorShift]] = {}
    for shift in problem.operator_shifts:
        if shift.operator_id not in operator_shifts:
            operator_shifts[shift.operator_id] = []
        operator_shifts[shift.operator_id].append(shift)

    # Add constraints for each operator assignment
    for (
        job_id,
        task_id,
        operator_id,
    ), assignment_var in task_operator_assigned.items():
        task_key = (job_id, task_id)

        if task_key not in task_starts or task_key not in task_ends:
            continue

        if operator_id not in operator_shifts:
            # Operator has no shifts defined - cannot be assigned
            model.Add(assignment_var == 0)
            constraints_added += 1
            continue

        # Get shifts for this operator
        shifts = operator_shifts[operator_id]

        if not shifts:
            # No shifts available - cannot be assigned
            model.Add(assignment_var == 0)
            constraints_added += 1
            continue

        # Task can only be assigned if it fits within at least one shift
        shift_compatibility_vars = []

        for shift in shifts:
            if not shift.is_available:
                continue

            # Create boolean variable for this shift compatibility
            shift_compat_var = model.NewBoolVar(
                f"shift_compat_{operator_id[:6]}_{job_id[:6]}_{task_id[:6]}_{shift.shift_date.day}"
            )

            # Task must fit within shift window
            model.Add(task_starts[task_key] >= shift.start_time).OnlyEnforceIf(
                shift_compat_var
            )
            model.Add(task_ends[task_key] <= shift.end_time).OnlyEnforceIf(
                shift_compat_var
            )

            shift_compatibility_vars.append(shift_compat_var)

        if shift_compatibility_vars:
            # If operator is assigned, task must be compatible with at least one shift
            # Create a boolean variable for "at least one shift compatible"
            any_shift_compatible = model.NewBoolVar(
                f"any_shift_{operator_id[:6]}_{job_id[:6]}_{task_id[:6]}"
            )
            model.Add(sum(shift_compatibility_vars) >= 1).OnlyEnforceIf(
                any_shift_compatible
            )
            model.Add(sum(shift_compatibility_vars) == 0).OnlyEnforceIf(
                any_shift_compatible.Not()
            )

            # Implication: if assigned, then at least one shift compatible
            model.AddImplication(assignment_var, any_shift_compatible)
            constraints_added += 1
        else:
            # No compatible shifts - cannot assign operator
            model.Add(assignment_var == 0)
            constraints_added += 1

    logger.info(f"Added {constraints_added} operator shift constraints")


def add_overtime_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> dict[str, cp_model.IntVar]:
    """Add overtime tracking constraints for operators.

    Creates overtime variables to track when operators work beyond
    their regular shift hours.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    Returns:
        Dictionary mapping operator_id to overtime variables

    Constraints added:
        - Overtime calculation for each operator
        - Overtime limits based on shift settings

    """
    logger.info("Adding overtime constraints...")

    overtime_vars: dict[str, cp_model.IntVar] = {}
    constraints_added = 0

    if not problem.operator_shifts:
        logger.info("No operator shifts defined, skipping overtime constraints")
        return overtime_vars

    # Group shifts by operator
    operator_shifts: dict[str, list[OperatorShift]] = {}
    for shift in problem.operator_shifts:
        if shift.operator_id not in operator_shifts:
            operator_shifts[shift.operator_id] = []
        operator_shifts[shift.operator_id].append(shift)

    # Create overtime variables for each operator
    for operator_id, shifts in operator_shifts.items():
        # Calculate maximum possible overtime across all shifts
        max_overtime = sum(
            (
                int(shift.max_overtime_hours * 4) if shift.overtime_allowed else 0
            )  # Convert hours to time units
            for shift in shifts
        )

        if max_overtime > 0:
            overtime_vars[operator_id] = model.NewIntVar(
                0, max_overtime, f"overtime_{operator_id[:8]}"
            )
        else:
            overtime_vars[operator_id] = model.NewIntVar(
                0, 0, f"overtime_{operator_id[:8]}"
            )

        # Calculate total work time for this operator
        work_time_terms = []

        for (job_id, task_id, op_id), assignment_var in task_operator_assigned.items():
            if op_id != operator_id:
                continue

            task_key = (job_id, task_id)
            if task_key in task_starts and task_key in task_ends:
                # Create intermediate variable for task duration
                task_duration_var = model.NewIntVar(
                    0, 1000, f"task_duration_{op_id[:6]}_{job_id[:6]}_{task_id[:6]}"
                )
                model.Add(
                    task_duration_var == task_ends[task_key] - task_starts[task_key]
                )

                # Create intermediate variable for work time contribution
                work_contribution = model.NewIntVar(
                    0, 1000, f"work_contrib_{op_id[:6]}_{job_id[:6]}_{task_id[:6]}"
                )
                model.Add(work_contribution == task_duration_var).OnlyEnforceIf(
                    assignment_var
                )
                model.Add(work_contribution == 0).OnlyEnforceIf(assignment_var.Not())

                work_time_terms.append(work_contribution)

        if work_time_terms:
            total_work_time = model.NewIntVar(0, 1000, f"total_work_{operator_id[:8]}")
            model.Add(total_work_time == sum(work_time_terms))

            # Calculate regular shift time
            regular_shift_time = sum(
                shift.shift_duration_hours * 4 for shift in shifts
            )  # Convert to time units
            regular_time_var = model.NewIntVar(
                0, int(regular_shift_time), f"regular_time_{operator_id[:8]}"
            )
            model.Add(regular_time_var == int(regular_shift_time))

            # Overtime = max(0, total_work_time - regular_shift_time)
            model.AddMaxEquality(
                overtime_vars[operator_id],
                [
                    0,  # No overtime
                    total_work_time - regular_time_var,  # Overtime amount
                ],
            )

            constraints_added += 1

    logger.info(f"Added {constraints_added} overtime constraints")
    return overtime_vars


def add_shift_calendar_constraints(
    model: cp_model.CpModel,
    task_starts: dict[TaskKey, cp_model.IntVar],
    task_ends: dict[TaskKey, cp_model.IntVar],
    task_operator_assigned: TaskOperatorAssignmentDict,
    problem: SchedulingProblem,
) -> dict[str, cp_model.IntVar]:
    """Add all shift calendar constraints for Phase 2.1b.

    Combines operator shift constraints with overtime tracking
    for complete shift calendar functionality.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Task start time variables
        task_ends: Task end time variables
        task_operator_assigned: Assignment variables
        problem: The scheduling problem

    Returns:
        Dictionary mapping operator_id to overtime variables

    """
    logger.info("Adding shift calendar constraints...")

    # Add basic shift constraints
    add_operator_shift_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # Add overtime tracking
    overtime_vars = add_overtime_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    logger.info("Shift calendar constraints added successfully")
    return overtime_vars
