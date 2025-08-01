"""Forced Concurrent Execution Demo.

This example creates a scenario that FORCES concurrent execution
by using precedence constraints that require parallel processing.
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
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)
from src.visualization.schedule_exporter import ScheduleExporter


def create_forced_concurrent_demo():
    """Create a problem that forces concurrent execution through precedences."""
    # Define high-capacity machines
    machines = [
        Machine("batch_processor", "batch", "Batch Processor", capacity=4),
        Machine("parallel_unit", "batch", "Parallel Processing Unit", capacity=6),
    ]

    # Define work cells
    work_cells = [
        WorkCell("batch", "Batch Processing", machines=machines),
    ]

    jobs = []
    tasks_by_id = {}

    # Create a setup task that must complete before parallel tasks can start
    setup_task = Task(
        task_id="setup_task",
        job_id="setup_job",
        name="Setup Phase",
        modes=[
            TaskMode("setup_mode", "setup_task", "batch_processor", 30),  # 2 time units
        ],
    )
    tasks_by_id["setup_task"] = setup_task

    setup_job = Job(
        job_id="setup_job",
        description="Setup Job",
        due_date=datetime.now(UTC) + timedelta(days=7),
        tasks=[setup_task],
    )
    jobs.append(setup_job)

    # Create 8 parallel tasks that all depend on setup
    # These MUST run concurrently to meet the deadline
    parallel_tasks = []
    for i in range(8):
        task = Task(
            task_id=f"parallel_task_{i}",
            job_id=f"parallel_job_{i}",
            name=f"Parallel Task {i}",
            modes=[
                # Each task takes 45 minutes and can use either machine
                TaskMode(
                    f"mode_batch_{i}", f"parallel_task_{i}", "batch_processor", 45
                ),
                TaskMode(
                    f"mode_parallel_{i}", f"parallel_task_{i}", "parallel_unit", 45
                ),
            ],
        )
        tasks_by_id[f"parallel_task_{i}"] = task
        parallel_tasks.append(task)

        job = Job(
            job_id=f"parallel_job_{i}",
            description=f"Parallel Job {i}",
            due_date=datetime.now(UTC) + timedelta(days=7),
            tasks=[task],
        )
        jobs.append(job)

    # Create a final task that depends on all parallel tasks
    final_task = Task(
        task_id="final_task",
        job_id="final_job",
        name="Final Phase",
        modes=[
            TaskMode("final_mode", "final_task", "parallel_unit", 30),  # 2 time units
        ],
    )
    tasks_by_id["final_task"] = final_task

    final_job = Job(
        job_id="final_job",
        description="Final Job",
        due_date=datetime.now(UTC) + timedelta(days=7),
        tasks=[final_task],
    )
    jobs.append(final_job)

    # Create precedences that force concurrent execution
    precedences = []

    # Setup must complete before all parallel tasks
    for i in range(8):
        precedences.append(Precedence("setup_task", f"parallel_task_{i}"))

    # All parallel tasks must complete before final task
    for i in range(8):
        precedences.append(Precedence(f"parallel_task_{i}", "final_task"))

    return SchedulingProblem(jobs, machines, work_cells, precedences)


def main():
    """Run the forced concurrent demo."""
    print("Forced Concurrent Execution Demo")
    print("=" * 40)

    # Create problem
    problem = create_forced_concurrent_demo()
    print("\nProblem Summary:")
    print(f"- Jobs: {len(problem.jobs)}")
    print(f"- Tasks: {sum(len(job.tasks) for job in problem.jobs)}")
    print(f"- Precedences: {len(problem.precedences)}")
    print(f"- Machines: {len(problem.machines)}")
    print("\nMachine Capacities:")
    for machine in problem.machines:
        print(f"  - {machine.name}: capacity = {machine.capacity}")

    print("\nPrecedence Structure:")
    print("  Setup Task → 8 Parallel Tasks → Final Task")
    print("  (Forces concurrent execution of middle tasks)")

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

    # Analyze concurrent execution
    print("\nConcurrent Execution Analysis:")

    # Check parallel task scheduling
    parallel_starts = []
    parallel_ends = []
    for i in range(8):
        task_id = f"parallel_task_{i}"
        if task_id in schedule:
            parallel_starts.append(schedule[task_id]["start"])
            parallel_ends.append(schedule[task_id]["end"])

    if parallel_starts:
        min_start = min(parallel_starts)
        max_start = max(parallel_starts)
        min_end = min(parallel_ends)
        max_end = max(parallel_ends)

        print("\nParallel Tasks:")
        print(f"- Start times: {min_start} to {max_start}")
        print(f"- End times: {min_end} to {max_end}")

        if max_start - min_start <= 3:  # Within one task duration
            print("✓ Tasks are scheduled concurrently!")
        else:
            print("✗ Tasks are NOT scheduled concurrently")

    # Count tasks per machine per time slot
    print("\nTime-based Analysis:")
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

            # Show critical time periods
            for t in range(0, int(makespan) + 1, 3):
                concurrent_tasks = [
                    task["task"] for task in tasks if task["start"] <= t < task["end"]
                ]
                if len(concurrent_tasks) > 1:
                    print(f"  - Time {t}: {len(concurrent_tasks)} concurrent tasks")

    # Export for visualization
    print("\nExporting schedule for visualization...")
    exporter = ScheduleExporter(problem, solution)

    # Create output directory
    output_dir = Path("output/forced_concurrent_demo")
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
