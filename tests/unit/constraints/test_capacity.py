"""Unit tests for machine capacity constraints."""

from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1.capacity import add_machine_capacity_constraints
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


def create_test_problem_with_capacity():
    """Create test problem with high-capacity machine."""
    # Machine with capacity 3
    high_cap_machine = Machine(
        resource_id="m1", cell_id="cell1", name="High Capacity Machine", capacity=3
    )

    # Regular machine with capacity 1
    regular_machine = Machine(
        resource_id="m2", cell_id="cell1", name="Regular Machine", capacity=1
    )

    machines = [high_cap_machine, regular_machine]

    # Create 4 tasks that can run on either machine
    jobs = []
    for job_idx in range(2):
        tasks = []
        for task_idx in range(2):
            task_id = f"task_{job_idx}_{task_idx}"
            modes = [
                TaskMode(
                    task_mode_id=f"mode_{task_id}_m1",
                    task_id=task_id,
                    machine_resource_id="m1",
                    duration_minutes=30,
                ),
                TaskMode(
                    task_mode_id=f"mode_{task_id}_m2",
                    task_id=task_id,
                    machine_resource_id="m2",
                    duration_minutes=30,
                ),
            ]
            tasks.append(
                Task(
                    task_id=task_id,
                    job_id=f"job_{job_idx}",
                    name=f"Task {task_idx}",
                    modes=modes,
                )
            )

        jobs.append(
            Job(
                job_id=f"job_{job_idx}",
                description=f"Job {job_idx}",
                due_date=datetime.now(UTC),
                tasks=tasks,
            )
        )

    return SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=[
            WorkCell(cell_id="cell1", name="Cell 1", capacity=2, machines=machines)
        ],
        precedences=[],
    )


def test_capacity_constraint_allows_parallel_tasks():
    """Test that high-capacity machine can run multiple tasks simultaneously."""
    # GIVEN: Model with high-capacity machine and multiple tasks
    model = cp_model.CpModel()
    problem = create_test_problem_with_capacity()

    # Create variables for all tasks in the problem
    task_intervals = {}
    task_assigned = {}

    # Create intervals for ALL tasks in the problem (not just the ones we're testing)
    for job in problem.jobs:
        for task in job.tasks:
            job_id = job.job_id
            task_id = task.task_id

            # For the first 3 tasks, schedule them at time 0-2
            if (job_id == "job_0" and task_id in ["task_0_0", "task_0_1"]) or (
                job_id == "job_1" and task_id == "task_1_0"
            ):
                start = model.NewIntVar(0, 0, f"start_{job_id}_{task_id}")
                end = model.NewIntVar(2, 2, f"end_{job_id}_{task_id}")
                interval = model.NewIntervalVar(
                    start, 2, end, f"interval_{job_id}_{task_id}"
                )

                # Assign to high-capacity machine m1
                task_assigned[(job_id, task_id, "m1")] = model.NewBoolVar(
                    f"assign_{job_id}_{task_id}_m1"
                )
                task_assigned[(job_id, task_id, "m2")] = model.NewBoolVar(
                    f"assign_{job_id}_{task_id}_m2"
                )
                model.Add(task_assigned[(job_id, task_id, "m1")] == 1)
                model.Add(task_assigned[(job_id, task_id, "m2")] == 0)
            else:
                # For the 4th task, schedule it later
                start = model.NewIntVar(3, 3, f"start_{job_id}_{task_id}")
                end = model.NewIntVar(5, 5, f"end_{job_id}_{task_id}")
                interval = model.NewIntervalVar(
                    start, 2, end, f"interval_{job_id}_{task_id}"
                )

                # Assign to regular machine m2
                task_assigned[(job_id, task_id, "m1")] = model.NewBoolVar(
                    f"assign_{job_id}_{task_id}_m1"
                )
                task_assigned[(job_id, task_id, "m2")] = model.NewBoolVar(
                    f"assign_{job_id}_{task_id}_m2"
                )
                model.Add(task_assigned[(job_id, task_id, "m1")] == 0)
                model.Add(task_assigned[(job_id, task_id, "m2")] == 1)

            task_intervals[(job_id, task_id)] = interval

    # WHEN: Adding capacity constraints
    add_machine_capacity_constraints(
        model, task_intervals, task_assigned, problem.machines, problem
    )

    # THEN: Model should be feasible (3 tasks on machine with capacity 3)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status == cp_model.OPTIMAL
    # First 3 tasks should run at time 0-2 on m1
    for job_id, task_id in [
        ("job_0", "task_0_0"),
        ("job_0", "task_0_1"),
        ("job_1", "task_1_0"),
    ]:
        assert solver.Value(task_intervals[(job_id, task_id)].StartExpr()) == 0
        assert solver.Value(task_intervals[(job_id, task_id)].EndExpr()) == 2


def test_capacity_constraint_prevents_overload():
    """Test that capacity constraints prevent overloading machine."""
    # GIVEN: Model with capacity 2 machine and 3 simultaneous tasks
    model = cp_model.CpModel()

    # Create machine with capacity 2
    machine = Machine(resource_id="m1", cell_id="cell1", name="Machine 1", capacity=2)

    # Create 3 tasks
    jobs = []
    for i in range(3):
        task = Task(
            task_id=f"t{i}",
            job_id=f"j{i}",
            name=f"Task {i}",
            modes=[TaskMode(f"mode_{i}", f"t{i}", "m1", 30)],
        )
        job = Job(
            job_id=f"j{i}",
            description=f"Job {i}",
            due_date=datetime.now(UTC),
            tasks=[task],
        )
        jobs.append(job)

    problem = SchedulingProblem(
        jobs=jobs, machines=[machine], work_cells=[], precedences=[]
    )

    # Create overlapping intervals
    task_intervals = {}
    task_assigned = {}

    for i in range(3):
        # All tasks want to run 0-2
        start = model.NewIntVar(0, 10, f"start_{i}")
        end = model.NewIntVar(0, 10, f"end_{i}")
        interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

        model.Add(start == 0)
        model.Add(end == 2)

        task_intervals[(f"j{i}", f"t{i}")] = interval
        task_assigned[(f"j{i}", f"t{i}", "m1")] = model.NewBoolVar(f"assign_{i}")
        model.Add(task_assigned[(f"j{i}", f"t{i}", "m1")] == 1)

    # WHEN: Adding capacity constraints
    add_machine_capacity_constraints(
        model, task_intervals, task_assigned, [machine], problem
    )

    # THEN: Model should be infeasible (3 tasks cannot run on capacity 2)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status == cp_model.INFEASIBLE


def test_capacity_constraint_with_mixed_assignments():
    """Test capacity constraints with tasks on different machines."""
    # GIVEN: Tasks distributed across machines
    model = cp_model.CpModel()
    problem = create_test_problem_with_capacity()

    task_intervals = {}
    task_assigned = {}

    # Task 0: on high-capacity machine
    task_intervals[("job_0", "task_0_0")] = model.NewIntervalVar(
        model.NewIntVar(0, 0, "s1"), 2, model.NewIntVar(2, 2, "e1"), "i1"
    )
    task_assigned[("job_0", "task_0_0", "m1")] = model.NewBoolVar("a1_m1")
    task_assigned[("job_0", "task_0_0", "m2")] = model.NewBoolVar("a1_m2")
    model.Add(task_assigned[("job_0", "task_0_0", "m1")] == 1)
    model.Add(task_assigned[("job_0", "task_0_0", "m2")] == 0)

    # Task 1: on regular machine
    task_intervals[("job_0", "task_0_1")] = model.NewIntervalVar(
        model.NewIntVar(0, 0, "s2"), 2, model.NewIntVar(2, 2, "e2"), "i2"
    )
    task_assigned[("job_0", "task_0_1", "m1")] = model.NewBoolVar("a2_m1")
    task_assigned[("job_0", "task_0_1", "m2")] = model.NewBoolVar("a2_m2")
    model.Add(task_assigned[("job_0", "task_0_1", "m1")] == 0)
    model.Add(task_assigned[("job_0", "task_0_1", "m2")] == 1)

    # Task 2: on high-capacity machine
    task_intervals[("job_1", "task_1_0")] = model.NewIntervalVar(
        model.NewIntVar(0, 0, "s3"), 2, model.NewIntVar(2, 2, "e3"), "i3"
    )
    task_assigned[("job_1", "task_1_0", "m1")] = model.NewBoolVar("a3_m1")
    task_assigned[("job_1", "task_1_0", "m2")] = model.NewBoolVar("a3_m2")
    model.Add(task_assigned[("job_1", "task_1_0", "m1")] == 1)
    model.Add(task_assigned[("job_1", "task_1_0", "m2")] == 0)

    # Task 3 (job_1, task_1_1): on regular machine, later time
    task_intervals[("job_1", "task_1_1")] = model.NewIntervalVar(
        model.NewIntVar(3, 3, "s4"), 2, model.NewIntVar(5, 5, "e4"), "i4"
    )
    task_assigned[("job_1", "task_1_1", "m1")] = model.NewBoolVar("a4_m1")
    task_assigned[("job_1", "task_1_1", "m2")] = model.NewBoolVar("a4_m2")
    model.Add(task_assigned[("job_1", "task_1_1", "m1")] == 0)
    model.Add(task_assigned[("job_1", "task_1_1", "m2")] == 1)

    # WHEN: Adding capacity constraints
    add_machine_capacity_constraints(
        model, task_intervals, task_assigned, problem.machines, problem
    )

    # THEN: Should be feasible (2 tasks on capacity 3, 1 task on capacity 1)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status == cp_model.OPTIMAL


def test_capacity_constraint_skips_unit_capacity():
    """Test that unit capacity machines are skipped (handled by no-overlap)."""
    # GIVEN: Only unit capacity machines
    model = cp_model.CpModel()

    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Machine 1", capacity=1),
        Machine(resource_id="m2", cell_id="cell1", name="Machine 2", capacity=1),
    ]

    problem = SchedulingProblem(
        jobs=[], machines=machines, work_cells=[], precedences=[]
    )

    # WHEN: Adding capacity constraints
    # Should not add any constraints since all machines have capacity 1
    constraint_count_before = len(model.Proto().constraints)

    add_machine_capacity_constraints(model, {}, {}, machines, problem)

    constraint_count_after = len(model.Proto().constraints)

    # THEN: No constraints should be added
    assert constraint_count_after == constraint_count_before
