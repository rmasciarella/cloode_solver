"""Factory for creating optimized mode test problems."""

from datetime import UTC, datetime, timedelta

from src.solver.models.problem import (
    JobInstance,
    JobOptimizedPattern,
    Machine,
    Operator,
    OperatorSkill,
    OptimizedTask,
    ProficiencyLevel,
    SchedulingProblem,
    Skill,
    TaskMode,
    TaskSkillRequirement,
    WorkCell,
)


def create_optimized_test_problem(
    num_instances: int = 2,
    optimized_tasks_count: int = 2,
    operators_count: int = 3,
    skills_count: int = 2,
    machines_count: int = 2,
) -> SchedulingProblem:
    """Create an optimized mode scheduling problem for testing.

    Args:
        num_instances: Number of job instances
        optimized_tasks_count: Number of tasks in the optimized pattern
        operators_count: Number of operators
        skills_count: Number of skills
        machines_count: Number of machines

    Returns:
        SchedulingProblem configured for optimized mode testing

    """
    # Create skills
    skills = []
    for i in range(skills_count):
        skills.append(
            Skill(
                skill_id=f"skill_{i}", name=f"Skill {i}", description=f"Test skill {i}"
            )
        )

    # Create machines
    machines = []
    for i in range(machines_count):
        machines.append(
            Machine(
                resource_id=f"machine_{i}",
                cell_id="cell_1",
                name=f"Machine {i}",
                capacity=1,
                cost_per_hour=50.0,
            )
        )

    # Create work cells
    work_cells = [
        WorkCell(cell_id="cell_1", name="Test Cell 1", capacity=machines_count)
    ]

    # Create operators with skills
    operators = []
    operator_skills = []
    for i in range(operators_count):
        operator = Operator(
            operator_id=f"operator_{i}",
            name=f"Operator {i}",
            employee_number=f"EMP{i:03d}",
        )
        operators.append(operator)

        # Assign skills to operators (rotating pattern)
        for j, skill in enumerate(skills):
            if (i + j) % 2 == 0:  # Some operators get some skills
                proficiency = [
                    ProficiencyLevel.NOVICE,
                    ProficiencyLevel.COMPETENT,
                    ProficiencyLevel.PROFICIENT,
                    ProficiencyLevel.EXPERT,
                ][i % 4]

                operator_skills.append(
                    OperatorSkill(
                        operator_id=operator.operator_id,
                        skill_id=skill.skill_id,
                        proficiency_level=proficiency,
                    )
                )

    # Create optimized tasks
    optimized_tasks = []
    task_skill_requirements = []

    for i in range(optimized_tasks_count):
        # Create task modes for each machine
        modes = []
        for j, machine in enumerate(machines):
            modes.append(
                TaskMode(
                    task_mode_id=f"optimized_task_{i}_mode_{j}",
                    task_id=f"optimized_task_{i}",
                    machine_resource_id=machine.resource_id,
                    duration_minutes=30 + (i * 15) + (j * 10),
                )
            )

        optimized_task = OptimizedTask(
            optimized_task_id=f"optimized_task_{i}",
            name=f"Optimized Task {i}",
            department_id="test_dept",
            modes=modes,
            min_operators=1,
            max_operators=min(2, operators_count),
            operator_efficiency_curve="linear",
        )
        optimized_tasks.append(optimized_task)

        # Add skill requirements (rotating pattern)
        for j, skill in enumerate(skills):
            if (i + j) % 3 == 0:  # Some tasks require some skills
                task_skill_requirements.append(
                    TaskSkillRequirement(
                        task_id=optimized_task.optimized_task_id,
                        skill_id=skill.skill_id,
                        required_proficiency=ProficiencyLevel.COMPETENT,
                        is_mandatory=True,
                    )
                )

    # Create job optimized pattern
    job_optimized_pattern = JobOptimizedPattern(
        optimized_pattern_id="test_optimized_pattern",
        name="Test Job Optimized Pattern",
        description="Optimized pattern for testing",
        optimized_tasks=optimized_tasks,
        optimized_precedences=[],
    )

    # Create job instances
    job_instances = []
    for i in range(num_instances):
        job_instances.append(
            JobInstance(
                instance_id=f"instance_{i}",
                optimized_pattern_id=job_optimized_pattern.optimized_pattern_id,
                description=f"Job instance {i}",
                due_date=datetime.now(UTC) + timedelta(hours=8),
            )
        )

    # Update operators with their skills
    for operator in operators:
        operator.skills = [
            skill
            for skill in operator_skills
            if skill.operator_id == operator.operator_id
        ]

    # Create the scheduling problem
    problem = SchedulingProblem(
        jobs=[],  # No unique mode jobs for optimized mode problem
        machines=machines,
        work_cells=work_cells,
        precedences=[],  # Optimized pattern precedences handled separately
        operators=operators,
        skills=skills,
        task_skill_requirements=task_skill_requirements,
        is_optimized_mode=True,
        job_optimized_pattern=job_optimized_pattern,
        job_instances=job_instances,
    )

    return problem


def create_simple_optimized_problem() -> SchedulingProblem:
    """Create a simple optimized mode problem for basic testing."""
    return create_optimized_test_problem(
        num_instances=2,
        optimized_tasks_count=2,
        operators_count=2,
        skills_count=1,
        machines_count=1,
    )


def create_complex_optimized_problem() -> SchedulingProblem:
    """Create a complex optimized mode problem for advanced testing."""
    return create_optimized_test_problem(
        num_instances=5,
        optimized_tasks_count=4,
        operators_count=6,
        skills_count=4,
        machines_count=3,
    )
