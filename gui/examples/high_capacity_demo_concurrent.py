"""High-Capacity Machine Scheduling Demo - Forced Concurrent Execution.

This example demonstrates scheduling with machines that have capacity > 1,
forcing concurrent execution by creating tasks with tight deadlines.
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


def create_concurrent_demo():
    """Create a problem that forces concurrent execution on high-capacity machines."""
    # Define machines with different capacities
    machines = [
        Machine("single_1", "single", "Single Machine 1", capacity=1),
        Machine("single_2", "single", "Single Machine 2", capacity=1),
        Machine("high_cap_1", "high", "High-Cap Machine 1", capacity=4),
        Machine("high_cap_2", "high", "High-Cap Machine 2", capacity=6),
    ]

    # Define work cells
    work_cells = [
        WorkCell(
            "single",
            "Single Capacity",
            machines=[m for m in machines if m.cell_id == "single"],
        ),
        WorkCell(
            "high",
            "High Capacity",
            machines=[m for m in machines if m.cell_id == "high"],
        ),
    ]

    jobs = []
    precedences = []

    # Create a set of urgent jobs that must use high-capacity machines
    # These have tight deadlines that force concurrent execution

    # Batch 1: 4 urgent jobs that need high-capacity processing
    for i in range(4):
        urgent_task = Task(
            task_id=f"urgent_task_{i}",
            job_id=f"urgent_job_{i}",
            name=f"Urgent Processing {i}",
            modes=[
                # Can only use high-capacity machines
                TaskMode(
                    f"urgent_mode_h1_{i}", f"urgent_task_{i}", "high_cap_1", 45
                ),  # 45 min
                TaskMode(
                    f"urgent_mode_h2_{i}", f"urgent_task_{i}", "high_cap_2", 45
                ),  # 45 min
            ],
        )

        job = Job(
            job_id=f"urgent_job_{i}",
            description=f"Urgent Job {i}",
            due_date=datetime.now(UTC)
            + timedelta(hours=6),  # Deadline to encourage concurrency
            tasks=[urgent_task],
        )
        jobs.append(job)

    # Batch 2: Jobs that have sequential dependencies and use high-capacity
    for i in range(3):
        prep_task = Task(
            task_id=f"prep_task_{i}",
            job_id=f"sequential_job_{i}",
            name=f"Preparation {i}",
            modes=[
                TaskMode(f"prep_mode_{i}", f"prep_task_{i}", "single_1", 30),
                TaskMode(f"prep_mode2_{i}", f"prep_task_{i}", "single_2", 30),
            ],
        )

        process_task = Task(
            task_id=f"process_task_{i}",
            job_id=f"sequential_job_{i}",
            name=f"High-Cap Process {i}",
            modes=[
                TaskMode(f"process_mode_h1_{i}", f"process_task_{i}", "high_cap_1", 60),
                TaskMode(f"process_mode_h2_{i}", f"process_task_{i}", "high_cap_2", 60),
            ],
        )

        job = Job(
            job_id=f"sequential_job_{i}",
            description=f"Sequential Job {i}",
            due_date=datetime.now(UTC) + timedelta(hours=8),
            tasks=[prep_task, process_task],
        )
        jobs.append(job)

        # Add precedence
        precedences.append(Precedence(f"prep_task_{i}", f"process_task_{i}"))

    # Batch 3: Large batch of small tasks that benefit from parallelization
    for i in range(8):
        batch_task = Task(
            task_id=f"batch_task_{i}",
            job_id=f"batch_job_{i}",
            name=f"Batch Item {i}",
            modes=[
                # Prefer high-capacity machines for efficiency
                TaskMode(
                    f"batch_mode_h1_{i}", f"batch_task_{i}", "high_cap_1", 15
                ),  # 15 min
                TaskMode(
                    f"batch_mode_h2_{i}", f"batch_task_{i}", "high_cap_2", 15
                ),  # 15 min
                # Can use single machines but slower
                TaskMode(
                    f"batch_mode_s1_{i}", f"batch_task_{i}", "single_1", 25
                ),  # 25 min
                TaskMode(
                    f"batch_mode_s2_{i}", f"batch_task_{i}", "single_2", 25
                ),  # 25 min
            ],
        )

        job = Job(
            job_id=f"batch_job_{i}",
            description=f"Batch Job {i}",
            due_date=datetime.now(UTC) + timedelta(hours=6),
            tasks=[batch_task],
        )
        jobs.append(job)

    return SchedulingProblem(jobs, machines, work_cells, precedences)


def main():
    """Run the concurrent execution demo."""
    print("High-Capacity Machine Scheduling Demo - Concurrent Execution")
    print("=" * 60)

    # Create problem
    problem = create_concurrent_demo()
    print("\nProblem Summary:")
    print(f"- Jobs: {len(problem.jobs)}")
    print(f"- Tasks: {sum(len(job.tasks) for job in problem.jobs)}")
    print(f"- Machines: {len(problem.machines)}")
    print("\nMachine Capacities:")
    for machine in problem.machines:
        print(f"  - {machine.name}: capacity = {machine.capacity}")

    # Solve
    print("\nSolving with tight deadlines to force concurrent execution...")
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=60)

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

    # Analyze high-capacity machine utilization
    machine_usage = {m.resource_id: [] for m in problem.machines}

    for task_key, task_schedule in schedule.items():
        machine_id = task_schedule["machine"]
        if machine_id in machine_usage:
            machine_usage[machine_id].append(
                {
                    "task": task_key,
                    "start": task_schedule["start"],
                    "end": task_schedule["end"],
                }
            )

    print("\nHigh-Capacity Machine Utilization:")
    for machine in problem.machines:
        if machine.capacity > 1:
            tasks = machine_usage[machine.resource_id]

            # Find max concurrent tasks
            max_concurrent = 0
            peak_time = 0
            concurrent_periods = []

            for t in range(int(makespan) + 1):
                concurrent_tasks = []
                for task in tasks:
                    if task["start"] <= t < task["end"]:
                        concurrent_tasks.append(task["task"])

                concurrent_count = len(concurrent_tasks)
                if concurrent_count > max_concurrent:
                    max_concurrent = concurrent_count
                    peak_time = t

                if concurrent_count > 1:
                    concurrent_periods.append((t, concurrent_count, concurrent_tasks))

            if makespan > 0 and machine.capacity > 0:
                utilization = (
                    sum(task["end"] - task["start"] for task in tasks)
                    / (makespan * machine.capacity)
                    * 100
                )
            else:
                utilization = 0

            print(f"\n  {machine.name} (capacity: {machine.capacity}):")
            print(f"    - Total tasks: {len(tasks)}")
            print(f"    - Max concurrent: {max_concurrent} at time {peak_time}")
            print(f"    - Utilization: {utilization:.1f}%")

            # Show concurrent execution periods
            if concurrent_periods:
                print("    - Concurrent execution periods:")
                shown = 0
                for time, count, tasks_at_time in concurrent_periods:
                    if shown < 3:  # Show first 3 periods
                        task_list = ", ".join(tasks_at_time[:3])
                        print(f"      Time {time}: {count} tasks - {task_list}")
                        shown += 1
                if len(concurrent_periods) > 3:
                    print(f"      ... and {len(concurrent_periods) - 3} more periods")

    # Export for visualization
    print("\nExporting schedule for visualization...")
    exporter = ScheduleExporter(problem, solution)

    # Create output directory
    output_dir = Path("output/concurrent_demo")
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
