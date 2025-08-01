"""Populate minimal test data in Supabase for fresh solver development.

Creates 2 jobs with 10 tasks total for unit testing.
"""

import os
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)


def clear_test_data():
    """Clear existing test data from all test tables."""
    print("Clearing existing test data...")

    # Clear in dependency order
    tables = [
        "test_task_precedences",
        "test_task_modes",
        "test_tasks",
        "test_jobs",
        "test_resources",
        "test_work_cells",
    ]

    for table in tables:
        try:
            supabase.table(table).delete().neq(
                "cell_id", "00000000-0000-0000-0000-000000000000"
            ).execute()
            print(f"Cleared {table}")
        except Exception:
            pass  # Ignore errors


def create_test_data():
    """Create minimal test dataset: 2 jobs, 10 tasks total."""
    print("\nCreating test data...")

    # Create work cells
    print("Creating work cells...")
    cell1_id = str(uuid.uuid4())
    cell2_id = str(uuid.uuid4())

    cells = [
        {"cell_id": cell1_id, "name": "Cell A", "capacity": 2},
        {"cell_id": cell2_id, "name": "Cell B", "capacity": 1},
    ]
    supabase.table("test_work_cells").insert(cells).execute()

    # Create machines (resources)
    print("Creating machines...")
    machine1_id = str(uuid.uuid4())
    machine2_id = str(uuid.uuid4())
    machine3_id = str(uuid.uuid4())

    machines = [
        {
            "resource_id": machine1_id,
            "cell_id": cell1_id,
            "name": "Machine 1",
            "resource_type": "machine",
            "capacity": 1,
            "cost_per_hour": 100,
        },
        {
            "resource_id": machine2_id,
            "cell_id": cell1_id,
            "name": "Machine 2",
            "resource_type": "machine",
            "capacity": 1,
            "cost_per_hour": 120,
        },
        {
            "resource_id": machine3_id,
            "cell_id": cell2_id,
            "name": "Machine 3",
            "resource_type": "machine",
            "capacity": 1,
            "cost_per_hour": 150,
        },
    ]
    supabase.table("test_resources").insert(machines).execute()

    # Create jobs
    print("Creating jobs...")
    job1_id = str(uuid.uuid4())
    job2_id = str(uuid.uuid4())

    jobs = [
        {
            "job_id": job1_id,
            "description": "Test Job 1",
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "job_id": job2_id,
            "description": "Test Job 2",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]
    supabase.table("test_jobs").insert(jobs).execute()

    # Create tasks
    print("Creating tasks...")
    task_ids = {}
    tasks = []

    # Job 1 tasks (1-5)
    for i in range(1, 6):
        task_id = str(uuid.uuid4())
        task_ids[f"job1_task{i}"] = task_id
        tasks.append(
            {
                "task_id": task_id,
                "job_id": job1_id,
                "name": f"Job 1 Task {i}",
                "department_id": "DEPT_A",
                "is_unattended": False,
                "is_setup": False,
            }
        )

    # Job 2 tasks (1-5)
    for i in range(1, 6):
        task_id = str(uuid.uuid4())
        task_ids[f"job2_task{i}"] = task_id
        tasks.append(
            {
                "task_id": task_id,
                "job_id": job2_id,
                "name": f"Job 2 Task {i}",
                "department_id": "DEPT_B",
                "is_unattended": False,
                "is_setup": False,
            }
        )

    supabase.table("test_tasks").insert(tasks).execute()

    # Create task modes (task-machine compatibility with durations)
    print("Creating task modes...")
    task_modes = []

    # Job 1 task modes
    for i in range(1, 6):
        task_id = task_ids[f"job1_task{i}"]
        # Each task can run on machine 1 or 2
        task_modes.extend(
            [
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine1_id,
                    "duration_minutes": (4 + i) * 15,  # 1-5 hours
                },
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine2_id,
                    "duration_minutes": (3 + i) * 15,  # Slightly faster on machine 2
                },
            ]
        )

    # Job 2 task modes
    for i in range(1, 6):
        task_id = task_ids[f"job2_task{i}"]
        # Tasks 1-3 can run on machine 2 or 3, tasks 4-5 only on machine 3
        if i <= 3:
            task_modes.extend(
                [
                    {
                        "task_mode_id": str(uuid.uuid4()),
                        "task_id": task_id,
                        "machine_resource_id": machine2_id,
                        "duration_minutes": (2 + i * 2) * 15,  # 4-8 time units
                    },
                    {
                        "task_mode_id": str(uuid.uuid4()),
                        "task_id": task_id,
                        "machine_resource_id": machine3_id,
                        "duration_minutes": (2 + i) * 15,  # Faster on machine 3
                    },
                ]
            )
        else:
            task_modes.append(
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine3_id,
                    "duration_minutes": (4 + i) * 15,  # 8-9 time units
                }
            )

    supabase.table("test_task_modes").insert(task_modes).execute()

    # Create precedence constraints
    print("Creating precedence constraints...")
    precedences = [
        # Job 1: Linear sequence 1->2->3->4->5
        {
            "predecessor_task_id": task_ids["job1_task1"],
            "successor_task_id": task_ids["job1_task2"],
        },
        {
            "predecessor_task_id": task_ids["job1_task2"],
            "successor_task_id": task_ids["job1_task3"],
        },
        {
            "predecessor_task_id": task_ids["job1_task3"],
            "successor_task_id": task_ids["job1_task4"],
        },
        {
            "predecessor_task_id": task_ids["job1_task4"],
            "successor_task_id": task_ids["job1_task5"],
        },
        # Job 2: More complex - 1->2, 1->3, 2->4, 3->4, 4->5
        {
            "predecessor_task_id": task_ids["job2_task1"],
            "successor_task_id": task_ids["job2_task2"],
        },
        {
            "predecessor_task_id": task_ids["job2_task1"],
            "successor_task_id": task_ids["job2_task3"],
        },
        {
            "predecessor_task_id": task_ids["job2_task2"],
            "successor_task_id": task_ids["job2_task4"],
        },
        {
            "predecessor_task_id": task_ids["job2_task3"],
            "successor_task_id": task_ids["job2_task4"],
        },
        {
            "predecessor_task_id": task_ids["job2_task4"],
            "successor_task_id": task_ids["job2_task5"],
        },
    ]

    supabase.table("test_task_precedences").insert(precedences).execute()

    print("\nTest data created successfully!")
    print("- 2 jobs")
    print("- 10 tasks (5 per job)")
    print("- 3 machines across 2 cells")
    print("- Task modes with varying durations")
    print("- Precedence constraints (linear for job 1, diamond for job 2)")

    return {
        "jobs": [job1_id, job2_id],
        "tasks": task_ids,
        "machines": [machine1_id, machine2_id, machine3_id],
        "cells": [cell1_id, cell2_id],
    }


if __name__ == "__main__":
    clear_test_data()
    test_data_ids = create_test_data()

    # Save IDs for reference
    import json

    with open("tests/test_data/test_ids.json", "w") as f:
        json.dump(test_data_ids, f, indent=2)

    print("\nTest IDs saved to tests/test_data/test_ids.json")
