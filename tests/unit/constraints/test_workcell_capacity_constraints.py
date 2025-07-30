"""Unit tests for WorkCell capacity constraint functions.

Tests WorkCell capacity constraints that limit simultaneous machine usage
within physical workspace limitations.
"""

from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1 import add_workcell_capacity_constraints
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


class TestWorkCellCapacityConstraints:
    """Test WorkCell capacity constraint function."""

    def test_workcell_capacity_basic(self):
        """Test basic WorkCell capacity constraint with 2 machines, capacity 1."""
        # GIVEN: Model with 2 machines in WorkCell with capacity 1
        model = cp_model.CpModel()

        # Create task variables for 2 tasks that can run on either machine
        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t1"),
                model.NewIntVar(1, 10, "duration_t1"),
                model.NewIntVar(1, 60, "end_t1"),
                "interval_t1",
            ),
            ("j1", "t2"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t2"),
                model.NewIntVar(1, 10, "duration_t2"),
                model.NewIntVar(1, 60, "end_t2"),
                "interval_t2",
            ),
        }

        # Assignment variables for both tasks on both machines
        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t1", "m2"): model.NewBoolVar("assign_t1_m2"),
            ("j1", "t2", "m1"): model.NewBoolVar("assign_t2_m1"),
            ("j1", "t2", "m2"): model.NewBoolVar("assign_t2_m2"),
        }

        # Each task must be assigned to exactly one machine
        model.AddExactlyOne(
            [task_assigned[("j1", "t1", "m1")], task_assigned[("j1", "t1", "m2")]]
        )
        model.AddExactlyOne(
            [task_assigned[("j1", "t2", "m1")], task_assigned[("j1", "t2", "m2")]]
        )

        # Create machines and WorkCell
        machine1 = Machine("m1", "cell1", "Machine 1", capacity=1)
        machine2 = Machine("m2", "cell1", "Machine 2", capacity=1)
        work_cell = WorkCell(
            "cell1", "Cell 1", capacity=1, machines=[machine1, machine2]
        )

        # Create problem
        task1 = Task(
            "t1",
            "j1",
            "Task 1",
            modes=[
                TaskMode("m1_mode", "t1", "m1", 30),
                TaskMode("m2_mode", "t1", "m2", 30),
            ],
        )
        task2 = Task(
            "t2",
            "j1",
            "Task 2",
            modes=[
                TaskMode("m1_mode", "t2", "m1", 30),
                TaskMode("m2_mode", "t2", "m2", 30),
            ],
        )
        job = Job("j1", "Job 1", datetime.now(UTC), [task1, task2])
        problem = SchedulingProblem([job], [machine1, machine2], [work_cell], [])

        # WHEN: Adding WorkCell capacity constraints
        add_workcell_capacity_constraints(
            model, task_intervals, task_assigned, [work_cell], problem
        )

        # Force both tasks to run at the same time (should fail with capacity 1)
        model.Add(task_intervals[("j1", "t1")].StartExpr() == 10)
        model.Add(task_intervals[("j1", "t2")].StartExpr() == 10)
        model.Add(task_intervals[("j1", "t1")].SizeExpr() == 5)
        model.Add(task_intervals[("j1", "t2")].SizeExpr() == 5)

        # Force assignment to different machines
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j1", "t2", "m2")] == 1)

        # THEN: Solver should find this infeasible (2 machines active but capacity=1)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # This should be infeasible because both machines would be active simultaneously
        assert status == cp_model.INFEASIBLE

    def test_workcell_capacity_allows_sequential(self):
        """Test WorkCell capacity allows sequential execution."""
        # GIVEN: Same setup as above but with sequential execution
        model = cp_model.CpModel()

        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t1"),
                model.NewIntVar(1, 10, "duration_t1"),
                model.NewIntVar(1, 60, "end_t1"),
                "interval_t1",
            ),
            ("j1", "t2"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t2"),
                model.NewIntVar(1, 10, "duration_t2"),
                model.NewIntVar(1, 60, "end_t2"),
                "interval_t2",
            ),
        }

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t1", "m2"): model.NewBoolVar("assign_t1_m2"),
            ("j1", "t2", "m1"): model.NewBoolVar("assign_t2_m1"),
            ("j1", "t2", "m2"): model.NewBoolVar("assign_t2_m2"),
        }

        # Each task assigned to exactly one machine
        model.AddExactlyOne(
            [task_assigned[("j1", "t1", "m1")], task_assigned[("j1", "t1", "m2")]]
        )
        model.AddExactlyOne(
            [task_assigned[("j1", "t2", "m1")], task_assigned[("j1", "t2", "m2")]]
        )

        # Create machines and WorkCell
        machine1 = Machine("m1", "cell1", "Machine 1", capacity=1)
        machine2 = Machine("m2", "cell1", "Machine 2", capacity=1)
        work_cell = WorkCell(
            "cell1", "Cell 1", capacity=1, machines=[machine1, machine2]
        )

        # Create problem
        task1 = Task(
            "t1",
            "j1",
            "Task 1",
            modes=[
                TaskMode("m1_mode", "t1", "m1", 30),
                TaskMode("m2_mode", "t1", "m2", 30),
            ],
        )
        task2 = Task(
            "t2",
            "j1",
            "Task 2",
            modes=[
                TaskMode("m1_mode", "t2", "m1", 30),
                TaskMode("m2_mode", "t2", "m2", 30),
            ],
        )
        job = Job("j1", "Job 1", datetime.now(UTC), [task1, task2])
        problem = SchedulingProblem([job], [machine1, machine2], [work_cell], [])

        # WHEN: Adding WorkCell capacity constraints
        add_workcell_capacity_constraints(
            model, task_intervals, task_assigned, [work_cell], problem
        )

        # Force sequential execution (no overlap)
        model.Add(task_intervals[("j1", "t1")].StartExpr() == 0)
        model.Add(task_intervals[("j1", "t1")].SizeExpr() == 5)
        model.Add(task_intervals[("j1", "t2")].StartExpr() == 10)  # After t1 ends
        model.Add(task_intervals[("j1", "t2")].SizeExpr() == 5)

        # Force assignment to different machines
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j1", "t2", "m2")] == 1)

        # THEN: Solver should find this feasible (machines active at different times)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

    def test_workcell_capacity_higher_capacity(self):
        """Test WorkCell with capacity 2 allows 2 machines to run simultaneously."""
        # GIVEN: WorkCell with capacity 2
        model = cp_model.CpModel()

        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t1"),
                model.NewIntVar(1, 10, "duration_t1"),
                model.NewIntVar(1, 60, "end_t1"),
                "interval_t1",
            ),
            ("j1", "t2"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t2"),
                model.NewIntVar(1, 10, "duration_t2"),
                model.NewIntVar(1, 60, "end_t2"),
                "interval_t2",
            ),
        }

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
            ("j1", "t1", "m2"): model.NewBoolVar("assign_t1_m2"),
            ("j1", "t2", "m1"): model.NewBoolVar("assign_t2_m1"),
            ("j1", "t2", "m2"): model.NewBoolVar("assign_t2_m2"),
        }

        # Each task assigned to exactly one machine
        model.AddExactlyOne(
            [task_assigned[("j1", "t1", "m1")], task_assigned[("j1", "t1", "m2")]]
        )
        model.AddExactlyOne(
            [task_assigned[("j1", "t2", "m1")], task_assigned[("j1", "t2", "m2")]]
        )

        # Create machines and WorkCell with capacity 2
        machine1 = Machine("m1", "cell1", "Machine 1", capacity=1)
        machine2 = Machine("m2", "cell1", "Machine 2", capacity=1)
        work_cell = WorkCell(
            "cell1", "Cell 1", capacity=2, machines=[machine1, machine2]
        )

        # Create problem
        task1 = Task(
            "t1",
            "j1",
            "Task 1",
            modes=[
                TaskMode("m1_mode", "t1", "m1", 30),
                TaskMode("m2_mode", "t1", "m2", 30),
            ],
        )
        task2 = Task(
            "t2",
            "j1",
            "Task 2",
            modes=[
                TaskMode("m1_mode", "t2", "m1", 30),
                TaskMode("m2_mode", "t2", "m2", 30),
            ],
        )
        job = Job("j1", "Job 1", datetime.now(UTC), [task1, task2])
        problem = SchedulingProblem([job], [machine1, machine2], [work_cell], [])

        # WHEN: Adding WorkCell capacity constraints
        add_workcell_capacity_constraints(
            model, task_intervals, task_assigned, [work_cell], problem
        )

        # Force both tasks to run at the same time
        model.Add(task_intervals[("j1", "t1")].StartExpr() == 10)
        model.Add(task_intervals[("j1", "t2")].StartExpr() == 10)
        model.Add(task_intervals[("j1", "t1")].SizeExpr() == 5)
        model.Add(task_intervals[("j1", "t2")].SizeExpr() == 5)

        # Force assignment to different machines
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j1", "t2", "m2")] == 1)

        # THEN: Solver should find this feasible (capacity 2 allows 2 machines)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

    def test_workcell_capacity_skips_unconstrained(self):
        """Test WorkCell capacity constraint skips cells with capacity >= machine count.

        Tests that capacity constraints are not applied to workcells where the
        capacity is greater than or equal to the number of machines.
        """
        # GIVEN: WorkCell with capacity equal to machine count
        model = cp_model.CpModel()

        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t1"),
                model.NewIntVar(1, 10, "duration_t1"),
                model.NewIntVar(1, 60, "end_t1"),
                "interval_t1",
            ),
        }

        task_assigned = {
            ("j1", "t1", "m1"): model.NewBoolVar("assign_t1_m1"),
        }

        # Create single machine with WorkCell capacity 1 (should be skipped)
        machine1 = Machine("m1", "cell1", "Machine 1", capacity=1)
        work_cell = WorkCell("cell1", "Cell 1", capacity=1, machines=[machine1])

        # Create problem
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("m1_mode", "t1", "m1", 30)])
        job = Job("j1", "Job 1", datetime.now(UTC), [task1])
        problem = SchedulingProblem([job], [machine1], [work_cell], [])

        # WHEN: Adding WorkCell capacity constraints
        # This should not add any constraints since capacity >= machine count
        add_workcell_capacity_constraints(
            model, task_intervals, task_assigned, [work_cell], problem
        )

        # Force assignment
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)

        # THEN: Should be feasible (no constraints were added)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

    def test_workcell_capacity_no_eligible_machines(self):
        """Test WorkCell capacity constraint when no machines are eligible for tasks."""
        # GIVEN: WorkCell with machines but tasks can't run on them
        model = cp_model.CpModel()

        task_intervals = {
            ("j1", "t1"): model.NewIntervalVar(
                model.NewIntVar(0, 50, "start_t1"),
                model.NewIntVar(1, 10, "duration_t1"),
                model.NewIntVar(1, 60, "end_t1"),
                "interval_t1",
            ),
        }

        task_assigned = {}  # No assignment variables since no eligible machines

        # Create machines in WorkCell but task can only run on different machine
        machine1 = Machine("m1", "cell1", "Machine 1", capacity=1)
        machine2 = Machine("m2", "cell1", "Machine 2", capacity=1)
        machine3 = Machine("m3", "cell2", "Machine 3", capacity=1)  # Different cell
        work_cell = WorkCell(
            "cell1", "Cell 1", capacity=1, machines=[machine1, machine2]
        )

        # Create task that can only run on machine outside the WorkCell
        task1 = Task("t1", "j1", "Task 1", modes=[TaskMode("m3_mode", "t1", "m3", 30)])
        job = Job("j1", "Job 1", datetime.now(UTC), [task1])
        problem = SchedulingProblem(
            [job], [machine1, machine2, machine3], [work_cell], []
        )

        # WHEN: Adding WorkCell capacity constraints
        # Should not add constraints since no tasks can run on WorkCell machines
        add_workcell_capacity_constraints(
            model, task_intervals, task_assigned, [work_cell], problem
        )

        # THEN: Should be feasible (no constraints were added for this WorkCell)
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
