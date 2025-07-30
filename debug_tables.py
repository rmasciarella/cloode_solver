#!/usr/bin/env python3
"""Debug script to check table visibility."""

import os

from dotenv import load_dotenv
from supabase import create_client


def debug_tables():
    """Check what tables are visible."""
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    supabase = create_client(url, key)

    try:
        # Try to query information_schema
        result = supabase.rpc("pg_tables_query", {}).execute()
        print("Available tables via RPC:", result.data)
    except Exception as e:
        print(f"RPC failed: {e}")

    try:
        # Try a direct SQL query
        query = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        result = supabase.postgrest.rpc("sql", {"query": query}).execute()
        print("Tables via SQL RPC:", result.data)
    except Exception as e:
        print(f"SQL RPC failed: {e}")

    # Try listing specific test tables
    test_tables = [
        "test_work_cells",
        "test_jobs",
        "test_tasks",
        "test_resources",
        "test_task_modes",
        "test_task_precedences",
    ]

    for table in test_tables:
        try:
            result = supabase.table(table).select("count").execute()
            print(f"✅ {table}: accessible")
        except Exception as e:
            print(f"❌ {table}: {e}")


if __name__ == "__main__":
    debug_tables()
