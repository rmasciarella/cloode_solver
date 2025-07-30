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
