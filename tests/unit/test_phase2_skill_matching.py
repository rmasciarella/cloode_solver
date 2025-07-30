"""Unit tests for Phase 2.1a skill matching constraints."""

from datetime import UTC, datetime

import pytest
from ortools.sat.python import cp_model

from src.solver.constraints.phase2.skill_matching import (
    add_basic_skill_matching_constraints,
    add_operator_capacity_constraints,
    add_skill_requirement_constraints,
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
def basic_skill_problem():
    """Create a basic scheduling problem with skills."""
    # Create skills
    skills = [
        Skill(skill_id="welding", name="Welding", description="Metal welding skills"),
        Skill(
            skill_id="assembly",
            name="Assembly",
            description="Component assembly skills",
        ),
    ]

    # Create operators with different skills
    operators = [
        Operator(
            operator_id="op1",
            name="Alice",
            employee_number="EMP001",
            skills=[
                OperatorSkill("op1", "welding", ProficiencyLevel.EXPERT),
                OperatorSkill("op1", "assembly", ProficiencyLevel.COMPETENT),
            ],
        ),
        Operator(
            operator_id="op2",
            name="Bob",
            employee_number="EMP002",
            skills=[
                OperatorSkill("op2", "assembly", ProficiencyLevel.PROFICIENT),
            ],
        ),
        Operator(
            operator_id="op3",
            name="Charlie",
            employee_number="EMP003",
            skills=[
                OperatorSkill("op3", "welding", ProficiencyLevel.NOVICE),
            ],
        ),
    ]

    # Create machines
    machines = [
        Machine(resource_id="m1", cell_id="cell1", name="Welder", capacity=1),
        Machine(resource_id="m2", cell_id="cell1", name="Assembly Station", capacity=1),
    ]

    # Create work cells
    work_cells = [
        WorkCell(cell_id="cell1", name="Main Cell", capacity=2, machines=machines)
    ]

    # Create tasks with skill requirements
    tasks = [
        Task(
            task_id="t1",
            job_id="j1",
            name="Weld Frame",
            modes=[TaskMode("tm1", "t1", "m1", 60)],  # 60 minutes
        ),
        Task(
            task_id="t2",
            job_id="j1",
            name="Assemble Parts",
            modes=[TaskMode("tm2", "t2", "m2", 45)],  # 45 minutes
        ),
    ]

    # Create job
    jobs = [
        Job(
            job_id="j1",
            description="Test Job",
            due_date=datetime.now(UTC),
            tasks=tasks,
        )
    ]

    # Create skill requirements
    skill_requirements = [
        TaskSkillRequirement(
            "t1", "welding", ProficiencyLevel.COMPETENT, is_mandatory=True
        ),
        TaskSkillRequirement(
            "t2", "assembly", ProficiencyLevel.NOVICE, is_mandatory=True
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


def test_get_qualified_operators(basic_skill_problem):
    """Test that qualified operators are correctly identified."""
    # Task t1 (welding) - requires COMPETENT level welding
    qualified_for_t1 = basic_skill_problem.get_qualified_operators("t1")
    qualified_ids = [op.operator_id for op in qualified_for_t1]

    # op1 (EXPERT welding) and op3 (NOVICE welding) can do welding
    # but only op1 meets COMPETENT requirement
    assert "op1" in qualified_ids
    assert "op3" not in qualified_ids  # NOVICE < COMPETENT
    assert "op2" not in qualified_ids  # No welding skill

    # Task t2 (assembly) - requires NOVICE level assembly
    qualified_for_t2 = basic_skill_problem.get_qualified_operators("t2")
    qualified_ids = [op.operator_id for op in qualified_for_t2]

    # op1 (COMPETENT) and op2 (PROFICIENT) both can do assembly at NOVICE+ level
    assert "op1" in qualified_ids
    assert "op2" in qualified_ids
    assert "op3" not in qualified_ids  # No assembly skill


def test_calculate_operator_task_efficiency(basic_skill_problem):
    """Test operator efficiency calculation for tasks."""
    # op1 has EXPERT welding (1.25x efficiency)
    efficiency_op1_t1 = basic_skill_problem.calculate_operator_task_efficiency(
        "op1", "t1"
    )
    assert efficiency_op1_t1 == 1.25

    # op2 has PROFICIENT assembly (1.0x efficiency)
    efficiency_op2_t2 = basic_skill_problem.calculate_operator_task_efficiency(
        "op2", "t2"
    )
    assert efficiency_op2_t2 == 1.0

    # op3 cannot do welding at required COMPETENT level (0.0 efficiency)
    efficiency_op3_t1 = basic_skill_problem.calculate_operator_task_efficiency(
        "op3", "t1"
    )
    assert efficiency_op3_t1 == 0.0


def test_skill_requirement_constraints(basic_skill_problem):
    """Test that skill requirement constraints are correctly enforced."""
    # GIVEN: A model with operator assignment variables
    model = cp_model.CpModel()
    problem = basic_skill_problem

    # Note: For this test, we only need operator assignment variables
    # Task timing variables are not needed for skill matching constraint validation

    # Create operator assignment variables (only for qualified operators)
    task_operator_assigned = {}

    # t1 (welding) - only op1 is qualified at COMPETENT level
    task_operator_assigned[("j1", "t1", "op1")] = model.NewBoolVar(
        "op_assigned_j1_t1_op1"
    )

    # t2 (assembly) - both op1 and op2 are qualified
    task_operator_assigned[("j1", "t2", "op1")] = model.NewBoolVar(
        "op_assigned_j1_t2_op1"
    )
    task_operator_assigned[("j1", "t2", "op2")] = model.NewBoolVar(
        "op_assigned_j1_t2_op2"
    )

    # WHEN: Adding skill requirement constraints
    add_skill_requirement_constraints(model, task_operator_assigned, problem)

    # THEN: Solver finds valid solution with qualified operators
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Task t1 should be assigned to op1 (only qualified operator)
    assert solver.Value(task_operator_assigned[("j1", "t1", "op1")]) == 1

    # Task t2 should be assigned to exactly one of op1 or op2
    t2_assignments = solver.Value(
        task_operator_assigned[("j1", "t2", "op1")]
    ) + solver.Value(task_operator_assigned[("j1", "t2", "op2")])
    assert t2_assignments == 1


def test_operator_capacity_constraints(basic_skill_problem):  # noqa: ARG001
    """Test that operators cannot work on overlapping tasks."""
    # GIVEN: A model with overlapping task assignments to the same operator
    model = cp_model.CpModel()

    # Create overlapping task timing
    task_starts = {
        ("j1", "t1"): model.NewIntVar(0, 10, "start_j1_t1"),
        ("j1", "t2"): model.NewIntVar(0, 10, "start_j1_t2"),
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(4, 14, "end_j1_t1"),  # 4 time units duration
        ("j1", "t2"): model.NewIntVar(3, 13, "end_j1_t2"),  # 3 time units duration
    }

    # Force both tasks to potentially overlap by assigning them to op1
    task_operator_assigned = {
        ("j1", "t1", "op1"): model.NewBoolVar("op_assigned_j1_t1_op1"),
        ("j1", "t2", "op1"): model.NewBoolVar("op_assigned_j1_t2_op1"),
    }

    # Force both assignments to op1
    model.Add(task_operator_assigned[("j1", "t1", "op1")] == 1)
    model.Add(task_operator_assigned[("j1", "t2", "op1")] == 1)

    # WHEN: Adding operator capacity constraints
    add_operator_capacity_constraints(
        model, task_starts, task_ends, task_operator_assigned
    )

    # THEN: Solver finds solution where tasks don't overlap
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify tasks don't overlap (one must finish before the other starts)
    t1_start = solver.Value(task_starts[("j1", "t1")])
    t1_end = solver.Value(task_ends[("j1", "t1")])
    t2_start = solver.Value(task_starts[("j1", "t2")])
    t2_end = solver.Value(task_ends[("j1", "t2")])

    # Either t1 finishes before t2 starts, or t2 finishes before t1 starts
    no_overlap = (t1_end <= t2_start) or (t2_end <= t1_start)
    assert no_overlap, f"Tasks overlap: t1({t1_start}-{t1_end}) t2({t2_start}-{t2_end})"


def test_basic_skill_matching_integration(basic_skill_problem):
    """Test complete skill matching functionality integration."""
    # GIVEN: A complete scheduling problem with skills
    problem = basic_skill_problem

    model = cp_model.CpModel()

    # Create timing variables
    task_starts = {
        ("j1", "t1"): model.NewIntVar(0, 100, "start_j1_t1"),
        ("j1", "t2"): model.NewIntVar(0, 100, "start_j1_t2"),
    }
    task_ends = {
        ("j1", "t1"): model.NewIntVar(4, 104, "end_j1_t1"),
        ("j1", "t2"): model.NewIntVar(3, 103, "end_j1_t2"),
    }

    # Create all possible operator assignments
    task_operator_assigned = {
        ("j1", "t1", "op1"): model.NewBoolVar("op_assigned_j1_t1_op1"),
        ("j1", "t2", "op1"): model.NewBoolVar("op_assigned_j1_t2_op1"),
        ("j1", "t2", "op2"): model.NewBoolVar("op_assigned_j1_t2_op2"),
    }

    # WHEN: Adding all basic skill matching constraints
    add_basic_skill_matching_constraints(
        model, task_starts, task_ends, task_operator_assigned, problem
    )

    # THEN: Solver finds valid skill-based assignment
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

    # Verify skill requirements are met
    assert (
        solver.Value(task_operator_assigned[("j1", "t1", "op1")]) == 1
    )  # Only qualified for welding

    # Verify exactly one operator assigned to each task
    t2_assignments = solver.Value(
        task_operator_assigned[("j1", "t2", "op1")]
    ) + solver.Value(task_operator_assigned[("j1", "t2", "op2")])
    assert t2_assignments == 1
