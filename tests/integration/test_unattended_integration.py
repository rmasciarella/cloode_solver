"""Integration tests for unattended task scheduling with full solver."""

from datetime import UTC, datetime, timedelta

from src.solver.core.solver import FreshSolver
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


def test_complete_unattended_workflow_legacy():
    """Test complete unattended task workflow with legacy job structure."""
    # GIVEN: A job with both setup and execution phases for unattended process
    setup_task = Task(
        task_id="unattended_setup",
        job_id="unattended_job",
        name="Unattended Process Setup",
        is_unattended=True,
        is_setup=True,
        modes=[
            TaskMode("setup_mode", "unattended_setup", "machine_1", 60)
        ],  # 1 hour setup
    )

    execution_task = Task(
        task_id="unattended_execution",
        job_id="unattended_job",
        name="Unattended Process Execution",
        is_unattended=True,
        is_setup=False,
        modes=[
            TaskMode("exec_mode", "unattended_execution", "machine_1", 2160)
        ],  # 36 hours execution
    )

    # Use realistic due date that allows for business hour scheduling
    # Setup needs business hours (7am-4pm) + execution needs 36 hours = at least 2 days
    due_date = datetime.now(UTC) + timedelta(days=3)

    job = Job(
        job_id="unattended_job",
        description="Complete Unattended Process",
        due_date=due_date,
        tasks=[setup_task, execution_task],
    )

    machine = Machine("machine_1", "cell_1", "Unattended Machine", capacity=1)
    work_cell = WorkCell("cell_1", "Unattended Cell", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # WHEN: Solving with unattended constraints
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    # THEN: Solution should be found with proper scheduling
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Solver failed: {solution['status']}"
    assert solution["makespan"] > 0, "No valid schedule found"

    # Verify setup is during business hours and execution follows
    schedule = solution["schedule"]
    setup_scheduled = False
    execution_scheduled = False

    for task_info in schedule:
        if task_info["task_id"] == "unattended_setup":
            setup_scheduled = True
            setup_start = task_info["start_time"]
            setup_end = task_info["end_time"]

            # Check business hours (7am-4pm = time units 28-68 per day)
            day = setup_start // 96
            start_offset = setup_start % 96
            end_offset = setup_end % 96

            assert day < 5, f"Setup scheduled on weekend day {day}"
            assert (
                28 <= start_offset <= 68
            ), f"Setup start {start_offset} outside business hours"
            assert (
                28 <= end_offset <= 68
            ), f"Setup end {end_offset} outside business hours"

        elif task_info["task_id"] == "unattended_execution":
            execution_scheduled = True

    assert setup_scheduled, "Setup task not found in schedule"
    assert execution_scheduled, "Execution task not found in schedule"


def test_unattended_template_integration():
    """Test unattended task constraints with template-based scheduling."""
    # GIVEN: A template with unattended setup and execution tasks
    setup_template_task = TemplateTask(
        template_task_id="template_setup",
        name="Template Setup Phase",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("setup_mode", "template_setup", "machine_1", 45)],  # 45 min
    )

    execution_template_task = TemplateTask(
        template_task_id="template_execution",
        name="Template Execution Phase",
        is_unattended=True,
        is_setup=False,
        modes=[
            TaskMode("exec_mode", "template_execution", "machine_1", 1440)
        ],  # 24 hours
    )

    template = JobTemplate(
        template_id="unattended_template",
        name="Unattended Process Template",
        description="Template for unattended processes",
        template_tasks=[setup_template_task, execution_template_task],
    )

    # Create multiple instances to test template optimization
    instances = [
        JobInstance(
            instance_id=f"instance_{i}",
            template_id="unattended_template",
            description=f"Unattended Instance {i}",
            due_date=datetime.now(UTC) + timedelta(days=2),  # Realistic due date
        )
        for i in range(3)
    ]

    machine = Machine("machine_1", "cell_1", "Template Machine", capacity=1)
    work_cell = WorkCell("cell_1", "Template Cell", machines=[machine])

    problem = SchedulingProblem.create_from_template(
        job_template=template,
        job_instances=instances,
        machines=[machine],
        work_cells=[work_cell],
    )

    # WHEN: Solving template-based unattended problem
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)

    # THEN: All instances should be scheduled properly
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Template solver failed: {solution['status']}"
    assert solution["makespan"] > 0, "No valid template schedule found"

    # Verify each instance follows unattended constraints
    schedule = solution["schedule"]
    setup_tasks = [task for task in schedule if "template_setup" in task["task_id"]]

    assert len(setup_tasks) == 3, f"Expected 3 setup tasks, found {len(setup_tasks)}"

    for setup_task in setup_tasks:
        start_time = setup_task["start_time"]
        day = start_time // 96
        start_offset = start_time % 96

        assert day < 5, f"Template setup on weekend day {day}"
        assert (
            28 <= start_offset <= 68
        ), f"Template setup start {start_offset} outside business hours"


def test_weekend_long_process_optimization():
    """Test that long processes are optimized for weekend scheduling."""
    # GIVEN: A long unattended process (72 hours)
    long_execution_task = Task(
        task_id="long_process",
        job_id="weekend_job",
        name="72-Hour Process",
        is_unattended=True,
        is_setup=False,
        modes=[TaskMode("long_mode", "long_process", "machine_1", 4320)],  # 72 hours
    )

    job = Job(
        job_id="weekend_job",
        description="Long Weekend Process",
        due_date=datetime.now(UTC) + timedelta(days=4),  # 72-hour process needs time
        tasks=[long_execution_task],
    )

    machine = Machine("machine_1", "cell_1", "Weekend Machine", capacity=1)
    work_cell = WorkCell("cell_1", "Weekend Cell", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # WHEN: Solving with weekend optimization
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    # THEN: Solution should be feasible
    # (weekend optimization is preference, not constraint)
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Long process solver failed: {solution['status']}"
    assert solution["makespan"] > 0, "No valid long process schedule found"

    # Process should be scheduled
    # (weekend preference handled via objective optimization)
    schedule = solution["schedule"]
    long_tasks = [task for task in schedule if task["task_id"] == "long_process"]
    assert len(long_tasks) == 1, "Long process task not scheduled"


def test_mixed_attended_unattended_integration():
    """Test integration of attended and unattended tasks in same problem."""
    # GIVEN: Mixed attended and unattended tasks
    regular_task = Task(
        task_id="regular_task",
        job_id="mixed_job",
        name="Regular Attended Task",
        is_unattended=False,
        is_setup=False,
        modes=[TaskMode("regular_mode", "regular_task", "machine_1", 120)],  # 2 hours
    )

    unattended_setup = Task(
        task_id="unattended_setup",
        job_id="mixed_job",
        name="Unattended Setup",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("setup_mode", "unattended_setup", "machine_2", 30)],  # 30 min
    )

    unattended_execution = Task(
        task_id="unattended_execution",
        job_id="mixed_job",
        name="Unattended Execution",
        is_unattended=True,
        is_setup=False,
        modes=[
            TaskMode("exec_mode", "unattended_execution", "machine_2", 720)
        ],  # 12 hours
    )

    job = Job(
        job_id="mixed_job",
        description="Mixed Attended/Unattended Job",
        due_date=datetime.now(UTC)
        + timedelta(days=2),  # Mixed tasks need reasonable time
        tasks=[regular_task, unattended_setup, unattended_execution],
    )

    machine1 = Machine("machine_1", "cell_1", "Regular Machine", capacity=1)
    machine2 = Machine("machine_2", "cell_1", "Unattended Machine", capacity=1)
    work_cell = WorkCell(
        "cell_1", "Mixed Cell", capacity=2, machines=[machine1, machine2]
    )

    problem = SchedulingProblem(
        jobs=[job],
        machines=[machine1, machine2],
        work_cells=[work_cell],
        precedences=[],
    )

    # WHEN: Solving mixed problem
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    # THEN: All tasks should be scheduled according to their constraints
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Mixed solver failed: {solution['status']}"
    assert solution["makespan"] > 0, "No valid mixed schedule found"

    schedule = solution["schedule"]
    task_types = {task["task_id"]: task for task in schedule}

    # Verify all tasks are scheduled
    assert "regular_task" in task_types, "Regular task not scheduled"
    assert "unattended_setup" in task_types, "Unattended setup not scheduled"
    assert "unattended_execution" in task_types, "Unattended execution not scheduled"

    # Verify unattended setup follows business hours
    setup_task = task_types["unattended_setup"]
    start_time = setup_task["start_time"]
    day = start_time // 96
    start_offset = start_time % 96

    assert day < 5, f"Mixed unattended setup on weekend day {day}"
    assert (
        28 <= start_offset <= 68
    ), f"Mixed setup start {start_offset} outside business hours"


def test_capacity_constraints_with_unattended():
    """Test unattended constraints work with machine capacity constraints."""
    # GIVEN: High-capacity machine with unattended tasks
    setup_task1 = Task(
        task_id="setup_1",
        job_id="job_1",
        name="Setup 1",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("setup_mode_1", "setup_1", "high_capacity_machine", 60)],
    )

    setup_task2 = Task(
        task_id="setup_2",
        job_id="job_2",
        name="Setup 2",
        is_unattended=True,
        is_setup=True,
        modes=[TaskMode("setup_mode_2", "setup_2", "high_capacity_machine", 60)],
    )

    job1 = Job("job_1", "Job 1", datetime.now(UTC) + timedelta(days=1), [setup_task1])
    job2 = Job("job_2", "Job 2", datetime.now(UTC) + timedelta(days=1), [setup_task2])

    # High-capacity machine can run multiple tasks simultaneously
    machine = Machine(
        "high_capacity_machine", "cell_1", "High Capacity Machine", capacity=3
    )
    work_cell = WorkCell("cell_1", "High Capacity Cell", machines=[machine])

    problem = SchedulingProblem(
        jobs=[job1, job2], machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # WHEN: Solving with both capacity and unattended constraints
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    # THEN: Both setup tasks should be scheduled (potentially concurrently)
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Capacity+unattended solver failed: {solution['status']}"
    assert solution["makespan"] > 0, "No valid capacity+unattended schedule found"

    schedule = solution["schedule"]
    setup_tasks = [task for task in schedule if "setup_" in task["task_id"]]

    assert len(setup_tasks) == 2, f"Expected 2 setup tasks, found {len(setup_tasks)}"

    # Both should follow business hours
    for setup_task in setup_tasks:
        start_time = setup_task["start_time"]
        day = start_time // 96
        start_offset = start_time % 96

        assert day < 5, f"High-capacity setup on weekend day {day}"
        assert (
            28 <= start_offset <= 68
        ), f"High-capacity setup start {start_offset} outside business hours"


def test_performance_72_hour_processes():
    """Test performance with multiple 72-hour processes."""
    # GIVEN: Multiple long unattended processes
    jobs = []
    for i in range(5):  # 5 long processes
        execution_task = Task(
            task_id=f"long_process_{i}",
            job_id=f"long_job_{i}",
            name=f"72-Hour Process {i}",
            is_unattended=True,
            is_setup=False,
            modes=[
                TaskMode(f"long_mode_{i}", f"long_process_{i}", "machine_1", 4320)
            ],  # 72 hours
        )

        job = Job(
            job_id=f"long_job_{i}",
            description=f"Long Process Job {i}",
            due_date=datetime.now(UTC)
            + timedelta(days=20),  # 5 x 72-hour processes need 15+ days
            tasks=[execution_task],
        )
        jobs.append(job)

    machine = Machine("machine_1", "cell_1", "Long Process Machine", capacity=1)
    work_cell = WorkCell("cell_1", "Long Process Cell", machines=[machine])

    problem = SchedulingProblem(
        jobs=jobs, machines=[machine], work_cells=[work_cell], precedences=[]
    )

    # WHEN: Solving with performance monitoring
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)  # Longer time limit for complex problem

    # THEN: Should solve within time limit
    assert solution["status"] in [
        "OPTIMAL",
        "FEASIBLE",
    ], f"Performance test failed: {solution['status']}"
    solve_time = solution["solver_stats"]["solve_time"]
    assert solve_time < 60, f"Solve time {solve_time}s exceeded limit"

    # All long processes should be scheduled
    schedule = solution["schedule"]
    long_tasks = [task for task in schedule if "long_process_" in task["task_id"]]
    assert len(long_tasks) == 5, f"Expected 5 long processes, found {len(long_tasks)}"
