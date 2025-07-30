"""Unit tests for Phase 2.1b shift calendar integration."""

from datetime import UTC, datetime

import pytest
from ortools.sat.python import cp_model

from src.solver.constraints.phase2.shift_calendar import (
    add_operator_shift_constraints,
    add_overtime_constraints,
    add_shift_calendar_constraints,
)
from src.solver.models.problem import (
    Job,
    Machine,
    Operator,
    OperatorShift,
    OperatorSkill,
    ProficiencyLevel,
    SchedulingProblem,
    Skill,
    Task,
    TaskMode,
    TaskSkillRequirement,
    WorkCell,
)


@pytest.fixture
def shift_calendar_problem():
    """Create a scheduling problem with operator shifts."""
    # Create skills
    skills = [
        Skill(skill_id="welding", name="Welding", description="Metal welding skills"),
    ]

    # Create operators with different shifts
    operators = [
        Operator(
            operator_id="op1",
            name="Day Shift Worker",
            employee_number="EMP001",
            skills=[
                OperatorSkill("op1", "welding", ProficiencyLevel.EXPERT),
            ],
        ),
        Operator(
            operator_id="op2",
            name="Evening Shift Worker",
            employee_number="EMP002",
            skills=[
                OperatorSkill("op2", "welding", ProficiencyLevel.PROFICIENT),
            ],
        ),
        Operator(
            operator_id="op3",
            name="Night Shift Worker",
            employee_number="EMP003",
            skills=[
                OperatorSkill("op3", "welding", ProficiencyLevel.COMPETENT),
            ],
        ),
    ]

    # Create operator shifts
    # Day shift: 8:00 AM - 4:00 PM (32-64 time units)
    # Evening shift: 4:00 PM - 12:00 AM (64-96 time units, wraps to next day)
    # Night shift: 12:00 AM - 8:00 AM (0-32 time units)
    shift_date = datetime.now(UTC)
    operator_shifts = [
        OperatorShift(
            operator_id="op1",
            shift_date=shift_date,
            start_time=32,  # 8:00 AM
            end_time=64,  # 4:00 PM
            is_available=True,
            overtime_allowed=True,
            max_overtime_hours=2.0,
        ),
        OperatorShift(
            operator_id="op2",
            shift_date=shift_date,
            start_time=64,  # 4:00 PM
            end_time=80,  # 8:00 PM (truncated evening shift for testing)
            is_available=True,
            overtime_allowed=False,
            max_overtime_hours=0.0,
        ),
        OperatorShift(
            operator_id="op3",
            shift_date=shift_date,
            start_time=0,  # 12:00 AM
            end_time=32,  # 8:00 AM
            is_available=True,
            overtime_allowed=True,
            max_overtime_hours=4.0,
        ),
        # Add unavailable shift for testing
        OperatorShift(
            operator_id="op1",
            shift_date=shift_date,
            start_time=80,  # 8:00 PM
            end_time=95,  # 11:45 PM (end of day)
            is_available=False,  # Not available
            overtime_allowed=False,
        ),
    ]

    # Create machines
    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Welder", capacity=1),
    ]

    # Create work cells
    work_cells = [
        WorkCell(cell_id="cell1", name="Main Cell", capacity=3, machines=machines)
    ]

    # Create tasks
    tasks = [
        Task(
            task_id="t1",
            job_id="j1",
            name="Day Task",
            modes=[TaskMode("tm1", "t1", "m1", 60)],  # 60 minutes (4 time units)
        ),
        Task(
            task_id="t2",
            job_id="j1",
            name="Evening Task",
            modes=[TaskMode("tm2", "t2", "m1", 120)],  # 120 minutes (8 time units)
        ),
        Task(
            task_id="t3",
            job_id="j1",
            name="Night Task",
            modes=[TaskMode("tm3", "t3", "m1", 90)],  # 90 minutes (6 time units)
        ),
    ]

    # Create job
    jobs = [
        Job(
            job_id="j1",
            description="Shift Calendar Test Job",
            due_date=datetime.now(UTC),
            tasks=tasks,
        )
    ]

    # Create skill requirements
    skill_requirements = [
        TaskSkillRequirement(
            "t1", "welding", ProficiencyLevel.NOVICE, is_mandatory=True
        ),
        TaskSkillRequirement(
            "t2", "welding", ProficiencyLevel.NOVICE, is_mandatory=True
        ),
        TaskSkillRequirement(
            "t3", "welding", ProficiencyLevel.NOVICE, is_mandatory=True
        ),
    ]

    return SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=work_cells,
        precedences=[],
        operators=operators,
        skills=skills,
        task_skill_requirements=skill_requirements,
        operator_shifts=operator_shifts,
    )


def test_operator_shift_validation():
    """Test OperatorShift data model validation."""
    shift_date = datetime.now(UTC)

    # Valid shift
    shift = OperatorShift(
        operator_id="op1",
        shift_date=shift_date,
        start_time=32,  # 8:00 AM
        end_time=64,  # 4:00 PM
        overtime_allowed=True,
        max_overtime_hours=2.0,
    )
    assert shift.shift_duration_hours == 8.0
    assert shift.max_total_hours == 10.0

    # Invalid: start >= end
    with pytest.raises(ValueError, match="Start time must be before end time"):
        OperatorShift(
            operator_id="op1",
            shift_date=shift_date,
            start_time=64,
            end_time=32,
        )

    # Invalid: time out of range
    with pytest.raises(ValueError, match="Start time must be 0-95"):
        OperatorShift(
            operator_id="op1",
            shift_date=shift_date,
            start_time=100,
            end_time=120,
        )

    # Invalid: negative overtime
    with pytest.raises(ValueError, match="Max overtime hours cannot be negative"):
        OperatorShift(
            operator_id="op1",
            shift_date=shift_date,
            start_time=32,
            end_time=64,
            max_overtime_hours=-1.0,
        )


def test_operator_shift_constraints(shift_calendar_problem):
    """Test operator shift constraints ensure tasks fit within shifts."""
    # GIVEN: A model with tasks and operator shifts
    model = cp_model.CpModel()
    problem = shift_calendar_problem

    # Create timing variables
    task_starts = {
        ("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1"),
        ("j1", "t2"): model.NewIntVar(0, 100, "start_j1_t2"),
        ("j1", "t3"): model.NewIntVar(0, 100, "start_j1_t3"),
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(4, 104, "end_j1_t1"),  # 60 min = 4 time units
        ("j1", "t2"): model.NewIntVar(8, 108, "end_j1_t2"),  # 120 min = 8 time units
        ("j1", "t3"): model.NewIntVar(6, 106, "end_j1_t3"),  # 90 min = 6 time units
    }

    # Create task duration constraints
    for task_key in task_starts:
        if task_key[1] == "t1":
            model.Add(task_ends[task_key] == task_starts[task_key] + 4)
        elif task_key[1] == "t2":
            model.Add(task_ends[task_key] == task_starts[task_key] + 8)
        elif task_key[1] == "t3":
            model.Add(task_ends[task_key] == task_starts[task_key] + 6)

    # Create operator assignments for qualified operators only
    task_operator_assigned = {}
    all_tasks = ["t1", "t2", "t3"]

    for task_id in all_tasks:
        qualified_ops = problem.get_qualified_operators(task_id)
        for operator in qualified_ops:
            key = ("j1", task_id, operator.operator_id)
            task_operator_assigned[key] = model.NewBoolVar(
                f"op_assigned_j1_{task_id}_{operator.operator_id}"
            )

    # Force some assignments to test shift constraints
    # Task t1 (day task) should be assigned to op1 (day shift worker)
    if ("j1", "t1", "op1") in task_operator_assigned:
        model.Add(task_operator_assigned[("j1", "t1", "op1")] == 1)
        model.Add(
            task_starts[("j1", "t1")] == 40
        )  # Start at 10:00 AM (within day shift)

    # WHEN: Adding operator shift constraints
    add_operator_shift_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Solver finds valid assignment respecting shift windows
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify task t1 is scheduled within op1's day shift (32-64)
    t1_start = solver.Value(task_starts[("j1", "t1")])
    t1_end = solver.Value(task_ends[("j1", "t1")])

    assert t1_start >= 32  # After shift start
    assert t1_end <= 64  # Before shift end


def test_operator_shift_constraints_no_assignment():
    """Test shift constraints prevent assignment when no valid shifts."""
    # GIVEN: Operator with no shifts defined
    model = cp_model.CpModel()

    operators = [
        Operator(
            operator_id="op_no_shift",
            name="No Shift Worker",
            employee_number="EMP999",
            skills=[OperatorSkill("op_no_shift", "welding", ProficiencyLevel.EXPERT)],
        )
    ]

    problem = SchedulingProblem(
        jobs=[
            Job(
                "j1",
                "Test Job",
                datetime.now(UTC),
                [
                    Task(
                        "t1", "j1", "Test Task", modes=[TaskMode("tm1", "t1", "m1", 60)]
                    )
                ],
            )
        ],
        machines=[Machine("m1", "cell1", "Test Machine")],
        work_cells=[WorkCell("cell1", "Test Cell", machines=[])],
        precedences=[],
        operators=operators,
        skills=[Skill("welding", "Welding")],
        task_skill_requirements=[
            TaskSkillRequirement("t1", "welding", ProficiencyLevel.NOVICE)
        ],
        operator_shifts=[],  # No shifts defined
    )

    task_starts = {("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1")}
    task_ends = {("j1", "t1"): model.NewIntVar(4, 104, "end_j1_t1")}

    task_operator_assigned = {
        ("j1", "t1", "op_no_shift"): model.NewBoolVar("op_assigned_j1_t1_op_no_shift")
    }

    # WHEN: Adding shift constraints with no shifts defined
    add_operator_shift_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Operator cannot be assigned (constraint forces assignment to 0)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify operator is not assigned
    assigned = solver.Value(task_operator_assigned[("j1", "t1", "op_no_shift")])
    assert assigned == 0


def test_overtime_constraints(shift_calendar_problem):
    """Test overtime tracking constraints."""
    # GIVEN: A model with operator assignments and shifts
    model = cp_model.CpModel()
    problem = shift_calendar_problem

    # Create timing variables for longer tasks that might cause overtime
    task_starts = {
        ("j1", "t1"): model.NewIntVar(32, 32, "start_j1_t1"),  # Fixed start at 8:00 AM
        ("j1", "t2"): model.NewIntVar(40, 40, "start_j1_t2"),  # Fixed start at 10:00 AM
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(
            36, 36, "end_j1_t1"
        ),  # End at 9:00 AM (4 time units)
        ("j1", "t2"): model.NewIntVar(
            48, 48, "end_j1_t2"
        ),  # End at 12:00 PM (8 time units)
    }

    # Create assignments that will result in overtime
    task_operator_assigned = {
        ("j1", "t1", "op1"): model.NewBoolVar("op_assigned_j1_t1_op1"),
        ("j1", "t2", "op1"): model.NewBoolVar("op_assigned_j1_t2_op1"),
    }

    # Force both tasks to be assigned to op1
    model.Add(task_operator_assigned[("j1", "t1", "op1")] == 1)
    model.Add(task_operator_assigned[("j1", "t2", "op1")] == 1)

    # WHEN: Adding overtime constraints
    overtime_vars = add_overtime_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Overtime variables are created and constrained
    assert "op1" in overtime_vars

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify overtime calculation
    # op1 works 12 time units (3 hours), regular shift is 32 time units (8 hours)
    # Since total work < regular shift, overtime should be 0
    op1_overtime = solver.Value(overtime_vars["op1"])
    assert op1_overtime == 0


def test_shift_calendar_integration(shift_calendar_problem):
    """Test complete shift calendar integration."""
    # GIVEN: Complete shift calendar problem
    model = cp_model.CpModel()
    problem = shift_calendar_problem

    # Create timing variables
    task_starts = {
        ("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1"),
        ("j1", "t2"): model.NewIntVar(0, 100, "start_j1_t2"),
        ("j1", "t3"): model.NewIntVar(0, 100, "start_j1_t3"),
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(4, 104, "end_j1_t1"),
        ("j1", "t2"): model.NewIntVar(8, 108, "end_j1_t2"),
        ("j1", "t3"): model.NewIntVar(6, 106, "end_j1_t3"),
    }

    # Create duration constraints
    model.Add(task_ends[("j1", "t1")] == task_starts[("j1", "t1")] + 4)
    model.Add(task_ends[("j1", "t2")] == task_starts[("j1", "t2")] + 8)
    model.Add(task_ends[("j1", "t3")] == task_starts[("j1", "t3")] + 6)

    # Create operator assignments
    task_operator_assigned = {}
    all_tasks = ["t1", "t2", "t3"]

    for task_id in all_tasks:
        qualified_ops = problem.get_qualified_operators(task_id)
        for operator in qualified_ops:
            key = ("j1", task_id, operator.operator_id)
            task_operator_assigned[key] = model.NewBoolVar(
                f"op_assigned_j1_{task_id}_{operator.operator_id}"
            )

    # Ensure exactly one operator per task
    for task_id in all_tasks:
        task_assignments = [
            var for key, var in task_operator_assigned.items() if key[1] == task_id
        ]
        if task_assignments:
            model.AddExactlyOne(task_assignments)

    # WHEN: Adding complete shift calendar constraints
    overtime_vars = add_shift_calendar_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Solver finds valid schedule respecting all shift constraints
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify all tasks are assigned and scheduled within appropriate shifts
    for task_id in all_tasks:
        # Find which operator is assigned
        assigned_operator = None
        for key, var in task_operator_assigned.items():
            if key[1] == task_id and solver.Value(var) == 1:
                assigned_operator = key[2]
                break

        assert assigned_operator is not None, f"Task {task_id} not assigned"

        # Get task timing
        task_start = solver.Value(task_starts[("j1", task_id)])
        task_end = solver.Value(task_ends[("j1", task_id)])

        # Find operator's shift
        operator_shifts = [
            shift
            for shift in problem.operator_shifts
            if shift.operator_id == assigned_operator and shift.is_available
        ]

        # Verify task fits within at least one shift
        fits_in_shift = False
        for shift in operator_shifts:
            if task_start >= shift.start_time and task_end <= shift.end_time:
                fits_in_shift = True
                break

        assert (
            fits_in_shift
        ), f"Task {task_id} assigned to {assigned_operator} doesn't fit in any shift"

    # Verify overtime variables exist for operators with shifts
    for operator in problem.operators:
        if any(
            shift.operator_id == operator.operator_id
            for shift in problem.operator_shifts
        ):
            assert operator.operator_id in overtime_vars


def test_shift_calendar_no_shifts():
    """Test shift calendar constraints with no shifts defined."""
    # GIVEN: Problem with no operator shifts
    model = cp_model.CpModel()

    problem = SchedulingProblem(
        jobs=[
            Job(
                "j1",
                "Test Job",
                datetime.now(UTC),
                [
                    Task(
                        "t1", "j1", "Test Task", modes=[TaskMode("tm1", "t1", "m1", 60)]
                    )
                ],
            )
        ],
        machines=[Machine("m1", "cell1", "Test Machine")],
        work_cells=[WorkCell("cell1", "Test Cell")],
        precedences=[],
        operators=[Operator("op1", "Test Operator", "EMP001")],
        operator_shifts=[],  # No shifts
    )

    task_starts = {("j1", "t1"): model.NewIntVar(0, 100, "start")}
    task_ends = {("j1", "t1"): model.NewIntVar(4, 104, "end")}
    task_operator_assigned = {("j1", "t1", "op1"): model.NewBoolVar("assigned")}

    # WHEN: Adding shift calendar constraints with no shifts
    overtime_vars = add_shift_calendar_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: No overtime variables created, constraints skip gracefully
    assert len(overtime_vars) == 0

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Should still be solvable
    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
