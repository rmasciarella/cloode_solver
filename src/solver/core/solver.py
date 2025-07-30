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
    add_task_duration_constraints,
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
        self.task_starts = {}  # Dict[Tuple[str, str], IntVar]
        self.task_ends = {}  # Dict[Tuple[str, str], IntVar]
        self.task_durations = {}  # Dict[Tuple[str, str], IntVar]
        self.task_intervals = {}  # Dict[Tuple[str, str], IntervalVar]
        self.task_assigned = {}  # Dict[Tuple[str, str, str], BoolVar]
        self.machine_intervals = defaultdict(list)  # Dict[str, List[IntervalVar]]

        # Solver parameters
        self.horizon = calculate_horizon(problem)
        self.solver = None

    def create_variables(self) -> None:
        """Create all decision variables for the model."""
        logger.info("Creating decision variables...")

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

        logger.info(f"Created {len(self.task_starts)} task timing variables")
        logger.info(f"Created {len(self.task_assigned)} assignment variables")

    def add_constraints(self) -> None:
        """Add all Phase 1 constraints to the model."""
        logger.info("Adding constraints...")

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

        logger.info("All constraints added")

    def set_objective(self) -> None:
        """Set the objective function - minimize makespan for Phase 1."""
        logger.info("Setting objective...")

        # Find the maximum end time across all tasks
        all_ends = []
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


def main():
    """Execute the solver testing workflow."""
    # Load test problem
    logger.info("Loading problem from database...")
    problem = load_test_problem()

    # Example setup times (in 15-minute intervals)
    # Format: (predecessor_task_id, successor_task_id, machine_id) -> setup_time
    setup_times = {
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
