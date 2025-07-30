"""Fresh OR-Tools CP-SAT Solver - Phase 1 Implementation.

Handles basic scheduling with timing, precedence, and machine assignment.
"""

import logging
from collections import defaultdict

from ortools.sat.python import cp_model

from src.data.loaders.database import load_test_problem
from src.solver.constraints.phase1 import (
    add_machine_assignment_constraints,
    add_machine_capacity_constraints,
    add_machine_no_overlap_constraints,
    add_precedence_constraints,
    add_redundant_precedence_constraints,
    add_setup_time_constraints,
    add_symmetry_breaking_constraints,
    add_task_duration_constraints,
    add_template_assignment_constraints,
    add_template_no_overlap_constraints,
    add_template_precedence_constraints,
    add_template_redundant_constraints,
)

# Type imports - using Any for now as OR-Tools types aren't directly importable
from src.solver.models.problem import SchedulingProblem
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

        # Solver parameters
        self.horizon = calculate_horizon(problem)
        self.solver: cp_model.CpSolver | None = None

    def create_variables(self) -> None:
        """Create all decision variables for the model."""
        logger.info("Creating decision variables...")

        if self.problem.is_template_based:
            self._create_template_variables()
        else:
            self._create_legacy_variables()

        logger.info(f"Created {len(self.task_starts)} task timing variables")
        logger.info(f"Created {len(self.task_assigned)} assignment variables")

    def _create_template_variables(self) -> None:
        """Create variables for template-based problems."""
        if not self.problem.job_template or not self.problem.job_instances:
            logger.warning("Template-based problem missing template or instances")
            return

        template = self.problem.job_template
        instances = self.problem.job_instances

        logger.info(
            f"Creating template variables for {len(instances)} instances of "
            f"{template.task_count} tasks"
        )

        # For each job instance, create variables for each template task
        for instance in instances:
            for template_task in template.template_tasks:
                # Generate task key for this instance-template combination
                instance_task_id = self.problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)

                # Calculate bounds
                earliest_start = 0
                # For template tasks, we use a simplified latest start calculation
                # Could be enhanced with template precedence analysis
                latest_start = max(0, self.horizon - template_task.min_duration // 15)

                # Timing variables
                self.task_starts[task_key] = self.model.NewIntVar(
                    earliest_start,
                    latest_start,
                    f"start_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}",
                )

                # Duration variable (constrained by machine mode selection)
                min_duration = min(
                    mode.duration_time_units for mode in template_task.modes
                )
                max_duration = max(
                    mode.duration_time_units for mode in template_task.modes
                )

                self.task_durations[task_key] = self.model.NewIntVar(
                    min_duration,
                    max_duration,
                    f"duration_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}",
                )

                # End variable
                self.task_ends[task_key] = self.model.NewIntVar(
                    earliest_start + min_duration,
                    min(self.horizon, latest_start + max_duration),
                    f"end_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}",
                )

                # Interval variable
                self.task_intervals[task_key] = self.model.NewIntervalVar(
                    self.task_starts[task_key],
                    self.task_durations[task_key],
                    self.task_ends[task_key],
                    f"interval_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}",
                )

                # Machine assignment variables for each mode
                for mode in template_task.modes:
                    machine_key = (
                        instance.instance_id,
                        instance_task_id,
                        mode.machine_resource_id,
                    )
                    self.task_assigned[machine_key] = self.model.NewBoolVar(
                        f"assigned_{instance.instance_id[:8]}_{template_task.template_task_id[:8]}_{mode.machine_resource_id[:8]}"
                    )

    def _create_legacy_variables(self) -> None:
        """Create variables for legacy job-based problems."""
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

    def add_constraints(self) -> None:
        """Add all Phase 1 constraints to the model."""
        logger.info("Adding constraints...")

        if self.problem.is_template_based:
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

        # Template-optimized precedence constraints
        add_template_precedence_constraints(
            self.model, self.task_starts, self.task_ends, self.problem
        )

        # Template-optimized machine assignment constraints
        add_template_assignment_constraints(
            self.model, self.task_assigned, self.task_durations, self.problem
        )

        # Template-optimized no overlap constraints (ONLY for capacity=1 machines)
        add_template_no_overlap_constraints(
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

        # Template-specific redundant constraints for better performance
        add_template_redundant_constraints(
            self.model, self.task_starts, self.task_ends, self.problem, self.horizon
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

    def set_objective(self) -> None:
        """Set the objective function - minimize makespan for Phase 1."""
        logger.info("Setting objective...")

        # Find the maximum end time across all tasks
        all_ends = []

        if self.problem.is_template_based and self.problem.job_template:
            # Template-based: collect all instance task end times
            for instance in self.problem.job_instances:
                for template_task in self.problem.job_template.template_tasks:
                    instance_task_id = self.problem.get_instance_task_id(
                        instance.instance_id, template_task.template_task_id
                    )
                    task_key = (instance.instance_id, instance_task_id)
                    if task_key in self.task_ends:
                        all_ends.append(self.task_ends[task_key])
        else:
            # Legacy: collect all job task end times
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
            if self.problem.is_template_based and self.problem.job_template:
                # Template-based calculation
                template_min_work = sum(
                    min(mode.duration_time_units for mode in template_task.modes)
                    for template_task in self.problem.job_template.template_tasks
                )
                total_work = template_min_work * len(self.problem.job_instances)
            else:
                # Legacy calculation
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

            if self.problem.is_template_based:
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

    def add_search_strategy(self) -> None:
        """Add search strategy to guide the solver."""
        if self.problem.is_template_based:
            self._add_template_search_strategy()
        else:
            self._add_legacy_search_strategy()

    def _add_template_search_strategy(self) -> None:
        """Add optimized search strategy for template-based problems."""
        if not self.problem.job_template:
            return

        has_high_capacity = any(m.capacity > 1 for m in self.problem.machines)
        has_precedences = len(self.problem.job_template.template_precedences) > 0

        # For template-based problems, prioritize scheduling by template task order
        # This takes advantage of identical structure across instances

        # Group variables by template task, then by instance
        template_task_groups = []

        for template_task in self.problem.job_template.template_tasks:
            task_group = []
            for instance in self.problem.job_instances:
                instance_task_id = self.problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)
                if task_key in self.task_starts:
                    task_group.append(self.task_starts[task_key])

            if task_group:
                template_task_groups.append(task_group)

        # Strategy: Schedule template tasks in order, with symmetry breaking
        for _i, task_group in enumerate(template_task_groups):
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
            f"{len(template_task_groups)} template tasks"
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

        return solution


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
