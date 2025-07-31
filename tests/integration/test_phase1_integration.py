"""Integration tests for Phase 1 components working together.

Tests the complete flow from data loading to solution extraction.
"""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from src.data.loaders.database import DatabaseLoader
from src.solver.core.solver import FreshSolver
from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
)


class TestPhase1FullIntegration:
    """Test complete Phase 1 integration."""

    @patch("src.data.loaders.optimized_database.create_client")
    @patch("src.data.loaders.database.create_client")
    def test_full_pipeline_with_mocked_db(
        self, mock_create_client, mock_optimized_create_client
    ):
        """Test complete pipeline from DB load to solution."""
        # GIVEN: Mock database with complete test data
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock optimized client as well
        mock_optimized_client = MagicMock()
        mock_optimized_create_client.return_value = mock_optimized_client

        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        # Mock optimized table access
        mock_optimized_table = MagicMock()
        mock_optimized_client.table.return_value = mock_optimized_table
        mock_optimized_table.select.return_value = mock_optimized_table
        mock_optimized_table.eq.return_value = mock_optimized_table

        # Optimized loader should return empty optimizeds (use unique mode)
        mock_optimized_table.execute.return_value = MagicMock(data=[])

        # Complete test data
        mock_responses = {
            "test_work_cells": [
                {"cell_id": "cell-1", "name": "Production Cell 1", "capacity": 3},
                {"cell_id": "cell-2", "name": "Production Cell 2", "capacity": 2},
            ],
            "test_resources": [
                {
                    "resource_id": "lathe-1",
                    "cell_id": "cell-1",
                    "name": "CNC Lathe 1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "50.0",
                },
                {
                    "resource_id": "mill-1",
                    "cell_id": "cell-1",
                    "name": "Milling Machine 1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "75.0",
                },
                {
                    "resource_id": "drill-1",
                    "cell_id": "cell-2",
                    "name": "Drill Press 1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "25.0",
                },
            ],
            "test_jobs": [
                {
                    "job_id": "order-001",
                    "description": "Customer Order 001",
                    "due_date": (datetime.now(UTC) + timedelta(hours=8)).isoformat(),
                    "created_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
                {
                    "job_id": "order-002",
                    "description": "Customer Order 002",
                    "due_date": (datetime.now(UTC) + timedelta(hours=12)).isoformat(),
                    "created_at": datetime.now(UTC).isoformat(),
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            ],
            "test_tasks": [
                # Job 1 tasks
                {
                    "task_id": "op-001-1",
                    "job_id": "order-001",
                    "name": "Rough Turning",
                    "department_id": "machining",
                    "is_setup": True,
                },
                {
                    "task_id": "op-001-2",
                    "job_id": "order-001",
                    "name": "Finish Turning",
                    "department_id": "machining",
                },
                {
                    "task_id": "op-001-3",
                    "job_id": "order-001",
                    "name": "Milling",
                    "department_id": "machining",
                },
                {
                    "task_id": "op-001-4",
                    "job_id": "order-001",
                    "name": "Drilling",
                    "department_id": "machining",
                },
                {
                    "task_id": "op-001-5",
                    "job_id": "order-001",
                    "name": "Quality Check",
                    "department_id": "quality",
                    "is_unattended": True,
                },
                # Job 2 tasks
                {
                    "task_id": "op-002-1",
                    "job_id": "order-002",
                    "name": "Setup Mill",
                    "department_id": "machining",
                    "is_setup": True,
                },
                {
                    "task_id": "op-002-2",
                    "job_id": "order-002",
                    "name": "Face Milling",
                    "department_id": "machining",
                },
                {
                    "task_id": "op-002-3",
                    "job_id": "order-002",
                    "name": "Pocket Milling",
                    "department_id": "machining",
                },
                {
                    "task_id": "op-002-4",
                    "job_id": "order-002",
                    "name": "Deburring",
                    "department_id": "finishing",
                },
                {
                    "task_id": "op-002-5",
                    "job_id": "order-002",
                    "name": "Final Inspection",
                    "department_id": "quality",
                },
            ],
            "test_task_modes": [
                # Job 1 modes
                {
                    "task_mode_id": "mode-001-1-1",
                    "task_id": "op-001-1",
                    "machine_resource_id": "lathe-1",
                    "duration_minutes": 45,
                },
                {
                    "task_mode_id": "mode-001-2-1",
                    "task_id": "op-001-2",
                    "machine_resource_id": "lathe-1",
                    "duration_minutes": 60,
                },
                {
                    "task_mode_id": "mode-001-3-1",
                    "task_id": "op-001-3",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 90,
                },
                {
                    "task_mode_id": "mode-001-4-1",
                    "task_id": "op-001-4",
                    "machine_resource_id": "drill-1",
                    "duration_minutes": 30,
                },
                {
                    "task_mode_id": "mode-001-5-1",
                    "task_id": "op-001-5",
                    "machine_resource_id": "lathe-1",
                    "duration_minutes": 15,
                },
                {
                    "task_mode_id": "mode-001-5-2",
                    "task_id": "op-001-5",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 15,
                },
                {
                    "task_mode_id": "mode-001-5-3",
                    "task_id": "op-001-5",
                    "machine_resource_id": "drill-1",
                    "duration_minutes": 15,
                },
                # Job 2 modes
                {
                    "task_mode_id": "mode-002-1-1",
                    "task_id": "op-002-1",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 20,
                },
                {
                    "task_mode_id": "mode-002-2-1",
                    "task_id": "op-002-2",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 45,
                },
                {
                    "task_mode_id": "mode-002-3-1",
                    "task_id": "op-002-3",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 120,
                },
                {
                    "task_mode_id": "mode-002-4-1",
                    "task_id": "op-002-4",
                    "machine_resource_id": "lathe-1",
                    "duration_minutes": 30,
                },
                {
                    "task_mode_id": "mode-002-4-2",
                    "task_id": "op-002-4",
                    "machine_resource_id": "drill-1",
                    "duration_minutes": 25,
                },
                {
                    "task_mode_id": "mode-002-5-1",
                    "task_id": "op-002-5",
                    "machine_resource_id": "mill-1",
                    "duration_minutes": 20,
                },
            ],
            "test_task_precedences": [
                # Job 1 precedences (sequential)
                {"predecessor_task_id": "op-001-1", "successor_task_id": "op-001-2"},
                {"predecessor_task_id": "op-001-2", "successor_task_id": "op-001-3"},
                {"predecessor_task_id": "op-001-3", "successor_task_id": "op-001-4"},
                {"predecessor_task_id": "op-001-4", "successor_task_id": "op-001-5"},
                # Job 2 precedences
                {"predecessor_task_id": "op-002-1", "successor_task_id": "op-002-2"},
                {"predecessor_task_id": "op-002-2", "successor_task_id": "op-002-3"},
                {"predecessor_task_id": "op-002-3", "successor_task_id": "op-002-4"},
                {"predecessor_task_id": "op-002-4", "successor_task_id": "op-002-5"},
            ],
        }

        def mock_execute(*_args, **_kwargs):
            table_name = mock_client.table.call_args[0][0]
            return MagicMock(data=mock_responses.get(table_name, []))

        mock_table.execute.side_effect = mock_execute

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading and solving
            with patch("builtins.print"):  # Suppress output
                # Load problem
                loader = DatabaseLoader(use_test_tables=True)
                problem = loader.load_problem()

                # Verify loaded correctly
                assert len(problem.jobs) == 2
                assert problem.total_task_count == 10
                assert len(problem.machines) == 3
                assert len(problem.precedences) == 8

                # Create and run solver
                solver = FreshSolver(problem)
                solution = solver.solve(time_limit=30)

            # THEN: Valid solution found
            assert solution["status"] in ["OPTIMAL", "FEASIBLE"]
            assert len(solution["schedule"]) == 10

            # Verify all tasks scheduled
            scheduled_tasks = {t["task_id"] for t in solution["schedule"]}
            expected_tasks = {f"op-001-{i}" for i in range(1, 6)} | {
                f"op-002-{i}" for i in range(1, 6)
            }
            assert scheduled_tasks == expected_tasks

            # Verify precedences respected
            task_times = {
                t["task_id"]: (t["start_time"], t["end_time"])
                for t in solution["schedule"]
            }

            for prec in problem.precedences:
                pred_end = task_times[prec.predecessor_task_id][1]
                succ_start = task_times[prec.successor_task_id][0]
                assert succ_start >= pred_end, (
                    f"{prec.successor_task_id} starts before "
                    f"{prec.predecessor_task_id} ends"
                )

            # Verify machine assignments
            for task in solution["schedule"]:
                assert task["machine_id"] in ["lathe-1", "mill-1", "drill-1"]
                assert task["machine_name"] is not None

            # Verify no machine conflicts (no overlaps)
            machine_schedules = {}
            for task in solution["schedule"]:
                machine = task["machine_id"]
                if machine not in machine_schedules:
                    machine_schedules[machine] = []
                machine_schedules[machine].append(
                    (task["start_time"], task["end_time"], task["task_id"])
                )

            for machine, schedule in machine_schedules.items():
                # Sort by start time
                schedule.sort(key=lambda x: x[0])
                # Check no overlaps
                for i in range(len(schedule) - 1):
                    assert schedule[i][1] <= schedule[i + 1][0], (
                        f"Overlap on {machine}: {schedule[i][2]} and "
                        f"{schedule[i + 1][2]}"
                    )

    def test_phase1_validation_errors(self):
        """Test that validation errors are handled gracefully."""
        # GIVEN: Problem with validation issues
        # Task with no modes
        task_no_modes = Task("t1", "j1", "Bad Task", modes=[])
        # Task with mode referencing non-existent machine
        mode_bad_machine = TaskMode("m1", "t2", "machine-999", 30)
        task_bad_ref = Task("t2", "j1", "Task 2", modes=[mode_bad_machine])

        job = Job(
            job_id="j1",
            description="Job",
            due_date=datetime.now(UTC),
            tasks=[task_no_modes, task_bad_ref],
        )

        # Precedence with non-existent tasks
        bad_precedence = Precedence("t999", "t888")

        problem = SchedulingProblem(
            jobs=[job], machines=[], work_cells=[], precedences=[bad_precedence]
        )

        # WHEN: Validating
        issues = problem.validate()

        # THEN: All issues found
        assert len(issues) >= 3
        assert any("no modes" in issue for issue in issues)
        assert any("non-existent machine" in issue for issue in issues)
        assert any(
            "non-existent" in issue and "precedence" in issue.lower()
            for issue in issues
        )

    def test_phase1_edge_cases(self):
        """Test Phase 1 with edge cases."""
        # GIVEN: Edge case scenarios
        # 1. Task with single mode
        single_mode_task = Task(
            "t1", "j1", "Single Mode", modes=[TaskMode("m1", "t1", "m1", 15)]
        )

        # 2. Job with past due date
        past_due_job = Job(
            "j1",
            "Past Due Job",
            datetime.now(UTC) - timedelta(hours=1),
            tasks=[single_mode_task],
        )

        # 3. Very long task
        long_task = Task(
            "t2", "j2", "Long Task", modes=[TaskMode("m2", "t2", "m1", 480)]
        )  # 8 hours
        normal_job = Job(
            "j2",
            "Normal Job",
            datetime.now(UTC) + timedelta(hours=10),
            tasks=[long_task],
        )

        # 4. Single machine for all tasks
        machine = Machine("m1", "c1", "Only Machine")

        problem = SchedulingProblem(
            jobs=[past_due_job, normal_job],
            machines=[machine],
            work_cells=[],
            precedences=[],
        )

        # WHEN: Solving
        with patch("builtins.print"):
            solver = FreshSolver(problem)
            solution = solver.solve(time_limit=10)

        # THEN: Solution handles edge cases
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]
        assert len(solution["schedule"]) == 2

        # Past due job should have high lateness
        assert solution["total_lateness_minutes"] > 0

        # Tasks must be sequential on single machine
        schedule = sorted(solution["schedule"], key=lambda x: x["start_time"])
        assert schedule[0]["end_time"] <= schedule[1]["start_time"]

    def test_phase1_performance_targets(self):
        """Test that Phase 1 meets performance targets for tiny dataset."""
        # GIVEN: Tiny dataset (2 jobs, 10 tasks) as per STANDARDS.md
        import time

        machines = [
            Machine("m1", "c1", "Machine 1", cost_per_hour=50),
            Machine("m2", "c1", "Machine 2", cost_per_hour=75),
            Machine("m3", "c2", "Machine 3", cost_per_hour=25),
        ]

        jobs = []
        all_tasks = []
        precedences = []

        # Create 2 jobs with 5 tasks each
        for j in range(2):
            tasks = []
            for t in range(5):
                task_id = f"task-{j}-{t}"
                # Each task can run on 2 machines with different durations
                # Use at least 2 different machines per task for flexibility
                machine1_idx = t % 3
                machine2_idx = (t + 1) % 3
                if machine1_idx == machine2_idx:
                    machine2_idx = (t + 2) % 3

                modes = [
                    TaskMode(
                        f"mode-{task_id}-1",
                        task_id,
                        machines[machine1_idx].resource_id,
                        30 + (t * 15),
                    ),
                    TaskMode(
                        f"mode-{task_id}-2",
                        task_id,
                        machines[machine2_idx].resource_id,
                        45 + (t * 10),
                    ),
                ]
                task = Task(task_id, f"job-{j}", f"Task {j}-{t}", modes=modes)
                tasks.append(task)
                all_tasks.append(task)

                # Chain precedences within job
                if t > 0:
                    precedences.append(Precedence(f"task-{j}-{t - 1}", task_id))

            job = Job(
                f"job-{j}",
                f"Job {j}",
                datetime.now(UTC) + timedelta(hours=8 + j * 4),
                tasks=tasks,
            )
            jobs.append(job)

        problem = SchedulingProblem(jobs, machines, [], precedences)

        # WHEN: Solving and timing
        start_time = time.time()

        with patch("builtins.print"):
            solver = FreshSolver(problem)
            solution = solver.solve(time_limit=10)

        solve_time = time.time() - start_time

        # THEN: Meets performance targets
        assert solution["status"] in ["OPTIMAL", "FEASIBLE"]
        assert solve_time < 1.0, f"Solve time {solve_time}s exceeds 1s target"
        assert len(solution["schedule"]) == 10

        # Verify solution quality
        print("\nPerformance test results:")
        print(f"  Solve time: {solve_time:.3f}s")
        print(f"  Status: {solution['status']}")
        print(f"  Makespan: {solution['makespan_hours']:.1f} hours")
        print(f"  Lateness: {solution['total_lateness_minutes']:.1f} minutes")
        print(f"  Solver conflicts: {solution['solver_stats']['conflicts']}")
        print(f"  Solver branches: {solution['solver_stats']['branches']}")
