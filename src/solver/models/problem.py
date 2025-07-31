"""Data models for the fresh OR-Tools solver.

Provides type safety, validation, and computed properties.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Optional


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

    # Phase 2.1b: Multi-operator support
    min_operators: int = 1  # Minimum operators required
    max_operators: int = 1  # Maximum operators that can work on this task
    operator_efficiency_curve: str = (
        "linear"  # How efficiency scales with operator count
    )

    # Sequence resource reservation support
    sequence_id: str | None = None  # Optional sequence this task belongs to

    def __post_init__(self) -> None:
        if not self.modes and hasattr(self, "_post_init_complete"):
            raise ValueError(f"Task {self.name} must have at least one mode")

        # Validate multi-operator constraints
        if self.min_operators <= 0:
            raise ValueError(
                f"Task {self.name} min_operators must be positive: {self.min_operators}"
            )
        if self.max_operators <= 0:
            raise ValueError(
                f"Task {self.name} max_operators must be positive: {self.max_operators}"
            )
        if self.min_operators > self.max_operators:
            raise ValueError(
                f"Task {self.name} min_operators ({self.min_operators}) "
                f"cannot exceed max_operators ({self.max_operators})"
            )

        # Validate efficiency curve type
        valid_curves = ["linear", "diminishing", "constant"]
        if self.operator_efficiency_curve not in valid_curves:
            raise ValueError(
                f"Task {self.name} efficiency curve must be one of {valid_curves}: "
                f"{self.operator_efficiency_curve}"
            )

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
    due_date: datetime | None = None
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Make datetime timezone-aware if it isn't already
        if self.due_date is not None and self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=UTC)

        # For testing, we'll allow past due dates but warn
        if self.due_date is not None:
            now = datetime.now(UTC)
            if self.due_date <= now:
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

    # User Story 4: WIP limit configuration
    wip_limit: int | None = None  # Optional WIP limit (defaults to capacity)
    target_utilization: float = 0.85  # Target utilization for adaptive WIP
    flow_priority: int = 1  # Priority for flow balancing (1=highest)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"Work cell capacity must be positive: {self.capacity}")

        # Validate WIP limit
        if self.wip_limit is not None and self.wip_limit <= 0:
            raise ValueError(f"WIP limit must be positive: {self.wip_limit}")

        # Validate target utilization
        if not 0.0 <= self.target_utilization <= 1.0:
            raise ValueError(
                f"Target utilization must be between 0.0 and 1.0: "
                f"{self.target_utilization}"
            )

        # Validate flow priority
        if self.flow_priority < 1:
            raise ValueError(f"Flow priority must be at least 1: {self.flow_priority}")

    @property
    def machine_count(self) -> int:
        """Get number of machines in this cell."""
        return len(self.machines)

    @property
    def total_machine_capacity(self) -> int:
        """Get total capacity across all machines."""
        return sum(machine.capacity for machine in self.machines)

    @property
    def effective_wip_limit(self) -> int:
        """Get the effective WIP limit (configured or default to capacity)."""
        return self.wip_limit if self.wip_limit is not None else self.capacity


@dataclass
class Precedence:
    """Represents a precedence constraint between tasks."""

    predecessor_task_id: str
    successor_task_id: str

    def __post_init__(self) -> None:
        if self.predecessor_task_id == self.successor_task_id:
            raise ValueError("Task cannot have precedence with itself")


@dataclass
class OptimizedPrecedence:
    """Represents a precedence constraint within a job optimized pattern."""

    predecessor_optimized_task_id: str
    successor_optimized_task_id: str

    def __post_init__(self) -> None:
        if self.predecessor_optimized_task_id == self.successor_optimized_task_id:
            raise ValueError("Optimized task cannot have precedence with itself")


@dataclass
class OptimizedTask:
    """Represents a task definition in a job optimized pattern."""

    optimized_task_id: str
    name: str
    department_id: str | None = None
    is_unattended: bool = False
    is_setup: bool = False
    modes: list[TaskMode] = field(default_factory=list)

    # Optimized pattern-specific precedence relationships
    precedence_successors: list[str] = field(default_factory=list)
    precedence_predecessors: list[str] = field(default_factory=list)

    # Phase 2.1b: Multi-operator support
    min_operators: int = 1  # Minimum operators required
    max_operators: int = 1  # Maximum operators that can work on this task
    operator_efficiency_curve: str = (
        "linear"  # How efficiency scales with operator count
    )

    # Sequence resource reservation support
    sequence_id: str | None = None  # Optional sequence this task belongs to

    def __post_init__(self) -> None:
        if not self.modes and hasattr(self, "_optimized_post_init_complete"):
            raise ValueError(f"Optimized task {self.name} must have at least one mode")

        # Validate multi-operator constraints
        if self.min_operators <= 0:
            raise ValueError(
                f"Optimized task {self.name} min_operators must be positive: "
                f"{self.min_operators}"
            )
        if self.max_operators <= 0:
            raise ValueError(
                f"Optimized task {self.name} max_operators must be positive: "
                f"{self.max_operators}"
            )
        if self.min_operators > self.max_operators:
            raise ValueError(
                f"Optimized task {self.name} min_operators ({self.min_operators}) "
                f"cannot exceed max_operators ({self.max_operators})"
            )

        # Validate efficiency curve type
        valid_curves = ["linear", "diminishing", "constant"]
        if self.operator_efficiency_curve not in valid_curves:
            raise ValueError(
                f"Optimized task {self.name} efficiency curve must be one of "
                f"{valid_curves}: {self.operator_efficiency_curve}"
            )

        self._optimized_post_init_complete = True

    @property
    def eligible_machines(self) -> list[str]:
        """Get list of machines this optimized task can run on."""
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
class JobOptimizedPattern:
    """Optimized pattern defining the structure of identical jobs."""

    optimized_pattern_id: str
    name: str
    description: str
    optimized_tasks: list[OptimizedTask] = field(default_factory=list)
    optimized_precedences: list[OptimizedPrecedence] = field(default_factory=list)

    # Computed lookups for efficiency
    optimized_task_lookup: dict[str, OptimizedTask] = field(init=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Build lookup dictionary
        self.optimized_task_lookup = {
            task.optimized_task_id: task for task in self.optimized_tasks
        }

        # Populate precedence relationships in optimized tasks
        for prec in self.optimized_precedences:
            if prec.predecessor_optimized_task_id in self.optimized_task_lookup:
                self.optimized_task_lookup[
                    prec.predecessor_optimized_task_id
                ].precedence_successors.append(prec.successor_optimized_task_id)
            if prec.successor_optimized_task_id in self.optimized_task_lookup:
                self.optimized_task_lookup[
                    prec.successor_optimized_task_id
                ].precedence_predecessors.append(prec.predecessor_optimized_task_id)

    @property
    def task_count(self) -> int:
        """Get number of tasks in this optimized pattern."""
        return len(self.optimized_tasks)

    @property
    def total_min_duration(self) -> int:
        """Calculate minimum total duration considering precedences (critical path)."""
        # Simple sum for now - would need graph analysis for true critical path
        return sum(task.min_duration for task in self.optimized_tasks)

    def get_optimized_task(self, optimized_task_id: str) -> OptimizedTask | None:
        """Find an optimized task by ID."""
        return self.optimized_task_lookup.get(optimized_task_id)

    def compute_critical_path_length(self) -> int:
        """Compute critical path length through optimized tasks (in minutes)."""
        # Simplified implementation - assumes linear precedence for now
        return self.total_min_duration

    def validate_pattern(self) -> list[str]:
        """Validate the optimized pattern definition. Returns list of issues."""
        issues = []

        # Check all optimized tasks have at least one mode
        for task in self.optimized_tasks:
            if not task.modes:
                issues.append(f"Optimized task {task.name} has no modes")

        # Check precedences reference valid optimized tasks
        for prec in self.optimized_precedences:
            if prec.predecessor_optimized_task_id not in self.optimized_task_lookup:
                issues.append(
                    f"Optimized precedence references non-existent predecessor "
                    f"{prec.predecessor_optimized_task_id}"
                )
            if prec.successor_optimized_task_id not in self.optimized_task_lookup:
                issues.append(
                    f"Optimized precedence references non-existent successor "
                    f"{prec.successor_optimized_task_id}"
                )

        # Check for circular precedences (simple check - no self-loops)
        for prec in self.optimized_precedences:
            if prec.predecessor_optimized_task_id == prec.successor_optimized_task_id:
                issues.append(
                    f"Circular precedence on optimized task "
                    f"{prec.predecessor_optimized_task_id}"
                )

        return issues


@dataclass
class JobInstance:
    """Lightweight job instance that references an optimized pattern."""

    instance_id: str
    optimized_pattern_id: str
    description: str
    due_date: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Make datetime timezone-aware if it isn't already
        if self.due_date is not None and self.due_date.tzinfo is None:
            self.due_date = self.due_date.replace(tzinfo=UTC)

        # For testing, we'll allow past due dates but warn
        if self.due_date is not None:
            now = datetime.now(UTC)
            if self.due_date <= now:
                pass  # In production, might want to raise ValueError


class ProficiencyLevel(Enum):
    """Skill proficiency levels for operator skill matching."""

    NOVICE = 1  # Can perform with supervision, 50% efficiency
    COMPETENT = 2  # Can perform independently, 75% efficiency
    PROFICIENT = 3  # Can perform efficiently, 100% efficiency
    EXPERT = 4  # Can perform optimally and train others, 125% efficiency


@dataclass
class Skill:
    """Represents a skill required for task execution."""

    skill_id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.skill_id.strip():
            raise ValueError("Skill ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Skill name cannot be empty")


@dataclass
class OperatorSkill:
    """Represents an operator's proficiency in a specific skill."""

    operator_id: str
    skill_id: str
    proficiency_level: ProficiencyLevel
    years_experience: float = 0.0
    last_used_date: datetime | None = None

    def __post_init__(self) -> None:
        if self.years_experience < 0:
            raise ValueError(
                f"Years experience cannot be negative: {self.years_experience}"
            )

    @property
    def efficiency_multiplier(self) -> float:
        """Get efficiency multiplier based on proficiency level."""
        multipliers = {
            ProficiencyLevel.NOVICE: 0.5,
            ProficiencyLevel.COMPETENT: 0.75,
            ProficiencyLevel.PROFICIENT: 1.0,
            ProficiencyLevel.EXPERT: 1.25,
        }
        return multipliers[self.proficiency_level]


@dataclass
class Operator:
    """Represents a human operator resource."""

    operator_id: str
    name: str
    employee_number: str
    skills: list[OperatorSkill] = field(default_factory=list)
    hourly_rate: float = 0.0
    max_hours_per_day: int = 8
    is_active: bool = True
    department_id: str | None = None

    # Skill lookup for efficient access
    skill_lookup: dict[str, OperatorSkill] = field(init=False)

    def __post_init__(self) -> None:
        if not self.operator_id.strip():
            raise ValueError("Operator ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Operator name cannot be empty")
        if self.hourly_rate < 0:
            raise ValueError(f"Hourly rate cannot be negative: {self.hourly_rate}")
        if self.max_hours_per_day <= 0:
            raise ValueError(
                f"Max hours per day must be positive: {self.max_hours_per_day}"
            )

        # Build skill lookup
        self.skill_lookup = {skill.skill_id: skill for skill in self.skills}

    @property
    def skill_ids(self) -> list[str]:
        """Get list of skill IDs this operator possesses."""
        return [skill.skill_id for skill in self.skills]

    def has_skill(
        self, skill_id: str, min_proficiency: ProficiencyLevel = ProficiencyLevel.NOVICE
    ) -> bool:
        """Check if operator has skill at minimum proficiency level."""
        if skill_id not in self.skill_lookup:
            return False
        return (
            self.skill_lookup[skill_id].proficiency_level.value >= min_proficiency.value
        )

    def get_skill_proficiency(self, skill_id: str) -> ProficiencyLevel | None:
        """Get operator's proficiency level for a skill."""
        skill = self.skill_lookup.get(skill_id)
        return skill.proficiency_level if skill else None

    def get_skill_efficiency(self, skill_id: str) -> float:
        """Get efficiency multiplier for a specific skill."""
        skill = self.skill_lookup.get(skill_id)
        return skill.efficiency_multiplier if skill else 0.0


@dataclass
class TaskSkillRequirement:
    """Represents a skill requirement for a task."""

    task_id: str
    skill_id: str
    required_proficiency: ProficiencyLevel
    is_mandatory: bool = True
    weight: float = 1.0  # For multi-skill optimization
    operators_needed: int = 1  # Number of operators needed with this skill

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError(
                f"Skill requirement weight must be positive: {self.weight}"
            )
        if self.operators_needed <= 0:
            raise ValueError(
                f"Operators needed must be positive: {self.operators_needed}"
            )


@dataclass
class OperatorShift:
    """Represents an operator's work shift schedule."""

    operator_id: str
    shift_date: datetime
    start_time: int  # Time units from midnight (15-minute intervals)
    end_time: int  # Time units from midnight (15-minute intervals)
    is_available: bool = True
    overtime_allowed: bool = False
    max_overtime_hours: float = 0.0

    def __post_init__(self) -> None:
        if self.start_time < 0 or self.start_time >= 96:  # 96 = 24 hours * 4 units/hour
            raise ValueError(f"Start time must be 0-95: {self.start_time}")
        if self.end_time < 0 or self.end_time >= 96:
            raise ValueError(f"End time must be 0-95: {self.end_time}")
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        if self.max_overtime_hours < 0:
            raise ValueError(
                f"Max overtime hours cannot be negative: {self.max_overtime_hours}"
            )

    @property
    def shift_duration_hours(self) -> float:
        """Get shift duration in hours."""
        return (self.end_time - self.start_time) * 0.25  # 15 minutes = 0.25 hours

    @property
    def max_total_hours(self) -> float:
        """Get maximum total hours including overtime."""
        return self.shift_duration_hours + (
            self.max_overtime_hours if self.overtime_allowed else 0
        )


@dataclass
class SchedulingProblem:
    """Complete problem definition for the solver."""

    jobs: list[Job]
    machines: list[Machine]
    work_cells: list[WorkCell]
    precedences: list[Precedence]

    # Phase 2: Resource and skill constraints
    operators: list[Operator] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    task_skill_requirements: list[TaskSkillRequirement] = field(default_factory=list)
    operator_shifts: list[OperatorShift] = field(default_factory=list)

    # Optimized mode architecture support
    job_optimized_pattern: JobOptimizedPattern | None = None
    job_instances: list[JobInstance] = field(default_factory=list)
    is_optimized_mode: bool = False

    # Phase 3: Multi-objective optimization
    multi_objective_config: Optional["MultiObjectiveConfiguration"] = None

    # Computed lookups for efficiency
    task_lookup: dict[str, Task] = field(init=False)
    machine_lookup: dict[str, Machine] = field(init=False)
    job_lookup: dict[str, Job] = field(init=False)
    optimized_task_lookup: dict[str, OptimizedTask] = field(init=False)
    job_instance_lookup: dict[str, JobInstance] = field(init=False)
    operator_lookup: dict[str, Operator] = field(init=False)
    skill_lookup: dict[str, Skill] = field(init=False)
    task_skill_lookup: dict[str, list[TaskSkillRequirement]] = field(init=False)

    def __post_init__(self) -> None:
        # Build lookup dictionaries
        self.task_lookup = {}
        self.job_lookup = {}
        self.optimized_task_lookup = {}
        self.job_instance_lookup = {}
        self.operator_lookup = {}
        self.skill_lookup = {}
        self.task_skill_lookup = {}

        # Handle unique mode job structure
        for job in self.jobs:
            self.job_lookup[job.job_id] = job
            for task in job.tasks:
                self.task_lookup[task.task_id] = task

        self.machine_lookup = {m.resource_id: m for m in self.machines}

        # Build Phase 2 lookups
        self.operator_lookup = {op.operator_id: op for op in self.operators}
        self.skill_lookup = {skill.skill_id: skill for skill in self.skills}

        # Build task skill requirements lookup
        for req in self.task_skill_requirements:
            if req.task_id not in self.task_skill_lookup:
                self.task_skill_lookup[req.task_id] = []
            self.task_skill_lookup[req.task_id].append(req)

        # Handle optimized mode structure
        if self.job_optimized_pattern:
            self.is_optimized_mode = True
            # Build optimized task lookup
            for optimized_task in self.job_optimized_pattern.optimized_tasks:
                self.optimized_task_lookup[optimized_task.optimized_task_id] = (
                    optimized_task
                )

            # Build job instance lookup
            for instance in self.job_instances:
                self.job_instance_lookup[instance.instance_id] = instance

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
        if self.is_optimized_mode and self.job_optimized_pattern:
            return len(self.job_instances) * self.job_optimized_pattern.task_count
        return sum(job.task_count for job in self.jobs)

    @property
    def total_machine_count(self) -> int:
        """Get total number of machines."""
        return len(self.machines)

    @property
    def instance_count(self) -> int:
        """Get number of job instances (for optimized mode problems)."""
        return len(self.job_instances)

    @property
    def optimized_task_count(self) -> int:
        """Get number of tasks in the pattern (for optimized mode problems)."""
        if self.job_optimized_pattern:
            return self.job_optimized_pattern.task_count
        return 0

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        return self.task_lookup.get(task_id)

    def get_machine(self, machine_id: str) -> Machine | None:
        """Get machine by ID."""
        return self.machine_lookup.get(machine_id)

    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self.job_lookup.get(job_id)

    def get_optimized_task(self, optimized_task_id: str) -> OptimizedTask | None:
        """Get optimized task by ID (for optimized mode problems)."""
        return self.optimized_task_lookup.get(optimized_task_id)

    def get_job_instance(self, instance_id: str) -> JobInstance | None:
        """Get job instance by ID (for optimized mode problems)."""
        return self.job_instance_lookup.get(instance_id)

    def get_operator(self, operator_id: str) -> Operator | None:
        """Get operator by ID."""
        return self.operator_lookup.get(operator_id)

    def get_skill(self, skill_id: str) -> Skill | None:
        """Get skill by ID."""
        return self.skill_lookup.get(skill_id)

    def get_task_skill_requirements(self, task_id: str) -> list[TaskSkillRequirement]:
        """Get skill requirements for a task."""
        return self.task_skill_lookup.get(task_id, [])

    def get_qualified_operators(self, task_id: str) -> list[Operator]:
        """Get operators qualified to perform a task based on skill requirements."""
        skill_requirements = self.get_task_skill_requirements(task_id)
        if not skill_requirements:
            # If no skill requirements, all operators can do the task
            return [op for op in self.operators if op.is_active]

        qualified_operators = []
        for operator in self.operators:
            if not operator.is_active:
                continue

            # Check if operator meets all mandatory skill requirements
            can_perform = True
            for req in skill_requirements:
                if req.is_mandatory and not operator.has_skill(
                    req.skill_id, req.required_proficiency
                ):
                    can_perform = False
                    break

            if can_perform:
                qualified_operators.append(operator)

        return qualified_operators

    def calculate_operator_task_efficiency(
        self, operator_id: str, task_id: str
    ) -> float:
        """Calculate operator's efficiency for a specific task based on skill match."""
        operator = self.get_operator(operator_id)
        if not operator:
            return 0.0

        skill_requirements = self.get_task_skill_requirements(task_id)
        if not skill_requirements:
            return 1.0  # No skill requirements, base efficiency

        # Calculate weighted average efficiency across all required skills
        total_weight = 0.0
        weighted_efficiency = 0.0

        for req in skill_requirements:
            efficiency = operator.get_skill_efficiency(req.skill_id)

            # Check if operator meets minimum proficiency requirement
            if req.is_mandatory and not operator.has_skill(
                req.skill_id, req.required_proficiency
            ):
                return 0.0  # Cannot perform mandatory skill at required level

            weighted_efficiency += efficiency * req.weight
            total_weight += req.weight

        return weighted_efficiency / total_weight if total_weight > 0 else 0.0

    def get_instance_task_id(self, instance_id: str, optimized_task_id: str) -> str:
        """Generate task ID for a specific instance and optimized task."""
        return f"{instance_id}_{optimized_task_id}"

    def parse_instance_task_id(self, task_id: str) -> tuple[str, str] | None:
        """Parse instance task ID into (instance_id, optimized_task_id)."""
        parts = task_id.split("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None

    def calculate_operator_optimized_task_efficiency(
        self, operator_id: str, optimized_task_id: str
    ) -> float:
        """Calculate operator's efficiency for optimized task based on skill match."""
        operator = self.get_operator(operator_id)
        if not operator:
            return 0.0

        optimized_task = self.get_optimized_task(optimized_task_id)
        if not optimized_task:
            return 0.0

        skill_requirements = self.get_required_skills_for_optimized_task(
            optimized_task_id
        )
        if not skill_requirements:
            return 1.0  # No skill requirements, base efficiency

        # Calculate weighted average efficiency across all required skills
        total_weight = 0.0
        weighted_efficiency = 0.0

        for skill in skill_requirements:
            efficiency = operator.get_skill_efficiency(skill.skill_id)
            weight = 1.0  # Default weight, could be skill-specific

            # Check if operator has required proficiency
            task_req = self.get_task_skill_requirement(
                optimized_task_id, skill.skill_id
            )
            if (
                task_req
                and task_req.is_mandatory
                and not operator.has_skill(
                    skill.skill_id, task_req.required_proficiency
                )
            ):
                return 0.0  # Cannot perform required skill at required level

            weighted_efficiency += efficiency * weight
            total_weight += weight

        return weighted_efficiency / total_weight if total_weight > 0 else 1.0

    def get_required_skills_for_optimized_task(
        self, optimized_task_id: str
    ) -> list[Skill]:
        """Get all skills required for an optimized task."""
        required_skills = []

        for req in self.task_skill_requirements:
            if req.task_id == optimized_task_id and req.is_mandatory:
                skill = self.get_skill(req.skill_id)
                if skill:
                    required_skills.append(skill)

        return required_skills

    def get_task_skill_requirement(
        self, task_id: str, skill_id: str
    ) -> TaskSkillRequirement | None:
        """Get specific task skill requirement."""
        for req in self.task_skill_requirements:
            if req.task_id == task_id and req.skill_id == skill_id:
                return req
        return None

    def get_operators_by_skill_groups(self) -> dict[str, list[Operator]]:
        """Group operators by their skill signature for workload balancing."""
        skill_groups: dict[str, list[Operator]] = {}

        for operator in self.operators:
            # Create skill signature (sorted skill IDs)
            skill_ids = sorted([skill.skill_id for skill in operator.skills])
            skill_signature = ",".join(skill_ids)

            if skill_signature not in skill_groups:
                skill_groups[skill_signature] = []
            skill_groups[skill_signature].append(operator)

        return skill_groups

    def get_skill_equivalent_operators(self) -> dict[str, list[Operator]]:
        """Group operators with equivalent skills for workload balancing."""
        skill_groups: dict[str, list[Operator]] = {}

        for operator in self.operators:
            # Create skill signature with proficiency levels
            skills_sig = []
            for skill in operator.skills:
                skills_sig.append(f"{skill.skill_id}:{skill.proficiency_level.value}")
            skill_signature = ",".join(sorted(skills_sig))

            if skill_signature not in skill_groups:
                skill_groups[skill_signature] = []
            skill_groups[skill_signature].append(operator)

        return skill_groups

    def operator_has_skill(self, operator_id: str, skill_id: str) -> bool:
        """Check if operator has a specific skill."""
        operator = self.get_operator(operator_id)
        if not operator:
            return False
        return operator.has_skill(skill_id)

    def validate(self) -> list[str]:
        """Validate the problem definition. Returns list of issues."""
        issues = []

        if self.is_optimized_mode and self.job_optimized_pattern:
            # Optimized mode validation
            pattern_issues = self.job_optimized_pattern.validate_pattern()
            issues.extend([f"Optimized Pattern: {issue}" for issue in pattern_issues])

            # Check optimized task machines exist
            for optimized_task in self.job_optimized_pattern.optimized_tasks:
                for mode in optimized_task.modes:
                    if mode.machine_resource_id not in self.machine_lookup:
                        issues.append(
                            f"Optimized task {optimized_task.name} references "
                            f"non-existent machine {mode.machine_resource_id}"
                        )

            # Validate job instances reference valid pattern
            for instance in self.job_instances:
                pattern_id = self.job_optimized_pattern.optimized_pattern_id
                if instance.optimized_pattern_id != pattern_id:
                    issues.append(
                        f"Job instance {instance.instance_id} references "
                        f"invalid pattern {instance.optimized_pattern_id}"
                    )
        else:
            # Unique mode validation
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

        # Check precedences reference valid tasks (both optimized and unique modes)
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

    @classmethod
    def create_from_optimized_pattern(
        cls,
        job_optimized_pattern: JobOptimizedPattern,
        job_instances: list[JobInstance],
        machines: list[Machine],
        work_cells: list[WorkCell],
        jobs: list[Job] | None = None,
        precedences: list[Precedence] | None = None,
    ) -> "SchedulingProblem":
        """Create an optimized mode scheduling problem.

        Args:
            job_optimized_pattern: The job pattern defining task structure
            job_instances: List of job instances to schedule
            machines: Available machines
            work_cells: Work cell definitions
            jobs: Generated jobs (optional, will be empty for pure optimized mode)
            precedences: Generated precedences (optional, will be empty for
                pure optimized mode)

        Returns:
            SchedulingProblem configured for optimized mode scheduling

        """
        return cls(
            jobs=jobs or [],
            machines=machines,
            work_cells=work_cells,
            precedences=precedences or [],
            job_optimized_pattern=job_optimized_pattern,
            job_instances=job_instances,
            is_optimized_mode=True,
        )


# Phase 3: Multi-Objective Optimization Models


class ObjectiveType(Enum):
    """Types of optimization objectives supported."""

    MINIMIZE_MAKESPAN = "minimize_makespan"
    MINIMIZE_TOTAL_LATENESS = "minimize_total_lateness"
    MINIMIZE_MAXIMUM_LATENESS = "minimize_maximum_lateness"
    MINIMIZE_TOTAL_COST = "minimize_total_cost"
    MINIMIZE_TOTAL_TARDINESS = "minimize_total_tardiness"
    MINIMIZE_WEIGHTED_COMPLETION_TIME = "minimize_weighted_completion_time"
    MAXIMIZE_MACHINE_UTILIZATION = "maximize_machine_utilization"
    MINIMIZE_SETUP_TIME = "minimize_setup_time"


class OptimizationStrategy(Enum):
    """Multi-objective optimization strategies."""

    LEXICOGRAPHICAL = "lexicographical"  # Prioritized objectives in order
    WEIGHTED_SUM = "weighted_sum"  # Weighted combination of objectives
    PARETO_OPTIMAL = "pareto_optimal"  # Find Pareto frontier
    EPSILON_CONSTRAINT = "epsilon_constraint"  # Constrain all but one objective


@dataclass
class ObjectiveWeight:
    """Represents a weighted objective in multi-objective optimization."""

    objective_type: ObjectiveType
    weight: float
    priority: int = 1  # For lexicographical optimization (1 = highest priority)
    epsilon_bound: float | None = None  # For epsilon-constraint method
    target_value: float | None = None  # Target/desired value for this objective

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError(f"Objective weight cannot be negative: {self.weight}")
        if self.priority < 1:
            raise ValueError(f"Objective priority must be at least 1: {self.priority}")
        if self.epsilon_bound is not None and self.epsilon_bound < 0:
            raise ValueError(f"Epsilon bound cannot be negative: {self.epsilon_bound}")


@dataclass
class MultiObjectiveConfiguration:
    """Configuration for multi-objective optimization."""

    strategy: OptimizationStrategy
    objectives: list[ObjectiveWeight] = field(default_factory=list)

    # Strategy-specific parameters
    lexicographical_tolerance: float = (
        0.01  # Tolerance for lexicographical optimization
    )
    pareto_iterations: int = 10  # Number of Pareto points to find

    def __post_init__(self) -> None:
        if not self.objectives:
            raise ValueError(
                "Multi-objective configuration must have at least one objective"
            )

        if self.lexicographical_tolerance <= 0:
            raise ValueError(
                f"Lexicographical tolerance must be positive: "
                f"{self.lexicographical_tolerance}"
            )

        if self.pareto_iterations <= 0:
            raise ValueError(
                f"Pareto iterations must be positive: {self.pareto_iterations}"
            )

        # Validate strategy-specific requirements
        if self.strategy == OptimizationStrategy.LEXICOGRAPHICAL:
            priorities = [obj.priority for obj in self.objectives]
            if len(set(priorities)) != len(priorities):
                raise ValueError(
                    "Lexicographical optimization requires unique priorities"
                )

        elif self.strategy == OptimizationStrategy.WEIGHTED_SUM:
            total_weight = sum(obj.weight for obj in self.objectives)
            if abs(total_weight - 1.0) > 1e-6:
                raise ValueError(
                    f"Weighted sum requires weights to sum to 1.0, got {total_weight}"
                )

        elif self.strategy == OptimizationStrategy.EPSILON_CONSTRAINT:
            epsilon_objectives = [
                obj for obj in self.objectives if obj.epsilon_bound is not None
            ]
            if len(epsilon_objectives) != len(self.objectives) - 1:
                raise ValueError(
                    "Epsilon constraint requires exactly one objective "
                    "without epsilon bound"
                )

    @property
    def primary_objective(self) -> ObjectiveWeight:
        """Get the primary (highest priority) objective."""
        if self.strategy == OptimizationStrategy.LEXICOGRAPHICAL:
            return min(self.objectives, key=lambda x: x.priority)
        elif self.strategy == OptimizationStrategy.WEIGHTED_SUM:
            return max(self.objectives, key=lambda x: x.weight)
        elif self.strategy == OptimizationStrategy.EPSILON_CONSTRAINT:
            # Return the objective without epsilon bound
            epsilon_free = [obj for obj in self.objectives if obj.epsilon_bound is None]
            return epsilon_free[0] if epsilon_free else self.objectives[0]
        else:
            return self.objectives[0]

    @property
    def sorted_objectives(self) -> list[ObjectiveWeight]:
        """Get objectives sorted by priority (for lexicographical optimization)."""
        return sorted(self.objectives, key=lambda x: x.priority)


@dataclass
class ObjectiveSolution:
    """Solution values for all objectives."""

    makespan: int | None = None
    total_lateness: int | None = None
    maximum_lateness: int | None = None
    total_cost: float | None = None
    total_tardiness: int | None = None
    weighted_completion_time: float | None = None
    machine_utilization: float | None = None
    total_setup_time: int | None = None

    # Solution metadata
    solve_time: float = 0.0
    solver_status: str = ""
    objective_value: float | None = None  # Primary objective value

    def get_objective_value(self, objective_type: ObjectiveType) -> float | None:
        """Get the value for a specific objective type."""
        mapping = {
            ObjectiveType.MINIMIZE_MAKESPAN: self.makespan,
            ObjectiveType.MINIMIZE_TOTAL_LATENESS: self.total_lateness,
            ObjectiveType.MINIMIZE_MAXIMUM_LATENESS: self.maximum_lateness,
            ObjectiveType.MINIMIZE_TOTAL_COST: self.total_cost,
            ObjectiveType.MINIMIZE_TOTAL_TARDINESS: self.total_tardiness,
            ObjectiveType.MINIMIZE_WEIGHTED_COMPLETION_TIME: (
                self.weighted_completion_time
            ),
            ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION: self.machine_utilization,
            ObjectiveType.MINIMIZE_SETUP_TIME: self.total_setup_time,
        }
        return mapping.get(objective_type)

    def set_objective_value(self, objective_type: ObjectiveType, value: float) -> None:
        """Set the value for a specific objective type."""
        if objective_type == ObjectiveType.MINIMIZE_MAKESPAN:
            self.makespan = int(value)
        elif objective_type == ObjectiveType.MINIMIZE_TOTAL_LATENESS:
            self.total_lateness = int(value)
        elif objective_type == ObjectiveType.MINIMIZE_MAXIMUM_LATENESS:
            self.maximum_lateness = int(value)
        elif objective_type == ObjectiveType.MINIMIZE_TOTAL_COST:
            self.total_cost = value
        elif objective_type == ObjectiveType.MINIMIZE_TOTAL_TARDINESS:
            self.total_tardiness = int(value)
        elif objective_type == ObjectiveType.MINIMIZE_WEIGHTED_COMPLETION_TIME:
            self.weighted_completion_time = value
        elif objective_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
            self.machine_utilization = value
        elif objective_type == ObjectiveType.MINIMIZE_SETUP_TIME:
            self.total_setup_time = int(value)


@dataclass
class ParetoSolution:
    """Single solution in Pareto frontier."""

    objectives: ObjectiveSolution
    schedule: dict = field(default_factory=dict)  # Full schedule solution
    is_dominated: bool = False

    def dominates(
        self, other: "ParetoSolution", objective_types: list[ObjectiveType]
    ) -> bool:
        """Check if this solution dominates another in Pareto sense."""
        at_least_one_better = False

        for obj_type in objective_types:
            self_value = self.objectives.get_objective_value(obj_type)
            other_value = other.objectives.get_objective_value(obj_type)

            if self_value is None or other_value is None:
                continue

            # For minimization objectives
            if obj_type != ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:
                if self_value > other_value:
                    return False  # Other is better in this objective
                elif self_value < other_value:
                    at_least_one_better = True
            else:
                # For maximization objectives
                if self_value < other_value:
                    return False  # Other is better in this objective
                elif self_value > other_value:
                    at_least_one_better = True

        return at_least_one_better


@dataclass
class ParetoFrontier:
    """Collection of Pareto-optimal solutions."""

    solutions: list[ParetoSolution] = field(default_factory=list)
    objective_types: list[ObjectiveType] = field(default_factory=list)

    def add_solution(self, solution: ParetoSolution) -> None:
        """Add a solution to the frontier, maintaining Pareto optimality."""
        # Check if new solution is dominated by any existing solution
        for existing in self.solutions:
            if existing.dominates(solution, self.objective_types):
                return  # New solution is dominated, don't add

        # Remove any existing solutions dominated by the new solution
        self.solutions = [
            s for s in self.solutions if not solution.dominates(s, self.objective_types)
        ]

        # Add the new solution
        self.solutions.append(solution)

    @property
    def solution_count(self) -> int:
        """Get number of Pareto-optimal solutions."""
        return len(self.solutions)

    def get_extreme_solutions(self) -> dict[ObjectiveType, ParetoSolution]:
        """Get solutions that are best for each individual objective."""
        extremes = {}

        for obj_type in self.objective_types:
            best_solution = None
            best_value = None

            for solution in self.solutions:
                value = solution.objectives.get_objective_value(obj_type)
                if value is None:
                    continue

                if best_value is None:
                    is_better = True
                elif obj_type == ObjectiveType.MAXIMIZE_MACHINE_UTILIZATION:  # type: ignore[unreachable]
                    # Maximization objective
                    is_better = value > best_value
                else:
                    # Minimization objective
                    is_better = value < best_value

                if is_better:
                    best_value = value
                    best_solution = solution

            if best_solution:
                extremes[obj_type] = best_solution

        return extremes


@dataclass
class TradeOffAnalysis:
    """Analysis of trade-offs between objectives."""

    pareto_frontier: ParetoFrontier
    objective_ranges: dict[ObjectiveType, tuple[float, float]] = field(
        default_factory=dict
    )
    correlation_matrix: dict[tuple[ObjectiveType, ObjectiveType], float] = field(
        default_factory=dict
    )
    recommended_solution: ParetoSolution | None = None

    def __post_init__(self) -> None:
        self._calculate_objective_ranges()
        self._calculate_correlations()

    def _calculate_objective_ranges(self) -> None:
        """Calculate min/max ranges for each objective across Pareto frontier."""
        for obj_type in self.pareto_frontier.objective_types:
            values = []
            for solution in self.pareto_frontier.solutions:
                value = solution.objectives.get_objective_value(obj_type)
                if value is not None:
                    values.append(value)

            if values:
                self.objective_ranges[obj_type] = (min(values), max(values))

    def _calculate_correlations(self) -> None:
        """Calculate correlation coefficients between objectives."""
        objectives = self.pareto_frontier.objective_types

        for i, obj1 in enumerate(objectives):
            for obj2 in objectives[i + 1 :]:
                values1 = []
                values2 = []

                for solution in self.pareto_frontier.solutions:
                    val1 = solution.objectives.get_objective_value(obj1)
                    val2 = solution.objectives.get_objective_value(obj2)

                    if val1 is not None and val2 is not None:
                        values1.append(val1)
                        values2.append(val2)

                if len(values1) > 1:
                    correlation = self._calculate_correlation(values1, values2)
                    self.correlation_matrix[(obj1, obj2)] = correlation

    def _calculate_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y, strict=False))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator_x = n * sum_x2 - sum_x * sum_x
        denominator_y = n * sum_y2 - sum_y * sum_y

        if denominator_x * denominator_y <= 0:
            return 0.0

        return float(numerator / (denominator_x * denominator_y) ** 0.5)

    def get_trade_off_summary(self) -> dict[str, str | float | int]:
        """Get summary of trade-offs in the Pareto frontier."""
        summary: dict[str, str | float | int] = {
            "pareto_solutions_count": self.pareto_frontier.solution_count,
            "objectives_analyzed": len(self.pareto_frontier.objective_types),
        }

        # Add objective ranges
        for obj_type, (min_val, max_val) in self.objective_ranges.items():
            range_pct = ((max_val - min_val) / min_val * 100) if min_val > 0 else 0.0
            summary[f"{obj_type.value}_range_percent"] = range_pct

        # Add strongest correlations
        if self.correlation_matrix:
            strongest_correlation = max(
                self.correlation_matrix.items(), key=lambda x: abs(x[1])
            )
            summary["strongest_correlation"] = float(abs(strongest_correlation[1]))
            summary["strongest_correlation_objectives"] = (
                f"{strongest_correlation[0][0].value} vs "
                f"{strongest_correlation[0][1].value}"
            )

        return summary
