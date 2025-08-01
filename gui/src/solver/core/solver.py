"""Fresh OR-Tools CP-SAT Solver - Phase 1 Implementation.

Handles basic scheduling with timing, precedence, and machine assignment.
"""

import logging
from collections import defaultdict

from ortools.sat.python import cp_model

from src.data.loaders.database import load_test_problem
from src.solver.constraints.phase1 import (
    add_adaptive_wip_adjustment_constraints,
    add_business_hours_setup_constraints,
    # User Story 3: Due date constraints and lateness penalties
    add_due_date_enforcement_constraints,
    add_lateness_penalty_variables,
    add_machine_assignment_constraints,
    add_machine_capacity_constraints,
    add_machine_no_overlap_constraints,
    add_optimized_assignment_constraints,
    add_optimized_no_overlap_constraints,
    add_optimized_precedence_constraints,
    add_optimized_redundant_constraints,
    add_precedence_constraints,
    add_redundant_precedence_constraints,
    add_setup_time_constraints,
    add_symmetry_breaking_constraints,
    add_task_duration_constraints,
    add_unattended_execution_constraints,
    add_weekend_optimization_constraints,
    # User Story 4: WIP limit constraints
    add_wip_limit_constraints,
    add_workcell_capacity_constraints,
    create_flow_balance_monitoring_variables,
    create_total_lateness_objective_variable,
)
from src.solver.constraints.phase1.sequence_reservation import (
    add_sequence_reservation_constraints,
    create_sequence_job_intervals,
)

# Phase 2 imports
from src.solver.constraints.phase2 import (
    add_advanced_skill_matching_constraints,
    add_shift_calendar_constraints,
)

# Phase 3 imports
from src.solver.constraints.phase3 import (
    add_epsilon_constraint_objective_constraints,
    add_lexicographical_objective_constraints,
    add_weighted_sum_objective_constraints,
    analyze_trade_offs,
    calculate_objective_values,
    create_multi_objective_variables,
    find_pareto_frontier,
    recommend_solution,
)

# Type imports - using Any for now as OR-Tools types aren't directly importable
from src.solver.models.problem import (
    ObjectiveSolution,
    ObjectiveType,
    SchedulingProblem,
)
from src.solver.utils.time_utils import (
    calculate_horizon,
    calculate_latest_start,
    extract_solution,
    print_solution_summary,
)

logger = logging.getLogger(__name__)


class FreshSolver:
    """Main solver class for OR-Tools scheduling."""

    def __init__(
        self,
        problem: SchedulingProblem,
        setup_times: dict[tuple[str, str, str], int] | None = None,
    ):
        """Initialize solver with problem definition.

        Args:
            problem: The scheduling problem to solve
            setup_times: Optional dictionary of setup times between tasks on machines
                        Key: (predecessor_task_id, successor_task_id, machine_id)
                        Value: Setup time in time units (15-minute intervals)

        """
        self.problem = problem
        self.model = cp_model.CpModel()
        self.setup_times = setup_times or {}

        # Decision variables - will be populated during solve
        self.task_starts: dict[tuple[str, str], cp_model.IntVar] = {}
        self.task_ends: dict[tuple[str, str], cp_model.IntVar] = {}
        self.task_durations: dict[tuple[str, str], cp_model.IntVar] = {}
        self.task_intervals: dict[tuple[str, str], cp_model.IntervalVar] = {}
        self.task_assigned: dict[tuple[str, str, str], cp_model.IntVar] = {}
        self.machine_intervals: dict[str, list[cp_model.IntervalVar]] = defaultdict(
            list
        )

        # Phase 2: Operator assignment variables
        self.task_operator_assigned: dict[tuple[str, str, str], cp_model.IntVar] = {}

        # Phase 3: Multi-objective variables
        self.objective_variables: dict[str, cp_model.IntVar] = {}

        # User Story 3: Due date and lateness variables
        self.completion_times: dict[str, cp_model.IntVar] = {}
        self.lateness_penalties: dict[str, cp_model.IntVar] = {}

        # User Story 4: WIP monitoring and flow balance variables
        self.wip_monitoring_vars: dict[str, dict[str, cp_model.IntVar]] = {}
        self.wip_adjustment_vars: dict[str, cp_model.IntVar] = {}
        self.flow_balance_vars: dict[str, cp_model.IntVar] = {}

        # Sequence resource reservation variables
        self.sequence_job_intervals: dict[tuple[str, str], cp_model.IntervalVar] = {}

        # Solver parameters
        self.horizon = calculate_horizon(problem)
        self.solver: cp_model.CpSolver | None = None

    def create_variables(self) -> None:
        """Create all decision variables for the model."""
        logger.info("Creating decision variables...")

        if self.problem.is_optimized_mode:
            self._create_optimized_variables()
        else:
            self._create_unique_variables()

        # Phase 3: Create multi-objective variables if configured
        if self.problem.multi_objective_config:
            self.objective_variables = create_multi_objective_variables(
                self.model,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.horizon,
            )

        # Create sequence job intervals for sequence resource reservation
        self.sequence_job_intervals = create_sequence_job_intervals(
            self.model, self.task_intervals, self.problem, self.horizon
        )

        logger.info(f"Created {len(self.task_starts)} task timing variables")
        logger.info(f"Created {len(self.task_assigned)} assignment variables")
        if self.sequence_job_intervals:
            logger.info(
                f"Created {len(self.sequence_job_intervals)} sequence reservation "
                "intervals"
            )
        if self.objective_variables:
            logger.info(
                f"Created {len(self.objective_variables)} multi-objective variables"
            )

    def _create_optimized_variables(self) -> None:
        """Create variables for optimized mode problems."""
        if not self.problem.job_optimized_pattern or not self.problem.job_instances:
            logger.warning("Optimized mode problem missing pattern or instances")
            return

        pattern = self.problem.job_optimized_pattern
        instances = self.problem.job_instances

        logger.info(
            f"Creating optimized variables for {len(instances)} instances of "
            f"{pattern.task_count} tasks"
        )

        # For each job instance, create variables for each optimized task
        for instance in instances:
            for optimized_task in pattern.optimized_tasks:
                # Generate task key for this instance-pattern combination
                instance_task_id = self.problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)

                # Calculate bounds
                earliest_start = 0
                # For optimized tasks, we use a simplified latest start calculation
                # Could be enhanced with optimized precedence analysis
                latest_start = max(0, self.horizon - optimized_task.min_duration // 15)

                # Timing variables
                self.task_starts[task_key] = self.model.NewIntVar(
                    earliest_start,
                    latest_start,
                    f"start_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}",
                )

                # Duration variable (constrained by machine mode selection)
                min_duration = min(
                    mode.duration_time_units for mode in optimized_task.modes
                )
                max_duration = max(
                    mode.duration_time_units for mode in optimized_task.modes
                )

                self.task_durations[task_key] = self.model.NewIntVar(
                    min_duration,
                    max_duration,
                    f"duration_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}",
                )

                # End variable
                self.task_ends[task_key] = self.model.NewIntVar(
                    earliest_start + min_duration,
                    min(self.horizon, latest_start + max_duration),
                    f"end_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}",
                )

                # Interval variable
                self.task_intervals[task_key] = self.model.NewIntervalVar(
                    self.task_starts[task_key],
                    self.task_durations[task_key],
                    self.task_ends[task_key],
                    f"interval_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}",
                )

                # Machine assignment variables for each mode
                for mode in optimized_task.modes:
                    machine_key = (
                        instance.instance_id,
                        instance_task_id,
                        mode.machine_resource_id,
                    )
                    self.task_assigned[machine_key] = self.model.NewBoolVar(
                        f"assigned_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}_{mode.machine_resource_id[:8]}"
                    )

                # Phase 2: Operator assignment variables for qualified operators only
                if self.problem.operators:
                    # Get qualified operators for this optimized task
                    qualified_operators = self.problem.get_qualified_operators(
                        instance_task_id
                    )
                    for operator in qualified_operators:
                        operator_key = (
                            instance.instance_id,
                            instance_task_id,
                            operator.operator_id,
                        )
                        self.task_operator_assigned[operator_key] = (
                            self.model.NewBoolVar(
                                f"op_assigned_{instance.instance_id[:8]}_{optimized_task.optimized_task_id[:8]}_{operator.operator_id[:8]}"
                            )
                        )

    def _create_unique_variables(self) -> None:
        """Create variables for unique mode job-based problems."""
        for job in self.problem.jobs:
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)

                # Calculate bounds
                earliest_start = 0
                latest_start = calculate_latest_start(task, job, self.horizon)

                # Timing variables
                self.task_starts[task_key] = self.model.NewIntVar(
                    earliest_start,
                    latest_start,
                    f"start_{job.job_id[:8]}_{task.task_id[:8]}",
                )

                # Duration variable (will be constrained by machine selection)
                min_duration = min(mode.duration_time_units for mode in task.modes)
                max_duration = max(mode.duration_time_units for mode in task.modes)

                self.task_durations[task_key] = self.model.NewIntVar(
                    min_duration,
                    max_duration,
                    f"duration_{job.job_id[:8]}_{task.task_id[:8]}",
                )

                # End variable
                self.task_ends[task_key] = self.model.NewIntVar(
                    earliest_start + min_duration,
                    min(self.horizon, latest_start + max_duration),
                    f"end_{job.job_id[:8]}_{task.task_id[:8]}",
                )

                # Interval variable
                self.task_intervals[task_key] = self.model.NewIntervalVar(
                    self.task_starts[task_key],
                    self.task_durations[task_key],
                    self.task_ends[task_key],
                    f"interval_{job.job_id[:8]}_{task.task_id[:8]}",
                )

                # Machine assignment variables
                for mode in task.modes:
                    machine_key = (job.job_id, task.task_id, mode.machine_resource_id)
                    self.task_assigned[machine_key] = self.model.NewBoolVar(
                        f"assigned_{job.job_id[:8]}_{task.task_id[:8]}_{mode.machine_resource_id[:8]}"
                    )

                # Phase 2: Operator assignment variables for qualified operators only
                if self.problem.operators:
                    # Get qualified operators for this task
                    qualified_operators = self.problem.get_qualified_operators(
                        task.task_id
                    )
                    for operator in qualified_operators:
                        operator_key = (job.job_id, task.task_id, operator.operator_id)
                        self.task_operator_assigned[operator_key] = (
                            self.model.NewBoolVar(
                                f"op_assigned_{job.job_id[:8]}_{task.task_id[:8]}_{operator.operator_id[:8]}"
                            )
                        )

    def add_constraints(self) -> None:
        """Add all Phase 1 constraints to the model."""
        logger.info("Adding constraints...")

        if self.problem.is_optimized_mode:
            self._add_template_constraints()
        else:
            self._add_legacy_constraints()

        logger.info("All constraints added")

    def _add_template_constraints(self) -> None:
        """Add optimized constraints for template-based problems."""
        logger.info("Adding template-optimized constraints...")

        # Task duration constraints (legacy function works for template too)
        add_task_duration_constraints(
            self.model,
            self.task_starts,
            self.task_ends,
            self.task_intervals,
            self.task_durations,
            self.problem,
        )

        # Optimized mode precedence constraints
        add_optimized_precedence_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )

        # Optimized mode machine assignment constraints
        add_optimized_assignment_constraints(
            self.model, self.task_assigned, self.task_durations, self.problem
        )

        # Optimized mode no overlap constraints (ONLY for capacity=1 machines)
        add_optimized_no_overlap_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.machine_intervals,
            self.problem,
        )

        # Machine capacity constraints (ONLY for machines with capacity > 1)
        # Uses AddCumulative which is necessary for parallel task scheduling
        add_machine_capacity_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem.machines,
            self.problem,
        )

        # WorkCell capacity constraints (physical workspace limitations)
        add_workcell_capacity_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem.work_cells,
            self.problem,
        )

        # Setup time constraints (if any setup times are defined)
        if self.setup_times:
            add_setup_time_constraints(
                self.model,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.setup_times,
                self.problem,
            )

        # Symmetry breaking constraints for identical jobs
        add_symmetry_breaking_constraints(self.model, self.task_starts, self.problem)

        # Optimized mode redundant constraints for better performance
        add_optimized_redundant_constraints(
            self.model, self.task_starts, self.task_ends, self.problem, self.horizon
        )

        # Sequence resource reservation constraints (exclusive sequence access)
        if self.sequence_job_intervals:
            add_sequence_reservation_constraints(
                self.model, self.sequence_job_intervals
            )

        # Unattended task constraints for business hours setup and 24/7 execution
        add_business_hours_setup_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )
        add_unattended_execution_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )
        add_weekend_optimization_constraints(
            self.model, self.task_starts, self.task_durations, self.problem
        )

        # Phase 2: Advanced skill-based operator assignment constraints
        if self.problem.operators and self.task_operator_assigned:
            # Add advanced skill matching with multi-operator support
            # and proficiency optimization
            add_advanced_skill_matching_constraints(
                self.model,
                self.task_starts,
                self.task_ends,
                self.task_operator_assigned,
                self.problem,
            )

            # Add shift calendar constraints if operator shifts are defined
            if self.problem.operator_shifts:
                add_shift_calendar_constraints(
                    self.model,
                    self.task_starts,
                    self.task_ends,
                    self.task_operator_assigned,
                    self.problem,
                )

        # User Story 3: Due date constraints and lateness penalties
        self.completion_times = add_due_date_enforcement_constraints(
            self.model, self.task_ends, self.problem, self.horizon
        )

        self.lateness_penalties = add_lateness_penalty_variables(
            self.model, self.completion_times, self.problem, self.horizon
        )

        # Add total lateness objective variable for template hierarchical optimization
        if self.lateness_penalties:
            total_lateness_var = create_total_lateness_objective_variable(
                self.model, self.lateness_penalties, self.horizon
            )
            self.objective_variables["total_lateness_enhanced"] = total_lateness_var

        # User Story 4: WIP limit constraints with adaptive adjustment
        wip_limits = {
            cell.cell_id: cell.effective_wip_limit for cell in self.problem.work_cells
        }

        self.wip_monitoring_vars = add_wip_limit_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem,
            wip_limits,
        )

        # Add adaptive WIP adjustment based on work cell utilization
        utilization_targets = {
            cell.cell_id: cell.target_utilization for cell in self.problem.work_cells
        }
        self.wip_adjustment_vars = add_adaptive_wip_adjustment_constraints(
            self.model, self.wip_monitoring_vars, self.problem, utilization_targets
        )

        # Add flow balance monitoring for cross-cell optimization
        self.flow_balance_vars = create_flow_balance_monitoring_variables(
            self.model, self.problem, self.horizon
        )

    def _add_legacy_constraints(self) -> None:
        """Add constraints for legacy job-based problems."""
        logger.info("Adding legacy constraints...")

        # Task duration constraints
        add_task_duration_constraints(
            self.model,
            self.task_starts,
            self.task_ends,
            self.task_intervals,
            self.task_durations,
            self.problem,
        )

        # Precedence constraints
        add_precedence_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )

        # Machine assignment constraints
        add_machine_assignment_constraints(
            self.model, self.task_assigned, self.task_durations, self.problem
        )

        # No overlap constraints (ONLY for capacity=1 machines)
        # High-capacity machines will use AddCumulative instead
        add_machine_no_overlap_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.machine_intervals,
            self.problem,
        )

        # Machine capacity constraints (ONLY for machines with capacity > 1)
        # Uses AddCumulative which is necessary for parallel task scheduling
        # but more expensive than no-overlap, so we only use it when needed
        add_machine_capacity_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem.machines,
            self.problem,
        )

        # WorkCell capacity constraints (physical workspace limitations)
        add_workcell_capacity_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem.work_cells,
            self.problem,
        )

        # Setup time constraints (if any setup times are defined)
        if self.setup_times:
            add_setup_time_constraints(
                self.model,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.setup_times,
                self.problem,
            )

        # Redundant constraints for better performance
        add_redundant_precedence_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )

        # Sequence resource reservation constraints (exclusive sequence access)
        if self.sequence_job_intervals:
            add_sequence_reservation_constraints(
                self.model, self.sequence_job_intervals
            )

        # Unattended task constraints for business hours setup and 24/7 execution
        add_business_hours_setup_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )
        add_unattended_execution_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )
        add_weekend_optimization_constraints(
            self.model, self.task_starts, self.task_durations, self.problem
        )

        # Phase 2: Advanced skill-based operator assignment constraints
        if self.problem.operators and self.task_operator_assigned:
            # Add advanced skill matching with multi-operator support
            # and proficiency optimization
            add_advanced_skill_matching_constraints(
                self.model,
                self.task_starts,
                self.task_ends,
                self.task_operator_assigned,
                self.problem,
            )

            # Add shift calendar constraints if operator shifts are defined
            if self.problem.operator_shifts:
                add_shift_calendar_constraints(
                    self.model,
                    self.task_starts,
                    self.task_ends,
                    self.task_operator_assigned,
                    self.problem,
                )

        # User Story 3: Due date constraints and lateness penalties (legacy mode)
        self.completion_times = add_due_date_enforcement_constraints(
            self.model, self.task_ends, self.problem, self.horizon
        )

        self.lateness_penalties = add_lateness_penalty_variables(
            self.model, self.completion_times, self.problem, self.horizon
        )

        # Add total lateness objective variable for multi-objective optimization
        if self.lateness_penalties:
            total_lateness_var = create_total_lateness_objective_variable(
                self.model, self.lateness_penalties, self.horizon
            )
            self.objective_variables["total_lateness_enhanced"] = total_lateness_var

        # User Story 4: WIP limit constraints with adaptive adjustment (legacy mode)
        wip_limits = {
            cell.cell_id: cell.effective_wip_limit for cell in self.problem.work_cells
        }

        self.wip_monitoring_vars = add_wip_limit_constraints(
            self.model,
            self.task_intervals,
            self.task_assigned,
            self.problem,
            wip_limits,
        )

        # Add adaptive WIP adjustment based on work cell utilization
        utilization_targets = {
            cell.cell_id: cell.target_utilization for cell in self.problem.work_cells
        }
        self.wip_adjustment_vars = add_adaptive_wip_adjustment_constraints(
            self.model, self.wip_monitoring_vars, self.problem, utilization_targets
        )

        # Add flow balance monitoring for cross-cell optimization
        self.flow_balance_vars = create_flow_balance_monitoring_variables(
            self.model, self.problem, self.horizon
        )

        # Phase 3: Multi-objective constraints
        if self.problem.multi_objective_config and self.objective_variables:
            self._add_multi_objective_constraints()

    def _add_multi_objective_constraints(self) -> None:
        """Add Phase 3 multi-objective optimization constraints."""
        logger.info("Adding multi-objective constraints...")

        config = self.problem.multi_objective_config
        if not config:
            return

        from src.solver.models.problem import OptimizationStrategy

        if config.strategy == OptimizationStrategy.LEXICOGRAPHICAL:
            add_lexicographical_objective_constraints(
                self.model,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.objective_variables,
                self.horizon,
            )
        elif config.strategy == OptimizationStrategy.WEIGHTED_SUM:
            add_weighted_sum_objective_constraints(
                self.model,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.objective_variables,
                self.horizon,
            )
        elif config.strategy == OptimizationStrategy.EPSILON_CONSTRAINT:
            add_epsilon_constraint_objective_constraints(
                self.model,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.objective_variables,
                self.horizon,
            )
        else:
            raise ValueError(
                f"Unsupported optimization strategy: {config.strategy}. "
                f"Supported strategies: {[s.value for s in OptimizationStrategy]}"
            )

        logger.info(f"Added {config.strategy.value} multi-objective constraints")

    def _add_optimality_constraint_to_main_model(
        self,
        objective_type: ObjectiveType,
        optimal_value: int,
    ) -> None:
        """Add constraint to maintain optimality of a previous objective.

        Args:
            objective_type: The objective type to constrain
            optimal_value: The optimal value that must be maintained

        """
        from src.solver.models.problem import ObjectiveType

        obj_var_name = self._get_objective_variable_name(objective_type)

        if obj_var_name in self.objective_variables:
            obj_var = self.objective_variables[obj_var_name]

            # Add constraint based on objective type
            if objective_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
                # For maximization, maintain the maximum value
                self.model.Add(obj_var >= optimal_value)
            else:
                # For minimization, maintain the minimum value
                self.model.Add(obj_var <= optimal_value)

            logger.info(
                f"Added optimality constraint: {obj_var_name} = {optimal_value}"
            )

    def _get_objective_variable_name(self, objective_type: ObjectiveType) -> str:
        """Get the variable name for an objective type."""
        mapping = {
            ObjectiveType.MINIMIZE_MAKESPAN: "makespan",
            ObjectiveType.MINIMIZE_TOTAL_LATENESS: "total_lateness",
            ObjectiveType.MINIMIZE_MAXIMUM_LATENESS: "maximum_lateness",
            ObjectiveType.MINIMIZE_TOTAL_COST: "total_cost",
            ObjectiveType.MINIMIZE_TOTAL_TARDINESS: "total_tardiness",
            ObjectiveType.MINIMIZE_WEIGHTED_COMPLETION_TIME: "weighted_completion_time",
            ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION: "machine_utilization",
            ObjectiveType.MINIMIZE_SETUP_TIME: "total_setup_time",
        }
        return mapping.get(objective_type, "unknown")

    def set_objective(self) -> None:
        """Set the objective function."""
        logger.info("Setting objective...")

        # Check if multi-objective optimization is configured
        if self.problem.multi_objective_config and self.objective_variables:
            # Multi-objective optimization handles its own objective setting
            logger.info(
                "Using multi-objective optimization - objectives set in constraints"
            )
            return

        # Optimized mode: Use hierarchical objective (total lateness > makespan > cost)
        if self.problem.is_optimized_mode:
            self._set_template_hierarchical_objective()
        else:
            # Default Phase 1 behavior: minimize makespan
            self._set_makespan_objective()

    def _set_makespan_objective(self) -> None:
        """Set single-objective makespan minimization (Phase 1 behavior)."""
        # Find the maximum end time across all tasks
        all_ends = []

        if self.problem.is_optimized_mode and self.problem.job_optimized_pattern:
            # Optimized mode: collect all instance task end times
            for instance in self.problem.job_instances:
                for (
                    optimized_task
                ) in self.problem.job_optimized_pattern.optimized_tasks:
                    instance_task_id = self.problem.get_instance_task_id(
                        instance.instance_id, optimized_task.optimized_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)
                    if task_key in self.task_ends:
                        all_ends.append(self.task_ends[task_key])
        else:
            # Unique mode: collect all job task end times
            for job in self.problem.jobs:
                for task in job.tasks:
                    task_key = (job.job_id, task.task_id)
                    all_ends.append(self.task_ends[task_key])

        # Create makespan variable
        makespan = self.model.NewIntVar(0, self.horizon, "makespan")
        for end_var in all_ends:
            self.model.Add(makespan >= end_var)

        # Check if we have high-capacity machines
        has_high_capacity = any(m.capacity > 1 for m in self.problem.machines)

        if has_high_capacity:
            # Calculate theoretical minimum for informational purposes
            if self.problem.is_optimized_mode and self.problem.job_optimized_pattern:
                # Optimized mode calculation
                pattern_min_work = sum(
                    min(mode.duration_time_units for mode in optimized_task.modes)
                    for optimized_task in (
                        self.problem.job_optimized_pattern.optimized_tasks
                    )
                )
                total_work = pattern_min_work * len(self.problem.job_instances)
            else:
                # Unique mode calculation
                total_work = sum(
                    min(mode.duration_time_units for mode in task.modes)
                    for job in self.problem.jobs
                    for task in job.tasks
                )

            total_capacity = sum(m.capacity for m in self.problem.machines)
            theoretical_min = (total_work + total_capacity - 1) // total_capacity

            logger.info(
                f"Objective: minimize makespan "
                f"(theoretical min: {theoretical_min} time units)"
            )

            if self.problem.is_optimized_mode:
                logger.info("Using template-based search hints")
            else:
                logger.info("Using search hints to encourage concurrent execution")

            # Add a hint to the solver about the expected makespan
            # This guides the search without making the problem infeasible
            self.model.AddHint(makespan, theoretical_min)
        else:
            logger.info("Objective: minimize makespan")

        # Minimize makespan
        self.model.Minimize(makespan)

    def _set_template_hierarchical_objective(self) -> None:
        """Set hierarchical objective: total lateness > makespan > cost."""
        logger.info(
            "Setting template hierarchical objective: total lateness > makespan > cost"
        )

        if not self.problem.job_optimized_pattern or not self.problem.job_instances:
            logger.warning(
                "Optimized mode problem missing pattern/instances - using makespan"
            )
            self._set_makespan_objective()
            return

        # Create objective variables for the hierarchical approach
        self._create_optimized_objective_variables()

        # Add objective definitions
        self._add_template_objective_definitions()

        # Set primary objective (highest priority: minimize total lateness)
        if "total_lateness" in self.objective_variables:
            self.model.Minimize(self.objective_variables["total_lateness"])
            logger.info(
                "Primary objective: minimize total lateness across all job instances"
            )
        else:
            logger.warning(
                "Total lateness variable not created - falling back to makespan"
            )
            self._set_makespan_objective()

    def _create_optimized_objective_variables(self) -> None:
        """Create objective variables for template hierarchical optimization."""
        # Total lateness (primary objective)
        max_total_lateness = self.horizon * len(self.problem.job_instances)
        self.objective_variables["total_lateness"] = self.model.NewIntVar(
            0, max_total_lateness, "total_lateness"
        )

        # Makespan (secondary objective)
        self.objective_variables["makespan"] = self.model.NewIntVar(
            0, self.horizon, "makespan"
        )

        # Total cost (tertiary objective)
        max_total_cost = self._calculate_max_template_cost()
        self.objective_variables["total_cost"] = self.model.NewIntVar(
            0, max_total_cost, "total_cost"
        )

        logger.info("Created template objective variables: lateness, makespan, cost")

    def _add_template_objective_definitions(self) -> None:
        """Add constraint definitions for template objective variables."""
        # Define total lateness objective
        self._define_template_total_lateness()

        # Define makespan objective
        self._define_template_makespan()

        # Define total cost objective
        self._define_template_total_cost()

    def _define_template_total_lateness(self) -> None:
        """Define total lateness as sum of job instance lateness values."""
        lateness_terms = []

        for instance in self.problem.job_instances:
            # Find last task end time for this instance
            instance_end_times = []
            if self.problem.job_optimized_pattern:
                for (
                    optimized_task
                ) in self.problem.job_optimized_pattern.optimized_tasks:
                    instance_task_id = self.problem.get_instance_task_id(
                        instance.instance_id, optimized_task.optimized_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)
                    if task_key in self.task_ends:
                        instance_end_times.append(self.task_ends[task_key])

            if instance_end_times:
                # Create job completion time variable
                job_completion = self.model.NewIntVar(
                    0, self.horizon, f"completion_{instance.instance_id}"
                )
                self.model.AddMaxEquality(job_completion, instance_end_times)

                # Calculate due date as time units from problem start (relative)
                from datetime import UTC, datetime

                # Use fixed reference time for deterministic behavior
                problem_start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
                if instance.due_date is not None:
                    due_date_delta = instance.due_date - problem_start
                    due_date_units = max(
                        0, int(due_date_delta.total_seconds() / 900)
                    )  # 900 seconds = 15 minutes
                else:
                    continue  # Skip instances without due dates

                # Create lateness variable (can be negative for early completion)
                job_lateness = self.model.NewIntVar(
                    -self.horizon, self.horizon, f"lateness_{instance.instance_id}"
                )
                self.model.Add(job_lateness == job_completion - due_date_units)

                lateness_terms.append(job_lateness)

        if lateness_terms and "total_lateness" in self.objective_variables:
            self.model.Add(
                self.objective_variables["total_lateness"] == sum(lateness_terms)
            )
            logger.info(
                f"Defined total lateness objective with {len(lateness_terms)} "
                "job instances"
            )

    def _define_template_makespan(self) -> None:
        """Define makespan as maximum task end time across all template instances."""
        all_ends = []

        for instance in self.problem.job_instances:
            if self.problem.job_optimized_pattern:
                for (
                    optimized_task
                ) in self.problem.job_optimized_pattern.optimized_tasks:
                    instance_task_id = self.problem.get_instance_task_id(
                        instance.instance_id, optimized_task.optimized_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)
                    if task_key in self.task_ends:
                        all_ends.append(self.task_ends[task_key])

        if all_ends and "makespan" in self.objective_variables:
            makespan_var = self.objective_variables["makespan"]
            for end_var in all_ends:
                self.model.Add(makespan_var >= end_var)
            logger.info(
                f"Defined makespan objective with {len(all_ends)} task end times"
            )

    def _define_template_total_cost(self) -> None:
        """Define total cost including machine costs for template-based scheduling."""
        cost_terms = []

        # Machine costs based on usage time
        for machine in self.problem.machines:
            if machine.cost_per_hour > 0:
                machine_usage_time = self.model.NewIntVar(
                    0,
                    self.horizon * len(self.problem.job_instances),
                    f"usage_{machine.resource_id}",
                )

                # Sum usage time for this machine across all assigned template tasks
                usage_terms = []
                for task_key, assign_var in self.task_assigned.items():
                    job_id, task_id, machine_id = task_key
                    if (
                        machine_id == machine.resource_id
                        and task_key[:2] in self.task_ends
                    ):
                        task_duration = (
                            self.task_ends[task_key[:2]]
                            - self.task_starts[task_key[:2]]
                        )
                        # Only count duration if task is assigned to this machine
                        usage_contribution = self.model.NewIntVar(
                            0,
                            self.horizon,
                            f"usage_contrib_{job_id}_{task_id}_{machine_id}",
                        )
                        self.model.Add(
                            usage_contribution == task_duration
                        ).OnlyEnforceIf(assign_var)
                        self.model.Add(usage_contribution == 0).OnlyEnforceIf(
                            assign_var.Not()
                        )
                        usage_terms.append(usage_contribution)

                if usage_terms:
                    self.model.Add(machine_usage_time == sum(usage_terms))

                    # Convert time units to hours and apply cost rate
                    # Scale by 100 to maintain precision with integers
                    cost_per_time_unit = int(
                        machine.cost_per_hour * 100 / 4
                    )  # 4 time units per hour
                    machine_cost = self.model.NewIntVar(
                        0,
                        self.horizon
                        * len(self.problem.job_instances)
                        * cost_per_time_unit,
                        f"cost_{machine.resource_id}",
                    )
                    self.model.Add(
                        machine_cost == machine_usage_time * cost_per_time_unit
                    )
                    cost_terms.append(machine_cost)

        if cost_terms and "total_cost" in self.objective_variables:
            self.model.Add(self.objective_variables["total_cost"] == sum(cost_terms))
            logger.info(
                f"Defined total cost objective with {len(cost_terms)} "
                "machine cost terms"
            )
        elif "total_cost" in self.objective_variables:
            # No machines with costs - set to 0
            self.model.Add(self.objective_variables["total_cost"] == 0)

    def _calculate_max_template_cost(self) -> int:
        """Calculate maximum possible total cost for template-based scheduling."""
        max_cost = 0
        instance_count = len(self.problem.job_instances)

        for machine in self.problem.machines:
            if machine.cost_per_hour > 0:
                # Assume all instances could use this machine for entire horizon
                machine_max_cost = int(
                    machine.cost_per_hour
                    * self.horizon
                    * instance_count
                    * machine.capacity
                    / 4
                    * 100
                )  # Scale by 100
                max_cost += machine_max_cost

        return max_cost

    def add_search_strategy(self) -> None:
        """Add search strategy to guide the solver."""
        if self.problem.is_optimized_mode:
            self._add_template_search_strategy()
        else:
            self._add_legacy_search_strategy()

    def _add_template_search_strategy(self) -> None:
        """Add optimized search strategy for template-based problems."""
        if not self.problem.job_optimized_pattern:
            return

        has_high_capacity = any(m.capacity > 1 for m in self.problem.machines)
        has_precedences = (
            len(self.problem.job_optimized_pattern.optimized_precedences) > 0
        )

        # For template-based problems, prioritize scheduling by template task order
        # This takes advantage of identical structure across instances

        # Group variables by template task, then by instance
        optimized_task_groups = []

        for optimized_task in self.problem.job_optimized_pattern.optimized_tasks:
            task_group = []
            for instance in self.problem.job_instances:
                instance_task_id = self.problem.get_instance_task_id(
                    instance.instance_id, optimized_task.optimized_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in self.task_starts:
                    task_group.append(self.task_starts[task_key])

            if task_group:
                optimized_task_groups.append(task_group)

        # Strategy: Schedule template tasks in order, with symmetry breaking
        for _i, task_group in enumerate(optimized_task_groups):
            if has_high_capacity and not has_precedences:
                # For parallel machines without precedences, schedule all instances
                # concurrently
                self.model.AddDecisionStrategy(
                    task_group, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
                )
            else:
                # For sequential scheduling, use earliest start heuristic
                self.model.AddDecisionStrategy(
                    task_group, cp_model.CHOOSE_LOWEST_MIN, cp_model.SELECT_MIN_VALUE
                )

        logger.info(
            f"Search strategy: template-based scheduling for "
            f"{len(self.problem.job_instances)} instances with "
            f"{len(optimized_task_groups)} optimized tasks"
        )

    def _add_legacy_search_strategy(self) -> None:
        """Add search strategy for legacy job-based problems."""
        has_high_capacity = any(m.capacity > 1 for m in self.problem.machines)

        if has_high_capacity and len(self.problem.precedences) == 0:
            # For problems without precedences and with high-capacity machines,
            # use a strategy that encourages concurrent starts

            # Group tasks by their possible start times
            # Tasks that can start at time 0 should be scheduled together
            early_start_tasks = []
            other_tasks = []

            for job in self.problem.jobs:
                for task in job.tasks:
                    task_key = (job.job_id, task.task_id)
                    start_var = self.task_starts[task_key]

                    # Check if this task can start at time 0
                    if start_var.Proto().domain[0] == 0:
                        early_start_tasks.append(start_var)
                    else:
                        other_tasks.append(start_var)

            # Strategy 1: Schedule early tasks first, all at the same time
            if early_start_tasks:
                # Sort by task ID to ensure consistent ordering
                early_start_tasks.sort(key=lambda x: str(x))

                # Use CHOOSE_FIRST with SELECT_MIN_VALUE to start them all at 0
                self.model.AddDecisionStrategy(
                    early_start_tasks, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
                )

            # Strategy 2: Then schedule remaining tasks
            if other_tasks:
                self.model.AddDecisionStrategy(
                    other_tasks, cp_model.CHOOSE_LOWEST_MIN, cp_model.SELECT_MIN_VALUE
                )

            logger.info(
                "Search strategy: concurrent batching for high-capacity machines"
            )
        else:
            # Standard strategy for problems with precedences or single-capacity
            task_start_vars = []
            for job in self.problem.jobs:
                for task in job.tasks:
                    task_key = (job.job_id, task.task_id)
                    task_start_vars.append(self.task_starts[task_key])

            self.model.AddDecisionStrategy(
                task_start_vars, cp_model.CHOOSE_LOWEST_MIN, cp_model.SELECT_MIN_VALUE
            )

            logger.info("Search strategy: standard sequential scheduling")

    def solve(self, time_limit: int = 60) -> dict:
        """Solve the scheduling problem.

        Args:
            time_limit: Maximum solving time in seconds

        Returns:
            Solution dictionary with schedule and statistics

        """
        logger.info(f"\nSolving with time limit: {time_limit} seconds...")

        # Optimized mode problems use hierarchical optimization
        # (lateness > makespan > cost)
        if self.problem.is_optimized_mode:
            return self.solve_optimized_hierarchical(time_limit)

        # Create variables and constraints
        self.create_variables()
        self.add_constraints()
        self.set_objective()
        self.add_search_strategy()

        # Configure solver
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit
        self.solver.parameters.num_search_workers = 8  # Use parallel search
        self.solver.parameters.log_search_progress = True

        # Solve
        logger.info("\nStarting solver...")
        status = self.solver.Solve(self.model)

        logger.info(f"\nSolver status: {self.solver.StatusName(status)}")

        # Extract solution
        solution = extract_solution(
            self.solver,
            self.model,
            self.problem,
            self.task_starts,
            self.task_ends,
            self.task_assigned,
            setup_times=self.setup_times,
        )

        # Add multi-objective values if configured
        if self.problem.multi_objective_config and self.objective_variables:
            objective_solution = calculate_objective_values(
                self.solver,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                self.objective_variables,
                self.horizon,
            )

            # Add multi-objective values to the solution
            solution["multi_objective"] = {
                "makespan": objective_solution.makespan,
                "total_lateness": objective_solution.total_lateness,
                "maximum_lateness": objective_solution.maximum_lateness,
                "total_cost": objective_solution.total_cost,
                "total_tardiness": objective_solution.total_tardiness,
                "weighted_completion_time": objective_solution.weighted_completion_time,
                "machine_utilization": objective_solution.machine_utilization,
                "total_setup_time": objective_solution.total_setup_time,
                "primary_objective_value": objective_solution.objective_value,
                "strategy": self.problem.multi_objective_config.strategy.value,
            }

        return solution

    def solve_lexicographic(self, time_limit_per_phase: int = 60) -> dict:
        """Solve using lexicographic multi-objective optimization.

        Optimizes objectives in priority order: each objective is optimized subject
        to the constraint that higher-priority objectives remain at optimal values.

        For the requested ordering: minimize total lateness > makespan > cost

        This implementation uses a simplified approach where we solve sequentially
        and add constraints to maintain optimality of higher-priority objectives.

        Args:
            time_limit_per_phase: Time limit for each optimization phase in seconds

        Returns:
            Solution dictionary with lexicographic optimization results

        """
        if not self.problem.multi_objective_config:
            logger.warning(
                "Lexicographic optimization requires multi-objective configuration"
            )
            return {"error": "No multi-objective configuration found"}

        from src.solver.models.problem import ObjectiveType, OptimizationStrategy

        config = self.problem.multi_objective_config
        if config.strategy != OptimizationStrategy.LEXICOGRAPHICAL:
            logger.warning("Configuration strategy is not lexicographical")
            return {"error": "Lexicographical strategy required"}

        logger.info("\nSolving with lexicographic multi-objective optimization...")

        # Create variables and constraints (shared across all phases)
        self.create_variables()
        self.add_constraints()
        self.add_search_strategy()

        # Get objectives sorted by priority (1 = highest priority)
        sorted_objectives = config.sorted_objectives
        obj_order = [obj.objective_type.value for obj in sorted_objectives]
        logger.info(f"Optimization order: {obj_order}")

        # Storage for optimal values from each phase
        optimal_values: dict[ObjectiveType, int] = {}
        phase_solutions: dict[int, ObjectiveSolution] = {}

        # Solve each objective in priority order
        for phase, obj_weight in enumerate(sorted_objectives, 1):
            logger.info(
                f"\n=== Phase {phase}: Optimizing {obj_weight.objective_type.value} ==="
            )

            # Add constraints from previous phases to maintain optimality
            for prev_obj_type, prev_optimal_value in optimal_values.items():
                logger.info(
                    f"Constraining {prev_obj_type.value} = {prev_optimal_value}"
                )
                self._add_optimality_constraint_to_main_model(
                    prev_obj_type, prev_optimal_value
                )

            # Set the objective for this phase
            obj_var_name = self._get_objective_variable_name(obj_weight.objective_type)
            if obj_var_name in self.objective_variables:
                # Clear any previous objective
                self.model.ClearObjective()

                if (
                    obj_weight.objective_type
                    == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION
                ):
                    self.model.Maximize(self.objective_variables[obj_var_name])
                else:
                    self.model.Minimize(self.objective_variables[obj_var_name])

            # Solve this phase
            phase_solver = cp_model.CpSolver()
            phase_solver.parameters.max_time_in_seconds = time_limit_per_phase
            phase_solver.parameters.num_search_workers = 8
            phase_solver.parameters.log_search_progress = True

            logger.info(f"Solving phase {phase}...")
            status = phase_solver.Solve(self.model)

            if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                logger.error(
                    f"Phase {phase} failed with status: "
                    f"{phase_solver.StatusName(status)}"
                )
                return {
                    "error": f"Phase {phase} optimization failed",
                    "status": phase_solver.StatusName(status),
                    "failed_objective": obj_weight.objective_type.value,
                }

            # Extract the optimal value for this objective
            if obj_var_name in self.objective_variables:
                optimal_value = phase_solver.Value(
                    self.objective_variables[obj_var_name]
                )
                optimal_values[obj_weight.objective_type] = optimal_value
                logger.info(f"Phase {phase} optimal value: {optimal_value}")

                # Store phase solution for analysis
                phase_solution = calculate_objective_values(
                    phase_solver,
                    self.problem,
                    self.task_starts,
                    self.task_ends,
                    self.task_assigned,
                    self.objective_variables,
                    self.horizon,
                )
                phase_solutions[phase] = phase_solution

            # Update the main solver with the final solution
            self.solver = phase_solver

        # Extract the final solution
        if self.solver:
            solution = extract_solution(
                self.solver,
                self.model,
                self.problem,
                self.task_starts,
                self.task_ends,
                self.task_assigned,
                setup_times=self.setup_times,
            )

            # Add lexicographic multi-objective results
            final_objectives = phase_solutions.get(len(sorted_objectives))
            if final_objectives:
                solution["multi_objective"] = {
                    "strategy": "lexicographical",
                    "makespan": final_objectives.makespan,
                    "total_lateness": final_objectives.total_lateness,
                    "maximum_lateness": final_objectives.maximum_lateness,
                    "total_cost": final_objectives.total_cost,
                    "total_tardiness": final_objectives.total_tardiness,
                    "weighted_completion_time": (
                        final_objectives.weighted_completion_time
                    ),
                    "machine_utilization": final_objectives.machine_utilization,
                    "total_setup_time": final_objectives.total_setup_time,
                    "optimization_order": [
                        obj.objective_type.value for obj in sorted_objectives
                    ],
                    "phase_results": [
                        {
                            "phase": phase,
                            "objective": obj.objective_type.value,
                            "optimal_value": optimal_values.get(obj.objective_type),
                            "solve_time": phase_sol.solve_time,
                            "status": phase_sol.solver_status,
                        }
                        for phase, (obj, phase_sol) in enumerate(
                            zip(
                                sorted_objectives,
                                phase_solutions.values(),
                                strict=False,
                            ),
                            1,
                        )
                    ],
                    "lexicographic_optimality": True,
                }

            return solution

        return {"error": "No solution found in any phase"}

    def solve_optimized_hierarchical(self, time_limit: int = 60) -> dict:
        """Solve template-based problems with hierarchical optimization.

        Objective order: total lateness > makespan > cost.

        This method implements a 3-phase lexicographical optimization specifically
        optimized for template-based scheduling problems.

        Args:
            time_limit: Total time limit in seconds (divided among 3 phases)

        Returns:
            Solution dictionary with hierarchical optimization results

        """
        logger.info("\nSolving template-based problem with hierarchical optimization:")
        logger.info("Phase 1: Minimize total lateness")
        logger.info("Phase 2: Minimize makespan (subject to optimal lateness)")
        logger.info("Phase 3: Minimize cost (subject to optimal lateness and makespan)")

        # Allocate time across phases: 50% for lateness, 30% for makespan, 20% for cost
        phase_times = [
            int(time_limit * 0.5),  # Phase 1: Total lateness (most important)
            int(time_limit * 0.3),  # Phase 2: Makespan
            int(time_limit * 0.2),  # Phase 3: Cost
        ]

        # Create variables and constraints once
        self.create_variables()
        self.add_constraints()
        self.add_search_strategy()

        solutions = {}

        # Phase 1: Minimize total lateness
        logger.info(
            f"\n=== PHASE 1: Minimize Total Lateness "
            f"(time limit: {phase_times[0]}s) ==="
        )

        # Set total lateness as primary objective
        self._create_optimized_objective_variables()
        self._add_template_objective_definitions()

        if "total_lateness" in self.objective_variables:
            self.model.Minimize(self.objective_variables["total_lateness"])

            # Configure and solve
            self.solver = cp_model.CpSolver()
            self.solver.parameters.max_time_in_seconds = phase_times[0]
            self.solver.parameters.num_search_workers = 8
            self.solver.parameters.log_search_progress = True

            status = self.solver.Solve(self.model)
            logger.info(f"Phase 1 status: {self.solver.StatusName(status)}")

            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                optimal_lateness = self.solver.Value(
                    self.objective_variables["total_lateness"]
                )
                logger.info(f"Optimal total lateness: {optimal_lateness}")

                # Constrain total lateness to optimal value for subsequent phases
                self.model.Add(
                    self.objective_variables["total_lateness"] <= optimal_lateness
                )

                solutions["phase1"] = {
                    "total_lateness": optimal_lateness,
                    "status": self.solver.StatusName(status),
                    "solve_time": self.solver.WallTime(),
                }

                # Phase 2: Minimize makespan subject to optimal lateness
                logger.info(
                    f"\n=== PHASE 2: Minimize Makespan "
                    f"(time limit: {phase_times[1]}s) ==="
                )
                logger.info(f"Subject to: total lateness <= {optimal_lateness}")

                if "makespan" in self.objective_variables:
                    self.model.Minimize(self.objective_variables["makespan"])

                    # Configure and solve
                    self.solver = cp_model.CpSolver()
                    self.solver.parameters.max_time_in_seconds = phase_times[1]
                    self.solver.parameters.num_search_workers = 8
                    self.solver.parameters.log_search_progress = True

                    status = self.solver.Solve(self.model)
                    logger.info(f"Phase 2 status: {self.solver.StatusName(status)}")

                    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                        optimal_makespan = self.solver.Value(
                            self.objective_variables["makespan"]
                        )
                        logger.info(f"Optimal makespan: {optimal_makespan}")

                        # Constrain makespan to optimal value for final phase
                        self.model.Add(
                            self.objective_variables["makespan"] <= optimal_makespan
                        )

                        solutions["phase2"] = {
                            "makespan": optimal_makespan,
                            "status": self.solver.StatusName(status),
                            "solve_time": self.solver.WallTime(),
                        }

                        # Phase 3: Minimize cost subject to optimal lateness/makespan
                        logger.info(
                            f"\n=== PHASE 3: Minimize Cost "
                            f"(time limit: {phase_times[2]}s) ==="
                        )
                        logger.info(
                            f"Subject to: total lateness <= {optimal_lateness}, "
                            f"makespan <= {optimal_makespan}"
                        )

                        if "total_cost" in self.objective_variables:
                            self.model.Minimize(self.objective_variables["total_cost"])

                            # Configure and solve
                            self.solver = cp_model.CpSolver()
                            self.solver.parameters.max_time_in_seconds = phase_times[2]
                            self.solver.parameters.num_search_workers = 8
                            self.solver.parameters.log_search_progress = True

                            status = self.solver.Solve(self.model)
                            logger.info(
                                f"Phase 3 status: {self.solver.StatusName(status)}"
                            )

                            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                                optimal_cost = (
                                    self.solver.Value(
                                        self.objective_variables["total_cost"]
                                    )
                                    / 100.0
                                )  # Unscale
                                logger.info(f"Optimal cost: ${optimal_cost:.2f}")

                                solutions["phase3"] = {
                                    "total_cost": optimal_cost,
                                    "status": self.solver.StatusName(status),
                                    "solve_time": self.solver.WallTime(),
                                }

                                # Extract final solution
                                solution = extract_solution(
                                    self.solver,
                                    self.model,
                                    self.problem,
                                    self.task_starts,
                                    self.task_ends,
                                    self.task_assigned,
                                    setup_times=self.setup_times,
                                )

                                # Add hierarchical objective values
                                solution["hierarchical_optimization"] = {
                                    "total_lateness": optimal_lateness,
                                    "makespan": optimal_makespan,
                                    "total_cost": optimal_cost,
                                    "phase_results": solutions,
                                    "optimization_strategy": "hierarchical_template",
                                    "objective_priority": [
                                        "total_lateness",
                                        "makespan",
                                        "total_cost",
                                    ],
                                }

                                logger.info(
                                    "\n=== HIERARCHICAL OPTIMIZATION COMPLETE ==="
                                )
                                logger.info(
                                    f"Final solution: lateness={optimal_lateness}, "
                                    f"makespan={optimal_makespan}, "
                                    f"cost=${optimal_cost:.2f}"
                                )

                                return solution

        # If any phase fails, fall back to regular solve
        logger.warning(
            "Hierarchical optimization failed - falling back to makespan minimization"
        )
        return self._solve_fallback_makespan(time_limit)

    def _solve_fallback_makespan(self, time_limit: int) -> dict:
        """Fallback to simple makespan minimization for templates."""
        # Clear any previous objectives
        self.model = cp_model.CpModel()

        # Recreate basic model
        self.create_variables()
        self.add_constraints()
        self._set_makespan_objective()
        self.add_search_strategy()

        # Solve with makespan objective
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit
        self.solver.parameters.num_search_workers = 8
        self.solver.parameters.log_search_progress = True

        status = self.solver.Solve(self.model)
        logger.info(f"Fallback status: {self.solver.StatusName(status)}")

        return extract_solution(
            self.solver,
            self.model,
            self.problem,
            self.task_starts,
            self.task_ends,
            self.task_assigned,
            setup_times=self.setup_times,
        )

    def solve_pareto_optimal(self, time_limit_per_solve: int = 30) -> dict:
        """Solve for Pareto-optimal solutions.

        Finds multiple non-dominated solutions exploring trade-offs between objectives.

        Args:
            time_limit_per_solve: Time limit for each individual solve in seconds

        Returns:
            Dictionary containing Pareto frontier and trade-off analysis

        """
        if not self.problem.multi_objective_config:
            logger.warning("Pareto optimization requires multi-objective configuration")
            return {"error": "No multi-objective configuration found"}

        logger.info("\nSolving for Pareto-optimal solutions...")

        # Create variables and constraints (but don't set objective yet)
        self.create_variables()
        self.add_constraints()
        self.add_search_strategy()

        # Find Pareto frontier
        frontier = find_pareto_frontier(
            self.problem,
            self.task_starts,
            self.task_ends,
            self.task_assigned,
            self.horizon,
            time_limit_per_solve,
        )

        # Analyze trade-offs
        analysis = analyze_trade_offs(frontier)

        # Get recommended solution
        recommended = recommend_solution(frontier)

        return {
            "pareto_frontier": {
                "solution_count": frontier.solution_count,
                "objective_types": [obj.value for obj in frontier.objective_types],
                "solutions": [
                    {
                        "objectives": {
                            "makespan": sol.objectives.makespan,
                            "total_lateness": sol.objectives.total_lateness,
                            "maximum_lateness": sol.objectives.maximum_lateness,
                            "total_cost": sol.objectives.total_cost,
                            "total_tardiness": sol.objectives.total_tardiness,
                            "weighted_completion_time": (
                                sol.objectives.weighted_completion_time
                            ),
                            "machine_utilization": sol.objectives.machine_utilization,
                            "total_setup_time": sol.objectives.total_setup_time,
                        }
                    }
                    for sol in frontier.solutions
                ],
            },
            "trade_off_analysis": analysis.get_trade_off_summary(),
            "recommended_solution": (
                {
                    "objectives": {
                        "makespan": recommended.objectives.makespan,
                        "total_lateness": recommended.objectives.total_lateness,
                        "maximum_lateness": recommended.objectives.maximum_lateness,
                        "total_cost": recommended.objectives.total_cost,
                        "total_tardiness": recommended.objectives.total_tardiness,
                        "weighted_completion_time": (
                            recommended.objectives.weighted_completion_time
                        ),
                        "machine_utilization": (
                            recommended.objectives.machine_utilization
                        ),
                        "total_setup_time": recommended.objectives.total_setup_time,
                    }
                }
                if recommended
                else None
            ),
        }


def main() -> dict:
    """Execute the solver testing workflow."""
    # Load test problem
    logger.info("Loading problem from database...")
    problem = load_test_problem()

    # Example setup times (in 15-minute intervals)
    # Format: (predecessor_task_id, successor_task_id, machine_id) -> setup_time
    setup_times: dict[tuple[str, str, str], int] = {
        # Add your setup times here if needed
        # Example: ("task_1", "task_2", "machine_1"): 2,  # 30 minutes setup
    }

    # Note: Machine capacities are defined in the database
    # Machines with capacity > 1 can run multiple tasks simultaneously
    # The solver will automatically use AddCumulative constraints for these

    # Create and run solver
    solver = FreshSolver(problem, setup_times=setup_times)
    solution = solver.solve(time_limit=30)

    # Print results
    print_solution_summary(solution)

    return solution


if __name__ == "__main__":
    main()
