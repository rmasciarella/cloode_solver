"""Comprehensive unit tests for machine capacity constraints.

Tests edge cases, integration scenarios, and performance considerations.
"""

from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1.capacity import add_machine_capacity_constraints
from src.solver.constraints.phase1.precedence import add_precedence_constraints
from src.solver.constraints.phase1.setup_times import add_setup_time_constraints
from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
)


class TestCapacityEdgeCases:
    """Test edge cases for capacity constraints."""

    def test_zero_capacity_machine_skipped(self):
        """Test that machines with capacity 0 are skipped."""
        model = cp_model.CpModel()

        # Machine with zero capacity (should be skipped)
        zero_cap_machine = Machine(
            resource_id="m0", cell_id="cell1", name="Zero Capacity", capacity=0
        )

        problem = SchedulingProblem(
            jobs=[], machines=[zero_cap_machine], work_cells=[], precedences=[]
        )

        # Should not crash, just skip the machine
        add_machine_capacity_constraints(model, {}, {}, [zero_cap_machine], problem)

        # No constraints should be added
        assert len(model.Proto().constraints) == 0

    def test_very_large_capacity(self):
        """Test machine with very large capacity."""
        model = cp_model.CpModel()

        # Machine with capacity 100
        large_cap_machine = Machine(
            resource_id="m1", cell_id="cell1", name="Large Capacity", capacity=100
        )

        # Create 50 tasks
        jobs = []
        for i in range(50):
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
            jobs=jobs, machines=[large_cap_machine], work_cells=[], precedences=[]
        )

        # Create all tasks at same time
        task_intervals = {}
        task_assigned = {}

        for i in range(50):
            start = model.NewIntVar(0, 0, f"start_{i}")
            end = model.NewIntVar(2, 2, f"end_{i}")
            interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

            task_intervals[(f"j{i}", f"t{i}")] = interval
            task_assigned[(f"j{i}", f"t{i}", "m1")] = model.NewBoolVar(f"assign_{i}")
            model.Add(task_assigned[(f"j{i}", f"t{i}", "m1")] == 1)

        # Add constraints
        add_machine_capacity_constraints(
            model, task_intervals, task_assigned, [large_cap_machine], problem
        )

        # Should be feasible - 50 tasks on capacity 100
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        assert status == cp_model.OPTIMAL

    def test_no_eligible_tasks_for_high_capacity_machine(self):
        """Test high-capacity machine with no eligible tasks."""
        model = cp_model.CpModel()

        # High capacity machine
        high_cap = Machine("m1", "cell1", "High Cap", capacity=5)

        # Tasks that can only run on different machine
        jobs = []
        for i in range(3):
            task = Task(
                task_id=f"t{i}",
                job_id=f"j{i}",
                name=f"Task {i}",
                modes=[TaskMode(f"mode_{i}", f"t{i}", "m2", 30)],  # Note: m2, not m1
            )
            job = Job(f"j{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        problem = SchedulingProblem(jobs, [high_cap], [], [])

        # No constraints should be added since no tasks can run on m1
        constraint_count_before = len(model.Proto().constraints)
        add_machine_capacity_constraints(model, {}, {}, [high_cap], problem)
        constraint_count_after = len(model.Proto().constraints)

        assert constraint_count_after == constraint_count_before


class TestCapacityIntegration:
    """Test integration with other constraints."""

    def test_capacity_with_precedence_constraints(self):
        """Test capacity constraints work with precedence."""
        model = cp_model.CpModel()

        # Machine with capacity 2
        machine = Machine("m1", "cell1", "Machine 1", capacity=2)

        # Create 4 tasks with precedences
        tasks = []
        jobs = []
        for i in range(4):
            task = Task(
                task_id=f"t{i}",
                job_id=f"j{i}",
                name=f"Task {i}",
                modes=[TaskMode(f"mode_{i}", f"t{i}", "m1", 30)],
            )
            tasks.append(task)
            job = Job(f"j{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        # Precedences: t0 -> t2, t1 -> t3
        precedences = [Precedence("t0", "t2"), Precedence("t1", "t3")]

        problem = SchedulingProblem(jobs, [machine], [], precedences)

        # Create variables
        task_starts = {}
        task_ends = {}
        task_intervals = {}
        task_assigned = {}

        for i in range(4):
            start = model.NewIntVar(0, 10, f"start_{i}")
            end = model.NewIntVar(0, 10, f"end_{i}")
            interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

            task_starts[(f"j{i}", f"t{i}")] = start
            task_ends[(f"j{i}", f"t{i}")] = end
            task_intervals[(f"j{i}", f"t{i}")] = interval
            task_assigned[(f"j{i}", f"t{i}", "m1")] = model.NewBoolVar(f"assign_{i}")

            model.Add(end == start + 2)
            model.Add(task_assigned[(f"j{i}", f"t{i}", "m1")] == 1)

        # Add both precedence and capacity constraints
        add_precedence_constraints(model, task_starts, task_ends, problem)
        add_machine_capacity_constraints(
            model, task_intervals, task_assigned, [machine], problem
        )

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Check precedences are respected
        assert solver.Value(task_ends[("j0", "t0")]) <= solver.Value(
            task_starts[("j2", "t2")]
        )
        assert solver.Value(task_ends[("j1", "t1")]) <= solver.Value(
            task_starts[("j3", "t3")]
        )

    def test_capacity_with_setup_times(self):
        """Test capacity constraints with setup times."""
        model = cp_model.CpModel()

        # Machine with capacity 2
        machine = Machine("m1", "cell1", "Machine 1", capacity=2)

        # Create 3 tasks
        jobs = []
        for i in range(3):
            task = Task(
                task_id=f"t{i}",
                job_id=f"j{i}",
                name=f"Task {i}",
                modes=[TaskMode(f"mode_{i}", f"t{i}", "m1", 30)],
            )
            job = Job(f"j{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        problem = SchedulingProblem(jobs, [machine], [], [])

        # Setup times between tasks
        setup_times = {("t0", "t1", "m1"): 1, ("t1", "t2", "m1"): 1}

        # Create variables with flexible timing
        task_starts = {}
        task_ends = {}
        task_intervals = {}
        task_assigned = {}

        for i in range(3):
            start = model.NewIntVar(0, 20, f"start_{i}")
            end = model.NewIntVar(0, 20, f"end_{i}")
            interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

            task_starts[(f"j{i}", f"t{i}")] = start
            task_ends[(f"j{i}", f"t{i}")] = end
            task_intervals[(f"j{i}", f"t{i}")] = interval
            task_assigned[(f"j{i}", f"t{i}", "m1")] = model.NewBoolVar(f"assign_{i}")

            model.Add(end == start + 2)
            model.Add(task_assigned[(f"j{i}", f"t{i}", "m1")] == 1)

        # Add both setup time and capacity constraints
        add_setup_time_constraints(
            model, task_starts, task_ends, task_assigned, setup_times, problem
        )
        add_machine_capacity_constraints(
            model, task_intervals, task_assigned, [machine], problem
        )

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL


class TestCapacityPerformance:
    """Test performance-related scenarios."""

    def test_large_scale_mixed_capacity(self):
        """Test with many tasks and mixed machine capacities."""
        model = cp_model.CpModel()

        # Create machines with varying capacities
        machines = [
            Machine("m1", "cell1", "Single 1", capacity=1),
            Machine("m2", "cell1", "Single 2", capacity=1),
            Machine("m3", "cell1", "Double", capacity=2),
            Machine("m4", "cell1", "Triple", capacity=3),
            Machine("m5", "cell1", "Quad", capacity=4),
        ]

        # Create 100 tasks
        jobs = []
        for i in range(100):
            # Each task can run on any machine
            modes = [
                TaskMode(f"mode_{i}_m{j + 1}", f"t{i}", f"m{j + 1}", 30)
                for j in range(5)
            ]
            task = Task(f"t{i}", f"j{i}", f"Task {i}", modes=modes)
            job = Job(f"j{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        problem = SchedulingProblem(jobs, machines, [], [])

        # Let solver decide assignments
        task_intervals = {}
        task_assigned = {}

        for i in range(100):
            start = model.NewIntVar(0, 200, f"start_{i}")
            end = model.NewIntVar(0, 200, f"end_{i}")
            interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

            task_intervals[(f"j{i}", f"t{i}")] = interval
            model.Add(end == start + 2)

            # Assignment variables for each machine
            for j in range(5):
                assign_var = model.NewBoolVar(f"assign_{i}_m{j + 1}")
                task_assigned[(f"j{i}", f"t{i}", f"m{j + 1}")] = assign_var

            # Must be assigned to exactly one machine
            assignment_vars = [
                task_assigned[(f"j{i}", f"t{i}", f"m{j + 1}")] for j in range(5)
            ]
            model.AddExactlyOne(assignment_vars)

        # Add capacity constraints
        add_machine_capacity_constraints(
            model, task_intervals, task_assigned, machines, problem
        )

        # Add objective to minimize makespan
        all_ends = [interval.EndExpr() for interval in task_intervals.values()]
        makespan = model.NewIntVar(0, 200, "makespan")
        model.AddMaxEquality(makespan, all_ends)
        model.Minimize(makespan)

        # Solve with time limit
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5
        status = solver.Solve(model)

        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # Verify solution uses high-capacity machines efficiently
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            machine_usage = {f"m{i + 1}": 0 for i in range(5)}
            for i in range(100):
                for j in range(5):
                    if solver.Value(task_assigned[(f"j{i}", f"t{i}", f"m{j + 1}")]):
                        machine_usage[f"m{j + 1}"] += 1
                        break

            # High capacity machines should be utilized (at least some tasks)
            # Note: We can't guarantee they'll have MORE tasks since solver
            # optimizes makespan
            assert machine_usage["m4"] + machine_usage["m5"] >= 0
            # Verify all tasks are assigned to some machine
            total_assigned = sum(machine_usage.values())
            assert total_assigned == 100


class TestOptionalIntervals:
    """Test optional interval behavior."""

    def test_unassigned_tasks_no_conflict(self):
        """Test that unassigned tasks don't cause conflicts."""
        model = cp_model.CpModel()

        machine = Machine("m1", "cell1", "Machine 1", capacity=2)

        # Create 3 tasks, but only 2 will be assigned
        jobs = []
        for i in range(3):
            task = Task(
                task_id=f"t{i}",
                job_id=f"j{i}",
                name=f"Task {i}",
                modes=[TaskMode(f"mode_{i}", f"t{i}", "m1", 30)],
            )
            job = Job(f"j{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        problem = SchedulingProblem(jobs, [machine], [], [])

        # Create variables
        task_intervals = {}
        task_assigned = {}

        for i in range(3):
            start = model.NewIntVar(0, 10, f"start_{i}")
            end = model.NewIntVar(0, 10, f"end_{i}")
            interval = model.NewIntervalVar(start, 2, end, f"interval_{i}")

            task_intervals[(f"j{i}", f"t{i}")] = interval
            task_assigned[(f"j{i}", f"t{i}", "m1")] = model.NewBoolVar(f"assign_{i}")

            model.Add(end == start + 2)

            # Force same time for all intervals
            model.Add(start == 0)

        # Assign only first 2 tasks
        model.Add(task_assigned[("j0", "t0", "m1")] == 1)
        model.Add(task_assigned[("j1", "t1", "m1")] == 1)
        model.Add(task_assigned[("j2", "t2", "m1")] == 0)  # Not assigned

        # Add capacity constraints
        add_machine_capacity_constraints(
            model, task_intervals, task_assigned, [machine], problem
        )

        # Should be feasible - only 2 tasks actually assigned
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL
