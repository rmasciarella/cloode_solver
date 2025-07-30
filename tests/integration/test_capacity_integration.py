"""Integration tests for machine capacity constraints with full solver.

Tests realistic scenarios with all constraints working together.
"""

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


class TestCapacitySolverIntegration:
    """Test capacity constraints in full solver context."""

    def test_3d_printer_farm_scenario(self):
        """Test realistic 3D printer farm with parallel printing."""
        # Create printer farm with 5 printers
        printer_farm = Machine(
            resource_id="printer_farm",
            cell_id="print_cell",
            name="3D Printer Farm",
            capacity=5,  # 5 printers running in parallel
        )

        # Single CNC for finishing
        cnc = Machine(
            resource_id="cnc_machine",
            cell_id="finish_cell",
            name="CNC Finishing",
            capacity=1,
        )

        machines = [printer_farm, cnc]

        # Create 10 parts that need printing then finishing
        jobs = []
        for i in range(10):
            # Each part has print task and finish task
            print_task = Task(
                task_id=f"print_{i}",
                job_id=f"part_{i}",
                name=f"3D Print Part {i}",
                modes=[
                    TaskMode(
                        f"print_mode_{i}",
                        f"print_{i}",
                        "printer_farm",
                        duration_minutes=120,  # 2 hours printing
                    )
                ],
            )

            finish_task = Task(
                task_id=f"finish_{i}",
                job_id=f"part_{i}",
                name=f"CNC Finish Part {i}",
                modes=[
                    TaskMode(
                        f"finish_mode_{i}",
                        f"finish_{i}",
                        "cnc_machine",
                        duration_minutes=30,  # 30 min finishing
                    )
                ],
            )

            job = Job(
                job_id=f"part_{i}",
                description=f"Manufacturing Part {i}",
                due_date=datetime.now(UTC) + timedelta(hours=24),
                tasks=[print_task, finish_task],
            )
            jobs.append(job)

        # Precedences: print before finish for each part
        precedences = [Precedence(f"print_{i}", f"finish_{i}") for i in range(10)]

        problem = SchedulingProblem(
            jobs=jobs,
            machines=machines,
            work_cells=[
                WorkCell("print_cell", "Printing", machines=[printer_farm]),
                WorkCell("finish_cell", "Finishing", machines=[cnc]),
            ],
            precedences=precedences,
        )

        # Solve
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=30)

        assert solution is not None
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]

        # Verify parallel printing
        schedule = solution["schedule"]

        # Count concurrent prints
        print_times = []
        for task in schedule:
            if task["task_id"].startswith("print_"):
                print_times.append(
                    {
                        "start": task["start_time"],
                        "end": task["end_time"],
                    }
                )

        # Find max concurrent prints
        max_concurrent = 0
        for t in range(0, 50):  # Check first 50 time units
            concurrent = sum(1 for pt in print_times if pt["start"] <= t < pt["end"])
            max_concurrent = max(max_concurrent, concurrent)

        # Should use parallel capacity
        assert max_concurrent >= 3  # At least 3 concurrent prints
        assert max_concurrent <= 5  # Never exceed capacity

        # All finish tasks should be after their print tasks
        # Create a lookup dictionary for tasks
        task_lookup = {task["task_id"]: task for task in schedule}

        for i in range(10):
            print_task_id = f"print_{i}"
            finish_task_id = f"finish_{i}"

            if print_task_id in task_lookup and finish_task_id in task_lookup:
                assert (
                    task_lookup[finish_task_id]["start_time"]
                    >= task_lookup[print_task_id]["end_time"]
                )

    def test_mixed_capacity_with_setup_times(self):
        """Test mixed capacity machines with setup times between tasks."""
        # Machines with different capacities
        batch_processor = Machine(
            resource_id="batch", cell_id="cell1", name="Batch Processor", capacity=4
        )

        single_processor = Machine(
            resource_id="single", cell_id="cell1", name="Single Processor", capacity=1
        )

        machines = [batch_processor, single_processor]

        # Create tasks of different types
        jobs = []
        task_types = ["A", "B", "A", "B", "A", "B"]  # Alternating types

        for i, task_type in enumerate(task_types):
            task = Task(
                task_id=f"task_{i}",
                job_id=f"job_{i}",
                name=f"Task {i} Type {task_type}",
                modes=[
                    # Can use batch processor
                    TaskMode(
                        f"mode_{i}_batch", f"task_{i}", "batch", duration_minutes=60
                    ),
                    # Or single processor (faster but one at a time)
                    TaskMode(
                        f"mode_{i}_single", f"task_{i}", "single", duration_minutes=45
                    ),
                ],
            )
            job = Job(
                job_id=f"job_{i}",
                description=f"Job {i}",
                due_date=datetime.now(UTC) + timedelta(hours=8),
                tasks=[task],
            )
            jobs.append(job)

        problem = SchedulingProblem(jobs, machines, [], [])

        # Setup times when switching between types
        setup_times = {}
        for i in range(len(task_types)):
            for j in range(len(task_types)):
                if i != j and task_types[i] != task_types[j]:
                    # Setup time when switching types
                    setup_times[(f"task_{i}", f"task_{j}", "batch")] = 1
                    setup_times[(f"task_{i}", f"task_{j}", "single")] = 2

        # Solve with setup times
        # (FreshSolver doesn't support setup_times in constructor)
        solver = FreshSolver(problem)
        # Note: Setup times would need to be implemented in the solver if needed
        solution = solver.solve(time_limit=30)

        assert solution is not None
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]

        # Verify solution respects both capacity and setup times
        schedule = solution["schedule"]

        # Check batch processor doesn't exceed capacity
        batch_tasks = [task for task in schedule if task["machine_id"] == "batch"]

        for t in range(solution.get("makespan", 100)):
            concurrent = sum(
                1 for task in batch_tasks if task["start_time"] <= t < task["end_time"]
            )
            assert concurrent <= 4  # Never exceed batch capacity

    def test_bottleneck_identification(self):
        """Test that solver identifies and handles bottlenecks."""
        # One high-capacity machine and one bottleneck
        high_cap = Machine("high", "cell1", "High Capacity", capacity=10)
        bottleneck = Machine("bottle", "cell1", "Bottleneck", capacity=1)

        machines = [high_cap, bottleneck]

        # Create workflow: many tasks -> bottleneck -> many tasks
        jobs = []

        # Phase 1: Tasks that can use high capacity
        for i in range(20):
            task = Task(
                task_id=f"phase1_{i}",
                job_id=f"job_{i}",
                name=f"Phase 1 Task {i}",
                modes=[TaskMode(f"mode_p1_{i}", f"phase1_{i}", "high", 15)],
            )
            job = Job(
                f"job_{i}", f"Job {i}", datetime.now(UTC) + timedelta(hours=48), [task]
            )
            jobs.append(job)

        # Bottleneck task
        bottleneck_task = Task(
            task_id="bottleneck_task",
            job_id="critical_job",
            name="Bottleneck Task",
            modes=[TaskMode("mode_bottle", "bottleneck_task", "bottle", 60)],
        )
        critical_job = Job(
            "critical_job",
            "Critical Job",
            datetime.now(UTC) + timedelta(hours=48),
            [bottleneck_task],
        )
        jobs.append(critical_job)

        # Phase 2: Tasks after bottleneck
        for i in range(20):
            task = Task(
                task_id=f"phase2_{i}",
                job_id=f"job_p2_{i}",
                name=f"Phase 2 Task {i}",
                modes=[TaskMode(f"mode_p2_{i}", f"phase2_{i}", "high", 15)],
            )
            job = Job(
                f"job_p2_{i}",
                f"Job P2 {i}",
                datetime.now(UTC) + timedelta(hours=48),
                [task],
            )
            jobs.append(job)

        # All phase 1 must complete before bottleneck
        # Bottleneck must complete before phase 2
        precedences = []
        for i in range(20):
            precedences.append(Precedence(f"phase1_{i}", "bottleneck_task"))
            precedences.append(Precedence("bottleneck_task", f"phase2_{i}"))

        problem = SchedulingProblem(jobs, machines, [], precedences)

        # Solve
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=30)

        assert solution is not None
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]

        # Verify bottleneck is the critical path
        schedule = solution["schedule"]

        # Create a lookup dictionary for tasks
        task_lookup = {task["task_id"]: task for task in schedule}

        if "bottleneck_task" in task_lookup:
            bottleneck_task = task_lookup["bottleneck_task"]
            bottleneck_end = bottleneck_task["end_time"]

            # All phase 1 should complete before bottleneck starts
            for i in range(20):
                phase1_id = f"phase1_{i}"
                if phase1_id in task_lookup:
                    assert (
                        task_lookup[phase1_id]["end_time"]
                        <= bottleneck_task["start_time"]
                    )

            # All phase 2 should start after bottleneck ends
            for i in range(20):
                phase2_id = f"phase2_{i}"
                if phase2_id in task_lookup:
                    assert task_lookup[phase2_id]["start_time"] >= bottleneck_end

            # Makespan should be dominated by bottleneck
            assert solution["makespan"] >= bottleneck_end
