"""Unit tests for data models.

Tests validation, computed properties, and error handling.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


class TestMachine:
    """Test Machine data model."""

    def test_machine_valid_creation(self):
        """Test creating a valid machine."""
        # GIVEN: Valid machine parameters
        # WHEN: Creating a machine
        machine = Machine(
            resource_id="machine-1",
            cell_id="cell-1",
            name="Test Machine",
            capacity=2,
            cost_per_hour=50.0,
        )

        # THEN: Machine is created successfully
        assert machine.resource_id == "machine-1"
        assert machine.capacity == 2
        assert machine.cost_per_hour == 50.0

    def test_machine_negative_capacity(self):
        """Test that negative capacity raises error."""
        # GIVEN: Negative capacity
        # WHEN/THEN: Creating machine raises ValueError
        with pytest.raises(ValueError, match="Machine capacity must be positive"):
            Machine("m1", "c1", "Machine", capacity=-1)

    def test_machine_zero_capacity(self):
        """Test that zero capacity raises error."""
        with pytest.raises(ValueError, match="Machine capacity must be positive"):
            Machine("m1", "c1", "Machine", capacity=0)

    def test_machine_negative_cost(self):
        """Test that negative cost raises error."""
        # GIVEN: Negative cost
        # WHEN/THEN: Creating machine raises ValueError
        with pytest.raises(ValueError, match="Machine cost cannot be negative"):
            Machine("m1", "c1", "Machine", capacity=1, cost_per_hour=-10.0)


class TestTaskMode:
    """Test TaskMode data model."""

    def test_taskmode_valid_creation(self):
        """Test creating a valid task mode."""
        # GIVEN: Valid parameters
        # WHEN: Creating task mode
        mode = TaskMode(
            task_mode_id="mode-1",
            task_id="task-1",
            machine_resource_id="machine-1",
            duration_minutes=45,
        )

        # THEN: Mode created successfully
        assert mode.duration_minutes == 45
        assert mode.duration_time_units == 3  # 45/15 = 3

    def test_taskmode_negative_duration(self):
        """Test that negative duration raises error."""
        with pytest.raises(ValueError, match="Task mode duration must be positive"):
            TaskMode("m1", "t1", "machine-1", duration_minutes=-10)

    def test_taskmode_zero_duration(self):
        """Test that zero duration raises error."""
        with pytest.raises(ValueError, match="Task mode duration must be positive"):
            TaskMode("m1", "t1", "machine-1", duration_minutes=0)

    def test_taskmode_time_unit_conversion(self):
        """Test time unit conversion with rounding."""
        # Test exact multiple
        mode1 = TaskMode("m1", "t1", "machine-1", duration_minutes=30)
        assert mode1.duration_time_units == 2  # 30/15 = 2

        # Test rounding up
        mode2 = TaskMode("m2", "t1", "machine-1", duration_minutes=31)
        assert mode2.duration_time_units == 3  # (31+14)/15 = 3

        mode3 = TaskMode("m3", "t1", "machine-1", duration_minutes=14)
        assert mode3.duration_time_units == 1  # (14+14)/15 = 1


class TestTask:
    """Test Task data model."""

    def test_task_valid_creation(self):
        """Test creating a valid task."""
        # GIVEN: Valid task with modes
        modes = [
            TaskMode("m1", "t1", "machine-1", 30),
            TaskMode("m2", "t1", "machine-2", 45),
        ]

        # WHEN: Creating task
        task = Task(
            task_id="task-1",
            job_id="job-1",
            name="Test Task",
            department_id="dept-1",
            is_unattended=True,
            is_setup=False,
            modes=modes,
        )

        # THEN: Task created with correct properties
        assert task.task_id == "task-1"
        assert task.is_unattended is True
        assert len(task.modes) == 2

    def test_task_empty_modes_validation(self):
        """Test that task validation only triggers after initialization."""
        # This is valid during construction
        task = Task("t1", "j1", "Task 1")
        assert len(task.modes) == 0

        # But accessing _post_init_complete shows it was set
        assert hasattr(task, "_post_init_complete")

    def test_task_computed_properties(self):
        """Test task computed properties."""
        # GIVEN: Task with multiple modes
        modes = [
            TaskMode("m1", "t1", "machine-1", 30),
            TaskMode("m2", "t1", "machine-2", 45),
            TaskMode("m3", "t1", "machine-3", 20),
        ]
        task = Task("t1", "j1", "Task", modes=modes)

        # THEN: Computed properties work correctly
        assert task.min_duration == 20
        assert task.max_duration == 45
        assert set(task.eligible_machines) == {"machine-1", "machine-2", "machine-3"}

    def test_task_get_duration_on_machine(self):
        """Test getting duration for specific machine."""
        # GIVEN: Task with modes
        modes = [
            TaskMode("m1", "t1", "machine-1", 30),
            TaskMode("m2", "t1", "machine-2", 45),
        ]
        task = Task("t1", "j1", "Task", modes=modes)

        # THEN: Can get duration for valid machines
        assert task.get_duration_on_machine("machine-1") == 30
        assert task.get_duration_on_machine("machine-2") == 45
        assert task.get_duration_on_machine("machine-999") is None

    def test_task_precedence_tracking(self):
        """Test precedence successor/predecessor lists."""
        task = Task("t1", "j1", "Task")
        task.precedence_successors = ["t2", "t3"]
        task.precedence_predecessors = ["t0"]

        assert len(task.precedence_successors) == 2
        assert "t0" in task.precedence_predecessors


class TestJob:
    """Test Job data model."""

    def test_job_valid_creation(self):
        """Test creating a valid job."""
        # GIVEN: Valid job parameters
        due_date = datetime.now(UTC) + timedelta(days=1)
        tasks = [
            Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "machine-1", 30)]),
            Task("t2", "j1", "Task 2", modes=[TaskMode("m2", "t2", "machine-1", 45)]),
        ]

        # WHEN: Creating job
        job = Job(
            job_id="job-1", description="Test Job", due_date=due_date, tasks=tasks
        )

        # THEN: Job created successfully
        assert job.job_id == "job-1"
        assert len(job.tasks) == 2
        assert job.task_count == 2
        assert job.total_min_duration == 75

    def test_job_timezone_handling(self):
        """Test job handles timezone conversion."""
        # GIVEN: Naive datetime
        naive_dt = datetime.now() + timedelta(days=1)

        # WHEN: Creating job with naive datetime
        job = Job("j1", "Job", due_date=naive_dt)

        # THEN: Due date is timezone-aware
        assert job.due_date.tzinfo is not None
        assert job.due_date.tzinfo == UTC

    def test_job_already_timezone_aware(self):
        """Test job preserves timezone-aware datetimes."""
        # GIVEN: Already timezone-aware datetime
        aware_dt = datetime.now(UTC) + timedelta(days=1)

        # WHEN: Creating job
        job = Job("j1", "Job", due_date=aware_dt)

        # THEN: Timezone preserved
        assert job.due_date == aware_dt

    def test_job_task_lookup(self):
        """Test finding tasks by ID."""
        # GIVEN: Job with tasks
        tasks = [
            Task("t1", "j1", "Task 1"),
            Task("t2", "j1", "Task 2"),
            Task("t3", "j1", "Task 3"),
        ]
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=tasks
        )

        # THEN: Can find tasks by ID
        assert job.get_task_by_id("t2").name == "Task 2"
        assert job.get_task_by_id("t999") is None


class TestWorkCell:
    """Test WorkCell data model."""

    def test_workcell_valid_creation(self):
        """Test creating valid work cell."""
        # GIVEN: Valid parameters with machines
        machines = [
            Machine("m1", "c1", "Machine 1", capacity=2),
            Machine("m2", "c1", "Machine 2", capacity=1),
        ]

        # WHEN: Creating work cell
        cell = WorkCell(cell_id="cell-1", name="Cell 1", capacity=3, machines=machines)

        # THEN: Cell created with correct properties
        assert cell.machine_count == 2
        assert cell.total_machine_capacity == 3

    def test_workcell_capacity_validation(self):
        """Test work cell capacity validation."""
        with pytest.raises(ValueError, match="Work cell capacity must be positive"):
            WorkCell("c1", "Cell", capacity=0)

        with pytest.raises(ValueError, match="Work cell capacity must be positive"):
            WorkCell("c1", "Cell", capacity=-5)


class TestPrecedence:
    """Test Precedence data model."""

    def test_precedence_valid_creation(self):
        """Test creating valid precedence."""
        # GIVEN/WHEN: Valid precedence
        prec = Precedence("task-1", "task-2")

        # THEN: Created successfully
        assert prec.predecessor_task_id == "task-1"
        assert prec.successor_task_id == "task-2"

    def test_precedence_self_loop_validation(self):
        """Test that self-loop precedence raises error."""
        with pytest.raises(ValueError, match="Task cannot have precedence with itself"):
            Precedence("task-1", "task-1")


class TestSchedulingProblem:
    """Test SchedulingProblem data model."""

    def test_scheduling_problem_creation(self, sample_problem_data):
        """Test creating a complete scheduling problem."""
        # GIVEN: Complete problem data
        # WHEN: Creating problem
        problem = SchedulingProblem(
            jobs=sample_problem_data["jobs"],
            machines=sample_problem_data["machines"],
            work_cells=sample_problem_data["cells"],
            precedences=sample_problem_data["precedences"],
        )

        # THEN: Problem created with lookups populated
        assert problem.total_task_count == 3
        assert problem.total_machine_count == 3
        assert problem.get_task("task-1-1") is not None
        assert problem.get_machine("machine-1").name == "Machine 1"
        assert problem.get_job("job-1").description == "Job 1"

    def test_scheduling_problem_precedence_population(self):
        """Test that precedences populate task relationships."""
        # GIVEN: Tasks and precedences
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "m1", 30)])
        task2 = Task("t2", "j1", "Task 2", modes=[TaskMode("m2", "t2", "m1", 30)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task1, task2],
        )
        precedence = Precedence("t1", "t2")

        # WHEN: Creating problem
        problem = SchedulingProblem(
            jobs=[job],
            machines=[Machine("m1", "c1", "Machine 1")],
            work_cells=[WorkCell("c1", "Cell 1")],
            precedences=[precedence],
        )

        # THEN: Task relationships populated
        assert "t2" in problem.get_task("t1").precedence_successors
        assert "t1" in problem.get_task("t2").precedence_predecessors

    def test_scheduling_problem_validation_missing_machine(self):
        """Test validation catches missing machines."""
        # GIVEN: Task referencing non-existent machine
        mode = TaskMode("m1", "t1", "machine-999", 30)
        task = Task("t1", "j1", "Task", modes=[mode])
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )

        # WHEN: Creating and validating problem
        problem = SchedulingProblem(
            jobs=[job],
            machines=[Machine("m1", "c1", "Machine 1")],
            work_cells=[],
            precedences=[],
        )
        issues = problem.validate()

        # THEN: Validation finds missing machine
        assert len(issues) == 1
        assert "non-existent machine machine-999" in issues[0]

    def test_scheduling_problem_validation_missing_tasks(self):
        """Test validation catches precedences with missing tasks."""
        # GIVEN: Precedence referencing non-existent tasks
        precedence = Precedence("task-999", "task-888")

        # WHEN: Creating and validating problem
        problem = SchedulingProblem(
            jobs=[], machines=[], work_cells=[], precedences=[precedence]
        )
        issues = problem.validate()

        # THEN: Validation finds missing tasks
        assert len(issues) == 2
        assert any("non-existent predecessor task-999" in issue for issue in issues)
        assert any("non-existent successor task-888" in issue for issue in issues)

    def test_scheduling_problem_empty_modes(self):
        """Test validation catches tasks with no modes."""
        # GIVEN: Task with no modes
        task = Task("t1", "j1", "Task")
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )

        # WHEN: Creating and validating problem
        problem = SchedulingProblem(
            jobs=[job], machines=[], work_cells=[], precedences=[]
        )
        issues = problem.validate()

        # THEN: Validation finds empty modes
        assert len(issues) == 1
        assert "Task has no modes" in issues[0]
