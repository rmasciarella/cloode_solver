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

    # Latest start is due date minus minimum duration
    min_duration_units = (task.min_duration + 14) // 15
    latest_start = due_time_units - min_duration_units

    # Ensure it's within horizon and non-negative
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
    machine_tasks = {}
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
    task_starts,  # Dict[Tuple[str, str], IntVar]
    task_ends,  # Dict[Tuple[str, str], IntVar]
    task_assigned,  # Dict[Tuple[str, str, str], BoolVar]
    _task_modes_selected=None,  # Future use - task mode selection
    setup_times=None,  # Optional[Dict[Tuple[str, str, str], int]]
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
                    "machine_name": (
                        problem.get_machine(assigned_machine).name
                        if assigned_machine
                        else None
                    ),
                }
            )

            job_end_time = max(job_end_time, end_time)

        # Calculate job lateness
        job_end_datetime = now + timedelta(minutes=job_end_time * 15)
        if job_end_datetime > job.due_date:
            lateness_minutes = (job_end_datetime - job.due_date).total_seconds() / 60
            total_lateness += lateness_minutes

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


def print_solution_summary(solution: dict) -> None:
    """Print a nice summary of the solution."""
    logger.info("\n")
    logger.info("SOLUTION SUMMARY")
    logger.info("=")

    logger.info(f"Status: {solution['status']}")
    logger.info(
        f"Makespan: {solution['makespan']} time units "
        f"({solution['makespan_hours']:.1f} hours)"
    )
    logger.info(f"Total Lateness: {solution['total_lateness_minutes']:.1f} minutes")

    # Print setup time metrics if available
    if (
        "setup_time_metrics" in solution
        and solution["setup_time_metrics"]["num_setups"] > 0
    ):
        metrics = solution["setup_time_metrics"]
        logger.info("\nSetup Time Metrics:")
        logger.info(
            f"  Total Setup Time: {metrics['total_setup_time']} units "
            f"({metrics['total_setup_minutes']} minutes)"
        )
        logger.info(f"  Number of Setups: {metrics['num_setups']}")
        logger.info(
            f"  Average Setup Time: {metrics['average_setup_time']:.1f} units "
            f"({metrics['average_setup_minutes']:.1f} minutes)"
        )

    logger.info("\nSolver Statistics:")
    stats = solution["solver_stats"]
    logger.info(f"  - Solve Time: {stats['solve_time']:.2f} seconds")
    logger.info(f"  - Branches: {stats['branches']:,}")
    logger.info(f"  - Conflicts: {stats['conflicts']:,}")

    logger.info(f"\nSchedule ({len(solution['schedule'])} tasks):")
    logger.info(f"{'Task':<20} {'Start':<6} {'End':<6} {'Duration':<8} {'Machine':<15}")
    logger.info("-")

    for task in solution["schedule"][:10]:  # Show first 10 tasks
        logger.info(f"{task['task_name']:<20} ")

    if len(solution["schedule"]) > 10:
        logger.info(f"... and {len(solution['schedule']) - 10} more tasks")

    logger.info("=")
