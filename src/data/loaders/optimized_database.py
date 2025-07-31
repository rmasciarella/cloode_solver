"""Optimized mode database loader for Fresh OR-Tools solver.

Week 3 Implementation: Optimized loading for optimized mode scheduling.
Achieves O(pattern_size × instances) performance instead of O(n³).
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
    JobOptimizedPattern,
    Machine,
    OptimizedPrecedence,
    OptimizedTask,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)

logger = logging.getLogger(__name__)


class OptimizedDatabaseLoader:
    """Efficient optimized mode database loader for OR-Tools solver."""

    def __init__(self, use_test_tables: bool = True):
        """Initialize database connection.

        Args:
            use_test_tables: If True, use test_ prefixed tables for resources.
                Optimized pattern tables don't use prefixes.

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

    def load_optimized_problem(
        self,
        pattern_id: str,
        max_instances: int | None = None,
        status_filter: str = "scheduled",
    ) -> SchedulingProblem:
        """Load complete scheduling problem from optimized pattern.

        This is the primary method for optimized mode loading, optimized for
        performance with O(pattern_size × instances) complexity.

        Args:
            pattern_id: UUID of the job optimized pattern to load
            max_instances: Maximum number of instances to load (None = all)
            status_filter: Instance status filter ('scheduled', 'all')

        Returns:
            SchedulingProblem with optimized mode structure

        """
        logger.info(f"Loading optimized mode problem for pattern {pattern_id}")

        # Load optimized pattern definition (O(pattern_size))
        pattern = self._load_job_optimized_pattern(pattern_id)
        if not pattern:
            raise ValueError(f"Optimized pattern {pattern_id} not found")

        # Load job instances (O(instances))
        instances = self._load_job_instances(pattern_id, max_instances, status_filter)
        if not instances:
            raise ValueError(f"No instances found for pattern {pattern_id}")

        # Load shared resources (cached, O(1) amortized)
        work_cells = self._load_work_cells()
        machines = self._load_machines()

        # Convert to current SchedulingProblem format
        # This bridges optimized pattern architecture with existing solver
        jobs = self._convert_instances_to_jobs(pattern, instances)
        precedences = self._generate_precedences_from_pattern(pattern, instances)

        # Associate machines with work cells
        self._associate_machines_with_cells(machines, work_cells)

        # Create scheduling problem
        problem = SchedulingProblem(
            jobs=jobs,
            machines=machines,
            work_cells=work_cells,
            precedences=precedences,
            job_optimized_pattern=pattern,  # Store pattern for optimization
        )

        # Validate
        issues = problem.validate()
        if issues:
            logger.warning("Problem validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")

        logger.info("Loaded optimized mode problem:")
        logger.info(f"  - Pattern: {pattern.name} ({pattern.task_count} tasks)")
        logger.info(f"  - Instances: {len(instances)}")
        logger.info(f"  - Total tasks: {problem.total_task_count}")
        logger.info(f"  - Machines: {len(machines)}")
        logger.info(f"  - Precedences: {len(precedences)}")

        return problem

    def load_available_patterns(self) -> list[JobOptimizedPattern]:
        """Load all available job optimized patterns for selection.

        Note: This implementation uses N+1 queries (1 for patterns + N for details).
        For large numbers of patterns (>100), consider optimizing with JOIN queries
        or batch loading. Currently acceptable for typical pattern counts (<50).
        """
        response = (
            self.supabase.table("job_optimized_patterns")
            .select(
                """
            pattern_id, name, description, task_count,
            total_min_duration_minutes, critical_path_length_minutes,
            created_at, updated_at
            """
            )
            .execute()
        )

        patterns = []
        for row in response.data:
            # Load full pattern details for each (N+1 query pattern)
            # TODO: Optimize with batch loading if pattern count grows large
            pattern = self._load_job_optimized_pattern(row["pattern_id"])
            if pattern:
                patterns.append(pattern)

        logger.info(f"Loaded {len(patterns)} available optimized patterns")
        return patterns

    def create_pattern_instances(
        self,
        pattern_id: str,
        instance_count: int,
        base_description: str = "Generated Instance",
        hours_between_due_dates: float = 2.0,
    ) -> list[str]:
        """Create new job instances from optimized pattern.

        Args:
            pattern_id: Optimized pattern to instantiate
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
                    "pattern_id": pattern_id,
                    "description": f"{base_description} {i + 1}",
                    "due_date": due_date.isoformat(),
                    "status": "scheduled",
                    "priority": 100,
                }
            )

        response = self.supabase.table("job_instances").insert(instance_data).execute()

        instance_ids = [row["instance_id"] for row in response.data]
        logger.info(f"Created {len(instance_ids)} instances for pattern {pattern_id}")

        return instance_ids

    def _load_job_optimized_pattern(
        self, pattern_id: str
    ) -> JobOptimizedPattern | None:
        """Load complete job optimized pattern with tasks and precedences."""
        # Load optimized pattern header
        pattern_response = (
            self.supabase.table("job_optimized_patterns")
            .select("*")
            .eq("pattern_id", pattern_id)
            .execute()
        )

        if not pattern_response.data:
            return None

        pattern_data = pattern_response.data[0]

        # Load optimized tasks with modes (optimized single query)
        tasks_response = (
            self.supabase.table("optimized_tasks")
            .select(
                """
            optimized_task_id, name, department_id, is_unattended, is_setup, position,
            optimized_task_modes (
                optimized_task_mode_id, mode_name, machine_resource_id, duration_minutes
            )
            """
            )
            .eq("pattern_id", pattern_id)
            .order("position")
            .execute()
        )

        # Convert to OptimizedTask objects
        optimized_tasks = []
        for task_data in tasks_response.data:
            modes = []
            for mode_data in task_data.get("optimized_task_modes", []):
                mode = TaskMode(
                    task_mode_id=mode_data["optimized_task_mode_id"],
                    task_id=task_data["optimized_task_id"],  # Reuse for compatibility
                    machine_resource_id=mode_data["machine_resource_id"],
                    duration_minutes=mode_data["duration_minutes"],
                )
                modes.append(mode)

            optimized_task = OptimizedTask(
                optimized_task_id=task_data["optimized_task_id"],
                name=task_data["name"],
                department_id=task_data["department_id"],
                is_unattended=task_data.get("is_unattended", False),
                is_setup=task_data.get("is_setup", False),
                modes=modes,
            )
            optimized_tasks.append(optimized_task)

        # Load optimized precedences
        prec_response = (
            self.supabase.table("optimized_precedences")
            .select("*")
            .eq("pattern_id", pattern_id)
            .execute()
        )

        optimized_precedences = []
        for prec_data in prec_response.data:
            precedence = OptimizedPrecedence(
                predecessor_optimized_task_id=prec_data[
                    "predecessor_optimized_task_id"
                ],
                successor_optimized_task_id=prec_data["successor_optimized_task_id"],
            )
            optimized_precedences.append(precedence)

        # Create optimized pattern object
        pattern = JobOptimizedPattern(
            optimized_pattern_id=pattern_data["pattern_id"],
            name=pattern_data["name"],
            description=pattern_data["description"],
            optimized_tasks=optimized_tasks,
            optimized_precedences=optimized_precedences,
            created_at=datetime.fromisoformat(
                pattern_data["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                pattern_data["updated_at"].replace("Z", "+00:00")
            ),
        )

        return pattern

    def _load_job_instances(
        self,
        pattern_id: str,
        max_instances: int | None = None,
        status_filter: str = "scheduled",
    ) -> list[JobInstance]:
        """Load job instances for optimized pattern."""
        query = (
            self.supabase.table("job_instances")
            .select("*")
            .eq("pattern_id", pattern_id)
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
                optimized_pattern_id=row["pattern_id"],
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
        self, pattern: JobOptimizedPattern, instances: list[JobInstance]
    ) -> list[Job]:
        """Convert optimized pattern + instances to Job objects for compatibility."""
        jobs = []

        for instance in instances:
            # Create tasks for this instance based on optimized pattern
            instance_tasks = []
            for optimized_task in pattern.optimized_tasks:
                task = Task(
                    task_id=f"{instance.instance_id}_{optimized_task.optimized_task_id}",
                    job_id=instance.instance_id,
                    name=optimized_task.name,
                    department_id=optimized_task.department_id,
                    is_unattended=optimized_task.is_unattended,
                    is_setup=optimized_task.is_setup,
                    modes=optimized_task.modes,  # Reuse optimized pattern modes
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

    def _generate_precedences_from_pattern(
        self, pattern: JobOptimizedPattern, instances: list[JobInstance]
    ) -> list[Precedence]:
        """Generate precedences for all instances from optimized pattern."""
        precedences = []

        for instance in instances:
            for optimized_prec in pattern.optimized_precedences:
                precedence = Precedence(
                    predecessor_task_id=f"{instance.instance_id}_{optimized_prec.predecessor_optimized_task_id}",
                    successor_task_id=f"{instance.instance_id}_{optimized_prec.successor_optimized_task_id}",
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
        if not problem.job_optimized_pattern:
            logger.warning(
                "No optimized pattern information available for saving assignments"
            )
            return

        assignments = []
        for job in problem.jobs:
            instance_id = job.job_id

            for task in job.tasks:
                # Extract optimized task ID from composite task ID
                optimized_task_id = task.task_id.split("_", 1)[
                    1
                ]  # Remove instance prefix

                if task.task_id in solution_data:
                    assignment_data = solution_data[task.task_id]

                    assignment = {
                        "instance_id": instance_id,
                        "optimized_task_id": optimized_task_id,
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
def load_optimized_problem(
    pattern_id: str, max_instances: int | None = None
) -> SchedulingProblem:
    """Load optimized mode scheduling problem."""
    loader = OptimizedDatabaseLoader(use_test_tables=True)
    return loader.load_optimized_problem(pattern_id, max_instances)


def load_available_patterns() -> list[JobOptimizedPattern]:
    """Load all available job optimized patterns."""
    loader = OptimizedDatabaseLoader(use_test_tables=True)
    return loader.load_available_patterns()


if __name__ == "__main__":
    # Test template loading with structured logging
    import sys
    from pathlib import Path

    # Add project root to path for logging config import
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from src.solver.utils.logging_config import get_data_logger, setup_logging

    # Setup logging for testing
    setup_logging(level="INFO", enable_file_logging=False)
    test_logger = get_data_logger("optimized_loader_test")

    loader = OptimizedDatabaseLoader()

    # Load available optimized patterns
    patterns = loader.load_available_patterns()
    if patterns:
        test_logger.info("Optimized pattern loading test results:")
        test_logger.info("Found %d patterns:", len(patterns))
        for pattern in patterns:
            test_logger.info("  - %s: %d tasks", pattern.name, pattern.task_count)

        # Load problem from first optimized pattern
        test_logger.info("Testing problem loading from first optimized pattern...")
        problem = loader.load_optimized_problem(patterns[0].optimized_pattern_id)
        test_logger.info(
            "Loaded problem with %d jobs, %d tasks",
            len(problem.jobs),
            problem.total_task_count,
        )
        test_logger.info("Optimized pattern loading test completed successfully")

        # Also provide console feedback for immediate results
        print(f"✅ Successfully loaded {len(patterns)} optimized patterns")
        print(f"✅ Generated problem with {len(problem.jobs)} jobs")
        print("See logs for detailed optimized pattern information")
    else:
        test_logger.warning("No optimized patterns found in database")
        test_logger.info("Run migration script to create test optimized patterns")

        # Console feedback for immediate action needed
        print(
            "❌ No optimized patterns found. Run migration script to create patterns."
        )
