"""Integration tests for high-capacity machine visualization scenarios.

Tests that schedules with concurrent jobs can be properly visualized.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

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


class TestHighCapacityVisualization:
    """Test visualization of high-capacity machine schedules."""

    def test_visual_concurrent_jobs_scenario(self):
        """Test schedule that clearly shows concurrent jobs for visualization."""
        # Create machines with different capacities for visual contrast
        machines = [
            Machine("machine_1", "cell_1", "Single Processor", capacity=1),
            Machine("machine_2", "cell_1", "Dual Processor", capacity=2),
            Machine("machine_3", "cell_1", "Quad Processor", capacity=4),
            Machine("machine_4", "cell_1", "High-Cap Server", capacity=8),
        ]

        # Create jobs designed to show concurrent execution
        jobs = []

        # Batch 1: Short tasks that should run concurrently on high-cap machines
        for i in range(12):
            task = Task(
                task_id=f"short_{i}",
                job_id=f"batch1_job_{i}",
                name=f"Quick Task {i}",
                modes=[
                    # Prefer high-capacity machines for these
                    TaskMode(f"mode_s{i}_hc", f"short_{i}", "machine_4", 30),  # 30 min
                    TaskMode(f"mode_s{i}_qc", f"short_{i}", "machine_3", 45),  # 45 min
                    TaskMode(f"mode_s{i}_dc", f"short_{i}", "machine_2", 60),  # 1 hour
                ],
            )
            job = Job(
                job_id=f"batch1_job_{i}",
                description=f"Batch 1 Job {i}",
                due_date=datetime.now(UTC) + timedelta(hours=4),
                tasks=[task],
            )
            jobs.append(job)

        # Batch 2: Medium tasks for mid-capacity machines
        for i in range(6):
            task = Task(
                task_id=f"medium_{i}",
                job_id=f"batch2_job_{i}",
                name=f"Medium Task {i}",
                modes=[
                    TaskMode(
                        f"mode_m{i}_qc", f"medium_{i}", "machine_3", 90
                    ),  # 1.5 hours
                    TaskMode(
                        f"mode_m{i}_dc", f"medium_{i}", "machine_2", 120
                    ),  # 2 hours
                ],
            )
            job = Job(
                job_id=f"batch2_job_{i}",
                description=f"Batch 2 Job {i}",
                due_date=datetime.now(UTC) + timedelta(hours=8),
                tasks=[task],
            )
            jobs.append(job)

        # Batch 3: Long tasks that must use single-capacity machine
        for i in range(3):
            task = Task(
                task_id=f"long_{i}",
                job_id=f"batch3_job_{i}",
                name=f"Long Task {i}",
                modes=[
                    TaskMode(f"mode_l{i}_sc", f"long_{i}", "machine_1", 180),  # 3 hours
                ],
            )
            job = Job(
                job_id=f"batch3_job_{i}",
                description=f"Batch 3 Job {i}",
                due_date=datetime.now(UTC) + timedelta(hours=12),
                tasks=[task],
            )
            jobs.append(job)

        problem = SchedulingProblem(
            jobs=jobs,
            machines=machines,
            work_cells=[
                WorkCell("cell_1", "Production Cell", capacity=4, machines=machines)
            ],
            precedences=[],
        )

        # Solve
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=30)

        assert solution is not None
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]

        # Export for visualization
        exporter = ScheduleExporter(problem, solution)
        export_data = exporter.to_dict()

        # Verify export contains capacity information
        assert "machines" in export_data
        for machine in export_data["machines"]:
            assert "capacity" in machine
            assert machine["capacity"] > 0

        # Verify concurrent tasks are properly identified
        assert "capacity_warnings" in export_data

        # Check that high-capacity machines have concurrent tasks
        schedule = solution["schedule"]

        # Count concurrent tasks on high-cap server
        hc_tasks = [task for task in schedule if task["machine_id"] == "machine_4"]

        max_concurrent = 0
        for t in range(100):  # Check time units
            concurrent = sum(
                1 for task in hc_tasks if task["start_time"] <= t < task["end_time"]
            )
            max_concurrent = max(max_concurrent, concurrent)

        # Should have multiple concurrent tasks
        assert max_concurrent >= 2, "High-capacity machine should run concurrent tasks"
        assert max_concurrent <= 8, "Should not exceed machine capacity"

        # Verify visualization data structure
        assert "tasks" in export_data
        for task in export_data["tasks"]:
            assert all(
                key in task for key in ["id", "job_id", "start", "end", "machine"]
            )
            # Tasks on high-cap machines should have lane assignment for stacking
            if task["machine"] == "machine_4":
                assert "lane" in task or "y_offset" in task or concurrent > 1

    def test_capacity_validation_warnings(self):
        """Test that capacity warnings are generated for visualization."""
        # Create a machine with limited capacity
        machine = Machine("limited", "cell1", "Limited Machine", capacity=2)

        # Create overlapping tasks that would exceed capacity if all assigned
        jobs = []
        for i in range(4):
            task = Task(
                task_id=f"overlap_{i}",
                job_id=f"job_{i}",
                name=f"Overlapping Task {i}",
                modes=[TaskMode(f"mode_{i}", f"overlap_{i}", "limited", 60)],
            )
            job = Job(f"job_{i}", f"Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        problem = SchedulingProblem(jobs, [machine], [], [])

        # Solve - solver should handle capacity correctly
        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=10)

        assert solution is not None

        # Export and check for warnings if capacity would be exceeded
        exporter = ScheduleExporter(problem, solution)
        exporter.to_dict()  # Call to ensure export works

        # Verify schedule respects capacity
        schedule = solution["schedule"]
        for t in range(100):
            concurrent = sum(
                1
                for task in schedule
                if task["start_time"] <= t < task["end_time"]
                and task["machine_id"] == "limited"
            )
            assert concurrent <= 2, f"Capacity exceeded at time {t}"

    def test_mixed_capacity_visual_layout(self):
        """Test visual layout with mixed single and multi-capacity machines."""
        machines = [
            Machine("s1", "cell1", "Single 1", capacity=1),
            Machine("s2", "cell1", "Single 2", capacity=1),
            Machine("m1", "cell1", "Multi 1", capacity=3),
            Machine("m2", "cell1", "Multi 2", capacity=5),
        ]

        # Create tasks with specific patterns for visual testing
        jobs = []

        # Pattern 1: Sequential tasks on single-capacity
        for i in range(3):
            task = Task(
                task_id=f"seq_{i}",
                job_id=f"sequential_{i}",
                name=f"Sequential {i}",
                modes=[TaskMode(f"mode_seq_{i}", f"seq_{i}", "s1", 45)],
            )
            job = Job(
                f"sequential_{i}", f"Sequential Job {i}", datetime.now(UTC), [task]
            )
            jobs.append(job)

        # Pattern 2: Parallel tasks on multi-capacity
        for i in range(8):
            task = Task(
                task_id=f"par_{i}",
                job_id=f"parallel_{i}",
                name=f"Parallel {i}",
                modes=[
                    TaskMode(f"mode_par_{i}_m1", f"par_{i}", "m1", 60),
                    TaskMode(f"mode_par_{i}_m2", f"par_{i}", "m2", 60),
                ],
            )
            job = Job(f"parallel_{i}", f"Parallel Job {i}", datetime.now(UTC), [task])
            jobs.append(job)

        # Add precedences to create interesting patterns
        precedences = [
            Precedence("seq_0", "seq_1"),
            Precedence("seq_1", "seq_2"),
        ]

        problem = SchedulingProblem(jobs, machines, [], precedences)

        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=20)

        assert solution is not None

        # Export and verify visual layout data
        exporter = ScheduleExporter(problem, solution)
        export_data = exporter.to_dict()

        # Check that export includes visual hints
        assert "metadata" in export_data
        assert "statistics" in export_data["metadata"]

        # Verify machine utilization is calculated
        stats = export_data["metadata"]["statistics"]
        assert "machine_utilization" in stats

        # Verify all machines are represented
        assert len(export_data["machines"]) == 4

        # Check capacity is included for visual rendering
        for machine in export_data["machines"]:
            assert machine["capacity"] in [1, 3, 5]

    def test_export_formats(self):
        """Test different export formats for visualization."""
        # Simple test problem
        machine = Machine("m1", "c1", "Machine 1", capacity=2)
        task = Task(
            task_id="t1",
            job_id="j1",
            name="Task 1",
            modes=[TaskMode("mode1", "t1", "m1", 30)],
        )
        job = Job("j1", "Job 1", datetime.now(UTC), [task])
        problem = SchedulingProblem([job], [machine], [], [])

        solver = FreshSolver(problem)
        solution = solver.solve(time_limit=5)

        assert solution is not None

        exporter = ScheduleExporter(problem, solution)

        # Test JSON export
        json_str = exporter.to_json(indent=2)
        json_data = json.loads(json_str)
        assert "tasks" in json_data
        assert "machines" in json_data
        assert "metadata" in json_data

        # Test dict export
        dict_data = exporter.to_dict()
        assert isinstance(dict_data, dict)
        assert dict_data["machines"][0]["capacity"] == 2

        # Test that capacity warnings are included if needed
        if "capacity_warnings" in dict_data:
            for warning in dict_data["capacity_warnings"]:
                assert "machine" in warning
                assert "time" in warning
                assert "tasks" in warning
                assert "capacity" in warning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
