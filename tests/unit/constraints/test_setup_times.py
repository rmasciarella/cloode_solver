"""Unit tests for setup time constraints."""

from datetime import UTC, datetime, timedelta

from ortools.sat.python import cp_model

from src.solver.constraints.phase1.setup_times import add_setup_time_constraints
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


def create_test_problem():
    """Create a simple test problem with 2 jobs, 2 tasks each, 2 machines."""
    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Machine 1"),
        Machine(resource_id="m2", cell_id="cell1", name="Machine 2"),
    ]

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
                    duration_minutes=45,
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
                due_date=datetime.now(UTC) + timedelta(hours=24),
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


def test_setup_time_constraints_basic():
    """Test that setup times are enforced between consecutive tasks."""
    # GIVEN: Model with two tasks that can run on same machine
    model = cp_model.CpModel()
    problem = create_test_problem()

    # Create variables
    task_starts = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "start_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "start_0_1"),
    }
    task_ends = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "end_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "end_0_1"),
    }

    # Add duration constraints
    model.Add(
        task_ends[("job_0", "task_0_0")] == task_starts[("job_0", "task_0_0")] + 2
    )
    model.Add(
        task_ends[("job_0", "task_0_1")] == task_starts[("job_0", "task_0_1")] + 2
    )

    # Both tasks assigned to machine 1
    task_assigned = {
        ("job_0", "task_0_0", "m1"): model.NewIntVar(0, 1, "assign_0_0_m1"),
        ("job_0", "task_0_1", "m1"): model.NewIntVar(0, 1, "assign_0_1_m1"),
        ("job_0", "task_0_0", "m2"): model.NewIntVar(0, 1, "assign_0_0_m2"),
        ("job_0", "task_0_1", "m2"): model.NewIntVar(0, 1, "assign_0_1_m2"),
    }

    # Force both tasks to machine 1
    model.Add(task_assigned[("job_0", "task_0_0", "m1")] == 1)
    model.Add(task_assigned[("job_0", "task_0_1", "m1")] == 1)

    # Add basic no-overlap constraint since tasks are on same machine
    # This is usually added by no_overlap constraints function
    b = model.NewBoolVar("task0_before_task1")
    model.Add(
        task_starts[("job_0", "task_0_1")] >= task_ends[("job_0", "task_0_0")]
    ).OnlyEnforceIf(b)
    model.Add(
        task_starts[("job_0", "task_0_0")] >= task_ends[("job_0", "task_0_1")]
    ).OnlyEnforceIf(b.Not())

    # Setup time of 5 units between tasks on machine 1
    setup_times = {
        ("task_0_0", "task_0_1", "m1"): 5,
        ("task_0_1", "task_0_0", "m1"): 0,  # No setup time in reverse direction
    }

    # WHEN: Adding setup time constraints
    add_setup_time_constraints(
        model, task_starts, task_ends, task_assigned, setup_times, problem
    )

    # Force task 0 to come before task 1
    model.Add(task_starts[("job_0", "task_0_0")] < task_starts[("job_0", "task_0_1")])

    # THEN: Solver respects setup time
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status == cp_model.OPTIMAL

    # Verify the schedule respects setup time
    task0_end = solver.Value(task_ends[("job_0", "task_0_0")])
    task1_start = solver.Value(task_starts[("job_0", "task_0_1")])

    # Since we forced task0 before task1, task1 should start at least
    # 5 units after task0 ends
    assert (
        task1_start >= task0_end + 5
    ), f"Task 1 starts at {task1_start}, but should start at least at {task0_end + 5}"


def test_setup_time_constraints_different_machines():
    """Test that setup times are NOT enforced when tasks on different machines."""
    # GIVEN: Model with two tasks on different machines
    model = cp_model.CpModel()
    problem = create_test_problem()

    task_starts = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "start_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "start_0_1"),
    }
    task_ends = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "end_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "end_0_1"),
    }

    # Add duration constraints
    model.Add(
        task_ends[("job_0", "task_0_0")] == task_starts[("job_0", "task_0_0")] + 2
    )
    model.Add(
        task_ends[("job_0", "task_0_1")] == task_starts[("job_0", "task_0_1")] + 2
    )

    # Tasks on different machines
    task_assigned = {
        ("job_0", "task_0_0", "m1"): model.NewIntVar(0, 1, "assign_0_0_m1"),
        ("job_0", "task_0_1", "m1"): model.NewIntVar(0, 1, "assign_0_1_m1"),
        ("job_0", "task_0_0", "m2"): model.NewIntVar(0, 1, "assign_0_0_m2"),
        ("job_0", "task_0_1", "m2"): model.NewIntVar(0, 1, "assign_0_1_m2"),
    }

    # Task 0 on machine 1, task 1 on machine 2
    model.Add(task_assigned[("job_0", "task_0_0", "m1")] == 1)
    model.Add(task_assigned[("job_0", "task_0_0", "m2")] == 0)
    model.Add(task_assigned[("job_0", "task_0_1", "m1")] == 0)
    model.Add(task_assigned[("job_0", "task_0_1", "m2")] == 1)

    # Setup time between tasks (should not apply)
    setup_times = {
        ("task_0_0", "task_0_1", "m1"): 10,
        ("task_0_0", "task_0_1", "m2"): 10,
    }

    # WHEN: Adding setup time constraints
    add_setup_time_constraints(
        model, task_starts, task_ends, task_assigned, setup_times, problem
    )

    # THEN: Tasks can overlap since on different machines
    solver = cp_model.CpSolver()

    # Force tasks to overlap
    model.Add(task_starts[("job_0", "task_0_1")] == 0)
    model.Add(task_starts[("job_0", "task_0_0")] == 0)

    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL

    # Both tasks can start at time 0
    assert solver.Value(task_starts[("job_0", "task_0_0")]) == 0
    assert solver.Value(task_starts[("job_0", "task_0_1")]) == 0


def test_setup_time_constraints_zero_setup():
    """Test that zero setup time allows immediate succession."""
    # GIVEN: Model with zero setup time
    model = cp_model.CpModel()
    problem = create_test_problem()

    task_starts = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "start_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "start_0_1"),
    }
    task_ends = {
        ("job_0", "task_0_0"): model.NewIntVar(0, 100, "end_0_0"),
        ("job_0", "task_0_1"): model.NewIntVar(0, 100, "end_0_1"),
    }

    # Add duration constraints
    model.Add(
        task_ends[("job_0", "task_0_0")] == task_starts[("job_0", "task_0_0")] + 2
    )
    model.Add(
        task_ends[("job_0", "task_0_1")] == task_starts[("job_0", "task_0_1")] + 2
    )

    # Both on same machine
    task_assigned = {
        ("job_0", "task_0_0", "m1"): model.NewIntVar(0, 1, "assign_0_0_m1"),
        ("job_0", "task_0_1", "m1"): model.NewIntVar(0, 1, "assign_0_1_m1"),
    }

    model.Add(task_assigned[("job_0", "task_0_0", "m1")] == 1)
    model.Add(task_assigned[("job_0", "task_0_1", "m1")] == 1)

    # Zero setup time
    setup_times = {}  # No setup times defined

    # WHEN: Adding constraints
    add_setup_time_constraints(
        model, task_starts, task_ends, task_assigned, setup_times, problem
    )

    # Force immediate succession
    model.Add(task_starts[("job_0", "task_0_1")] == task_ends[("job_0", "task_0_0")])

    # THEN: Should be feasible
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status == cp_model.OPTIMAL
    assert solver.Value(task_starts[("job_0", "task_0_1")]) == solver.Value(
        task_ends[("job_0", "task_0_0")]
    )
