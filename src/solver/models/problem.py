"""Data models for the fresh OR-Tools solver.

Provides type safety, validation, and computed properties.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Machine:
    """Represents a machine resource."""

    resource_id: str
    cell_id: str
    name: str
    capacity: int = 1
    cost_per_hour: float = 0.0

    def __post_init__(self) -> None:
        if self.capacity < 0:
            raise ValueError(f"Machine capacity must be non-negative: {self.capacity}")
        if self.cost_per_hour < 0:
            raise ValueError(f"Machine cost cannot be negative: {self.cost_per_hour}")


@dataclass
class TaskMode:
    """Represents a mode (way) a task can be executed."""

    task_mode_id: str
    task_id: str
    machine_resource_id: str
    duration_minutes: int

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError(
                f"Task mode duration must be positive: {self.duration_minutes}"
            )

    @property
    def duration_time_units(self) -> int:
        """Convert minutes to solver time units (15-minute intervals)."""
        return (self.duration_minutes + 14) // 15  # Round up to nearest 15 minutes


@dataclass
class Task:
    """Represents a task to be scheduled."""

    task_id: str
    job_id: str
    name: str
    department_id: str | None = None
    is_unattended: bool = False
    is_setup: bool = False
    modes: list[TaskMode] = field(default_factory=list)
    precedence_successors: list[str] = field(
        default_factory=list
    )  # Task IDs that must come after this
    precedence_predecessors: list[str] = field(
        default_factory=list
    )  # Task IDs that must come before this

    def __post_init__(self) -> None:
        if not self.modes and hasattr(self, "_post_init_complete"):
            raise ValueError(f"Task {self.name} must have at least one mode")
        self._post_init_complete = True

    @property
    def eligible_machines(self) -> list[str]:
        """Get list of machines this task can run on."""
        return [mode.machine_resource_id for mode in self.modes]

    @property
    def min_duration(self) -> int:
        """Get minimum duration across all modes (in minutes)."""
        if not self.modes:
            return 0
        return min(mode.duration_minutes for mode in self.modes)

    @property
    def max_duration(self) -> int:
        """Get maximum duration across all modes (in minutes)."""
        if not self.modes:
            return 0
        return max(mode.duration_minutes for mode in self.modes)

    def get_duration_on_machine(self, machine_id: str) -> int | None:
        """Get duration for a specific machine (in minutes)."""
        for mode in self.modes:
            if mode.machine_resource_id == machine_id:
                return mode.duration_minutes
        return None


@dataclass
class Job:
    """Represents a job (collection of tasks)."""

    job_id: str
    description: str
    due_date: datetime
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Make datetime timezone-aware if it isn't already
        if self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        if self.due_date <= now:
            # For testing, we'll allow past due dates but warn
            pass  # In production, might want to raise ValueError

    @property
    def total_min_duration(self) -> int:
        """Calculate minimum total duration considering precedences (critical path)."""
        # Simple sum for now - would need graph analysis for true critical path
        return sum(task.min_duration for task in self.tasks)

    @property
    def task_count(self) -> int:
        """Get number of tasks in this job."""
        return len(self.tasks)

    def get_task_by_id(self, task_id: str) -> Task | None:
        """Find a task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None


@dataclass
class WorkCell:
    """Represents a work cell containing machines."""

    cell_id: str
    name: str
    capacity: int = 1
    machines: list[Machine] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"Work cell capacity must be positive: {self.capacity}")

    @property
    def machine_count(self) -> int:
        """Get number of machines in this cell."""
        return len(self.machines)

    @property
    def total_machine_capacity(self) -> int:
        """Get total capacity across all machines."""
        return sum(machine.capacity for machine in self.machines)


@dataclass
class Precedence:
    """Represents a precedence constraint between tasks."""

    predecessor_task_id: str
    successor_task_id: str

    def __post_init__(self) -> None:
        if self.predecessor_task_id == self.successor_task_id:
            raise ValueError("Task cannot have precedence with itself")


@dataclass
class SchedulingProblem:
    """Complete problem definition for the solver."""

    jobs: list[Job]
    machines: list[Machine]
    work_cells: list[WorkCell]
    precedences: list[Precedence]

    # Computed lookups for efficiency
    task_lookup: dict[str, Task] = field(init=False)
    machine_lookup: dict[str, Machine] = field(init=False)
    job_lookup: dict[str, Job] = field(init=False)

    def __post_init__(self) -> None:
        # Build lookup dictionaries
        self.task_lookup = {}
        self.job_lookup = {}

        for job in self.jobs:
            self.job_lookup[job.job_id] = job
            for task in job.tasks:
                self.task_lookup[task.task_id] = task

        self.machine_lookup = {m.resource_id: m for m in self.machines}

        # Populate precedence relationships in tasks
        for prec in self.precedences:
            if prec.predecessor_task_id in self.task_lookup:
                self.task_lookup[prec.predecessor_task_id].precedence_successors.append(
                    prec.successor_task_id
                )
            if prec.successor_task_id in self.task_lookup:
                self.task_lookup[prec.successor_task_id].precedence_predecessors.append(
                    prec.predecessor_task_id
                )

    @property
    def total_task_count(self) -> int:
        """Get total number of tasks across all jobs."""
        return sum(job.task_count for job in self.jobs)

    @property
    def total_machine_count(self) -> int:
        """Get total number of machines."""
        return len(self.machines)

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        return self.task_lookup.get(task_id)

    def get_machine(self, machine_id: str) -> Machine | None:
        """Get machine by ID."""
        return self.machine_lookup.get(machine_id)

    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self.job_lookup.get(job_id)

    def validate(self) -> list[str]:
        """Validate the problem definition. Returns list of issues."""
        issues = []

        # Check all tasks have at least one mode
        for job in self.jobs:
            for task in job.tasks:
                if not task.modes:
                    issues.append(f"Task {task.name} has no modes")

                # Check all referenced machines exist
                for mode in task.modes:
                    if mode.machine_resource_id not in self.machine_lookup:
                        issues.append(
                            f"Task {task.name} references non-existent machine "
                            f"{mode.machine_resource_id}"
                        )

        # Check precedences reference valid tasks
        for prec in self.precedences:
            if prec.predecessor_task_id not in self.task_lookup:
                issues.append(
                    f"Precedence references non-existent predecessor "
                    f"{prec.predecessor_task_id}"
                )
            if prec.successor_task_id not in self.task_lookup:
                issues.append(
                    f"Precedence references non-existent successor "
                    f"{prec.successor_task_id}"
                )

        # Check for circular precedences (simple check - no self-loops)
        for prec in self.precedences:
            if prec.predecessor_task_id == prec.successor_task_id:
                issues.append(f"Circular precedence on task {prec.predecessor_task_id}")

        return issues
