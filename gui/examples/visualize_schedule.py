"""Example script demonstrating schedule visualization."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.solver.data_models import (
    Job,
    Machine,
    Precedence,
    ScheduledTask,
    SchedulingProblem,
    SchedulingSolution,
    Task,
    TaskMode,
)
from src.visualization.schedule_exporter import ScheduleExporter


def create_example_solution():
    """Create an example scheduling solution with high-capacity machines."""
    # Create jobs
    jobs = [
        Job(id=1, name="Assembly A"),
        Job(id=2, name="Assembly B"),
        Job(id=3, name="Packaging"),
        Job(id=4, name="Testing"),
    ]

    # Create machines with different capacities
    machines = [
        Machine(id=1, name="CNC Machine", capacity=1),  # Single capacity
        Machine(id=2, name="Assembly Station", capacity=3),  # High capacity
        Machine(id=3, name="Test Bench", capacity=2),  # Medium capacity
        Machine(id=4, name="Packaging Line", capacity=4),  # High capacity
    ]

    # Create tasks
    tasks = [
        # Job 1 tasks
        Task(id=1, job_id=1, name="Cut Parts", position=1),
        Task(id=2, job_id=1, name="Assemble", position=2),
        Task(id=3, job_id=1, name="Test", position=3),
        # Job 2 tasks
        Task(id=4, job_id=2, name="Cut Parts", position=1),
        Task(id=5, job_id=2, name="Assemble", position=2),
        Task(id=6, job_id=2, name="Test", position=3),
        # Job 3 tasks
        Task(id=7, job_id=3, name="Package A", position=1),
        Task(id=8, job_id=3, name="Package B", position=2),
        # Job 4 tasks
        Task(id=9, job_id=4, name="Unit Test", position=1),
        Task(id=10, job_id=4, name="Integration Test", position=2),
    ]

    # Create task modes
    task_modes = [
        # Job 1 modes
        TaskMode(task_id=1, machine_id=1, mode_id=1, duration_minutes=60),
        TaskMode(task_id=2, machine_id=2, mode_id=1, duration_minutes=90),
        TaskMode(task_id=3, machine_id=3, mode_id=1, duration_minutes=45),
        # Job 2 modes
        TaskMode(task_id=4, machine_id=1, mode_id=1, duration_minutes=60),
        TaskMode(task_id=5, machine_id=2, mode_id=1, duration_minutes=90),
        TaskMode(task_id=6, machine_id=3, mode_id=1, duration_minutes=45),
        # Job 3 modes
        TaskMode(task_id=7, machine_id=4, mode_id=1, duration_minutes=30),
        TaskMode(task_id=8, machine_id=4, mode_id=1, duration_minutes=30),
        # Job 4 modes
        TaskMode(task_id=9, machine_id=3, mode_id=1, duration_minutes=60),
        TaskMode(task_id=10, machine_id=3, mode_id=1, duration_minutes=75),
    ]

    # Create precedences
    precedences = [
        Precedence(predecessor_task_id=1, successor_task_id=2),
        Precedence(predecessor_task_id=2, successor_task_id=3),
        Precedence(predecessor_task_id=4, successor_task_id=5),
        Precedence(predecessor_task_id=5, successor_task_id=6),
        Precedence(predecessor_task_id=7, successor_task_id=8),
        Precedence(predecessor_task_id=9, successor_task_id=10),
    ]

    # Create problem
    problem = SchedulingProblem(
        jobs=jobs,
        tasks=tasks,
        machines=machines,
        task_modes=task_modes,
        precedences=precedences,
    )

    # Create scheduled tasks (simulating concurrent execution on high-capacity machines)
    scheduled_tasks = [
        # Job 1 - Sequential on different machines
        ScheduledTask(
            job_id=1, task_id=1, machine_id=1, mode_id=1, start_time=0, end_time=4
        ),  # 60 min = 4 units
        ScheduledTask(
            job_id=1, task_id=2, machine_id=2, mode_id=1, start_time=4, end_time=10
        ),  # 90 min = 6 units
        ScheduledTask(
            job_id=1, task_id=3, machine_id=3, mode_id=1, start_time=10, end_time=13
        ),  # 45 min = 3 units
        # Job 2 - Overlapping with Job 1 on high-capacity machines
        ScheduledTask(
            job_id=2, task_id=4, machine_id=1, mode_id=1, start_time=5, end_time=9
        ),  # Starts after Job 1 task 1
        ScheduledTask(
            job_id=2, task_id=5, machine_id=2, mode_id=1, start_time=9, end_time=15
        ),  # Concurrent with Job 1 task 2
        ScheduledTask(
            job_id=2, task_id=6, machine_id=3, mode_id=1, start_time=15, end_time=18
        ),  # After Job 1 task 3
        # Job 3 - Concurrent tasks on high-capacity packaging line
        ScheduledTask(
            job_id=3, task_id=7, machine_id=4, mode_id=1, start_time=0, end_time=2
        ),  # 30 min = 2 units
        ScheduledTask(
            job_id=3, task_id=8, machine_id=4, mode_id=1, start_time=2, end_time=4
        ),  # Sequential to task 7
        # Job 4 - Concurrent with Job 2 on test bench
        ScheduledTask(
            job_id=4, task_id=9, machine_id=3, mode_id=1, start_time=0, end_time=4
        ),  # Concurrent with other testing
        ScheduledTask(
            job_id=4, task_id=10, machine_id=3, mode_id=1, start_time=4, end_time=9
        ),  # 75 min = 5 units
    ]

    # Create solution
    solution = SchedulingSolution(
        scheduled_tasks=scheduled_tasks,
        makespan=18,  # Maximum end time
        solve_time=1.234,
        solver_status="OPTIMAL",
    )

    return solution, problem


def main():
    """Demonstrate visualization export functionality."""
    # Create example solution
    solution, problem = create_example_solution()

    # Create exporter
    exporter = ScheduleExporter()

    # Export to JSON
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "example_schedule.json"
    exporter.export_to_json(solution, problem, json_path)

    print(f"Schedule exported to: {json_path}")
    print(f"Total tasks: {len(solution.scheduled_tasks)}")
    print(f"Makespan: {solution.makespan} time units")

    # Also export to CSV
    csv_path = output_dir / "example_schedule.csv"
    exporter.export_to_csv(solution, problem, csv_path)
    print(f"CSV exported to: {csv_path}")

    # Print instructions
    print("\nTo view the visualization:")
    print("1. Open src/visualization/static/index.html in a web browser")
    print(f"2. Click 'Load Schedule' and select: {json_path}")

    # Check for capacity warnings
    visualization = exporter._create_visualization(solution, problem)
    if visualization.warnings:
        print("\nWarnings detected:")
        for warning in visualization.warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
