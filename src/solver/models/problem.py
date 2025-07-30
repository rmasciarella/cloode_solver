"""Data models for the fresh OR-Tools solver.

Provides type safety, validation, and computed properties.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


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
class TemplatePrecedence:
    """Represents a precedence constraint within a job template."""

    predecessor_template_task_id: str
    successor_template_task_id: str

    def __post_init__(self) -> None:
        if self.predecessor_template_task_id == self.successor_template_task_id:
            raise ValueError("Template task cannot have precedence with itself")


@dataclass
class TemplateTask:
    """Represents a task definition in a job template (without job instance binding)."""

    template_task_id: str
    name: str
    department_id: str | None = None
    is_unattended: bool = False
    is_setup: bool = False
    modes: list[TaskMode] = field(default_factory=list)

    # Template-specific precedence relationships
    precedence_successors: list[str] = field(default_factory=list)
    precedence_predecessors: list[str] = field(default_factory=list)

    # Phase 2.1b: Multi-operator support
    min_operators: int = 1  # Minimum operators required
    max_operators: int = 1  # Maximum operators that can work on this task
    operator_efficiency_curve: str = (
        "linear"  # How efficiency scales with operator count
    )

    def __post_init__(self) -> None:
        if not self.modes and hasattr(self, "_template_post_init_complete"):
            raise ValueError(f"Template task {self.name} must have at least one mode")

        # Validate multi-operator constraints
        if self.min_operators <= 0:
            raise ValueError(
                f"Template task {self.name} min_operators must be positive: "
                f"{self.min_operators}"
            )
        if self.max_operators <= 0:
            raise ValueError(
                f"Template task {self.name} max_operators must be positive: "
                f"{self.max_operators}"
            )
        if self.min_operators > self.max_operators:
            raise ValueError(
                f"Template task {self.name} min_operators ({self.min_operators}) "
                f"cannot exceed max_operators ({self.max_operators})"
            )

        # Validate efficiency curve type
        valid_curves = ["linear", "diminishing", "constant"]
        if self.operator_efficiency_curve not in valid_curves:
            raise ValueError(
                f"Template task {self.name} efficiency curve must be one of "
                f"{valid_curves}: {self.operator_efficiency_curve}"
            )

        self._template_post_init_complete = True

    @property
    def eligible_machines(self) -> list[str]:
        """Get list of machines this template task can run on."""
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
class JobTemplate:
    """Template defining the structure of identical jobs."""

    template_id: str
    name: str
    description: str
    template_tasks: list[TemplateTask] = field(default_factory=list)
    template_precedences: list[TemplatePrecedence] = field(default_factory=list)

    # Computed lookups for efficiency
    template_task_lookup: dict[str, TemplateTask] = field(init=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        # Build lookup dictionary
        self.template_task_lookup = {
            task.template_task_id: task for task in self.template_tasks
        }

        # Populate precedence relationships in template tasks
        for prec in self.template_precedences:
            if prec.predecessor_template_task_id in self.template_task_lookup:
                self.template_task_lookup[
                    prec.predecessor_template_task_id
                ].precedence_successors.append(prec.successor_template_task_id)
            if prec.successor_template_task_id in self.template_task_lookup:
                self.template_task_lookup[
                    prec.successor_template_task_id
                ].precedence_predecessors.append(prec.predecessor_template_task_id)

    @property
    def task_count(self) -> int:
        """Get number of tasks in this template."""
        return len(self.template_tasks)

    @property
    def total_min_duration(self) -> int:
        """Calculate minimum total duration considering precedences (critical path)."""
        # Simple sum for now - would need graph analysis for true critical path
        return sum(task.min_duration for task in self.template_tasks)

    def get_template_task(self, template_task_id: str) -> TemplateTask | None:
        """Find a template task by ID."""
        return self.template_task_lookup.get(template_task_id)

    def compute_critical_path_length(self) -> int:
        """Compute critical path length through template tasks (in minutes)."""
        # Simplified implementation - assumes linear precedence for now
        return self.total_min_duration

    def validate_template(self) -> list[str]:
        """Validate the template definition. Returns list of issues."""
        issues = []

        # Check all template tasks have at least one mode
        for task in self.template_tasks:
            if not task.modes:
                issues.append(f"Template task {task.name} has no modes")

        # Check precedences reference valid template tasks
        for prec in self.template_precedences:
            if prec.predecessor_template_task_id not in self.template_task_lookup:
                issues.append(
                    f"Template precedence references non-existent predecessor "
                    f"{prec.predecessor_template_task_id}"
                )
            if prec.successor_template_task_id not in self.template_task_lookup:
                issues.append(
                    f"Template precedence references non-existent successor "
                    f"{prec.successor_template_task_id}"
                )

        # Check for circular precedences (simple check - no self-loops)
        for prec in self.template_precedences:
            if prec.predecessor_template_task_id == prec.successor_template_task_id:
                issues.append(
                    f"Circular precedence on template task "
                    f"{prec.predecessor_template_task_id}"
                )

        return issues


@dataclass
class JobInstance:
    """Lightweight job instance that references a template."""

    instance_id: str
    template_id: str
    description: str
    due_date: datetime
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

    # Template-based architecture support
    job_template: JobTemplate | None = None
    job_instances: list[JobInstance] = field(default_factory=list)
    is_template_based: bool = False

    # Computed lookups for efficiency
    task_lookup: dict[str, Task] = field(init=False)
    machine_lookup: dict[str, Machine] = field(init=False)
    job_lookup: dict[str, Job] = field(init=False)
    template_task_lookup: dict[str, TemplateTask] = field(init=False)
    job_instance_lookup: dict[str, JobInstance] = field(init=False)
    operator_lookup: dict[str, Operator] = field(init=False)
    skill_lookup: dict[str, Skill] = field(init=False)
    task_skill_lookup: dict[str, list[TaskSkillRequirement]] = field(init=False)

    def __post_init__(self) -> None:
        # Build lookup dictionaries
        self.task_lookup = {}
        self.job_lookup = {}
        self.template_task_lookup = {}
        self.job_instance_lookup = {}
        self.operator_lookup = {}
        self.skill_lookup = {}
        self.task_skill_lookup = {}

        # Handle legacy job structure
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

        # Handle template-based structure
        if self.job_template:
            self.is_template_based = True
            # Build template task lookup
            for template_task in self.job_template.template_tasks:
                self.template_task_lookup[template_task.template_task_id] = (
                    template_task
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
        if self.is_template_based and self.job_template:
            return len(self.job_instances) * self.job_template.task_count
        return sum(job.task_count for job in self.jobs)

    @property
    def total_machine_count(self) -> int:
        """Get total number of machines."""
        return len(self.machines)

    @property
    def instance_count(self) -> int:
        """Get number of job instances (for template-based problems)."""
        return len(self.job_instances)

    @property
    def template_task_count(self) -> int:
        """Get number of tasks in the template (for template-based problems)."""
        if self.job_template:
            return self.job_template.task_count
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

    def get_template_task(self, template_task_id: str) -> TemplateTask | None:
        """Get template task by ID (for template-based problems)."""
        return self.template_task_lookup.get(template_task_id)

    def get_job_instance(self, instance_id: str) -> JobInstance | None:
        """Get job instance by ID (for template-based problems)."""
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

    def get_instance_task_id(self, instance_id: str, template_task_id: str) -> str:
        """Generate task ID for a specific instance and template task."""
        return f"{instance_id}_{template_task_id}"

    def parse_instance_task_id(self, task_id: str) -> tuple[str, str] | None:
        """Parse instance task ID into (instance_id, template_task_id)."""
        parts = task_id.split("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None

    def calculate_operator_template_task_efficiency(
        self, operator_id: str, template_task_id: str
    ) -> float:
        """Calculate operator's efficiency for a template task based on skill match."""
        operator = self.get_operator(operator_id)
        if not operator:
            return 0.0

        template_task = self.get_template_task(template_task_id)
        if not template_task:
            return 0.0

        skill_requirements = self.get_required_skills_for_template_task(
            template_task_id
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
            task_req = self.get_task_skill_requirement(template_task_id, skill.skill_id)
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

    def get_required_skills_for_template_task(
        self, template_task_id: str
    ) -> list[Skill]:
        """Get all skills required for a template task."""
        required_skills = []

        for req in self.task_skill_requirements:
            if req.task_id == template_task_id and req.is_mandatory:
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

        if self.is_template_based and self.job_template:
            # Template-based validation
            template_issues = self.job_template.validate_template()
            issues.extend([f"Template: {issue}" for issue in template_issues])

            # Check template task machines exist
            for template_task in self.job_template.template_tasks:
                for mode in template_task.modes:
                    if mode.machine_resource_id not in self.machine_lookup:
                        issues.append(
                            f"Template task {template_task.name} references "
                            f"non-existent machine {mode.machine_resource_id}"
                        )

            # Validate job instances reference valid template
            for instance in self.job_instances:
                if instance.template_id != self.job_template.template_id:
                    issues.append(
                        f"Job instance {instance.instance_id} references "
                        f"invalid template {instance.template_id}"
                    )
        else:
            # Legacy validation
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

        # Check precedences reference valid tasks (both template and legacy)
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
    def create_from_template(
        cls,
        job_template: JobTemplate,
        job_instances: list[JobInstance],
        machines: list[Machine],
        work_cells: list[WorkCell],
        jobs: list[Job] | None = None,
        precedences: list[Precedence] | None = None,
    ) -> "SchedulingProblem":
        """Create a template-based scheduling problem.

        Args:
            job_template: The job template defining task structure
            job_instances: List of job instances to schedule
            machines: Available machines
            work_cells: Work cell definitions
            jobs: Generated jobs (optional, will be empty for pure template)
            precedences: Generated precedences (optional, will be empty for
                pure template)

        Returns:
            SchedulingProblem configured for template-based scheduling

        """
        return cls(
            jobs=jobs or [],
            machines=machines,
            work_cells=work_cells,
            precedences=precedences or [],
            job_template=job_template,
            job_instances=job_instances,
            is_template_based=True,
        )
