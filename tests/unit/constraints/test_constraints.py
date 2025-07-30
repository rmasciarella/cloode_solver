"""Unit tests for constraint functions.

Tests each constraint function independently with OR-Tools models.
"""

from collections import defaultdict
from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1 import (
    add_machine_assignment_constraints,
    add_machine_no_overlap_constraints,
    add_precedence_constraints,
    add_redundant_precedence_constraints,
    add_task_duration_constraints,
)
from src.solver.models.problem import Job, Precedence, SchedulingProblem, Task, TaskMode


class TestTaskDurationConstraints:
    """Test task duration constraint function."""

    def test_duration_constraints_basic(self):
        """Test that duration constraints link start, end, and duration."""
        # GIVEN: Model with task variables
        model = cp_model.CpModel()

        task_starts = {("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1")}
        task_ends = {("j1", "t1"): model.NewIntVar(0, 100, "end_j1_t1")}
        task_durations = {("j1", "t1"): model.NewIntVar(1, 10, "duration_j1_t1")}
        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                task_starts[("j1", "t1")],
                task_durations[("j1", "t1")],
                task_ends[("j1", "t1")],
                "interval_j1_t1",
            )
        }

        # Create problem with one task
        task = Task("t1", "j1", "Task 1", modes=[TaskMode("m1", "t1", "m1", 30)])
        job = Job(
            job_id="j1", description="Job 1", due_date=datetime.now(UTC), tasks=[task]
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Adding duration constraints
        add_task_duration_constraints(
            model, task_starts, task_ends, task_intervals, task_durations, problem
        )

        # THEN: Constraint enforces end = start + duration
        # Set specific values and solve
        model.Add(task_starts[("j1", "t1")] == 5)
        model.Add(task_durations[("j1", "t1")] == 3)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
        assert solver.Value(task_ends[("j1", "t1")]) == 8  # 5 + 3

    def test_duration_constraints_multiple_tasks(self):
        """Test duration constraints with multiple tasks."""
        # GIVEN: Multiple tasks
        model = cp_model.CpModel()

        tasks = []
        task_starts = {}
        task_ends = {}
        task_durations = {}
        task_intervals = {}

        for i in range(3):
            task_id = f"t{i}"
            key = ("j1", task_id)

            task_starts[key] = model.NewIntVar(0, 100, f"start_{task_id}")
            task_ends[key] = model.NewIntVar(0, 100, f"end_{task_id}")
            task_durations[key] = model.NewIntVar(1, 10, f"duration_{task_id}")
            task_intervals[key] = model.NewIntervalVar(
                task_starts[key],
                task_durations[key],
                task_ends[key],
                f"interval_{task_id}",
            )

            task = Task(
                task_id, "j1", f"Task {i}", modes=[TaskMode(f"m{i}", task_id, "m1", 30)]
            )
            tasks.append(task)

        job = Job(
            job_id="j1", description="Job 1", due_date=datetime.now(UTC), tasks=tasks
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Adding constraints
        add_task_duration_constraints(
            model, task_starts, task_ends, task_intervals, task_durations, problem
        )

        # THEN: All tasks have duration constraints
        # Verify by solving with specific values
        for i in range(3):
            key = ("j1", f"t{i}")
            model.Add(task_starts[key] == i * 10)
            model.Add(task_durations[key] == 5)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
        for i in range(3):
            key = ("j1", f"t{i}")
            assert solver.Value(task_ends[key]) == i * 10 + 5


class TestPrecedenceConstraints:
    """Test precedence constraint function."""

    def test_precedence_constraints_basic(self):
        """Test basic precedence constraint."""
        # GIVEN: Two tasks with precedence
        model = cp_model.CpModel()

        task_starts = {
            ("j1", "t1"): model.NewIntVar(0, 100, "start_t1"),
            ("j1", "t2"): model.NewIntVar(0, 100, "start_t2"),
        }
        task_ends = {
            ("j1", "t1"): model.NewIntVar(0, 100, "end_t1"),
            ("j1", "t2"): model.NewIntVar(0, 100, "end_t2"),
        }

        # Create tasks and precedence
        task1 = Task("t1", "j1", "Task 1")
        task2 = Task("t2", "j1", "Task 2")
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task1, task2],
        )
        precedence = Precedence("t1", "t2")
        problem = SchedulingProblem([job], [], [], [precedence])

        # WHEN: Adding precedence constraints
        add_precedence_constraints(model, task_starts, task_ends, problem)

        # THEN: Task 2 must start after task 1 ends
        model.Add(task_starts[("j1", "t1")] == 10)
        model.Add(task_ends[("j1", "t1")] == 15)
        model.Add(task_starts[("j1", "t2")] >= 0)  # Can be anything >= 15

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
        assert solver.Value(task_starts[("j1", "t2")]) >= 15

    def test_precedence_constraints_missing_tasks(self):
        """Test precedence with missing tasks is ignored."""
        # GIVEN: Precedence referencing non-existent task
        model = cp_model.CpModel()

        task_starts = {("j1", "t1"): model.NewIntVar(0, 100, "start_t1")}
        task_ends = {("j1", "t1"): model.NewIntVar(0, 100, "end_t1")}

        task1 = Task("t1", "j1", "Task 1")
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task1]
        )
        precedence = Precedence("t1", "t999")  # t999 doesn't exist
        problem = SchedulingProblem([job], [], [], [precedence])

        # WHEN: Adding precedence constraints
        add_precedence_constraints(model, task_starts, task_ends, problem)

        # THEN: No constraint added, model still solvable
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.OPTIMAL

    def test_precedence_chain(self):
        """Test chain of precedences."""
        # GIVEN: Three tasks in sequence
        model = cp_model.CpModel()

        task_starts = {}
        task_ends = {}
        tasks = []

        for i in range(1, 4):
            key = ("j1", f"t{i}")
            task_starts[key] = model.NewIntVar(0, 100, f"start_t{i}")
            task_ends[key] = model.NewIntVar(0, 100, f"end_t{i}")
            task = Task(f"t{i}", "j1", f"Task {i}")
            tasks.append(task)

        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=tasks
        )
        precedences = [Precedence("t1", "t2"), Precedence("t2", "t3")]
        problem = SchedulingProblem([job], [], [], precedences)

        # WHEN: Adding precedence constraints
        add_precedence_constraints(model, task_starts, task_ends, problem)

        # Set task durations
        for i in range(1, 4):
            key = ("j1", f"t{i}")
            model.Add(task_ends[key] == task_starts[key] + 5)

        # Force first task to start at 0
        model.Add(task_starts[("j1", "t1")] == 0)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # THEN: Tasks execute in sequence
        assert status == cp_model.OPTIMAL
        assert solver.Value(task_starts[("j1", "t1")]) == 0
        assert solver.Value(task_starts[("j1", "t2")]) >= 5
        assert solver.Value(task_starts[("j1", "t3")]) >= 10


class TestMachineAssignmentConstraints:
    """Test machine assignment constraint function."""

    def test_machine_assignment_exactly_one(self):
        """Test that each task is assigned to exactly one machine."""
        # GIVEN: Task with multiple eligible machines
        model = cp_model.CpModel()

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t1", "m2"): model.NewBoolVar("assign_t1_m2"),
            ("j1", "t1", "m3"): model.NewBoolVar("assign_t1_m3"),
        }
        task_durations = {("j1", "t1"): model.NewIntVar(1, 10, "duration_t1")}

        # Create task with three modes
        modes = [
            TaskMode("mode1", "t1", "m1", 30),
            TaskMode("mode2", "t1", "m2", 45),
            TaskMode("mode3", "t1", "m3", 60),
        ]
        task = Task("t1", "j1", "Task 1", modes=modes)
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Adding assignment constraints
        add_machine_assignment_constraints(
            model, task_assigned, task_durations, problem
        )

        # THEN: Exactly one machine selected
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
        assigned_count = sum(
            solver.Value(task_assigned[("j1", "t1", f"m{i}")]) for i in range(1, 4)
        )
        assert assigned_count == 1

    def test_machine_assignment_duration_link(self):
        """Test that duration depends on machine selection."""
        # GIVEN: Task with different durations per machine
        model = cp_model.CpModel()

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t1", "m2"): model.NewBoolVar("assign_t1_m2"),
        }
        task_durations = {("j1", "t1"): model.NewIntVar(0, 10, "duration_t1")}

        # Different durations: m1=2 units, m2=4 units
        modes = [
            TaskMode("mode1", "t1", "m1", 30),  # 2 time units
            TaskMode("mode2", "t1", "m2", 60),  # 4 time units
        ]
        task = Task("t1", "j1", "Task 1", modes=modes)
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Adding assignment constraints
        add_machine_assignment_constraints(
            model, task_assigned, task_durations, problem
        )

        # Force selection of m2
        model.Add(task_assigned[("j1", "t1", "m2")] == 1)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # THEN: Duration matches selected machine
        assert status == cp_model.OPTIMAL
        assert solver.Value(task_durations[("j1", "t1")]) == 4

    def test_machine_assignment_no_modes(self):
        """Test task with no modes (shouldn't happen but handle gracefully)."""
        # GIVEN: Task with no modes
        model = cp_model.CpModel()
        task_assigned = {}
        task_durations = {("j1", "t1"): model.NewIntVar(1, 10, "duration_t1")}

        task = Task("t1", "j1", "Task 1", modes=[])
        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=[task]
        )
        problem = SchedulingProblem([job], [], [], [])

        # WHEN: Adding assignment constraints
        add_machine_assignment_constraints(
            model, task_assigned, task_durations, problem
        )

        # THEN: No constraints added, model still solvable
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.OPTIMAL


class TestMachineNoOverlapConstraints:
    """Test machine no-overlap constraint function."""

    def test_no_overlap_basic(self):
        """Test that tasks on same machine don't overlap."""
        # GIVEN: Two tasks that could use same machine
        model = cp_model.CpModel()

        # Create intervals
        interval1 = model.NewIntervalVar(
            model.NewIntVar(0, 100, "start1"),
            model.NewIntVar(5, 5, "size1"),  # Fixed size 5
            model.NewIntVar(0, 100, "end1"),
            "interval1",
        )
        interval2 = model.NewIntervalVar(
            model.NewIntVar(0, 100, "start2"),
            model.NewIntVar(5, 5, "size2"),  # Fixed size 5
            model.NewIntVar(0, 100, "end2"),
            "interval2",
        )

        task_intervals = {("j1", "t1"): interval1, ("j1", "t2"): interval2}

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t2", "m1"): model.NewBoolVar("assign_t2_m1"),
        }

        machine_intervals = defaultdict(list)

        # Create tasks
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("mode1", "t1", "m1", 75)])
        task2 = Task("t2", "j1", "Task 2", modes=[TaskMode("mode2", "t2", "m1", 75)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task1, task2],
        )
        problem = SchedulingProblem([job], [], [], [])

        # Force both tasks to use m1
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j1", "t2", "m1")] == 1)

        # WHEN: Adding no-overlap constraints
        add_machine_no_overlap_constraints(
            model, task_intervals, task_assigned, machine_intervals, problem
        )

        # THEN: Tasks don't overlap
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
        start1 = solver.Value(interval1.StartExpr())
        end1 = solver.Value(interval1.EndExpr())
        start2 = solver.Value(interval2.StartExpr())
        end2 = solver.Value(interval2.EndExpr())

        # Either task1 before task2 or task2 before task1
        assert (end1 <= start2) or (end2 <= start1)

    def test_no_overlap_different_machines(self):
        """Test that tasks on different machines can overlap."""
        # GIVEN: Two tasks on different machines
        model = cp_model.CpModel()

        # Create intervals at same time
        interval1 = model.NewIntervalVar(
            model.NewIntVar(10, 10, "start1"),  # Fixed at 10
            model.NewIntVar(5, 5, "size1"),
            model.NewIntVar(15, 15, "end1"),  # Fixed at 15
            "interval1",
        )
        interval2 = model.NewIntervalVar(
            model.NewIntVar(12, 12, "start2"),  # Fixed at 12 (overlaps)
            model.NewIntVar(5, 5, "size2"),
            model.NewIntVar(17, 17, "end2"),  # Fixed at 17
            "interval2",
        )

        task_intervals = {("j1", "t1"): interval1, ("j1", "t2"): interval2}

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t2", "m2"): model.NewBoolVar("assign_t2_m2"),
        }

        machine_intervals = defaultdict(list)

        # Create tasks on different machines
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("mode1", "t1", "m1", 75)])
        task2 = Task("t2", "j1", "Task 2", modes=[TaskMode("mode2", "t2", "m2", 75)])
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task1, task2],
        )
        problem = SchedulingProblem([job], [], [], [])

        # Assign to different machines
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j1", "t2", "m2")] == 1)

        # WHEN: Adding no-overlap constraints
        add_machine_no_overlap_constraints(
            model, task_intervals, task_assigned, machine_intervals, problem
        )

        # THEN: Model is still feasible (tasks can overlap)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.OPTIMAL


class TestRedundantPrecedenceConstraints:
    """Test redundant precedence constraint function."""

    def test_redundant_transitive_constraints(self):
        """Test that transitive precedences are added."""
        # GIVEN: Chain A->B->C
        model = cp_model.CpModel()

        task_starts = {
            ("j1", "A"): model.NewIntVar(0, 100, "start_A"),
            ("j1", "B"): model.NewIntVar(0, 100, "start_B"),
            ("j1", "C"): model.NewIntVar(0, 100, "start_C"),
        }
        task_ends = {
            ("j1", "A"): model.NewIntVar(0, 100, "end_A"),
            ("j1", "B"): model.NewIntVar(0, 100, "end_B"),
            ("j1", "C"): model.NewIntVar(0, 100, "end_C"),
        }

        # Create tasks and precedences
        taskA = Task("A", "j1", "Task A")
        taskB = Task("B", "j1", "Task B")
        taskC = Task("C", "j1", "Task C")
        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[taskA, taskB, taskC],
        )

        precedences = [Precedence("A", "B"), Precedence("B", "C")]
        problem = SchedulingProblem([job], [], [], precedences)

        # Add basic precedences first
        add_precedence_constraints(model, task_starts, task_ends, problem)

        # WHEN: Adding redundant constraints
        add_redundant_precedence_constraints(model, task_starts, task_ends, problem)

        # Set specific times to test
        model.Add(task_starts[("j1", "A")] == 0)
        model.Add(task_ends[("j1", "A")] == 5)
        model.Add(task_starts[("j1", "B")] == 5)
        model.Add(task_ends[("j1", "B")] == 10)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # THEN: C starts after A ends (transitive constraint)
        assert status == cp_model.OPTIMAL
        assert solver.Value(task_starts[("j1", "C")]) >= 5  # After A ends

    def test_redundant_no_deep_chains(self):
        """Test that we don't create chains deeper than 3."""
        # GIVEN: Chain A->B->C->D
        model = cp_model.CpModel()

        task_starts = {}
        task_ends = {}
        tasks = []

        for task_id in ["A", "B", "C", "D"]:
            key = ("j1", task_id)
            task_starts[key] = model.NewIntVar(0, 100, f"start_{task_id}")
            task_ends[key] = model.NewIntVar(0, 100, f"end_{task_id}")
            task = Task(task_id, "j1", f"Task {task_id}")
            tasks.append(task)

        job = Job(
            job_id="j1", description="Job", due_date=datetime.now(UTC), tasks=tasks
        )

        precedences = [Precedence("A", "B"), Precedence("B", "C"), Precedence("C", "D")]
        problem = SchedulingProblem([job], [], [], precedences)

        # WHEN: Adding redundant constraints
        add_redundant_precedence_constraints(model, task_starts, task_ends, problem)

        # THEN: Model is still solvable (no constraint explosion)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.OPTIMAL
