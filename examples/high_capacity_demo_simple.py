"""Simple High-Capacity Machine Demo.

This example creates a scenario that guarantees concurrent execution
by having tasks that can ONLY run on high-capacity machines.
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)
from src.visualization.schedule_exporter import ScheduleExporter


def create_simple_concurrent_demo():
    """Create a simple problem that guarantees concurrent execution."""
    # Define machines - only high-capacity machines
    machines = [
        Machine("batch_processor", "batch", "Batch Processor", capacity=4),
        Machine("parallel_unit", "batch", "Parallel Processing Unit", capacity=6),
    ]

    # Define work cells
    work_cells = [
        WorkCell("batch", "Batch Processing", machines=machines),
    ]

    jobs = []

    # Create 10 simple jobs that all need the same processing time
    # This will force concurrent execution to meet any reasonable makespan
    for i in range(10):
        task = Task(
            task_id=f"task_{i}",
            job_id=f"job_{i}",
            name=f"Process Item {i}",
            modes=[
                # Each task takes 45 minutes (3 time units)
                TaskMode(f"mode_batch_{i}", f"task_{i}", "batch_processor", 45),
                TaskMode(f"mode_parallel_{i}", f"task_{i}", "parallel_unit", 45),
            ],
        )

        job = Job(
            job_id=f"job_{i}",
            description=f"Job {i}",
            due_date=datetime.now(UTC) + timedelta(days=7),  # Relaxed due date
            tasks=[task],
        )
        jobs.append(job)

    # No precedences - all tasks are independent
    precedences = []

    return SchedulingProblem(jobs, machines, work_cells, precedences)


def main():
    """Run the simple concurrent demo."""
    print("Simple High-Capacity Machine Demo")
    print("=" * 40)

    # Create problem
    problem = create_simple_concurrent_demo()
    print("\nProblem Summary:")
    print(f"- Jobs: {len(problem.jobs)}")
    print(f"- Tasks: {sum(len(job.tasks) for job in problem.jobs)}")
    print(f"- Machines: {len(problem.machines)}")
    print("\nMachine Capacities:")
    for machine in problem.machines:
        print(f"  - {machine.name}: capacity = {machine.capacity}")

    # Solve
    print("\nSolving...")
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    if solution is None or solution.get("status") == "INFEASIBLE":
        print("No feasible solution found!")
        if solution:
            print(f"Status: {solution.get('status')}")
        return

    print("\nSolution found!")
    print(f"- Status: {solution['status']}")

    # Get makespan from solution
    makespan = solution.get("makespan", 0)

    # Get schedule (convert list to dict if needed)
    schedule_data = solution.get("schedule", [])
    schedule = {}
    if isinstance(schedule_data, list):
        for item in schedule_data:
            task_id = item.get("task_id")
            if task_id:
                schedule[task_id] = {
                    "start": item.get("start_time", 0),
                    "end": item.get("end_time", 0),
                    "machine": item.get("machine_id", "unknown"),
                }

    print(f"- Makespan: {makespan} time units ({makespan * 15} minutes)")
    print(f"- Solve time: {solution.get('solve_time', 0):.2f} seconds")

    # Calculate theoretical minimum makespan
    total_task_time = 10 * 3  # 10 tasks * 3 time units each
    total_capacity = 4 + 6  # Sum of machine capacities
    theoretical_min = (total_task_time + total_capacity - 1) // total_capacity
    print(f"- Theoretical minimum: {theoretical_min} time units")

    # Analyze concurrent execution
    print("\nConcurrent Execution Analysis:")

    # Count tasks per machine
    tasks_per_machine = {}
    for task_id, task_schedule in schedule.items():
        machine_id = task_schedule["machine"]
        if machine_id not in tasks_per_machine:
            tasks_per_machine[machine_id] = []
        tasks_per_machine[machine_id].append(
            {
                "task": task_id,
                "start": task_schedule["start"],
                "end": task_schedule["end"],
            }
        )

    for machine in problem.machines:
        if machine.resource_id in tasks_per_machine:
            tasks = tasks_per_machine[machine.resource_id]
            print(f"\n{machine.name} (capacity: {machine.capacity}):")
            print(f"  - Total tasks: {len(tasks)}")

            # Find max concurrent
            max_concurrent = 0
            concurrent_at = 0

            for t in range(int(makespan) + 1):
                concurrent = sum(
                    1 for task in tasks if task["start"] <= t < task["end"]
                )
                if concurrent > max_concurrent:
                    max_concurrent = concurrent
                    concurrent_at = t

            print(f"  - Max concurrent: {max_concurrent} at time {concurrent_at}")

            # Show timeline
            print("  - Timeline:")
            for time_slot in range(0, int(makespan) + 1, 3):
                concurrent_tasks = [
                    task["task"]
                    for task in tasks
                    if task["start"] <= time_slot < task["end"]
                ]
                if concurrent_tasks:
                    print(
                        f"    Time {time_slot}: {len(concurrent_tasks)} tasks - "
                        + ", ".join(concurrent_tasks[:4])
                        + ("..." if len(concurrent_tasks) > 4 else "")
                    )

    # Export for visualization
    print("\nExporting schedule for visualization...")
    exporter = ScheduleExporter(problem, solution)

    # Create output directory
    output_dir = Path("output/simple_concurrent_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export JSON
    json_path = output_dir / "schedule.json"
    exporter.to_file(json_path)
    print(f"  - JSON exported to: {json_path}")

    # Copy visualization files
    import shutil

    viz_dir = Path("src/visualization/static")
    if viz_dir.exists():
        for file in viz_dir.glob("*"):
            if file.is_file():
                shutil.copy(file, output_dir / file.name)
        print(f"  - Visualization files copied to: {output_dir}")
        print(f"\nTo view: Open {output_dir}/index.html in a browser")


if __name__ == "__main__":
    main()
