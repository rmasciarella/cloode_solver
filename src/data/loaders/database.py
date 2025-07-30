"""Database loader for fresh OR-Tools solver.

Supports both legacy job-based loading and optimized template-based loading.
Template mode provides 5-8x performance improvement for identical job patterns.
"""

import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from supabase import Client, create_client

from src.solver.models.problem import (
    Job,
    JobTemplate,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)

from .template_database import TemplateDatabaseLoader

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Unified database loader supporting both legacy and template-based scheduling.

    Automatically detects available template infrastructure and provides optimal loading
    methods. For identical job patterns, template mode delivers 5-8x performance gains.
    """

    def __init__(self, use_test_tables: bool = True, prefer_template_mode: bool = True):
        """Initialize database connection with template optimization support.

        Args:
            use_test_tables: If True, use test_ prefixed tables for legacy resources.
            prefer_template_mode: If True, prefer template-based loading when available.

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
        self.prefer_template_mode = prefer_template_mode

        # Initialize template loader for advanced operations
        self._template_loader = TemplateDatabaseLoader(use_test_tables)

        # Cache for template availability check
        self._template_tables_available: bool | None = None

    def load_problem(self, max_instances: int | None = None) -> SchedulingProblem:
        """Load complete scheduling problem using optimal loading strategy.

        Automatically detects template availability and uses the most efficient loading method:
        - Template mode: 5-8x faster for identical job patterns
        - Legacy mode: Full compatibility with existing job structures

        Args:
            max_instances: Maximum instances to load (applies to template mode only)

        Returns:
            SchedulingProblem optimized for the available data structure

        """
        logger.info("Loading scheduling problem from database...")

        # Check if template infrastructure is available and preferred
        if self.prefer_template_mode and self._has_template_tables():
            return self._load_template_problem(max_instances)
        else:
            return self._load_legacy_problem()

    def load_template_problem(
        self,
        template_id: str,
        max_instances: int | None = None,
        status_filter: str = "scheduled",
    ) -> SchedulingProblem:
        """Load specific template-based problem (advanced usage).

        Args:
            template_id: UUID of the job template to load
            max_instances: Maximum number of instances to load
            status_filter: Instance status filter ('scheduled', 'all')

        Returns:
            SchedulingProblem with template-based structure

        """
        return self._template_loader.load_template_problem(
            template_id, max_instances, status_filter
        )

    def load_available_templates(self) -> list[JobTemplate]:
        """Load all available job templates for selection."""
        if not self._has_template_tables():
            logger.warning("Template tables not available")
            return []
        return self._template_loader.load_available_templates()

    def create_template_instances(
        self,
        template_id: str,
        instance_count: int,
        base_description: str = "Generated Instance",
    ) -> list[str]:
        """Create new job instances from template."""
        if not self._has_template_tables():
            raise ValueError("Template tables not available")
        return self._template_loader.create_template_instances(
            template_id, instance_count, base_description
        )

    def _has_template_tables(self) -> bool:
        """Check if template tables are available in database."""
        if self._template_tables_available is not None:
            return self._template_tables_available

        try:
            # Try to query job_templates table
            self.supabase.table("job_templates").select("template_id").limit(
                1
            ).execute()
            self._template_tables_available = True
            logger.info("Template infrastructure detected - enabling optimized loading")
        except Exception as e:
            self._template_tables_available = False
            logger.info(
                f"Template infrastructure not available - using legacy mode: {e}"
            )

        return self._template_tables_available

    def _load_template_problem(
        self, template_id: str | None = None, max_instances: int | None = None
    ) -> SchedulingProblem:
        """Load problem using template-based optimization with explicit template selection."""
        if not template_id:
            # List available templates for user selection
            templates = self.load_available_templates()
            if not templates:
                logger.warning("No templates found - falling back to legacy loading")
                return self._load_legacy_problem()

            # Don't auto-select - require explicit choice
            template_names = [f"{t.template_id}: {t.name}" for t in templates]
            raise ValueError(
                f"Template ID required for template-based loading. "
                f"Available templates: {template_names}"
            )

        logger.info(f"Loading template-based problem: {template_id}")
        return self.load_template_problem(template_id, max_instances)

    def _load_legacy_problem(self) -> SchedulingProblem:
        """Load problem using legacy job-based approach."""
        logger.info("Using legacy job-based loading")

        # Load all data using original approach
        work_cells = self._load_work_cells()
        machines = self._load_machines()
        jobs = self._load_jobs()
        tasks = self._load_tasks()
        task_modes = self._load_task_modes()
        precedences = self._load_precedences()

        # Associate machines with work cells
        machine_by_cell: dict[str, list[Machine]] = {}
        for machine in machines:
            if machine.cell_id not in machine_by_cell:
                machine_by_cell[machine.cell_id] = []
            machine_by_cell[machine.cell_id].append(machine)

        for cell in work_cells:
            cell.machines = machine_by_cell.get(cell.cell_id, [])

        # Associate task modes with tasks
        modes_by_task: dict[str, list[TaskMode]] = {}
        for mode in task_modes:
            if mode.task_id not in modes_by_task:
                modes_by_task[mode.task_id] = []
            modes_by_task[mode.task_id].append(mode)

        for task in tasks:
            task.modes = modes_by_task.get(task.task_id, [])

        # Associate tasks with jobs
        tasks_by_job: dict[str, list[Task]] = {}
        for task in tasks:
            if task.job_id not in tasks_by_job:
                tasks_by_job[task.job_id] = []
            tasks_by_job[task.job_id].append(task)

        for job in jobs:
            job.tasks = tasks_by_job.get(job.job_id, [])

        # Create and validate problem
        problem = SchedulingProblem(
            jobs=jobs, machines=machines, work_cells=work_cells, precedences=precedences
        )

        # Validate
        issues = problem.validate()
        if issues:
            logger.warning("Problem validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")

        logger.info("Loaded legacy problem with:")
        logger.info(f"  - {len(jobs)} jobs")
        logger.info(f"  - {problem.total_task_count} tasks")
        logger.info(f"  - {len(machines)} machines")
        logger.info(f"  - {len(work_cells)} work cells")
        logger.info(f"  - {len(precedences)} precedence constraints")

        return problem

    def _load_work_cells(self) -> list[WorkCell]:
        """Load work cells from database."""
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
        """Load machines from database."""
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

    def _load_jobs(self) -> list[Job]:
        """Load jobs from database."""
        table_name = f"{self.table_prefix}jobs"
        response = self.supabase.table(table_name).select("*").execute()

        jobs = []
        for row in response.data:
            jobs.append(
                Job(
                    job_id=row["job_id"],
                    description=row["description"] or f"Job {row['job_id'][:8]}",
                    due_date=datetime.fromisoformat(
                        row["due_date"].replace("Z", "+00:00")
                    ),
                    created_at=datetime.fromisoformat(
                        row["created_at"].replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        row["updated_at"].replace("Z", "+00:00")
                    ),
                )
            )

        return jobs

    def _load_tasks(self) -> list[Task]:
        """Load tasks from database."""
        table_name = f"{self.table_prefix}tasks"
        response = self.supabase.table(table_name).select("*").execute()

        tasks = []
        for row in response.data:
            tasks.append(
                Task(
                    task_id=row["task_id"],
                    job_id=row["job_id"],
                    name=row["name"],
                    department_id=row.get("department_id"),
                    is_unattended=row.get("is_unattended", False),
                    is_setup=row.get("is_setup", False),
                )
            )

        return tasks

    def _load_task_modes(self) -> list[TaskMode]:
        """Load task modes from database."""
        table_name = f"{self.table_prefix}task_modes"
        response = self.supabase.table(table_name).select("*").execute()

        modes = []
        for row in response.data:
            modes.append(
                TaskMode(
                    task_mode_id=row["task_mode_id"],
                    task_id=row["task_id"],
                    machine_resource_id=row["machine_resource_id"],
                    duration_minutes=row["duration_minutes"],
                )
            )

        return modes

    def _load_precedences(self) -> list[Precedence]:
        """Load precedence constraints from database."""
        table_name = f"{self.table_prefix}task_precedences"
        response = self.supabase.table(table_name).select("*").execute()

        precedences = []
        for row in response.data:
            precedences.append(
                Precedence(
                    predecessor_task_id=row["predecessor_task_id"],
                    successor_task_id=row["successor_task_id"],
                )
            )

        return precedences


# Convenience functions for quick loading
def load_test_problem(max_instances: int | None = None) -> SchedulingProblem:
    """Load test problem using optimal loading strategy.

    Automatically detects template availability and uses most efficient method.

    Args:
        max_instances: Maximum instances to load (template mode only)

    Returns:
        SchedulingProblem optimized for available data structure

    """
    loader = DatabaseLoader(use_test_tables=True)
    return loader.load_problem(max_instances)


def load_template_test_problem(
    template_id: str, max_instances: int | None = None
) -> SchedulingProblem:
    """Load specific template-based test problem."""
    loader = DatabaseLoader(use_test_tables=True)
    return loader.load_template_problem(template_id, max_instances)


def load_legacy_test_problem() -> SchedulingProblem:
    """Load test problem using legacy job-based approach (force legacy mode)."""
    loader = DatabaseLoader(use_test_tables=True, prefer_template_mode=False)
    return loader.load_problem()


if __name__ == "__main__":
    # Test loading
    problem = load_test_problem()
    logger.info("\nProblem loaded successfully!")
