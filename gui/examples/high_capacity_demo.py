"""High-Capacity Machine Scheduling Demo.

This example demonstrates scheduling with machines that have capacity > 1,
allowing multiple jobs to run concurrently on the same machine.

Use Case: Production facility with different types of machines:
- Single-capacity CNC machines for precision work
- Multi-capacity 3D printer farms for parallel printing
- High-capacity batch processors for chemical treatments
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


def create_demo_problem():
    """Create a realistic production scheduling problem with high-capacity machines."""
    # Define machines with different capacities
    machines = [
        # Single-capacity machines (traditional)
        Machine("cnc_1", "precision", "CNC Machine 1", capacity=1),
        Machine("cnc_2", "precision", "CNC Machine 2", capacity=1),
        # Multi-capacity machines
        Machine("printer_farm", "printing", "3D Printer Farm", capacity=5),
        Machine("batch_processor", "treatment", "Chemical Bath", capacity=8),
        Machine("assembly_line", "assembly", "Assembly Stations", capacity=3),
    ]

    # Define work cells
    work_cells = [
        WorkCell(
            "precision",
            "Precision Machining",
            machines=[m for m in machines if m.cell_id == "precision"],
        ),
        WorkCell(
            "printing",
            "3D Printing",
            machines=[m for m in machines if m.cell_id == "printing"],
        ),
        WorkCell(
            "treatment",
            "Chemical Treatment",
            machines=[m for m in machines if m.cell_id == "treatment"],
        ),
        WorkCell(
            "assembly",
            "Assembly",
            machines=[m for m in machines if m.cell_id == "assembly"],
        ),
    ]

    jobs = []
    precedences = []

    # Product A: Requires precision machining, then assembly
    for i in range(3):  # Reduced from 4 to make problem easier
        machining_task = Task(
            task_id=f"product_a_machining_{i}",
            job_id=f"product_a_{i}",
            name=f"Machine Part A-{i}",
            modes=[
                TaskMode(
                    f"a_cnc1_{i}", f"product_a_machining_{i}", "cnc_1", 60
                ),  # Reduced from 90
                TaskMode(f"a_cnc2_{i}", f"product_a_machining_{i}", "cnc_2", 60),
            ],
        )

        assembly_task = Task(
            task_id=f"product_a_assembly_{i}",
            job_id=f"product_a_{i}",
            name=f"Assemble A-{i}",
            modes=[
                TaskMode(
                    f"a_asm_{i}", f"product_a_assembly_{i}", "assembly_line", 30
                ),  # Reduced from 45
            ],
        )

        job = Job(
            job_id=f"product_a_{i}",
            description=f"Product A Unit {i}",
            due_date=datetime.now(UTC) + timedelta(hours=24),  # More relaxed deadline
            tasks=[machining_task, assembly_task],
        )
        jobs.append(job)

        # Precedence: machining before assembly
        precedences.append(
            Precedence(f"product_a_machining_{i}", f"product_a_assembly_{i}")
        )

    # Product B: Requires 3D printing (can be parallel) then chemical treatment
    for i in range(8):  # Reduced from 10
        printing_task = Task(
            task_id=f"product_b_print_{i}",
            job_id=f"product_b_{i}",
            name=f"Print Part B-{i}",
            modes=[
                TaskMode(
                    f"b_print_{i}", f"product_b_print_{i}", "printer_farm", 90
                ),  # Reduced from 120
            ],
        )

        treatment_task = Task(
            task_id=f"product_b_treat_{i}",
            job_id=f"product_b_{i}",
            name=f"Treat B-{i}",
            modes=[
                TaskMode(f"b_treat_{i}", f"product_b_treat_{i}", "batch_processor", 30),
            ],
        )

        job = Job(
            job_id=f"product_b_{i}",
            description=f"Product B Unit {i}",
            due_date=datetime.now(UTC) + timedelta(hours=48),  # More relaxed deadline
            tasks=[printing_task, treatment_task],
        )
        jobs.append(job)

        # Precedence: printing before treatment
        precedences.append(Precedence(f"product_b_print_{i}", f"product_b_treat_{i}"))

    # Product C: Simple workflow - just assembly (to ensure feasibility)
    for i in range(2):  # Reduced from 3
        assembly_task = Task(
            task_id=f"product_c_assembly_{i}",
            job_id=f"product_c_{i}",
            name=f"Assemble C-{i}",
            modes=[
                TaskMode(f"c_asm_{i}", f"product_c_assembly_{i}", "assembly_line", 45),
            ],
        )

        job = Job(
            job_id=f"product_c_{i}",
            description=f"Product C Unit {i}",
            due_date=datetime.now(UTC) + timedelta(hours=36),
            tasks=[assembly_task],
        )
        jobs.append(job)

    return SchedulingProblem(jobs, machines, work_cells, precedences)


def main():
    """Run the high-capacity machine demo."""
    print("High-Capacity Machine Scheduling Demo")
    print("=" * 50)

    # Create problem
    problem = create_demo_problem()
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
            for t in range(int(makespan) + 1):
                concurrent = sum(
                    1 for task in tasks if task["start"] <= t < task["end"]
                )
                if concurrent > max_concurrent:
                    max_concurrent = concurrent
                    peak_time = t

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

            # Show concurrent tasks at peak time
            if max_concurrent > 1:
                concurrent_tasks = [
                    task["task"]
                    for task in tasks
                    if task["start"] <= peak_time < task["end"]
                ]
                concurrent_str = ", ".join(str(t) for t in concurrent_tasks[:3])
                print(f"    - Concurrent at peak: {concurrent_str}...")

    # Export for visualization
    print("\nExporting schedule for visualization...")
    exporter = ScheduleExporter(problem, solution)

    # Create output directory
    output_dir = Path("output/high_capacity_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export JSON
    json_path = output_dir / "schedule.json"
    exporter.to_file(json_path)
    print(f"  - JSON exported to: {json_path}")

    # Copy visualization files
    viz_dir = Path("src/visualization/static")
    if viz_dir.exists():
        print("\nTo view the schedule:")
        print(f"1. Copy the visualization files from {viz_dir} to {output_dir}")
        print(f"2. Open {output_dir}/index.html in a web browser")
        print("3. Load the schedule.json file using the 'Load Schedule' button")

    # Print example concurrent tasks
    print("\nExample of Concurrent Execution:")
    printer_tasks = [
        (task_id, sched)
        for task_id, sched in schedule.items()
        if sched["machine"] == "printer_farm"
    ]

    if len(printer_tasks) >= 3:
        print("\n  3D Printer Farm (capacity: 5) running concurrently:")
        for _i, (task_id, sched) in enumerate(printer_tasks[:3]):
            print(f"    - {task_id}: time {sched['start']} to {sched['end']}")

    batch_tasks = [
        (task_id, sched)
        for task_id, sched in schedule.items()
        if sched["machine"] == "batch_processor"
    ]

    if len(batch_tasks) >= 3:
        print("\n  Chemical Bath (capacity: 8) processing together:")
        for _i, (task_id, sched) in enumerate(batch_tasks[:3]):
            print(f"    - {task_id}: time {sched['start']} to {sched['end']}")


if __name__ == "__main__":
    main()
