#!/usr/bin/env python3
"""Create test tables and populate with test data.

Since we can't execute raw SQL via Supabase client, this script creates tables
using Supabase's table creation approach and then populates them.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    exit(1)

print("Connecting to Supabase...")
supabase = create_client(url, key)

print("\n" + "=" * 60)
print("IMPORTANT: Tables must be created manually in Supabase")
print("=" * 60)
print("\nPlease follow these steps:")
print("1. Go to your Supabase dashboard")
print("2. Navigate to the SQL Editor")
print("3. Copy and paste the content of: migrations/000_create_test_tables.sql")
print("4. Run the SQL to create the tables")
print("\nOnce tables are created, press Enter to continue with data population...")
input()

# Now populate the test data
print("\nPopulating test data...")

try:
    # Create work cells
    print("Creating work cells...")
    cell1_id = str(uuid.uuid4())
    cell2_id = str(uuid.uuid4())

    cells = [
        {"cell_id": cell1_id, "name": "Cell A", "capacity": 2},
        {"cell_id": cell2_id, "name": "Cell B", "capacity": 1},
    ]
    result = supabase.table("test_work_cells").insert(cells).execute()
    print(f"  Created {len(result.data)} work cells")

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
    result = supabase.table("test_resources").insert(machines).execute()
    print(f"  Created {len(result.data)} machines")

    # Create jobs
    print("Creating jobs...")
    job1_id = str(uuid.uuid4())
    job2_id = str(uuid.uuid4())

    jobs = [
        {
            "job_id": job1_id,
            "description": "Test Job 1 - Linear workflow",
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        {
            "job_id": job2_id,
            "description": "Test Job 2 - Diamond workflow",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
    ]
    result = supabase.table("test_jobs").insert(jobs).execute()
    print(f"  Created {len(result.data)} jobs")

    # Create tasks
    print("Creating tasks...")
    task_ids = {}
    tasks = []

    # Job 1 tasks (1-5) - Linear sequence
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
                "is_setup": i == 1,  # First task is setup
            }
        )

    # Job 2 tasks (1-5) - Diamond pattern
    for i in range(1, 6):
        task_id = str(uuid.uuid4())
        task_ids[f"job2_task{i}"] = task_id
        tasks.append(
            {
                "task_id": task_id,
                "job_id": job2_id,
                "name": f"Job 2 Task {i}",
                "department_id": "DEPT_B",
                "is_unattended": i == 3,  # Task 3 is unattended
                "is_setup": False,
            }
        )

    result = supabase.table("test_tasks").insert(tasks).execute()
    print(f"  Created {len(result.data)} tasks")

    # Create task modes (task-machine compatibility with durations)
    print("Creating task modes...")
    task_modes = []

    # Job 1 task modes - each task can run on machine 1 or 2
    for i in range(1, 6):
        task_id = task_ids[f"job1_task{i}"]
        # Machine 1 mode
        task_modes.append(
            {
                "task_mode_id": str(uuid.uuid4()),
                "task_id": task_id,
                "machine_resource_id": machine1_id,
                "duration_minutes": (4 + i) * 15,  # 60-120 minutes
            }
        )
        # Machine 2 mode (slightly faster)
        task_modes.append(
            {
                "task_mode_id": str(uuid.uuid4()),
                "task_id": task_id,
                "machine_resource_id": machine2_id,
                "duration_minutes": (3 + i) * 15,  # 45-105 minutes
            }
        )

    # Job 2 task modes - more complex
    for i in range(1, 6):
        task_id = task_ids[f"job2_task{i}"]
        # Tasks 1-3 can run on machine 2 or 3
        if i <= 3:
            # Machine 2 mode
            task_modes.append(
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine2_id,
                    "duration_minutes": (2 + i * 2) * 15,  # 60-120 minutes
                }
            )
            # Machine 3 mode (faster)
            task_modes.append(
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine3_id,
                    "duration_minutes": (2 + i) * 15,  # 45-75 minutes
                }
            )
        else:
            # Tasks 4-5 only on machine 3
            task_modes.append(
                {
                    "task_mode_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "machine_resource_id": machine3_id,
                    "duration_minutes": (4 + i) * 15,  # 120-135 minutes
                }
            )

    result = supabase.table("test_task_modes").insert(task_modes).execute()
    print(f"  Created {len(result.data)} task modes")

    # Create precedence constraints
    print("Creating precedence constraints...")
    precedences = []

    # Job 1: Linear sequence 1->2->3->4->5
    for i in range(1, 5):
        precedences.append(
            {
                "predecessor_task_id": task_ids[f"job1_task{i}"],
                "successor_task_id": task_ids[f"job1_task{i + 1}"],
            }
        )

    # Job 2: Diamond pattern
    # 1 -> 2
    # 1 -> 3
    # 2 -> 4
    # 3 -> 4
    # 4 -> 5
    precedences.extend(
        [
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
    )

    result = supabase.table("test_task_precedences").insert(precedences).execute()
    print(f"  Created {len(result.data)} precedence constraints")

    print("\n" + "=" * 60)
    print("Test data created successfully!")
    print("=" * 60)
    print("\nSummary:")
    print("- 2 work cells")
    print("- 3 machines across 2 cells")
    print("- 2 jobs")
    print("- 10 tasks (5 per job)")
    print(f"- {len(task_modes)} task modes with varying durations")
    print(f"- {len(precedences)} precedence constraints")
    print("\nJob 1: Linear workflow (1->2->3->4->5)")
    print("Job 2: Diamond workflow (1 splits to 2&3, both converge to 4, then 5)")

    # Save IDs for reference
    test_data = {
        "cells": {"cell_a": cell1_id, "cell_b": cell2_id},
        "machines": {
            "machine_1": machine1_id,
            "machine_2": machine2_id,
            "machine_3": machine3_id,
        },
        "jobs": {"job_1": job1_id, "job_2": job2_id},
        "tasks": task_ids,
    }

    import json

    os.makedirs("tests/test_data", exist_ok=True)
    with open("tests/test_data/test_ids.json", "w") as f:
        json.dump(test_data, f, indent=2)

    print("\nTest IDs saved to: tests/test_data/test_ids.json")

    # Verify by loading with DatabaseLoader
    print("\n" + "=" * 60)
    print("Verifying data with DatabaseLoader...")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from data.loaders.database import DatabaseLoader

    loader = DatabaseLoader(use_test_tables=True)
    problem = loader.load_problem()

    print("\nData loaded successfully!")

except Exception as e:
    print(f"\nERROR: {e}")
    print(
        "\nPlease ensure the tables are created in Supabase before running this script."
    )
    print("Migration file: migrations/000_create_test_tables.sql")
