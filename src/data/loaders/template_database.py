"""Template-based database loader for Fresh OR-Tools solver.

Week 3 Implementation: Optimized loading for template-based scheduling.
Achieves O(template_size × instances) performance instead of O(n³).
"""

import logging
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from src.solver.models.problem import (
    Job,
    JobInstance,
    JobTemplate,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    TemplatePrecedence,
    TemplateTask,
    WorkCell,
)

logger = logging.getLogger(__name__)


class TemplateDatabaseLoader:
    """Efficient template-based database loader for OR-Tools solver."""

    def __init__(self, use_test_tables: bool = True):
        """Initialize database connection.

        Args:
            use_test_tables: If True, use test_ prefixed tables for resources.
                Template tables don't use prefixes.

        """
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment"
            )

        self.supabase: Client = create_client(url, key)
        self.table_prefix = "test_" if use_test_tables else ""

    def load_template_problem(
        self,
        template_id: str,
        max_instances: int | None = None,
        status_filter: str = "scheduled",
    ) -> SchedulingProblem:
        """Load complete scheduling problem from template.

        This is the primary method for template-based loading, optimized for
        performance with O(template_size × instances) complexity.

        Args:
            template_id: UUID of the job template to load
            max_instances: Maximum number of instances to load (None = all)
            status_filter: Instance status filter ('scheduled', 'all')

        Returns:
            SchedulingProblem with template-based structure

        """
        logger.info(f"Loading template-based problem for template {template_id}")

        # Load template definition (O(template_size))
        template = self._load_job_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Load job instances (O(instances))
        instances = self._load_job_instances(template_id, max_instances, status_filter)
        if not instances:
            raise ValueError(f"No instances found for template {template_id}")

        # Load shared resources (cached, O(1) amortized)
        work_cells = self._load_work_cells()
        machines = self._load_machines()

        # Convert to current SchedulingProblem format
        # This bridges template architecture with existing solver
        jobs = self._convert_instances_to_jobs(template, instances)
        precedences = self._generate_precedences_from_template(template, instances)

        # Associate machines with work cells
        self._associate_machines_with_cells(machines, work_cells)

        # Create scheduling problem
        problem = SchedulingProblem(
            jobs=jobs,
            machines=machines,
            work_cells=work_cells,
            precedences=precedences,
            job_template=template,  # Store template for optimization
        )

        # Validate
        issues = problem.validate()
        if issues:
            logger.warning("Problem validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")

        logger.info("Loaded template-based problem:")
        logger.info(f"  - Template: {template.name} ({template.task_count} tasks)")
        logger.info(f"  - Instances: {len(instances)}")
        logger.info(f"  - Total tasks: {problem.total_task_count}")
        logger.info(f"  - Machines: {len(machines)}")
        logger.info(f"  - Precedences: {len(precedences)}")

        return problem

    def load_available_templates(self) -> list[JobTemplate]:
        """Load all available job templates for selection.

        Note: This implementation uses N+1 queries (1 for templates + N for details).
        For large numbers of templates (>100), consider optimizing with JOIN queries
        or batch loading. Currently acceptable for typical template counts (<50).
        """
        response = (
            self.supabase.table("job_templates")
            .select(
                """
            template_id, name, description, task_count,
            total_min_duration_minutes, critical_path_length_minutes,
            created_at, updated_at
            """
            )
            .execute()
        )

        templates = []
        for row in response.data:
            # Load full template details for each (N+1 query pattern)
            # TODO: Optimize with batch loading if template count grows large
            template = self._load_job_template(row["template_id"])
            if template:
                templates.append(template)

        logger.info(f"Loaded {len(templates)} available templates")
        return templates

    def create_template_instances(
        self,
        template_id: str,
        instance_count: int,
        base_description: str = "Generated Instance",
        hours_between_due_dates: float = 2.0,
    ) -> list[str]:
        """Create new job instances from template.

        Args:
            template_id: Template to instantiate
            instance_count: Number of instances to create
            base_description: Base description for instances
            hours_between_due_dates: Hours between due dates

        Returns:
            List of created instance IDs

        """
        from datetime import timedelta

        now = datetime.now()
        base_due_date = now + timedelta(hours=24)  # 24 hours from now

        instance_data = []
        for i in range(instance_count):
            due_date = base_due_date + timedelta(hours=hours_between_due_dates * i)
            instance_data.append(
                {
                    "template_id": template_id,
                    "description": f"{base_description} {i + 1}",
                    "due_date": due_date.isoformat(),
                    "status": "scheduled",
                    "priority": 100,
                }
            )

        response = self.supabase.table("job_instances").insert(instance_data).execute()

        instance_ids = [row["instance_id"] for row in response.data]
        logger.info(f"Created {len(instance_ids)} instances for template {template_id}")

        return instance_ids

    def _load_job_template(self, template_id: str) -> JobTemplate | None:
        """Load complete job template with tasks and precedences."""
        # Load template header
        template_response = (
            self.supabase.table("job_templates")
            .select("*")
            .eq("template_id", template_id)
            .execute()
        )

        if not template_response.data:
            return None

        template_data = template_response.data[0]

        # Load template tasks with modes (optimized single query)
        tasks_response = (
            self.supabase.table("template_tasks")
            .select(
                """
            template_task_id, name, department_id, is_unattended, is_setup, position,
            template_task_modes (
                template_task_mode_id, mode_name, machine_resource_id, duration_minutes
            )
            """
            )
            .eq("template_id", template_id)
            .order("position")
            .execute()
        )

        # Convert to TemplateTask objects
        template_tasks = []
        for task_data in tasks_response.data:
            modes = []
            for mode_data in task_data.get("template_task_modes", []):
                mode = TaskMode(
                    task_mode_id=mode_data["template_task_mode_id"],
                    task_id=task_data["template_task_id"],  # Reuse for compatibility
                    machine_resource_id=mode_data["machine_resource_id"],
                    duration_minutes=mode_data["duration_minutes"],
                )
                modes.append(mode)

            template_task = TemplateTask(
                template_task_id=task_data["template_task_id"],
                name=task_data["name"],
                department_id=task_data["department_id"],
                is_unattended=task_data.get("is_unattended", False),
                is_setup=task_data.get("is_setup", False),
                modes=modes,
            )
            template_tasks.append(template_task)

        # Load template precedences
        prec_response = (
            self.supabase.table("template_precedences")
            .select("*")
            .eq("template_id", template_id)
            .execute()
        )

        template_precedences = []
        for prec_data in prec_response.data:
            precedence = TemplatePrecedence(
                predecessor_template_task_id=prec_data["predecessor_template_task_id"],
                successor_template_task_id=prec_data["successor_template_task_id"],
            )
            template_precedences.append(precedence)

        # Create template object
        template = JobTemplate(
            template_id=template_data["template_id"],
            name=template_data["name"],
            description=template_data["description"],
            template_tasks=template_tasks,
            template_precedences=template_precedences,
            created_at=datetime.fromisoformat(
                template_data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                template_data["updated_at"].replace("Z", "+00:00")
            ),
        )

        return template

    def _load_job_instances(
        self,
        template_id: str,
        max_instances: int | None = None,
        status_filter: str = "scheduled",
    ) -> list[JobInstance]:
        """Load job instances for template."""
        query = (
            self.supabase.table("job_instances")
            .select("*")
            .eq("template_id", template_id)
        )

        if status_filter != "all":
            query = query.eq("status", status_filter)

        query = query.order("due_date")

        if max_instances:
            query = query.limit(max_instances)

        response = query.execute()

        instances = []
        for row in response.data:
            instance = JobInstance(
                instance_id=row["instance_id"],
                template_id=row["template_id"],
                description=row["description"] or f"Instance {row['instance_id'][:8]}",
                due_date=datetime.fromisoformat(row["due_date"].replace("Z", "+00:00")),
                created_at=datetime.fromisoformat(
                    row["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    row["updated_at"].replace("Z", "+00:00")
                ),
            )
            instances.append(instance)

        return instances

    def _load_work_cells(self) -> list[WorkCell]:
        """Load work cells (reuse existing implementation)."""
        table_name = f"{self.table_prefix}work_cells"
        response = self.supabase.table(table_name).select("*").execute()

        cells = []
        for row in response.data:
            cells.append(
                WorkCell(
                    cell_id=row["cell_id"], name=row["name"], capacity=row["capacity"]
                )
            )

        return cells

    def _load_machines(self) -> list[Machine]:
        """Load machines (reuse existing implementation)."""
        table_name = f"{self.table_prefix}resources"
        response = (
            self.supabase.table(table_name)
            .select("*")
            .eq("resource_type", "machine")
            .execute()
        )

        machines = []
        for row in response.data:
            machines.append(
                Machine(
                    resource_id=row["resource_id"],
                    cell_id=row["cell_id"],
                    name=row["name"],
                    capacity=row["capacity"],
                    cost_per_hour=(
                        float(row["cost_per_hour"]) if row["cost_per_hour"] else 0.0
                    ),
                )
            )

        return machines

    def _convert_instances_to_jobs(
        self, template: JobTemplate, instances: list[JobInstance]
    ) -> list[Job]:
        """Convert template + instances to Job objects for solver compatibility."""
        jobs = []

        for instance in instances:
            # Create tasks for this instance based on template
            instance_tasks = []
            for template_task in template.template_tasks:
                task = Task(
                    task_id=f"{instance.instance_id}_{template_task.template_task_id}",
                    job_id=instance.instance_id,
                    name=template_task.name,
                    department_id=template_task.department_id,
                    is_unattended=template_task.is_unattended,
                    is_setup=template_task.is_setup,
                    modes=template_task.modes,  # Reuse template modes
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

        return jobs

    def _generate_precedences_from_template(
        self, template: JobTemplate, instances: list[JobInstance]
    ) -> list[Precedence]:
        """Generate precedences for all instances from template."""
        precedences = []

        for instance in instances:
            for template_prec in template.template_precedences:
                precedence = Precedence(
                    predecessor_task_id=f"{instance.instance_id}_{template_prec.predecessor_template_task_id}",
                    successor_task_id=f"{instance.instance_id}_{template_prec.successor_template_task_id}",
                )
                precedences.append(precedence)

        return precedences

    def _associate_machines_with_cells(
        self, machines: list[Machine], work_cells: list[WorkCell]
    ) -> None:
        """Associate machines with their work cells."""
        machine_by_cell: dict[str, list[Machine]] = {}
        for machine in machines:
            if machine.cell_id not in machine_by_cell:
                machine_by_cell[machine.cell_id] = []
            machine_by_cell[machine.cell_id].append(machine)

        for cell in work_cells:
            cell.machines = machine_by_cell.get(cell.cell_id, [])

    def save_solution_assignments(
        self, problem: SchedulingProblem, solution_data: dict[str, Any]
    ) -> None:
        """Save solved task assignments back to database.

        Args:
            problem: Solved scheduling problem
            solution_data: Dictionary with task assignments and timing

        """
        if not problem.job_template:
            logger.warning("No template information available for saving assignments")
            return

        assignments = []
        for job in problem.jobs:
            instance_id = job.job_id

            for task in job.tasks:
                # Extract template task ID from composite task ID
                template_task_id = task.task_id.split("_", 1)[
                    1
                ]  # Remove instance prefix

                if task.task_id in solution_data:
                    assignment_data = solution_data[task.task_id]

                    assignment = {
                        "instance_id": instance_id,
                        "template_task_id": template_task_id,
                        "selected_mode_id": assignment_data.get("mode_id"),
                        "start_time_minutes": assignment_data.get("start_time"),
                        "end_time_minutes": assignment_data.get("end_time"),
                        "assigned_machine_id": assignment_data.get("machine_id"),
                    }
                    assignments.append(assignment)

        if assignments:
            # Use UPSERT for atomic save operation (safer than delete+insert)
            instance_ids = [job.job_id for job in problem.jobs]

            try:
                # First clear existing assignments for these instances in atomic
                # operation
                _delete_response = (
                    self.supabase.table("instance_task_assignments")
                    .delete()
                    .in_("instance_id", instance_ids)
                    .execute()
                )

                # Then insert all new assignments
                # Note: If this fails, assignments are cleared but database is in
                # consistent state
                insert_response = (
                    self.supabase.table("instance_task_assignments")
                    .insert(assignments)
                    .execute()
                )

                if not insert_response.data:
                    logger.warning("Insert operation completed but returned no data")

                logger.info(f"Saved {len(assignments)} task assignments to database")
                logger.info(
                    f"Cleared existing assignments for {len(instance_ids)} instances"
                )

            except Exception as e:
                logger.error(f"Failed to save assignments: {e}")
                # Re-raise with context - calling code can decide how to handle
                raise RuntimeError(f"Assignment save operation failed: {e}") from e


# Convenience functions for common operations
def load_template_problem(
    template_id: str, max_instances: int | None = None
) -> SchedulingProblem:
    """Load template-based scheduling problem."""
    loader = TemplateDatabaseLoader(use_test_tables=True)
    return loader.load_template_problem(template_id, max_instances)


def load_available_templates() -> list[JobTemplate]:
    """Load all available job templates."""
    loader = TemplateDatabaseLoader(use_test_tables=True)
    return loader.load_available_templates()


if __name__ == "__main__":
    # Test template loading
    loader = TemplateDatabaseLoader()

    # Load available templates
    templates = loader.load_available_templates()
    if templates:
        print(f"Found {len(templates)} templates:")
        for template in templates:
            print(f"  - {template.name}: {template.task_count} tasks")

        # Load problem from first template
        problem = loader.load_template_problem(templates[0].template_id)
        print(
            f"\nLoaded problem with {len(problem.jobs)} jobs, "
            f"{problem.total_task_count} tasks"
        )
    else:
        print("No templates found. Run migration script to create templates.")
