"""Example demonstrating machine capacity constraints.

Shows how high-capacity machines can run multiple tasks simultaneously.
"""

from datetime import UTC, datetime

from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    SchedulingProblem,
    Task,
    TaskMode,
    WorkCell,
)


def create_capacity_example():
    """Create example with high-capacity machine."""
    # Machine 1: High capacity (can run 3 tasks at once)
    high_cap_machine = Machine(
        resource_id="machine_1",
        cell_id="cell_1",
        name="3D Printer Farm",
        capacity=3,  # Can print 3 items simultaneously
    )

    # Machine 2: Regular capacity
    regular_machine = Machine(
        resource_id="machine_2",
        cell_id="cell_1",
        name="CNC Machine",
        capacity=1,  # Traditional single-task machine
    )

    machines = [high_cap_machine, regular_machine]

    # Create 5 tasks that need printing
    jobs = []
    for i in range(5):
        task = Task(
            task_id=f"print_task_{i}",
            job_id=f"job_{i}",
            name=f"3D Print Part {i}",
            modes=[
                # Can use high-capacity printer (2 hours)
                TaskMode(
                    task_mode_id=f"mode_{i}_printer",
                    task_id=f"print_task_{i}",
                    machine_resource_id="machine_1",
                    duration_minutes=120,
                ),
                # Or use CNC machine (1 hour but one at a time)
                TaskMode(
                    task_mode_id=f"mode_{i}_cnc",
                    task_id=f"print_task_{i}",
                    machine_resource_id="machine_2",
                    duration_minutes=60,
                ),
            ],
        )

        job = Job(
            job_id=f"job_{i}",
            description=f"Manufacturing Order {i}",
            due_date=datetime.now(UTC),
            tasks=[task],
        )
        jobs.append(job)

    return SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=[
            WorkCell(cell_id="cell_1", name="Manufacturing Cell", machines=machines)
        ],
        precedences=[],
    )


def main():
    """Run the capacity example."""
    print("=== Machine Capacity Example ===\n")

    # Create problem
    problem = create_capacity_example()

    print("Problem setup:")
    print("- 5 printing tasks")
    print("- Machine 1 (3D Printer Farm): capacity = 3")
    print("- Machine 2 (CNC Machine): capacity = 1")
    print("\nThe solver should schedule 3 tasks in parallel on the printer farm.\n")

    # Solve
    solver = FreshSolver(problem)
    solution = solver.solve(time_limit=30)

    if solution:
        print("\n=== Solution ===")
        print(f"Makespan: {solution['objective']} time units")

        # Group by machine
        machine_schedules = {}
        for task_id, schedule in solution["schedule"].items():
            machine = schedule["machine"]
            if machine not in machine_schedules:
                machine_schedules[machine] = []
            machine_schedules[machine].append(
                {"task": task_id, "start": schedule["start"], "end": schedule["end"]}
            )

        # Show utilization
        for machine, tasks in machine_schedules.items():
            print(f"\n{machine}:")
            # Sort by start time
            tasks.sort(key=lambda x: x["start"])

            # Check for parallel execution
            parallel_count = 0
            for i, task in enumerate(tasks):
                overlaps = 0
                for j, other in enumerate(tasks):
                    if i != j and not (
                        task["end"] <= other["start"] or other["end"] <= task["start"]
                    ):
                        overlaps += 1
                parallel_count = max(parallel_count, overlaps + 1)

                print(f"  {task['task']}: {task['start']} -> {task['end']}")

            if parallel_count > 1:
                print(f"  (Running up to {parallel_count} tasks in parallel)")
    else:
        print("No solution found!")


if __name__ == "__main__":
    main()
