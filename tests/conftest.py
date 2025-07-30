"""Pytest configuration and shared fixtures for fresh solver tests."""

import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.solver.models.problem import Job, Machine, Precedence, Task, TaskMode, WorkCell


@pytest.fixture
def sample_machine():
    """Create a sample machine for testing."""
    return Machine(
        resource_id="machine-1",
        cell_id="cell-1",
        name="Machine 1",
        capacity=1,
        cost_per_hour=10.0,
    )


@pytest.fixture
def sample_task_mode():
    """Create a sample task mode for testing."""
    return TaskMode(
        task_mode_id="mode-1",
        task_id="task-1",
        machine_resource_id="machine-1",
        duration_minutes=30,
    )


@pytest.fixture
def sample_task():
    """Create a sample task with modes."""
    mode1 = TaskMode("mode-1", "task-1", "machine-1", 30)
    mode2 = TaskMode("mode-2", "task-1", "machine-2", 45)
    return Task(
        task_id="task-1",
        job_id="job-1",
        name="Task 1",
        department_id="dept-1",
        modes=[mode1, mode2],
    )


@pytest.fixture
def sample_job():
    """Create a sample job with tasks."""
    task1 = Task(
        "task-1",
        "job-1",
        "Task 1",
        modes=[TaskMode("mode-1", "task-1", "machine-1", 30)],
    )
    task2 = Task(
        "task-2",
        "job-1",
        "Task 2",
        modes=[TaskMode("mode-2", "task-2", "machine-1", 45)],
    )

    return Job(
        job_id="job-1",
        description="Sample Job",
        due_date=datetime.now(UTC) + timedelta(days=1),
        tasks=[task1, task2],
    )


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    mock_client = MagicMock()

    # Mock table method returns self for chaining
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table

    # Default empty response
    mock_table.execute.return_value = MagicMock(data=[])

    return mock_client


@pytest.fixture
def mock_database_loader():
    """Create a properly mocked DatabaseLoader with comprehensive test data."""
    from unittest.mock import MagicMock, patch

    from src.data.loaders.database import DatabaseLoader

    # Complete test data for mocking
    mock_test_data = {
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
        ],
        "test_jobs": [
            {
                "job_id": "order-001",
                "description": "Customer Order 001",
                "due_date": "2025-07-31T08:00:00+00:00",
                "created_at": "2025-07-30T12:00:00+00:00",
                "updated_at": "2025-07-30T12:00:00+00:00",
            },
        ],
        "test_tasks": [
            {
                "task_id": "op-001-1",
                "job_id": "order-001",
                "name": "Setup Operation",
                "department_id": "machining",
                "is_setup": True,
                "is_unattended": False,
            },
            {
                "task_id": "op-001-2",
                "job_id": "order-001",
                "name": "Main Operation",
                "department_id": "machining",
                "is_setup": False,
                "is_unattended": False,
            },
        ],
        "test_task_modes": [
            {
                "task_mode_id": "mode-1",
                "task_id": "op-001-1",
                "machine_resource_id": "lathe-1",
                "duration_minutes": 30,
            },
            {
                "task_mode_id": "mode-2",
                "task_id": "op-001-2",
                "machine_resource_id": "lathe-1",
                "duration_minutes": 60,
            },
        ],
        "test_task_precedences": [
            {
                "predecessor_task_id": "op-001-1",
                "successor_task_id": "op-001-2",
            },
        ],
    }

    def create_mock_client(url=None, key=None):  # noqa: ARG001
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        # Configure mock to return appropriate test data based on table name
        def mock_execute():
            # Get the table name from the last call
            call_args = getattr(mock_client.table, "call_args_list", [])
            if call_args:
                table_name = mock_client.table.call_args_list[-1][0][0]
                return MagicMock(data=mock_test_data.get(table_name, []))
            return MagicMock(data=[])

        mock_table.execute.side_effect = mock_execute
        return mock_client

    with (
        patch(
            "src.data.loaders.database.create_client", side_effect=create_mock_client
        ),
        patch(
            "src.data.loaders.template_database.create_client",
            side_effect=create_mock_client,
        ),
        patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://mock.supabase.co",
                "SUPABASE_ANON_KEY": "mock-anon-key",
            },
        ),
    ):
        yield DatabaseLoader


@pytest.fixture
def sample_problem_data():
    """Create sample data for a complete scheduling problem."""
    # Machines
    machines = [
        Machine("machine-1", "cell-1", "Machine 1", capacity=1),
        Machine("machine-2", "cell-1", "Machine 2", capacity=1),
        Machine("machine-3", "cell-2", "Machine 3", capacity=1),
    ]

    # Work cells
    cells = [
        WorkCell("cell-1", "Cell 1", capacity=2),
        WorkCell("cell-2", "Cell 2", capacity=1),
    ]

    # Jobs with tasks
    job1_tasks = [
        Task(
            "task-1-1",
            "job-1",
            "Job 1 Task 1",
            modes=[
                TaskMode("mode-1-1", "task-1-1", "machine-1", 30),
                TaskMode("mode-1-2", "task-1-1", "machine-2", 45),
            ],
        ),
        Task(
            "task-1-2",
            "job-1",
            "Job 1 Task 2",
            modes=[TaskMode("mode-1-3", "task-1-2", "machine-2", 60)],
        ),
    ]

    job2_tasks = [
        Task(
            "task-2-1",
            "job-2",
            "Job 2 Task 1",
            modes=[
                TaskMode("mode-2-1", "task-2-1", "machine-1", 45),
                TaskMode("mode-2-2", "task-2-1", "machine-3", 30),
            ],
        )
    ]

    jobs = [
        Job("job-1", "Job 1", datetime.now(UTC) + timedelta(hours=4), job1_tasks),
        Job("job-2", "Job 2", datetime.now(UTC) + timedelta(hours=6), job2_tasks),
    ]

    # Precedences
    precedences = [
        Precedence("task-1-1", "task-1-2"),  # Within job 1
    ]

    return {
        "machines": machines,
        "cells": cells,
        "jobs": jobs,
        "precedences": precedences,
    }
