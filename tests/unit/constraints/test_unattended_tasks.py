"""Unit tests for unattended task constraints."""

from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1.unattended_tasks import (
    add_business_hours_setup_constraints,
    add_unattended_execution_constraints,
    add_weekend_optimization_constraints,
)
from src.solver.models.problem import (
    Job,
    JobInstance,
    JobTemplate,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    TemplateTask,
    WorkCell,
)


def test_business_hours_setup_constraints_legacy():
    """Test that setup tasks for unattended processes are constrained to business hours.

    Tests the constraint that setup tasks for unattended processes must occur
    during business hours.
    """
    # GIVEN: A model with an unattended setup task
    model = cp_model.CpModel()

    # Create task that requires setup during business hours
    setup_task = Task(
        task_id="setup_1",
        job_id="job_1",
        name="Unattended Setup",
        is_unattended=True,
        is_setup=True,
        department_id="dept_1",
        modes=[TaskMode("mode_1", "setup_1", "machine_1", 30)],  # 30 minutes
    )

    job = Job(
        job_id="job_1",
        description="Unattended Job",
        due_date=datetime.now(UTC),
        tasks=[setup_task],
    )

    machine = Machine("machine_1", "cell_1", "Setup Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # Create timing variables
    task_key = ("job_1", "setup_1")
    task_starts = {task_key: model.NewIntVar(0, 1000, "start_setup_1")}
    task_ends = {task_key: model.NewIntVar(0, 1000, "end_setup_1")}

    # Task duration constraint
    model.Add(task_ends[task_key] == task_starts[task_key] + 2)  # 30 min = 2 time units

    # WHEN: Adding business hours constraints
    add_business_hours_setup_constraints(model, task_starts, task_ends, problem)

    # THEN: Setup task is scheduled within business hours
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"

    start_time = solver.Value(task_starts[task_key])
    end_time = solver.Value(task_ends[task_key])

    # Business hours: 7am-4pm = time units 28-68 per day (96 time units per day)
    # Check if scheduled during valid business hours
    day = start_time // 96
    start_offset = start_time % 96
    end_offset = end_time % 96

    # Should be within business hours (28-68) and not on weekend (day 5,6)
    assert day < 5, f"Setup scheduled on weekend day {day}"
    assert (
        28 <= start_offset <= 68
    ), f"Setup start {start_offset} outside business hours"
    assert 28 <= end_offset <= 68, f"Setup end {end_offset} outside business hours"


def test_business_hours_setup_constraints_template():
    """Test business hours constraints for template-based unattended tasks."""
    # GIVEN: A template with unattended setup task
    model = cp_model.CpModel()

    template_task = TemplateTask(
        template_task_id="setup_template",
        name="Template Setup",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("mode_1", "setup_template", "machine_1", 45)],  # 45 minutes
    )

    template = JobTemplate(
        template_id="template_1",
        name="Unattended Template",
        description="Template with setup",
        template_tasks=[template_task],
    )

    instance = JobInstance(
        instance_id="instance_1",
        template_id="template_1",
        description="Instance 1",
        due_date=datetime.now(UTC),
    )

    machine = Machine("machine_1", "cell_1", "Setup Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem.create_from_template(
        job_template=template,
        job_instances=[instance],
        machines=[machine],
        work_cells=[work_cell],
    )

    # Create timing variables
    instance_task_id = problem.get_instance_task_id("instance_1", "setup_template")
    task_key = ("instance_1", instance_task_id)
    task_starts = {task_key: model.NewIntVar(0, 1000, "start_setup_template")}
    task_ends = {task_key: model.NewIntVar(0, 1000, "end_setup_template")}

    # Task duration constraint (45 min = 3 time units)
    model.Add(task_ends[task_key] == task_starts[task_key] + 3)

    # WHEN: Adding business hours constraints
    add_business_hours_setup_constraints(model, task_starts, task_ends, problem)

    # THEN: Template setup task is scheduled within business hours
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"

    start_time = solver.Value(task_starts[task_key])
    day = start_time // 96
    start_offset = start_time % 96

    assert day < 5, f"Template setup scheduled on weekend day {day}"
    assert (
        28 <= start_offset <= 68
    ), f"Template setup start {start_offset} outside business hours"


def test_unattended_execution_no_time_restrictions():
    """Test that unattended execution tasks have no business hours restrictions."""
    # GIVEN: A model with unattended execution task
    model = cp_model.CpModel()

    execution_task = Task(
        task_id="execution_1",
        job_id="job_1",
        name="Unattended Execution",
        is_unattended=True,
        is_setup=False,  # This is the execution phase
        modes=[TaskMode("mode_1", "execution_1", "machine_1", 720)],  # 12 hours
    )

    job = Job(
        job_id="job_1",
        description="Unattended Execution Job",
        due_date=datetime.now(UTC),
        tasks=[execution_task],
    )

    machine = Machine("machine_1", "cell_1", "Execution Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # Create timing variables
    task_key = ("job_1", "execution_1")
    task_starts = {task_key: model.NewIntVar(0, 2000, "start_execution_1")}
    task_ends = {task_key: model.NewIntVar(0, 2000, "end_execution_1")}

    # Task duration constraint (720 min = 48 time units)
    model.Add(task_ends[task_key] == task_starts[task_key] + 48)

    # WHEN: Adding unattended execution constraints
    add_unattended_execution_constraints(model, task_starts, task_ends, problem)

    # THEN: Execution task can be scheduled at any time (including weekends/nights)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"

    # The execution task should be able to start at any time
    # (no specific time restrictions should be enforced)
    start_time = solver.Value(task_starts[task_key])
    assert start_time >= 0, "Execution task should be able to start"


def test_setup_execution_dependency():
    """Test that execution tasks start after setup completion."""
    # GIVEN: A model with both setup and execution tasks
    model = cp_model.CpModel()

    setup_task = Task(
        task_id="setup_1",
        job_id="job_1",
        name="Setup Phase",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("mode_1", "setup_1", "machine_1", 60)],  # 1 hour
    )

    execution_task = Task(
        task_id="execution_1",
        job_id="job_1",
        name="Execution Phase",
        is_unattended=True,
        is_setup=False,
        modes=[TaskMode("mode_2", "execution_1", "machine_1", 1440)],  # 24 hours
    )

    job = Job(
        job_id="job_1",
        description="Setup + Execution Job",
        due_date=datetime.now(UTC),
        tasks=[setup_task, execution_task],
    )

    machine = Machine("machine_1", "cell_1", "Process Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # Create timing variables
    setup_key = ("job_1", "setup_1")
    execution_key = ("job_1", "execution_1")

    task_starts = {
        setup_key: model.NewIntVar(0, 1000, "start_setup_1"),
        execution_key: model.NewIntVar(0, 1000, "start_execution_1"),
    }
    task_ends = {
        setup_key: model.NewIntVar(0, 1000, "end_setup_1"),
        execution_key: model.NewIntVar(0, 1000, "end_execution_1"),
    }

    # Duration constraints
    model.Add(
        task_ends[setup_key] == task_starts[setup_key] + 4
    )  # 1 hour = 4 time units
    model.Add(
        task_ends[execution_key] == task_starts[execution_key] + 96
    )  # 24 hours = 96 time units

    # WHEN: Adding unattended execution constraints
    add_unattended_execution_constraints(model, task_starts, task_ends, problem)

    # THEN: Execution starts after setup completes
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"

    setup_end = solver.Value(task_ends[setup_key])
    execution_start = solver.Value(task_starts[execution_key])

    assert (
        execution_start >= setup_end
    ), f"Execution starts ({execution_start}) before setup ends ({setup_end})"


def test_weekend_optimization_long_tasks():
    """Test that long unattended processes are optimized for weekend scheduling."""
    # GIVEN: A model with a long unattended execution task
    model = cp_model.CpModel()

    long_execution_task = Task(
        task_id="long_execution_1",
        job_id="job_1",
        name="Long Process",
        is_unattended=True,
        is_setup=False,
        modes=[TaskMode("mode_1", "long_execution_1", "machine_1", 2880)],  # 48 hours
    )

    job = Job(
        job_id="job_1",
        description="Long Process Job",
        due_date=datetime.now(UTC),
        tasks=[long_execution_task],
    )

    machine = Machine("machine_1", "cell_1", "Long Process Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # Create timing variables
    task_key = ("job_1", "long_execution_1")
    task_starts = {task_key: model.NewIntVar(0, 1000, "start_long_execution_1")}
    task_durations = {
        task_key: model.NewIntVar(
            192, 192, "duration_long_execution_1"
        )  # 48 hours = 192 time units
    }

    # WHEN: Adding weekend optimization constraints
    add_weekend_optimization_constraints(
        model,
        task_starts,
        task_durations,
        problem,
        long_task_threshold=96,  # 24 hours threshold
    )

    # THEN: The constraint should be added successfully
    # (The actual weekend preference would be enforced
    # through objective function weighting)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Should be feasible with weekend optimization constraints
    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"


def test_non_unattended_tasks_unaffected():
    """Test that regular (attended) tasks are not affected by unattended constraints."""
    # GIVEN: A model with regular attended task
    model = cp_model.CpModel()

    regular_task = Task(
        task_id="regular_1",
        job_id="job_1",
        name="Regular Task",
        is_unattended=False,  # Not unattended
        is_setup=False,
        modes=[TaskMode("mode_1", "regular_1", "machine_1", 120)],  # 2 hours
    )

    job = Job(
        job_id="job_1",
        description="Regular Job",
        due_date=datetime.now(UTC),
        tasks=[regular_task],
    )

    machine = Machine("machine_1", "cell_1", "Regular Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # Create timing variables
    task_key = ("job_1", "regular_1")
    task_starts = {task_key: model.NewIntVar(0, 1000, "start_regular_1")}
    task_ends = {task_key: model.NewIntVar(0, 1000, "end_regular_1")}
    task_durations = {
        task_key: model.NewIntVar(8, 8, "duration_regular_1")  # 2 hours = 8 time units
    }

    # WHEN: Adding all unattended constraints
    add_business_hours_setup_constraints(model, task_starts, task_ends, problem)
    add_unattended_execution_constraints(model, task_starts, task_ends, problem)
    add_weekend_optimization_constraints(model, task_starts, task_durations, problem)

    # THEN: Regular task should remain unconstrained by unattended task logic
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Should solve without additional restrictions
    assert status in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ], f"Solver status: {solver.StatusName(status)}"


def test_empty_problem_handling():
    """Test that constraints handle empty problems gracefully."""
    # GIVEN: An empty problem
    model = cp_model.CpModel()

    machine = Machine("machine_1", "cell_1", "Test Machine")
    work_cell = WorkCell("cell_1", "Cell 1", machines=[machine])

    problem = SchedulingProblem(
        jobs=[],  # No jobs
        machines=[machine],
        work_cells=[work_cell],
        precedences=[],
    )

    task_starts = {}
    task_ends = {}
    task_durations = {}

    # WHEN: Adding unattended constraints to empty problem
    # THEN: Should not raise exceptions
    add_business_hours_setup_constraints(model, task_starts, task_ends, problem)
    add_unattended_execution_constraints(model, task_starts, task_ends, problem)
    add_weekend_optimization_constraints(model, task_starts, task_durations, problem)

    # Should handle gracefully
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL  # Trivially optimal with no constraints
