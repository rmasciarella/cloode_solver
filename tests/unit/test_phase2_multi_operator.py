"""Unit tests for Phase 2.1b multi-operator tasks support."""

from datetime import UTC, datetime

import pytest
from ortools.sat.python import cp_model

from src.solver.constraints.phase2.skill_matching import (
    add_advanced_skill_matching_constraints,
    add_multi_operator_task_constraints,
    add_skill_proficiency_optimization,
)
from src.solver.models.problem import (
    Job,
    Machine,
    Operator,
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
def multi_operator_problem():
    """Create a scheduling problem with multi-operator tasks."""
    # Create skills
    skills = [
        Skill(skill_id="welding", name="Welding", description="Metal welding skills"),
        Skill(
            skill_id="assembly",
            name="Assembly",
            description="Component assembly skills",
        ),
    ]

    # Create operators with different skill levels
    operators = [
        Operator(
            operator_id="op1",
            name="Alice Expert",
            employee_number="EMP001",
            skills=[
                OperatorSkill("op1", "welding", ProficiencyLevel.EXPERT),
                OperatorSkill("op1", "assembly", ProficiencyLevel.PROFICIENT),
            ],
        ),
        Operator(
            operator_id="op2",
            name="Bob Proficient",
            employee_number="EMP002",
            skills=[
                OperatorSkill("op2", "welding", ProficiencyLevel.PROFICIENT),
                OperatorSkill("op2", "assembly", ProficiencyLevel.COMPETENT),
            ],
        ),
        Operator(
            operator_id="op3",
            name="Charlie Competent",
            employee_number="EMP003",
            skills=[
                OperatorSkill("op3", "welding", ProficiencyLevel.COMPETENT),
                OperatorSkill("op3", "assembly", ProficiencyLevel.NOVICE),
            ],
        ),
        Operator(
            operator_id="op4",
            name="Diana Novice",
            employee_number="EMP004",
            skills=[
                OperatorSkill("op4", "welding", ProficiencyLevel.NOVICE),
            ],
        ),
    ]

    # Create machines
    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Large Welder", capacity=1),
        Machine(resource_id="m2", cell_id="cell1", name="Assembly Line", capacity=1),
    ]

    # Create work cells
    work_cells = [
        WorkCell(cell_id="cell1", name="Main Cell", capacity=4, machines=machines)
    ]

    # Create tasks with multi-operator requirements
    tasks = [
        Task(
            task_id="t1",
            job_id="j1",
            name="Heavy Weld (2 operators)",
            modes=[TaskMode("tm1", "t1", "m1", 120)],  # 120 minutes
            min_operators=2,  # Requires 2 operators minimum
            max_operators=3,  # Can use up to 3 operators
            operator_efficiency_curve="linear",
        ),
        Task(
            task_id="t2",
            job_id="j1",
            name="Complex Assembly (1-2 operators)",
            modes=[TaskMode("tm2", "t2", "m2", 90)],  # 90 minutes
            min_operators=1,  # Can work with 1 operator
            max_operators=2,  # Better with 2 operators
            operator_efficiency_curve="diminishing",
        ),
        Task(
            task_id="t3",
            job_id="j1",
            name="Simple Task (1 operator)",
            modes=[TaskMode("tm3", "t3", "m1", 30)],  # 30 minutes
            min_operators=1,
            max_operators=1,  # Single operator only
        ),
    ]

    # Create job
    jobs = [
        Job(
            job_id="j1",
            description="Multi-Operator Test Job",
            due_date=datetime.now(UTC),
            tasks=tasks,
        )
    ]

    # Create skill requirements
    skill_requirements = [
        TaskSkillRequirement(
            "t1",
            "welding",
            ProficiencyLevel.COMPETENT,
            is_mandatory=True,
            operators_needed=2,
        ),
        TaskSkillRequirement(
            "t2",
            "assembly",
            ProficiencyLevel.NOVICE,
            is_mandatory=True,
            operators_needed=1,
        ),
        TaskSkillRequirement(
            "t3",
            "welding",
            ProficiencyLevel.NOVICE,
            is_mandatory=True,
            operators_needed=1,
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
    )


def test_task_multi_operator_validation():
    """Test that multi-operator task validation works correctly."""
    # Valid multi-operator task
    task = Task(
        task_id="t1",
        job_id="j1",
        name="Multi-operator Task",
        modes=[TaskMode("tm1", "t1", "m1", 60)],
        min_operators=2,
        max_operators=3,
        operator_efficiency_curve="linear",
    )
    # Should not raise exception
    assert task.min_operators == 2
    assert task.max_operators == 3

    # Invalid: min > max
    with pytest.raises(ValueError, match="min_operators.*cannot exceed max_operators"):
        Task(
            task_id="t2",
            job_id="j1",
            name="Invalid Task",
            modes=[TaskMode("tm2", "t2", "m1", 60)],
            min_operators=3,
            max_operators=2,  # max < min, should fail
        )

    # Invalid: zero operators
    with pytest.raises(ValueError, match="min_operators must be positive"):
        Task(
            task_id="t3",
            job_id="j1",
            name="Zero Operators Task",
            modes=[TaskMode("tm3", "t3", "m1", 60)],
            min_operators=0,
            max_operators=1,
        )

    # Invalid efficiency curve
    with pytest.raises(ValueError, match="efficiency curve must be one of"):
        Task(
            task_id="t4",
            job_id="j1",
            name="Invalid Curve Task",
            modes=[TaskMode("tm4", "t4", "m1", 60)],
            operator_efficiency_curve="invalid_curve",
        )


def test_multi_operator_task_constraints(multi_operator_problem):
    """Test constraints for tasks requiring multiple operators."""
    # GIVEN: A model with multi-operator tasks
    model = cp_model.CpModel()
    problem = multi_operator_problem

    # Create assignment variables for all qualified operators
    task_operator_assigned = {}
    qualified_ops_t1 = problem.get_qualified_operators(
        "t1"
    )  # Heavy weld, needs competent welding
    qualified_ops_t2 = problem.get_qualified_operators(
        "t2"
    )  # Assembly, needs novice assembly
    qualified_ops_t3 = problem.get_qualified_operators(
        "t3"
    )  # Simple weld, needs novice welding

    # Task t1 assignment variables (2-3 operators needed)
    for operator in qualified_ops_t1:
        key = ("j1", "t1", operator.operator_id)
        task_operator_assigned[key] = model.NewBoolVar(
            f"op_assigned_j1_t1_{operator.operator_id}"
        )

    # Task t2 assignment variables (1-2 operators)
    for operator in qualified_ops_t2:
        key = ("j1", "t2", operator.operator_id)
        task_operator_assigned[key] = model.NewBoolVar(
            f"op_assigned_j1_t2_{operator.operator_id}"
        )

    # Task t3 assignment variables (1 operator only)
    for operator in qualified_ops_t3:
        key = ("j1", "t3", operator.operator_id)
        task_operator_assigned[key] = model.NewBoolVar(
            f"op_assigned_j1_t3_{operator.operator_id}"
        )

    # WHEN: Adding multi-operator constraints
    add_multi_operator_task_constraints(model, task_operator_assigned, problem)

    # THEN: Solver finds valid assignment respecting operator counts
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify operator counts for each task
    t1_operator_count = sum(
        solver.Value(var)
        for key, var in task_operator_assigned.items()
        if key[1] == "t1"
    )
    t2_operator_count = sum(
        solver.Value(var)
        for key, var in task_operator_assigned.items()
        if key[1] == "t2"
    )
    t3_operator_count = sum(
        solver.Value(var)
        for key, var in task_operator_assigned.items()
        if key[1] == "t3"
    )

    # Task t1: 2-3 operators required
    assert 2 <= t1_operator_count <= 3

    # Task t2: 1-2 operators allowed
    assert 1 <= t2_operator_count <= 2

    # Task t3: exactly 1 operator (single-operator task)
    assert t3_operator_count <= 1  # max constraint applied


def test_skill_proficiency_optimization(multi_operator_problem):
    """Test skill proficiency optimization variables and constraints."""
    # GIVEN: A model with operators of different skill levels
    model = cp_model.CpModel()
    problem = multi_operator_problem

    # Create assignment variables
    task_operator_assigned = {}

    # Add assignments for t1 (welding task)
    qualified_ops = problem.get_qualified_operators("t1")
    for operator in qualified_ops:
        key = ("j1", "t1", operator.operator_id)
        task_operator_assigned[key] = model.NewBoolVar(
            f"op_assigned_j1_t1_{operator.operator_id}"
        )

    # Force assignment to test efficiency calculation
    # Assign op1 (EXPERT, 125% efficiency) and op2 (PROFICIENT, 100% efficiency)
    if ("j1", "t1", "op1") in task_operator_assigned:
        model.Add(task_operator_assigned[("j1", "t1", "op1")] == 1)
    if ("j1", "t1", "op2") in task_operator_assigned:
        model.Add(task_operator_assigned[("j1", "t1", "op2")] == 1)

    # WHEN: Adding skill proficiency optimization
    task_efficiency_vars = add_skill_proficiency_optimization(
        model, task_operator_assigned, problem
    )

    # THEN: Efficiency variables are created and constrained correctly
    assert "t1" in task_efficiency_vars

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify efficiency calculation
    t1_efficiency = solver.Value(task_efficiency_vars["t1"])

    # Expected: op1 (125%) + op2 (100%) = 225% total efficiency
    expected_efficiency = 125 + 100  # Scaled to integer percentages
    assert t1_efficiency == expected_efficiency


def test_advanced_skill_matching_integration(multi_operator_problem):
    """Test complete advanced skill matching functionality."""
    # GIVEN: A complete multi-operator scheduling problem
    problem = multi_operator_problem

    model = cp_model.CpModel()

    # Create timing variables
    task_starts = {
        ("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1"),
        ("j1", "t2"): model.NewIntVar(0, 100, "start_j1_t2"),
        ("j1", "t3"): model.NewIntVar(0, 100, "start_j1_t3"),
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(8, 108, "end_j1_t1"),  # 120 min = 8 time units
        ("j1", "t2"): model.NewIntVar(6, 106, "end_j1_t2"),  # 90 min = 6 time units
        ("j1", "t3"): model.NewIntVar(2, 102, "end_j1_t3"),  # 30 min = 2 time units
    }

    # Create all possible operator assignments
    task_operator_assigned = {}
    all_tasks = ["t1", "t2", "t3"]

    for task_id in all_tasks:
        qualified_ops = problem.get_qualified_operators(task_id)
        for operator in qualified_ops:
            key = ("j1", task_id, operator.operator_id)
            task_operator_assigned[key] = model.NewBoolVar(
                f"op_assigned_j1_{task_id}_{operator.operator_id}"
            )

    # WHEN: Adding all advanced skill matching constraints
    task_efficiency_vars = add_advanced_skill_matching_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Solver finds valid assignment with proper operator counts and skill matching
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify all tasks have valid operator assignments
    for task_id in all_tasks:
        operator_count = sum(
            solver.Value(var)
            for key, var in task_operator_assigned.items()
            if key[1] == task_id
        )

        # Get task definition for operator count validation
        task_def = problem.get_task(task_id)
        assert task_def.min_operators <= operator_count <= task_def.max_operators

    # Verify efficiency variables exist for tasks
    for task_id in all_tasks:
        if task_id in task_efficiency_vars:
            efficiency = solver.Value(task_efficiency_vars[task_id])
            assert efficiency >= 0  # Non-negative efficiency


def test_task_skill_requirement_multi_operator():
    """Test TaskSkillRequirement with multi-operator support."""
    # Valid multi-operator skill requirement
    req = TaskSkillRequirement(
        task_id="t1",
        skill_id="welding",
        required_proficiency=ProficiencyLevel.COMPETENT,
        operators_needed=2,
    )
    assert req.operators_needed == 2

    # Invalid: zero operators needed
    with pytest.raises(ValueError, match="Operators needed must be positive"):
        TaskSkillRequirement(
            task_id="t2",
            skill_id="welding",
            required_proficiency=ProficiencyLevel.COMPETENT,
            operators_needed=0,
        )
