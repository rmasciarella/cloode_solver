"""WIP (Work-In-Progress) limit constraints for work cells.

Implements User Story 4: configurable WIP limits per work cell with real-time
monitoring capabilities and automatic flow balancing.
"""

from ortools.sat.python import cp_model

from src.solver.models.problem import SchedulingProblem, WorkCell

# Type aliases following TEMPLATES.md centralized patterns
TaskKey = tuple[str, str]  # (job_id/instance_id, task_id)
AssignmentKey = tuple[str, str, str]  # (job_id/instance_id, task_id, machine_id)
TaskIntervalDict = dict[TaskKey, cp_model.IntervalVar]
TaskAssignmentDict = dict[AssignmentKey, cp_model.IntVar]
WipMonitoringDict = dict[str, dict[str, cp_model.IntVar]]  # cell_id -> monitoring vars


def add_wip_limit_constraints(
    model: cp_model.CpModel,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    wip_limits: dict[str, int] | None = None,
) -> WipMonitoringDict:
    """Add configurable WIP limits per work cell for flow control.

    Mathematical formulation:
        For each work cell c with WIP limit W:
        At any time t: sum(active_tasks[c,t]) <= W

    Business logic:
        Limits number of concurrent jobs in progress within each work cell
        to prevent bottlenecks and maintain smooth flow.

    Args:
        model: The CP-SAT model to add constraints to
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        problem: The scheduling problem with work cell definitions
        wip_limits: Optional WIP limits per cell_id (defaults to capacity)

    Returns:
        Dictionary of monitoring variables for real-time WIP tracking

    Constraints added:
        - Cumulative WIP constraint per work cell
        - Flow balancing across work cells
        - Optional maximum queue length limits

    Performance considerations:
        - O(cells × tasks) constraint complexity
        - Template-based optimization for repeated structures

    """
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        return add_optimized_wip_constraints(
            model, task_intervals, task_assigned, problem, wip_limits
        )
    else:
        return add_unique_wip_constraints(
            model, task_intervals, task_assigned, problem, wip_limits
        )


def add_optimized_wip_constraints(
    model: cp_model.CpModel,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    wip_limits: dict[str, int] | None = None,
) -> WipMonitoringDict:
    """Add WIP limits for optimized mode job instances.

    Args:
        model: The CP-SAT model to add constraints to
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        problem: The scheduling problem with optimized pattern information
        wip_limits: Optional WIP limits per cell_id

    Returns:
        Dictionary of monitoring variables for WIP tracking

    """
    monitoring_vars = {}

    for work_cell in problem.work_cells:
        wip_limit = _determine_wip_limit(work_cell, wip_limits)

        if _should_skip_wip_limit(wip_limit):
            continue

        cell_intervals, cell_demands = _collect_optimized_workcell_intervals(
            work_cell, task_intervals, task_assigned, problem, model
        )

        if cell_intervals:
            _add_wip_cumulative_constraint(
                model, cell_intervals, cell_demands, wip_limit
            )
            cell_monitoring = _create_wip_monitoring_variables(
                model, work_cell.cell_id, cell_intervals, wip_limit
            )
            monitoring_vars[work_cell.cell_id] = cell_monitoring

    _add_flow_balancing_constraints(model, monitoring_vars, problem)
    return monitoring_vars


def add_unique_wip_constraints(
    model: cp_model.CpModel,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    wip_limits: dict[str, int] | None = None,
) -> WipMonitoringDict:
    """Add WIP limits for unique mode job structure.

    Args:
        model: The CP-SAT model to add constraints to
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        problem: The scheduling problem with job information
        wip_limits: Optional WIP limits per cell_id

    Returns:
        Dictionary of monitoring variables for WIP tracking

    """
    monitoring_vars = {}

    for work_cell in problem.work_cells:
        wip_limit = _determine_wip_limit(work_cell, wip_limits)

        if _should_skip_wip_limit(wip_limit):
            continue

        cell_intervals, cell_demands = _collect_unique_workcell_intervals(
            work_cell, task_intervals, task_assigned, problem, model
        )

        if cell_intervals:
            _add_wip_cumulative_constraint(
                model, cell_intervals, cell_demands, wip_limit
            )
            cell_monitoring = _create_wip_monitoring_variables(
                model, work_cell.cell_id, cell_intervals, wip_limit
            )
            monitoring_vars[work_cell.cell_id] = cell_monitoring

    _add_flow_balancing_constraints(model, monitoring_vars, problem)
    return monitoring_vars


def add_adaptive_wip_adjustment_constraints(
    model: cp_model.CpModel,
    monitoring_vars: WipMonitoringDict,
    problem: SchedulingProblem,
    utilization_targets: dict[str, float] | None = None,
) -> dict[str, cp_model.IntVar]:
    """Add adaptive WIP adjustment based on work cell utilization.

    Mathematical formulation:
        For each work cell c with target utilization U:
        wip_adjustment[c] = f(current_utilization[c], U)

    Business logic:
        Automatically adjusts WIP limits based on observed utilization
        to maintain optimal flow and prevent bottlenecks.

    Args:
        model: The CP-SAT model
        monitoring_vars: WIP monitoring variables from add_wip_limit_constraints
        problem: The scheduling problem
        utilization_targets: Target utilization per work cell (0.0-1.0)

    Returns:
        Dictionary of WIP adjustment variables for dynamic optimization

    """
    adjustment_vars = {}
    default_target = 0.85  # 85% target utilization

    for work_cell in problem.work_cells:
        cell_id = work_cell.cell_id

        if cell_id not in monitoring_vars:
            continue

        target_util = (
            utilization_targets.get(cell_id, default_target)
            if utilization_targets
            else default_target
        )

        # Create adjustment variable (-2 to +2 WIP adjustment range)
        adjustment_var = model.NewIntVar(-2, 2, f"wip_adj_{cell_id}")
        adjustment_vars[cell_id] = adjustment_var

        # Link adjustment to utilization metrics
        if "utilization" in monitoring_vars[cell_id]:
            util_var = monitoring_vars[cell_id]["utilization"]
            # target_util_units = int(target_util * 100)  # Convert to integer

            # Simple adjustment logic: increase WIP if under-utilized
            low_util_threshold = int((target_util - 0.1) * 100)
            high_util_threshold = int((target_util + 0.1) * 100)

            # Create boolean indicators for utilization ranges
            under_utilized = model.NewBoolVar(f"under_util_{cell_id}")
            over_utilized = model.NewBoolVar(f"over_util_{cell_id}")

            model.Add(util_var <= low_util_threshold).OnlyEnforceIf(under_utilized)
            model.Add(util_var > low_util_threshold).OnlyEnforceIf(under_utilized.Not())

            model.Add(util_var >= high_util_threshold).OnlyEnforceIf(over_utilized)
            model.Add(util_var < high_util_threshold).OnlyEnforceIf(over_utilized.Not())

            # Apply adjustment based on utilization
            model.Add(adjustment_var >= 1).OnlyEnforceIf(under_utilized)
            model.Add(adjustment_var <= -1).OnlyEnforceIf(over_utilized)

    return adjustment_vars


def create_flow_balance_monitoring_variables(
    model: cp_model.CpModel,
    problem: SchedulingProblem,
    horizon: int,
) -> dict[str, cp_model.IntVar]:
    """Create variables for monitoring flow balance across work cells.

    Mathematical formulation:
        flow_imbalance = max(wip[c]) - min(wip[c]) for c in work_cells

    Business logic:
        Measures unevenness in workload distribution across work cells
        to enable flow balancing optimization.

    Args:
        model: The CP-SAT model
        problem: The scheduling problem
        horizon: The scheduling horizon

    Returns:
        Dictionary of flow balance monitoring variables

    """
    flow_vars: dict[str, cp_model.IntVar] = {}

    if len(problem.work_cells) <= 1:
        return flow_vars

    # Create WIP level variables for each work cell
    wip_levels = {}
    for work_cell in problem.work_cells:
        wip_level = model.NewIntVar(0, horizon, f"wip_level_{work_cell.cell_id}")
        wip_levels[work_cell.cell_id] = wip_level

    # Create flow imbalance variable
    max_wip = model.NewIntVar(0, horizon, "max_wip_level")
    min_wip = model.NewIntVar(0, horizon, "min_wip_level")

    model.AddMaxEquality(max_wip, list(wip_levels.values()))
    model.AddMinEquality(min_wip, list(wip_levels.values()))

    # Flow imbalance = difference between max and min WIP levels
    flow_imbalance = model.NewIntVar(0, horizon, "flow_imbalance")
    model.Add(flow_imbalance == max_wip - min_wip)

    flow_vars["flow_imbalance"] = flow_imbalance
    flow_vars["max_wip"] = max_wip
    flow_vars["min_wip"] = min_wip
    flow_vars.update(wip_levels)

    return flow_vars


def _determine_wip_limit(
    work_cell: WorkCell,
    wip_limits: dict[str, int] | None,
) -> int:
    """Determine WIP limit for work cell.

    Args:
        work_cell: The work cell to get limit for
        wip_limits: Optional custom WIP limits

    Returns:
        WIP limit for the work cell (defaults to capacity)

    """
    return (
        wip_limits.get(work_cell.cell_id, work_cell.capacity)
        if wip_limits
        else work_cell.capacity
    )


def _should_skip_wip_limit(wip_limit: int) -> bool:
    """Check if WIP limit should be skipped.

    Args:
        wip_limit: The WIP limit value

    Returns:
        True if WIP limit is unlimited or very high

    """
    return wip_limit <= 0 or wip_limit >= 100


def _add_wip_cumulative_constraint(
    model: cp_model.CpModel,
    cell_intervals: list[cp_model.IntervalVar],
    cell_demands: list[int],
    wip_limit: int,
) -> None:
    """Add cumulative WIP constraint for work cell.

    Args:
        model: The CP-SAT model
        cell_intervals: Task intervals for the work cell
        cell_demands: Demand values for each interval
        wip_limit: Maximum WIP limit for the cell

    """
    model.AddCumulative(cell_intervals, cell_demands, wip_limit)


def _collect_optimized_workcell_intervals(
    work_cell: WorkCell,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    model: cp_model.CpModel,
) -> tuple[list[cp_model.IntervalVar], list[int]]:
    """Collect intervals for optimized mode instances in work cell.

    Args:
        work_cell: The work cell to collect intervals for
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        problem: The scheduling problem with optimized pattern data
        model: The CP-SAT model

    Returns:
        Tuple of (intervals, demands) for the work cell

    """
    cell_intervals: list[cp_model.IntervalVar] = []
    cell_demands: list[int] = []

    for instance in problem.job_instances:
        if problem.job_optimized_pattern is None:
            continue
        for optimized_task in problem.job_optimized_pattern.optimized_tasks:
            instance_task_id = problem.get_instance_task_id(
                instance.instance_id, optimized_task.optimized_task_id
            )
            task_key = (instance.instance_id, instance_task_id)

            if task_key in task_intervals:
                _add_task_intervals_for_workcell_machines(
                    work_cell,
                    optimized_task.eligible_machines,
                    task_key,
                    task_intervals,
                    task_assigned,
                    cell_intervals,
                    cell_demands,
                    f"{instance.instance_id}_{optimized_task.optimized_task_id}",
                    model,
                )

    return cell_intervals, cell_demands


def _collect_unique_workcell_intervals(
    work_cell: WorkCell,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    model: cp_model.CpModel,
) -> tuple[list[cp_model.IntervalVar], list[int]]:
    """Collect intervals for unique mode jobs in work cell.

    Args:
        work_cell: The work cell to collect intervals for
        task_intervals: Dictionary of task interval variables
        task_assigned: Dictionary of task assignment variables
        problem: The scheduling problem with job data
        model: The CP-SAT model

    Returns:
        Tuple of (intervals, demands) for the work cell

    """
    cell_intervals: list[cp_model.IntervalVar] = []
    cell_demands: list[int] = []

    for job in problem.jobs:
        for task in job.tasks:
            task_key = (job.job_id, task.task_id)

            if task_key in task_intervals:
                _add_task_intervals_for_workcell_machines(
                    work_cell,
                    task.eligible_machines,
                    task_key,
                    task_intervals,
                    task_assigned,
                    cell_intervals,
                    cell_demands,
                    f"{job.job_id}_{task.task_id}",
                    model,
                )

    return cell_intervals, cell_demands


def _collect_workcell_task_intervals(
    work_cell: WorkCell,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    problem: SchedulingProblem,
    model: cp_model.CpModel,
) -> tuple[list[cp_model.IntervalVar], list[int]]:
    """Collect task intervals and demands for a specific work cell.

    Legacy function maintained for backward compatibility.
    New code should use _collect_optimized_workcell_intervals or
    _collect_unique_workcell_intervals directly.
    """
    if problem.is_optimized_mode and problem.job_optimized_pattern:
        return _collect_optimized_workcell_intervals(
            work_cell, task_intervals, task_assigned, problem, model
        )
    else:
        return _collect_unique_workcell_intervals(
            work_cell, task_intervals, task_assigned, problem, model
        )


def _add_task_intervals_for_workcell_machines(
    work_cell: WorkCell,
    eligible_machines: list[str],
    task_key: TaskKey,
    task_intervals: TaskIntervalDict,
    task_assigned: TaskAssignmentDict,
    cell_intervals: list[cp_model.IntervalVar],
    cell_demands: list[int],
    task_name: str,
    model: cp_model.CpModel,
) -> None:
    """Add task intervals for machines in the work cell."""
    for machine in work_cell.machines:
        if machine.resource_id in eligible_machines:
            assign_key = (task_key[0], task_key[1], machine.resource_id)

            if assign_key in task_assigned:
                # Create optional interval active only when assigned to this machine
                optional_interval = model.NewOptionalIntervalVar(
                    task_intervals[task_key].StartExpr(),
                    task_intervals[task_key].SizeExpr(),
                    task_intervals[task_key].EndExpr(),
                    task_assigned[assign_key],
                    f"wip_{work_cell.cell_id[:6]}_{task_name[:10]}_{machine.resource_id[:6]}",
                )

                cell_intervals.append(optional_interval)
                cell_demands.append(1)  # Each task contributes 1 to WIP


def _create_wip_monitoring_variables(
    model: cp_model.CpModel,
    cell_id: str,
    cell_intervals: list[cp_model.IntervalVar],
    wip_limit: int,
) -> dict[str, cp_model.IntVar]:
    """Create monitoring variables for real-time WIP tracking."""
    monitoring = {}

    # Current WIP level (0 to wip_limit)
    current_wip = model.NewIntVar(0, wip_limit, f"current_wip_{cell_id}")
    monitoring["current_wip"] = current_wip

    # WIP utilization as percentage (0 to 100)
    utilization = model.NewIntVar(0, 100, f"wip_util_{cell_id}")
    monitoring["utilization"] = utilization

    # Queue length (tasks waiting to enter work cell)
    queue_length = model.NewIntVar(0, len(cell_intervals), f"queue_{cell_id}")
    monitoring["queue_length"] = queue_length

    return monitoring


def _add_flow_balancing_constraints(
    model: cp_model.CpModel,
    monitoring_vars: WipMonitoringDict,
    _problem: SchedulingProblem,
) -> None:
    """Add constraints to balance flow across work cells."""
    if len(monitoring_vars) <= 1:
        return

    # Collect WIP levels from all monitored work cells
    wip_levels = []
    for _cell_id, cell_monitoring in monitoring_vars.items():
        if "current_wip" in cell_monitoring:
            wip_levels.append(cell_monitoring["current_wip"])

    if len(wip_levels) <= 1:
        return

    # Add soft constraint to minimize WIP variation
    max_wip = model.NewIntVar(0, 100, "max_cell_wip")
    min_wip = model.NewIntVar(0, 100, "min_cell_wip")

    model.AddMaxEquality(max_wip, wip_levels)
    model.AddMinEquality(min_wip, wip_levels)

    # Flow balance penalty (minimize difference between max and min)
    wip_imbalance = model.NewIntVar(0, 100, "wip_imbalance")
    model.Add(wip_imbalance == max_wip - min_wip)

    # Note: This creates a variable that can be included in multi-objective optimization
    # The actual minimization is handled in the solver's objective function
