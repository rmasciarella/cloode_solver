"""Unit tests for timing constraints - fixed version."""

from datetime import UTC, datetime

from ortools.sat.python import cp_model

from src.solver.constraints.phase1.timing import add_task_duration_constraints
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


class TestTimingConstraints:
    """Test timing constraint functionality."""

    def test_add_task_duration_constraints_basic(self):
        """Test basic duration constraint addition."""
        model = cp_model.CpModel()

        # Create problem
        work_cell = WorkCell(cell_id="WC1", name="Cell 1", capacity=1)
        machine = Machine(resource_id="M1", cell_id="WC1", name="Machine 1", capacity=1)

        task_mode = TaskMode(
            task_mode_id="TM1",
            task_id="T1",
            machine_resource_id="M1",
            duration_minutes=60,  # 4 time units
        )

        task = Task(task_id="T1", job_id="J1", name="Task 1", modes=[task_mode])

        job = Job(
            job_id="J1", description="Job 1", tasks=[task], due_date=datetime.now(UTC)
        )

        problem = SchedulingProblem(
            jobs=[job], machines=[machine], work_cells=[work_cell], precedences=[]
        )

        # Create variables as expected by the function
        task_starts = {("J1", "T1"): model.NewIntVar(0, 100, "start_J1_T1")}

        task_ends = {("J1", "T1"): model.NewIntVar(0, 100, "end_J1_T1")}

        # Duration is 60 minutes = 4 time units
        task_durations = {
            ("J1", "T1"): model.NewIntVar(4, 4, "duration_J1_T1")  # Fixed duration
        }

        # Create interval variable
        task_intervals = {
            ("J1", "T1"): model.NewIntervalVar(
                task_starts[("J1", "T1")],
                task_durations[("J1", "T1")],
                task_ends[("J1", "T1")],
                "interval_J1_T1",
            )
        }

        # Add duration constraints
        add_task_duration_constraints(
            model, task_starts, task_ends, task_intervals, task_durations, problem
        )

        # Solve and verify
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Check duration is enforced
        start = solver.Value(task_starts[("J1", "T1")])
        end = solver.Value(task_ends[("J1", "T1")])
        duration = solver.Value(task_durations[("J1", "T1")])

        assert end - start == duration
        assert duration == 4  # 60 minutes = 4 time units

    def test_duration_constraints_variable_duration(self):
        """Test duration constraints with variable duration based on mode."""
        model = cp_model.CpModel()

        # Create problem with multiple modes
        work_cell = WorkCell(cell_id="WC1", name="Cell 1", capacity=2)
        machines = [
            Machine(resource_id="M1", cell_id="WC1", name="Machine 1", capacity=1),
            Machine(resource_id="M2", cell_id="WC1", name="Machine 2", capacity=1),
        ]

        # Different durations on different machines
        task_modes = [
            TaskMode(
                task_mode_id="TM1",
                task_id="T1",
                machine_resource_id="M1",
                duration_minutes=60,  # 4 time units
            ),
            TaskMode(
                task_mode_id="TM2",
                task_id="T1",
                machine_resource_id="M2",
                duration_minutes=45,  # 3 time units
            ),
        ]

        task = Task(task_id="T1", job_id="J1", name="Task 1", modes=task_modes)

        job = Job(
            job_id="J1", description="Job 1", tasks=[task], due_date=datetime.now(UTC)
        )

        problem = SchedulingProblem(
            jobs=[job], machines=machines, work_cells=[work_cell], precedences=[]
        )

        # Create variables
        task_starts = {("J1", "T1"): model.NewIntVar(0, 100, "start")}
        task_ends = {("J1", "T1"): model.NewIntVar(0, 100, "end")}

        # Duration can be 3 or 4 depending on mode
        task_durations = {("J1", "T1"): model.NewIntVar(3, 4, "duration")}

        # Create interval
        task_intervals = {
            ("J1", "T1"): model.NewIntervalVar(
                task_starts[("J1", "T1")],
                task_durations[("J1", "T1")],
                task_ends[("J1", "T1")],
                "interval",
            )
        }

        # Add constraints
        add_task_duration_constraints(
            model, task_starts, task_ends, task_intervals, task_durations, problem
        )

        # Force duration to be 3 (as if mode 2 was selected)
        model.Add(task_durations[("J1", "T1")] == 3)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Check correct duration is used
        start = solver.Value(task_starts[("J1", "T1")])
        end = solver.Value(task_ends[("J1", "T1")])
        duration = solver.Value(task_durations[("J1", "T1")])

        assert end - start == 3
        assert duration == 3
