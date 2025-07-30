"""Template-based test data generator for identical jobs scheduling.

This module creates test data using job templates to enable efficient
scheduling of multiple identical job instances.
"""

from datetime import UTC, datetime, timedelta

from src.solver.models.problem import (
    JobInstance,
    JobTemplate,
    Machine,
    SchedulingProblem,
    TaskMode,
    TemplatePrecedence,
    TemplateTask,
    WorkCell,
)


def create_manufacturing_job_template() -> JobTemplate:
    """Create a realistic manufacturing job template.

    This template represents a typical manufacturing process with:
    - Setup tasks
    - Production tasks
    - Quality control
    - Cleanup/teardown

    Returns:
        JobTemplate with realistic manufacturing workflow

    """
    # Define template tasks
    template_tasks = [
        TemplateTask(
            template_task_id="setup_machine",
            name="Machine Setup",
            department_id="production",
            is_setup=True,
            modes=[
                TaskMode(
                    "mode_setup_m1", "setup_machine", "machine_1", 30
                ),  # 30 minutes
                TaskMode(
                    "mode_setup_m2", "setup_machine", "machine_2", 45
                ),  # 45 minutes
            ],
        ),
        TemplateTask(
            template_task_id="load_material",
            name="Load Raw Material",
            department_id="production",
            modes=[
                TaskMode(
                    "mode_load_m1", "load_material", "machine_1", 15
                ),  # 15 minutes
                TaskMode(
                    "mode_load_m2", "load_material", "machine_2", 20
                ),  # 20 minutes
            ],
        ),
        TemplateTask(
            template_task_id="primary_operation",
            name="Primary Manufacturing Operation",
            department_id="production",
            modes=[
                TaskMode(
                    "mode_primary_m1", "primary_operation", "machine_1", 90
                ),  # 1.5 hours
                TaskMode(
                    "mode_primary_m2", "primary_operation", "machine_2", 75
                ),  # 1.25 hours
                TaskMode(
                    "mode_primary_m3", "primary_operation", "machine_3", 120
                ),  # 2 hours (slower machine)
            ],
        ),
        TemplateTask(
            template_task_id="secondary_operation",
            name="Secondary Manufacturing Operation",
            department_id="production",
            modes=[
                TaskMode(
                    "mode_secondary_m2", "secondary_operation", "machine_2", 60
                ),  # 1 hour
                TaskMode(
                    "mode_secondary_m3", "secondary_operation", "machine_3", 45
                ),  # 45 minutes
            ],
        ),
        TemplateTask(
            template_task_id="quality_check",
            name="Quality Control Inspection",
            department_id="quality",
            modes=[
                TaskMode(
                    "mode_qc_station", "quality_check", "qc_station", 30
                ),  # 30 minutes
            ],
        ),
        TemplateTask(
            template_task_id="packaging",
            name="Package Finished Product",
            department_id="packaging",
            modes=[
                TaskMode(
                    "mode_pack_station", "packaging", "pack_station", 20
                ),  # 20 minutes
            ],
        ),
        TemplateTask(
            template_task_id="cleanup",
            name="Machine Cleanup",
            department_id="production",
            is_setup=True,
            modes=[
                TaskMode("mode_cleanup_m1", "cleanup", "machine_1", 20),  # 20 minutes
                TaskMode("mode_cleanup_m2", "cleanup", "machine_2", 25),  # 25 minutes
                TaskMode("mode_cleanup_m3", "cleanup", "machine_3", 15),  # 15 minutes
            ],
        ),
    ]

    # Define precedence relationships (manufacturing workflow)
    template_precedences = [
        TemplatePrecedence("setup_machine", "load_material"),
        TemplatePrecedence("load_material", "primary_operation"),
        TemplatePrecedence("primary_operation", "secondary_operation"),
        TemplatePrecedence("secondary_operation", "quality_check"),
        TemplatePrecedence("quality_check", "packaging"),
        TemplatePrecedence("packaging", "cleanup"),
    ]

    return JobTemplate(
        template_id="manufacturing_job_template",
        name="Standard Manufacturing Job",
        description="Complete manufacturing process from setup to packaging",
        template_tasks=template_tasks,
        template_precedences=template_precedences,
    )


def create_test_machines() -> list[Machine]:
    """Create realistic test machines for manufacturing template."""
    return [
        Machine(
            resource_id="machine_1",
            cell_id="production_cell_1",
            name="CNC Machine #1",
            capacity=1,
            cost_per_hour=150.0,
        ),
        Machine(
            resource_id="machine_2",
            cell_id="production_cell_1",
            name="CNC Machine #2",
            capacity=1,
            cost_per_hour=175.0,
        ),
        Machine(
            resource_id="machine_3",
            cell_id="production_cell_2",
            name="Manual Assembly Station",
            capacity=2,  # Can handle 2 jobs simultaneously
            cost_per_hour=80.0,
        ),
        Machine(
            resource_id="qc_station",
            cell_id="quality_cell",
            name="Quality Control Station",
            capacity=1,
            cost_per_hour=100.0,
        ),
        Machine(
            resource_id="pack_station",
            cell_id="packaging_cell",
            name="Packaging Station",
            capacity=3,  # High throughput packaging
            cost_per_hour=60.0,
        ),
    ]


def create_test_work_cells() -> list[WorkCell]:
    """Create work cells for test machines."""
    return [
        WorkCell(
            cell_id="production_cell_1", name="Primary Production Cell", capacity=2
        ),
        WorkCell(
            cell_id="production_cell_2", name="Secondary Production Cell", capacity=2
        ),
        WorkCell(cell_id="quality_cell", name="Quality Control Cell", capacity=1),
        WorkCell(cell_id="packaging_cell", name="Packaging Cell", capacity=3),
    ]


def create_template_problem(
    template: JobTemplate,
    num_instances: int,
    base_due_hours: float = 24.0,
    due_hour_increment: float = 2.0,
) -> SchedulingProblem:
    """Create a scheduling problem from job template with multiple instances.

    Args:
        template: The job template to instantiate
        num_instances: Number of identical job instances to create
        base_due_hours: Hours from now for first job due date
        due_hour_increment: Hours to add between job due dates

    Returns:
        SchedulingProblem with template-based structure

    """
    # Create job instances
    now = datetime.now(UTC)
    job_instances = []

    for i in range(num_instances):
        due_date = now + timedelta(hours=base_due_hours + (i * due_hour_increment))

        instance = JobInstance(
            instance_id=f"job_instance_{i:03d}",
            template_id=template.template_id,
            description=f"Manufacturing Job Instance {i + 1}",
            due_date=due_date,
        )
        job_instances.append(instance)

    # Convert template structure to current SchedulingProblem format
    # This is a bridge implementation until full template support is added
    jobs = []
    all_precedences = []

    from src.solver.models.problem import Job, Precedence, Task

    for instance in job_instances:
        # Create tasks for this job instance based on template
        instance_tasks = []
        for template_task in template.template_tasks:
            task = Task(
                task_id=f"{instance.instance_id}_{template_task.template_task_id}",
                job_id=instance.instance_id,
                name=template_task.name,
                department_id=template_task.department_id,
                is_unattended=template_task.is_unattended,
                is_setup=template_task.is_setup,
                modes=template_task.modes,  # Reuse template task modes
            )
            instance_tasks.append(task)

        # Create job from instance
        job = Job(
            job_id=instance.instance_id,
            description=instance.description,
            due_date=instance.due_date,
            tasks=instance_tasks,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
        )
        jobs.append(job)

        # Create precedences for this job instance
        for template_prec in template.template_precedences:
            precedence = Precedence(
                predecessor_task_id=f"{instance.instance_id}_{template_prec.predecessor_template_task_id}",
                successor_task_id=f"{instance.instance_id}_{template_prec.successor_template_task_id}",
            )
            all_precedences.append(precedence)

    # Create machines and work cells
    machines = create_test_machines()
    work_cells = create_test_work_cells()

    # Create scheduling problem
    problem = SchedulingProblem(
        jobs=jobs, machines=machines, work_cells=work_cells, precedences=all_precedences
    )

    return problem


def create_small_template_problem() -> SchedulingProblem:
    """Create a small template-based problem for testing (5 identical jobs)."""
    template = create_manufacturing_job_template()
    return create_template_problem(template, num_instances=5)


def create_medium_template_problem() -> SchedulingProblem:
    """Create a medium template-based problem for testing (50 identical jobs)."""
    template = create_manufacturing_job_template()
    return create_template_problem(template, num_instances=50)


def create_large_template_problem() -> SchedulingProblem:
    """Create a large template-based problem for scalability (200 identical jobs)."""
    template = create_manufacturing_job_template()
    return create_template_problem(template, num_instances=200)


if __name__ == "__main__":
    # Test template generation
    template = create_manufacturing_job_template()
    print(f"Created template: {template.name}")
    print(f"Template tasks: {template.task_count}")
    print(f"Template precedences: {len(template.template_precedences)}")

    # Validate template
    issues = template.validate_template()
    if issues:
        print("Template validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Template validation: PASSED")

    # Create small test problem
    problem = create_small_template_problem()
    print(f"\nGenerated problem with {len(problem.jobs)} identical jobs")
    print(f"Total tasks: {problem.total_task_count}")
    print(f"Total precedences: {len(problem.precedences)}")
    print(f"Machines: {len(problem.machines)}")
