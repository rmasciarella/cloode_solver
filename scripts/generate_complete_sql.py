#!/usr/bin/env python3
"""Generate complete SQL file with both table creation and test data.

This creates a single SQL file that can be run in Supabase SQL Editor.
"""

import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_complete_sql():
    """Generate complete SQL with tables and data."""
    # Read the table creation SQL
    sql_file = (
        Path(__file__).parent.parent / "migrations" / "000_create_test_tables.sql"
    )
    with open(sql_file) as f:
        create_tables_sql = f.read()

    # Generate test data SQL
    now = datetime.now(UTC)
    due_date_1 = now + timedelta(days=2)
    due_date_2 = now + timedelta(days=3)

    # Generate UUIDs for consistent references
    cell_a_id = str(uuid.uuid4())
    cell_b_id = str(uuid.uuid4())

    machine_1_id = str(uuid.uuid4())
    machine_2_id = str(uuid.uuid4())
    machine_3_id = str(uuid.uuid4())

    job_1_id = str(uuid.uuid4())
    job_2_id = str(uuid.uuid4())

    # Task IDs for Job 1
    job1_task_ids = [str(uuid.uuid4()) for _ in range(5)]

    # Task IDs for Job 2
    job2_task_ids = [str(uuid.uuid4()) for _ in range(5)]

    insert_data_sql = f"""
-- Insert test data for fresh solver

-- Insert work cells
INSERT INTO test_work_cells (cell_id, name, capacity) VALUES
('{cell_a_id}', 'Cell A', 2),
('{cell_b_id}', 'Cell B', 1);

-- Insert machines
INSERT INTO test_resources (
    resource_id, cell_id, name, resource_type, capacity, cost_per_hour
) VALUES
('{machine_1_id}', '{cell_a_id}', 'Machine 1', 'machine', 1, 100.00),
('{machine_2_id}', '{cell_a_id}', 'Machine 2', 'machine', 1, 120.00),
('{machine_3_id}', '{cell_b_id}', 'Machine 3', 'machine', 1, 80.00);

-- Insert jobs
INSERT INTO test_jobs (job_id, description, due_date) VALUES
('{job_1_id}', 'Test Job 1 - Linear Workflow', '{due_date_1.isoformat()}'),
('{job_2_id}', 'Test Job 2 - Diamond Workflow', '{due_date_2.isoformat()}');

-- Insert tasks for Job 1 (Linear workflow)
INSERT INTO test_tasks (
    task_id, job_id, name, department_id, is_unattended, is_setup
) VALUES
('{job1_task_ids[0]}', '{job_1_id}', 'J1-T1: Setup', 'dept_a', false, true),
('{job1_task_ids[1]}', '{job_1_id}', 'J1-T2: Process A', 'dept_a', false, false),
('{job1_task_ids[2]}', '{job_1_id}', 'J1-T3: Process B', 'dept_b', true, false),
('{job1_task_ids[3]}', '{job_1_id}', 'J1-T4: Process C', 'dept_a', false, false),
('{job1_task_ids[4]}', '{job_1_id}', 'J1-T5: Cleanup', 'dept_b', false, false);

-- Insert tasks for Job 2 (Diamond workflow)
INSERT INTO test_tasks (
    task_id, job_id, name, department_id, is_unattended, is_setup
) VALUES
('{job2_task_ids[0]}', '{job_2_id}', 'J2-T1: Initial Setup', 'dept_a', false, true),
('{job2_task_ids[1]}', '{job_2_id}', 'J2-T2: Branch A', 'dept_a', false, false),
('{job2_task_ids[2]}', '{job_2_id}', 'J2-T3: Branch B', 'dept_b', true, false),
('{job2_task_ids[3]}', '{job_2_id}', 'J2-T4: Merge Process', 'dept_a', false, false),
('{job2_task_ids[4]}', '{job_2_id}', 'J2-T5: Final Assembly', 'dept_b', false, false);

-- Insert task modes for Job 1
INSERT INTO test_task_modes (task_id, machine_resource_id, duration_minutes) VALUES
-- Task 1: Can run on machines 1 or 2
('{job1_task_ids[0]}', '{machine_1_id}', 30),
('{job1_task_ids[0]}', '{machine_2_id}', 25),
-- Task 2: Only on machine 1
('{job1_task_ids[1]}', '{machine_1_id}', 45),
-- Task 3: Can run on any machine (unattended)
('{job1_task_ids[2]}', '{machine_1_id}', 60),
('{job1_task_ids[2]}', '{machine_2_id}', 60),
('{job1_task_ids[2]}', '{machine_3_id}', 75),
-- Task 4: Machines 2 or 3
('{job1_task_ids[3]}', '{machine_2_id}', 40),
('{job1_task_ids[3]}', '{machine_3_id}', 50),
-- Task 5: Only on machine 3
('{job1_task_ids[4]}', '{machine_3_id}', 20);

-- Insert task modes for Job 2
INSERT INTO test_task_modes (task_id, machine_resource_id, duration_minutes) VALUES
-- Task 1: Setup on machine 1
('{job2_task_ids[0]}', '{machine_1_id}', 15),
-- Task 2: Branch A on machines 1 or 2
('{job2_task_ids[1]}', '{machine_1_id}', 35),
('{job2_task_ids[1]}', '{machine_2_id}', 30),
-- Task 3: Branch B (unattended) on machine 3
('{job2_task_ids[2]}', '{machine_3_id}', 90),
-- Task 4: Merge on machine 2
('{job2_task_ids[3]}', '{machine_2_id}', 55),
-- Task 5: Final assembly on machines 1 or 3
('{job2_task_ids[4]}', '{machine_1_id}', 40),
('{job2_task_ids[4]}', '{machine_3_id}', 45);

-- Insert precedences for Job 1 (Linear: 1->2->3->4->5)
INSERT INTO test_task_precedences (predecessor_task_id, successor_task_id) VALUES
('{job1_task_ids[0]}', '{job1_task_ids[1]}'),
('{job1_task_ids[1]}', '{job1_task_ids[2]}'),
('{job1_task_ids[2]}', '{job1_task_ids[3]}'),
('{job1_task_ids[3]}', '{job1_task_ids[4]}');

-- Insert precedences for Job 2 (Diamond: 1->2,3; 2,3->4; 4->5)
INSERT INTO test_task_precedences (predecessor_task_id, successor_task_id) VALUES
('{job2_task_ids[0]}', '{job2_task_ids[1]}'),
('{job2_task_ids[0]}', '{job2_task_ids[2]}'),
('{job2_task_ids[1]}', '{job2_task_ids[3]}'),
('{job2_task_ids[2]}', '{job2_task_ids[3]}'),
('{job2_task_ids[3]}', '{job2_task_ids[4]}');
"""

    # Combine both parts
    complete_sql = f"{create_tables_sql}\n\n{insert_data_sql}"

    # Write to file
    output_file = (
        Path(__file__).parent.parent / "migrations" / "complete_test_setup.sql"
    )
    with open(output_file, "w") as f:
        f.write(complete_sql)

    print(f"✓ Generated complete SQL file: {output_file}")
    print("\nTo set up your test data:")
    print("1. Go to your Supabase Dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy the entire contents of migrations/complete_test_setup.sql")
    print("4. Paste and run it")
    print("\nThis will create all tables and insert test data in one step.")

    return str(output_file)


if __name__ == "__main__":
    generate_complete_sql()
