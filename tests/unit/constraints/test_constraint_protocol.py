"""Unit tests for constraint protocol/interface."""

from typing import Any

from ortools.sat.python import cp_model

from src.solver.models.problem import Job, Machine, SchedulingProblem, Task, TaskMode


def mock_constraint_function(
    model: cp_model.CpModel, variables: dict[str, Any], _problem: SchedulingProblem
) -> None:
    """Create mock constraints following the protocol."""
    # Add simple constraints for testing
    if "task_starts" in variables:
        for (_job_id, _task_id), start_var in variables["task_starts"].items():
            model.Add(start_var >= 0)
            model.Add(start_var <= 100)


class TestConstraintProtocol:
    """Test the constraint function protocol."""

    def test_constraint_function_signature(self):
        """Test that constraint functions follow the protocol."""
        # Mock function should match the protocol
        assert callable(mock_constraint_function)

        # Test it can be called with correct arguments
        model = cp_model.CpModel()
        variables = {}
        problem = create_test_problem()

        # Should not raise
        mock_constraint_function(model, variables, problem)

    def test_constraint_with_variables(self):
        """Test constraint function with actual variables."""
        model = cp_model.CpModel()

        # Create variables
        variables = {
            "task_starts": {
                ("J1", "T1"): model.NewIntVar(0, 200, "start_j1_t1"),
                ("J1", "T2"): model.NewIntVar(0, 200, "start_j1_t2"),
            }
        }

        problem = create_test_problem()

        # Apply constraint
        mock_constraint_function(model, variables, problem)

        # Verify constraints were added by solving
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Check that constraints are respected
        for (_job_id, _task_id), start_var in variables["task_starts"].items():
            value = solver.Value(start_var)
            assert 0 <= value <= 100  # Our constraint bounds

    def test_multiple_constraint_functions(self):
        """Test composing multiple constraint functions."""

        def constraint1(model, variables, _problem):
            """First constraint: starts >= 10."""
            if "task_starts" in variables:
                for start_var in variables["task_starts"].values():
                    model.Add(start_var >= 10)

        def constraint2(model, variables, _problem):
            """Second constraint: starts <= 50."""
            if "task_starts" in variables:
                for start_var in variables["task_starts"].values():
                    model.Add(start_var <= 50)

        # Both functions follow the protocol
        constraints = [constraint1, constraint2, mock_constraint_function]

        model = cp_model.CpModel()
        variables = {"task_starts": {("J1", "T1"): model.NewIntVar(0, 200, "start")}}
        problem = create_test_problem()

        # Apply all constraints
        for constraint_func in constraints:
            constraint_func(model, variables, problem)

        # Solve and verify
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Value should satisfy all constraints: 10 <= x <= 50
        value = solver.Value(variables["task_starts"][("J1", "T1")])
        assert 10 <= value <= 50

    def test_constraint_with_problem_data(self):
        """Test constraint that uses problem data."""

        def machine_specific_constraint(model, variables, problem):
            """Constraint that uses machine data from problem."""
            if "task_assigned" not in variables:
                return

            # Limit assignments based on machine capacity
            for machine in problem.machines:
                machine_vars = [
                    var
                    for (j, t, m), var in variables["task_assigned"].items()
                    if m == machine.resource_id
                ]

                if machine_vars:
                    # Sum of assignments to this machine <= capacity
                    model.Add(sum(machine_vars) <= machine.capacity)

        model = cp_model.CpModel()
        problem = create_test_problem()

        # Create assignment variables
        variables = {"task_assigned": {}}

        for job in problem.jobs:
            for task in job.tasks:
                for machine in problem.machines:
                    var = model.NewBoolVar(
                        f"assign_{task.task_id}_{machine.resource_id}"
                    )
                    variables["task_assigned"][
                        (job.job_id, task.task_id, machine.resource_id)
                    ] = var

        # Apply constraint
        machine_specific_constraint(model, variables, problem)

        # Add requirement that each task is assigned
        for job in problem.jobs:
            for task in job.tasks:
                task_vars = [
                    variables["task_assigned"][
                        (job.job_id, task.task_id, m.resource_id)
                    ]
                    for m in problem.machines
                ]
                model.AddExactlyOne(task_vars)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status == cp_model.OPTIMAL

        # Verify capacity constraints are respected
        for machine in problem.machines:
            assigned_count = sum(
                solver.Value(var)
                for (j, t, m), var in variables["task_assigned"].items()
                if m == machine.resource_id
            )
            assert assigned_count <= machine.capacity


def create_test_problem() -> SchedulingProblem:
    """Create a simple test problem."""
    machines = [
        Machine(
            resource_id="M1",
            cell_id="cell1",
            name="Machine 1",
            capacity=2,
            cost_per_hour=10,
        ),
        Machine(
            resource_id="M2",
            cell_id="cell1",
            name="Machine 2",
            capacity=1,
            cost_per_hour=15,
        ),
    ]

    tasks = []
    for i in range(3):
        task = Task(
            task_id=f"T{i + 1}",
            job_id="J1",
            name=f"Task {i + 1}",
            modes=[
                TaskMode(
                    task_mode_id="tm_auto",
                    task_id="auto",
                    machine_resource_id="M1",
                    duration_minutes=60,
                ),
                TaskMode(
                    task_mode_id="tm_auto",
                    task_id="auto",
                    machine_resource_id="M2",
                    duration_minutes=45,
                ),
            ],
        )
        tasks.append(task)

    from datetime import UTC, datetime, timedelta

    jobs = [
        Job(
            job_id="J1",
            description="Job 1",
            tasks=tasks,
            due_date=datetime.now(UTC) + timedelta(hours=24),
        )
    ]

    return SchedulingProblem(
        jobs=jobs, machines=machines, work_cells=[], precedences=[]
    )
