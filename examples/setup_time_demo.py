#!/usr/bin/env python3
"""Demo script to showcase setup time functionality."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import UTC, datetime, timedelta

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)
from src.solver.utils.time_utils import print_solution_summary
from src.visualization.schedule_exporter import ScheduleExporter

UTC = UTC


def create_setup_time_demo():
    """Create a demo problem with setup times between different product types."""
    # Create machines
    machines = [
        Machine(resource_id="machine_1", name="CNC Mill", cell_id="cell_1", capacity=1),
        Machine(
            resource_id="machine_2",
            name="3D Printer",
            cell_id="cell_1",
            capacity=2,  # Can handle 2 jobs simultaneously
        ),
    ]

    # Create work cell
    work_cells = [
        WorkCell(
            cell_id="cell_1", name="Production Cell 1", capacity=1, machines=machines
        )
    ]

    # Create jobs with different product types
    jobs = []

    # Product Type A jobs
    for i in range(2):
        job_id = f"job_a_{i + 1}"
        jobs.append(
            Job(
                job_id=job_id,
                description=f"Product A - Unit {i + 1}",
                due_date=datetime.now(UTC) + timedelta(hours=8),
                tasks=[
                    Task(
                        task_id=f"{job_id}_task_1",
                        job_id=job_id,
                        name=f"Machining A{i + 1}",
                        modes=[
                            TaskMode(
                                task_mode_id=f"{job_id}_task_1_mode_1",
                                task_id=f"{job_id}_task_1",
                                machine_resource_id="machine_1",
                                duration_minutes=30,
                            ),
                        ],
                    ),
                    Task(
                        task_id=f"{job_id}_task_2",
                        job_id=job_id,
                        name=f"Printing A{i + 1}",
                        modes=[
                            TaskMode(
                                task_mode_id=f"{job_id}_task_2_mode_1",
                                task_id=f"{job_id}_task_2",
                                machine_resource_id="machine_2",
                                duration_minutes=45,
                            ),
                        ],
                    ),
                ],
            )
        )

    # Product Type B jobs (different product requiring setup)
    for i in range(2):
        job_id = f"job_b_{i + 1}"
        jobs.append(
            Job(
                job_id=job_id,
                description=f"Product B - Unit {i + 1}",
                due_date=datetime.now(UTC) + timedelta(hours=8),
                tasks=[
                    Task(
                        task_id=f"{job_id}_task_1",
                        job_id=job_id,
                        name=f"Machining B{i + 1}",
                        modes=[
                            TaskMode(
                                task_mode_id=f"{job_id}_task_1_mode_1",
                                task_id=f"{job_id}_task_1",
                                machine_resource_id="machine_1",
                                duration_minutes=25,
                            ),
                        ],
                    ),
                    Task(
                        task_id=f"{job_id}_task_2",
                        job_id=job_id,
                        name=f"Printing B{i + 1}",
                        modes=[
                            TaskMode(
                                task_mode_id=f"{job_id}_task_2_mode_1",
                                task_id=f"{job_id}_task_2",
                                machine_resource_id="machine_2",
                                duration_minutes=40,
                            ),
                        ],
                    ),
                ],
            )
        )

    # Define precedences (task 1 must complete before task 2 in each job)
    precedences = []
    for job in jobs:
        precedences.append(
            Precedence(
                predecessor_task_id=job.tasks[0].task_id,
                successor_task_id=job.tasks[1].task_id,
            )
        )

    # Create problem
    problem = SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=work_cells,
        precedences=precedences,
    )

    # Define setup times between different product types
    # Format: (from_task, to_task, machine) -> setup_time_units
    setup_times = {}

    # Setup time when switching from Product A to Product B on CNC Mill
    for i in range(2):
        for j in range(2):
            # A to B setup on machine_1 (15 minutes = 1 time unit)
            setup_times[
                (f"job_a_{i + 1}_task_1", f"job_b_{j + 1}_task_1", "machine_1")
            ] = 1  # 15 minutes setup

            # B to A setup on machine_1 (30 minutes = 2 time units)
            setup_times[
                (f"job_b_{i + 1}_task_1", f"job_a_{j + 1}_task_1", "machine_1")
            ] = 2  # 30 minutes setup

            # A to B setup on machine_2 (15 minutes = 1 time unit)
            setup_times[
                (f"job_a_{i + 1}_task_2", f"job_b_{j + 1}_task_2", "machine_2")
            ] = 1  # 15 minutes setup

            # B to A setup on machine_2 (15 minutes = 1 time unit)
            setup_times[
                (f"job_b_{i + 1}_task_2", f"job_a_{j + 1}_task_2", "machine_2")
            ] = 1  # 15 minutes setup

    return problem, setup_times


def main():
    """Run the setup time demo."""
    print("=== Setup Time Demo ===")
    print(
        "Demonstrating sequence-dependent setup times between different product types\n"
    )

    # Create demo problem
    problem, setup_times = create_setup_time_demo()

    print("Problem created with:")
    product_a_count = len([j for j in problem.jobs if "job_a" in j.job_id])
    product_b_count = len([j for j in problem.jobs if "job_b" in j.job_id])
    print(
        f"- {len(problem.jobs)} jobs ({product_a_count} Product A, "
        f"{product_b_count} Product B)"
    )
    print(f"- {len(problem.machines)} machines (1 single-capacity, 1 high-capacity)")
    print(f"- {len(setup_times)} setup time configurations")
    print("- Setup times: A→B = 15 min, B→A = 30 min on CNC Mill")
    print()

    # Create and run solver with setup times
    solver = FreshSolver(problem, setup_times=setup_times)
    solution = solver.solve(time_limit=30)

    # Print results
    print_solution_summary(solution)

    # Export visualization if solution found
    if solution["status"] in ["OPTIMAL", "FEASIBLE"]:
        output_dir = Path("output/setup_time_demo")
        output_dir.mkdir(parents=True, exist_ok=True)

        exporter = ScheduleExporter(problem, solution)
        exporter.to_file(output_dir / "schedule.json")

        # Copy visualization files
        import shutil

        viz_files = ["index.html", "styles.css", "schedule_viewer_fixed.js"]
        for file in viz_files:
            src = Path("output/simple_concurrent_demo") / file
            if src.exists():
                shutil.copy(src, output_dir / file)

        print(f"\nVisualization exported to: {output_dir}")
        print("Run 'python serve_visualization.py output/setup_time_demo' to view")


if __name__ == "__main__":
    main()
