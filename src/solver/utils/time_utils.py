"""Utility functions for the OR-Tools solver.

Handles time calculations, horizon computation, and solution extraction.
"""

import logging
from datetime import UTC, datetime, timedelta

from ortools.sat.python import cp_model

# Type annotations - OR-Tools types
from src.solver.models.problem import Job, SchedulingProblem, Task

logger = logging.getLogger(__name__)


def calculate_horizon(problem: SchedulingProblem) -> int:
    """Calculate a reasonable horizon for the scheduling problem.

    Returns time units (15-minute intervals) from now to latest due date plus buffer.
    """
    if problem.is_template_based:
        # Template-based horizon calculation
        if not problem.job_instances:
            # No instances, use default horizon
            return 100

        # Find the latest due date from job instances
        latest_due = max(instance.due_date for instance in problem.job_instances)

        # Calculate total work content from template
        if problem.job_template:
            template_work_minutes = sum(
                template_task.min_duration
                for template_task in problem.job_template.template_tasks
            )
            total_work_minutes = template_work_minutes * len(problem.job_instances)
        else:
            total_work_minutes = 0
    else:
        # Legacy horizon calculation
        if not problem.jobs:
            return 100

        # Find the latest due date
        latest_due = max(job.due_date for job in problem.jobs)

        # Calculate total work content (sum of all minimum durations)
        total_work_minutes = sum(
            task.min_duration for job in problem.jobs for task in job.tasks
        )

    # Convert to time units (15-minute intervals)
    total_work_units = (total_work_minutes + 14) // 15

    # Calculate time from now to latest due date
    now = datetime.now(UTC)
    time_to_due = latest_due - now
    available_units = int(time_to_due.total_seconds() / 900)  # 900 seconds = 15 minutes

    # Use the larger of available time or 2x total work (to allow for machine conflicts)
    # Add 20% buffer
    horizon = int(max(available_units, total_work_units * 2) * 1.2)

    # Ensure minimum horizon
    MIN_HORIZON = 100  # At least 25 hours
    horizon = max(horizon, MIN_HORIZON)

    logger.info(
        f"Calculated horizon: {horizon} time units ({horizon * 15 / 60:.1f} hours)"
    )

    return horizon


def calculate_latest_start(task: Task, job: Job, horizon: int) -> int:
    """Calculate the latest start time for a task based on job due date.

    Args:
        task: The task to calculate for
        job: The job containing the task
        horizon: The problem horizon

    Returns:
        Latest start time in time units

    """
    # Convert due date to time units from now
    now = datetime.now(UTC)
    time_to_due = job.due_date - now
    due_time_units = int(time_to_due.total_seconds() / 900)

    # Find task position and calculate remaining work
    task_index = next(i for i, t in enumerate(job.tasks) if t.task_id == task.task_id)

    # Calculate total duration of remaining tasks (including this one)
    remaining_duration = sum(
        (t.min_duration + 14) // 15 for t in job.tasks[task_index:]
    )

    # Latest start is due date minus all remaining work
    latest_start = due_time_units - remaining_duration

    # Ensure it's within horizon and non-negative
    min_duration_units = (task.min_duration + 14) // 15
    latest_start = min(latest_start, horizon - min_duration_units)
    latest_start = max(latest_start, 0)

    return latest_start


def calculate_setup_time_metrics(
    schedule: list[dict], setup_times: dict[tuple[str, str, str], int]
) -> dict:
    """Calculate setup time metrics from the schedule.

    Args:
        schedule: List of scheduled tasks with machine assignments
        setup_times: Dictionary of setup times between tasks on machines

    Returns:
        Dictionary with setup time metrics

    """
    # Group tasks by machine and sort by start time
    machine_tasks: dict[str, list[dict]] = {}
    for task in schedule:
        machine_id = task.get("machine_id")
        if machine_id:
            if machine_id not in machine_tasks:
                machine_tasks[machine_id] = []
            machine_tasks[machine_id].append(task)

    # Sort tasks on each machine by start time
    for machine_id in machine_tasks:
        machine_tasks[machine_id].sort(key=lambda t: t["start_time"])

    # Calculate setup times
    total_setup_time = 0
    setup_instances = []
    machine_setup_times = {}

    for machine_id, tasks in machine_tasks.items():
        machine_setup_time = 0

        for i in range(len(tasks) - 1):
            current_task = tasks[i]
            next_task = tasks[i + 1]

            # Check if there's a setup time between these tasks
            setup_key = (current_task["task_id"], next_task["task_id"], machine_id)
            setup_time = setup_times.get(setup_key, 0)

            if setup_time > 0:
                total_setup_time += setup_time
                machine_setup_time += setup_time

                setup_instances.append(
                    {
                        "from_task": current_task["task_id"],
                        "to_task": next_task["task_id"],
                        "machine": machine_id,
                        "setup_time": setup_time,
                        "setup_time_minutes": setup_time * 15,
                        "start_time": current_task["end_time"],
                        "end_time": current_task["end_time"] + setup_time,
                    }
                )

        machine_setup_times[machine_id] = {
            "total_setup_time": machine_setup_time,
            "total_setup_minutes": machine_setup_time * 15,
            "num_setups": len(
                [s for s in setup_instances if s["machine"] == machine_id]
            ),
        }

    return {
        "total_setup_time": total_setup_time,
        "total_setup_minutes": total_setup_time * 15,
        "num_setups": len(setup_instances),
        "setup_instances": setup_instances,
        "machine_setup_times": machine_setup_times,
        "average_setup_time": (
            total_setup_time / len(setup_instances) if setup_instances else 0
        ),
        "average_setup_minutes": (
            (total_setup_time * 15) / len(setup_instances) if setup_instances else 0
        ),
    }


def extract_solution(
    solver: cp_model.CpSolver,
    _model: cp_model.CpModel,  # Not used in current implementation
    problem: SchedulingProblem,
    task_starts: dict[tuple[str, str], cp_model.IntVar],
    task_ends: dict[tuple[str, str], cp_model.IntVar],
    task_assigned: dict[tuple[str, str, str], cp_model.IntVar],
    _task_modes_selected: dict[tuple[str, str], cp_model.IntVar] | None = None,
    setup_times: dict[tuple[str, str, str], int] | None = None,
) -> dict:
    """Extract solution from solved model.

    Returns:
        Dictionary with solution details including:
        - schedule: List of scheduled tasks with times and assignments
        - makespan: Total schedule length
        - lateness: Total lateness across all jobs
        - solver_stats: Solver statistics

    """
    if solver.StatusName() not in ["OPTIMAL", "FEASIBLE"]:
        return {
            "status": solver.StatusName(),
            "schedule": [],
            "makespan": 0,
            "lateness": 0,
            "solver_stats": {
                "status": solver.StatusName(),
                "solve_time": solver.WallTime(),
                "branches": solver.NumBranches(),
                "conflicts": solver.NumConflicts(),
            },
        }

    schedule = []
    makespan = 0
    total_lateness = 0
    now = datetime.now(UTC)

    if problem.is_template_based and problem.job_template:
        # Template-based solution extraction
        for instance in problem.job_instances:
            instance_end_time = 0

            for template_task in problem.job_template.template_tasks:
                instance_task_id = problem.get_instance_task_id(
                    instance.instance_id, template_task.template_task_id
                )
                task_key = (instance.instance_id, instance_task_id)

                # Get timing
                start_time = solver.Value(task_starts[task_key])
                end_time = solver.Value(task_ends[task_key])

                # Find assigned machine
                assigned_machine = None
                for machine in problem.machines:
                    machine_key = (
                        instance.instance_id,
                        instance_task_id,
                        machine.resource_id,
                    )
                    if machine_key in task_assigned and solver.Value(
                        task_assigned[machine_key]
                    ):
                        assigned_machine = machine.resource_id
                        break

                # Convert times to datetime
                start_datetime = now + timedelta(minutes=start_time * 15)
                end_datetime = now + timedelta(minutes=end_time * 15)

                # Get machine name safely
                machine_obj = (
                    problem.get_machine(assigned_machine) if assigned_machine else None
                )
                machine_name = machine_obj.name if machine_obj else None

                schedule.append(
                    {
                        "job_id": instance.instance_id,  # Use instance ID as job ID
                        "task_id": instance_task_id,
                        "task_name": template_task.name,
                        "template_task_id": template_task.template_task_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "start_datetime": start_datetime.isoformat(),
                        "end_datetime": end_datetime.isoformat(),
                        "duration_minutes": (end_time - start_time) * 15,
                        "machine_id": assigned_machine,
                        "machine_name": machine_name,
                        "is_template_based": True,
                    }
                )

                instance_end_time = max(instance_end_time, end_time)

            # Calculate instance lateness
            instance_end_datetime = now + timedelta(minutes=instance_end_time * 15)
            if instance_end_datetime > instance.due_date:
                lateness_minutes = (
                    instance_end_datetime - instance.due_date
                ).total_seconds() / 60
                total_lateness += int(lateness_minutes)

            makespan = max(makespan, instance_end_time)
    else:
        # Legacy solution extraction
        for job in problem.jobs:
            job_end_time = 0

            for task in job.tasks:
                task_key = (job.job_id, task.task_id)

                # Get timing
                start_time = solver.Value(task_starts[task_key])
                end_time = solver.Value(task_ends[task_key])

                # Find assigned machine
                assigned_machine = None
                for machine in problem.machines:
                    machine_key = (job.job_id, task.task_id, machine.resource_id)
                    if machine_key in task_assigned and solver.Value(
                        task_assigned[machine_key]
                    ):
                        assigned_machine = machine.resource_id
                        break

                # Convert times to datetime
                start_datetime = now + timedelta(minutes=start_time * 15)
                end_datetime = now + timedelta(minutes=end_time * 15)

                # Get machine name safely
                machine_obj = (
                    problem.get_machine(assigned_machine) if assigned_machine else None
                )
                machine_name = machine_obj.name if machine_obj else None

                schedule.append(
                    {
                        "job_id": job.job_id,
                        "task_id": task.task_id,
                        "task_name": task.name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "start_datetime": start_datetime.isoformat(),
                        "end_datetime": end_datetime.isoformat(),
                        "duration_minutes": (end_time - start_time) * 15,
                        "machine_id": assigned_machine,
                        "machine_name": machine_name,
                        "is_template_based": False,
                    }
                )

                job_end_time = max(job_end_time, end_time)

            # Calculate job lateness
            job_end_datetime = now + timedelta(minutes=job_end_time * 15)
            if job_end_datetime > job.due_date:
                lateness_minutes = (
                    job_end_datetime - job.due_date
                ).total_seconds() / 60
                total_lateness += int(lateness_minutes)

            makespan = max(makespan, job_end_time)

    # Calculate setup time metrics
    setup_time_metrics = calculate_setup_time_metrics(schedule, setup_times or {})

    return {
        "status": solver.StatusName(),
        "schedule": sorted(
            schedule, key=lambda x: (x["start_time"], x["job_id"], x["task_id"])
        ),
        "makespan": makespan,
        "makespan_hours": makespan * 15 / 60,
        "total_lateness_minutes": total_lateness,
        "setup_time_metrics": setup_time_metrics,
        "solver_stats": {
            "status": solver.StatusName(),
            "solve_time": solver.WallTime(),
            "branches": solver.NumBranches(),
            "conflicts": solver.NumConflicts(),
            "objective_value": (
                solver.ObjectiveValue() if hasattr(solver, "ObjectiveValue") else None
            ),
        },
    }


def log_solution_summary(solution: dict, logger: logging.Logger | None = None) -> None:
    """Log a comprehensive summary of the solution using structured logging.

    Args:
        solution: Solution dictionary from extract_solution()
        logger: Optional logger instance. Uses module logger if None.

    """
    if logger is None:
        logger = globals()["logger"]

    logger.info("=" * 50)
    logger.info("SOLUTION SUMMARY")
    logger.info("=" * 50)

    # Handle missing keys gracefully
    status = solution.get("status", "UNKNOWN")
    if "solver_stats" in solution:
        status = solution["solver_stats"].get("status", status)

    logger.info("Solution status: %s", status)

    if "makespan" in solution:
        makespan = solution["makespan"]
        makespan_hours = solution.get("makespan_hours", makespan * 15 / 60)
        logger.info("Makespan: %d time units (%.1f hours)", makespan, makespan_hours)

    if "total_lateness_minutes" in solution:
        logger.info("Total lateness: %.1f minutes", solution["total_lateness_minutes"])

    # Log setup time metrics if available
    if (
        "setup_time_metrics" in solution
        and solution["setup_time_metrics"]["num_setups"] > 0
    ):
        metrics = solution["setup_time_metrics"]
        logger.info("Setup time metrics:")
        logger.info(
            "  Total setup time: %d units (%d minutes)",
            metrics["total_setup_time"],
            metrics["total_setup_minutes"],
        )
        logger.info("  Number of setups: %d", metrics["num_setups"])
        logger.info(
            "  Average setup time: %.1f units (%.1f minutes)",
            metrics["average_setup_time"],
            metrics["average_setup_minutes"],
        )

    # Log solver statistics if available
    if "solver_stats" in solution:
        logger.info("Solver statistics:")
        stats = solution["solver_stats"]
        if "solve_time" in stats:
            logger.info("  Solve time: %.2f seconds", stats["solve_time"])
        if "branches" in stats:
            logger.info("  Branches explored: %s", f"{stats['branches']:,}")
        if "conflicts" in stats:
            logger.info("  Conflicts encountered: %s", f"{stats['conflicts']:,}")

    # Log schedule summary if available
    if "schedule" in solution:
        schedule = solution["schedule"]
        logger.info("Schedule summary: %d tasks total", len(schedule))

        # Log first few tasks as examples
        tasks_to_show = []
        if isinstance(schedule, list):
            tasks_to_show = schedule[:5]  # Show first 5 tasks in logs
        elif isinstance(schedule, dict):
            # Flatten dict structure for display
            for job_data in schedule.values():
                if isinstance(job_data, dict):
                    for task_data in job_data.values():
                        if isinstance(task_data, dict):
                            tasks_to_show.append(task_data)
                            if len(tasks_to_show) >= 5:
                                break

        if tasks_to_show:
            logger.info("Sample scheduled tasks:")
            for i, task in enumerate(tasks_to_show):
                # Handle different task formats
                task_name = task.get("task_name", task.get("name", "Unknown"))
                start = task.get("start", task.get("start_time", 0))
                end = task.get("end", task.get("end_time", 0))
                duration = (
                    end - start
                    if isinstance(end, int | float) and isinstance(start, int | float)
                    else 0
                )
                machine = task.get("machine", task.get("machine_id", "Unknown"))

                logger.info(
                    "  Task %d: %s (start=%s, end=%s, duration=%s, machine=%s)",
                    i + 1,
                    task_name,
                    start,
                    end,
                    duration,
                    machine,
                )

        # Show truncation message if there are more tasks
        total_tasks = (
            len(schedule)
            if isinstance(schedule, list)
            else sum(
                len(job_data) if isinstance(job_data, dict) else 1
                for job_data in schedule.values()
            )
        )
        if total_tasks > 5:
            logger.info("... and %d more tasks", total_tasks - 5)

    logger.info("=" * 50)


def print_solution_summary(solution: dict) -> None:
    """Print a nice summary of the solution.

    DEPRECATED: Use log_solution_summary() instead for structured logging.
    This function is kept for backward compatibility but logs a deprecation warning.
    """
    logger.warning(
        "print_solution_summary() is deprecated. Use log_solution_summary() instead."
    )

    # For backward compatibility, still provide console output but also log
    log_solution_summary(solution, logger)

    # Simple console output for immediate user feedback
    status = solution.get("status", "UNKNOWN")
    if "solver_stats" in solution:
        status = solution["solver_stats"].get("status", status)

    print(f"\nSolution Status: {status}")

    if "makespan" in solution:
        makespan_hours = solution.get("makespan_hours", solution["makespan"] * 15 / 60)
        print(
            f"Makespan: {solution['makespan']} time units ({makespan_hours:.1f} hours)"
        )

    if "schedule" in solution:
        print(f"Tasks scheduled: {len(solution['schedule'])}")

    print("(See logs for detailed solution analysis)")
