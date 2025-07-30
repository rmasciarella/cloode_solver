"""Factory for creating template-based test problems."""

from datetime import UTC, datetime, timedelta

from src.solver.models.problem import (
    JobInstance,
    JobTemplate,
    Machine,
    Operator,
    OperatorSkill,
    ProficiencyLevel,
    SchedulingProblem,
    Skill,
    TaskMode,
    TaskSkillRequirement,
    TemplateTask,
    WorkCell,
)


def create_template_test_problem(
    num_instances: int = 2,
    template_tasks_count: int = 2,
    operators_count: int = 3,
    skills_count: int = 2,
    machines_count: int = 2,
) -> SchedulingProblem:
    """Create a template-based scheduling problem for testing.

    Args:
        num_instances: Number of job instances
        template_tasks_count: Number of tasks in the template
        operators_count: Number of operators
        skills_count: Number of skills
        machines_count: Number of machines

    Returns:
        SchedulingProblem configured for template-based testing

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

    # Create template tasks
    template_tasks = []
    task_skill_requirements = []

    for i in range(template_tasks_count):
        # Create task modes for each machine
        modes = []
        for j, machine in enumerate(machines):
            modes.append(
                TaskMode(
                    task_mode_id=f"template_task_{i}_mode_{j}",
                    task_id=f"template_task_{i}",
                    machine_resource_id=machine.resource_id,
                    duration_minutes=30 + (i * 15) + (j * 10),
                )
            )

        template_task = TemplateTask(
            template_task_id=f"template_task_{i}",
            name=f"Template Task {i}",
            department_id="test_dept",
            modes=modes,
            min_operators=1,
            max_operators=min(2, operators_count),
            operator_efficiency_curve="linear",
        )
        template_tasks.append(template_task)

        # Add skill requirements (rotating pattern)
        for j, skill in enumerate(skills):
            if (i + j) % 3 == 0:  # Some tasks require some skills
                task_skill_requirements.append(
                    TaskSkillRequirement(
                        task_id=template_task.template_task_id,
                        skill_id=skill.skill_id,
                        required_proficiency=ProficiencyLevel.COMPETENT,
                        is_mandatory=True,
                    )
                )

    # Create job template
    job_template = JobTemplate(
        template_id="test_template",
        name="Test Job Template",
        description="Template for testing",
        template_tasks=template_tasks,
        template_precedences=[],
    )

    # Create job instances
    job_instances = []
    for i in range(num_instances):
        job_instances.append(
            JobInstance(
                instance_id=f"instance_{i}",
                template_id=job_template.template_id,
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
        jobs=[],  # No legacy jobs for template-based problem
        machines=machines,
        work_cells=work_cells,
        precedences=[],  # Template precedences handled separately
        operators=operators,
        skills=skills,
        task_skill_requirements=task_skill_requirements,
        is_template_based=True,
        job_template=job_template,
        job_instances=job_instances,
    )

    return problem


def create_simple_template_problem() -> SchedulingProblem:
    """Create a simple template problem for basic testing."""
    return create_template_test_problem(
        num_instances=2,
        template_tasks_count=2,
        operators_count=2,
        skills_count=1,
        machines_count=1,
    )


def create_complex_template_problem() -> SchedulingProblem:
    """Create a complex template problem for advanced testing."""
    return create_template_test_problem(
        num_instances=5,
        template_tasks_count=4,
        operators_count=6,
        skills_count=4,
        machines_count=3,
    )
