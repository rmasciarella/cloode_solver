#!/usr/bin/env python3
"""Check which tables are accessible via anon role."""

import os

from dotenv import load_dotenv
from supabase import create_client


def check_accessible_tables():
    """Check which tables are accessible."""
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    supabase = create_client(url, key)

    # List of known tables from the MCP query
    known_tables = [
        "jobs",
        "tasks",
        "resources",
        "work_cells",
        "task_modes",
        "task_precedences",
        "optimization_runs",
        "skills",
        "labor_skills",
        "holiday_calendar",
        "test_work_cells",
        "test_jobs",
        "test_tasks",
        "test_resources",
        "test_task_modes",
        "test_task_precedences",
    ]

    accessible_tables = []

    for table in known_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            accessible_tables.append(table)
            print(f"✅ {table}: accessible (rows: {len(result.data)})")
        except Exception as e:
            print(f"❌ {table}: {str(e)[:100]}")

    print(f"\nSUMMARY: {len(accessible_tables)}/{len(known_tables)} tables accessible")
    print("Accessible tables:", accessible_tables)


if __name__ == "__main__":
    check_accessible_tables()
