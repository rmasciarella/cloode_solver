#!/usr/bin/env python3
"""Setup Supabase test data by creating tables and populating them.

This script combines table creation and data population in one step.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.populate_test_data import create_test_data


def create_test_tables(supabase: Client) -> bool:
    """Create test tables using the migration SQL."""
    sql_file = (
        Path(__file__).parent.parent / "migrations" / "000_create_test_tables.sql"
    )

    try:
        with open(sql_file) as f:
            sql_content = f.read()

        print("Creating test tables...")
        supabase.rpc("exec_sql", {"query": sql_content}).execute()
        print("✓ Test tables created successfully")
        return True
    except Exception:
        # Try executing the SQL directly as a fallback
        print("Note: exec_sql RPC not available, trying direct execution...")

        # Split SQL into individual statements and execute
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    # Execute using the query builder approach
                    print(f"Executing statement {i + 1}/{len(statements)}...")
                    # Since Supabase client doesn't have direct SQL execution,
                    # we'll need to use the populate script approach
                    print(f"Statement preview: {statement[:50]}...")
                except Exception as stmt_error:
                    print(f"Error executing statement {i + 1}: {stmt_error}")
                    return False

        print("Note: Direct SQL execution not supported by Supabase client.")
        print("Please run the SQL manually in Supabase Dashboard SQL Editor.")
        return False


def check_tables_exist(supabase: Client) -> bool:
    """Check if test tables exist."""
    try:
        # Try to query each test table
        tables = [
            "test_work_cells",
            "test_resources",
            "test_jobs",
            "test_tasks",
            "test_task_modes",
            "test_task_precedences",
        ]

        for table in tables:
            supabase.table(table).select("*").limit(1).execute()
            print(f"✓ Table {table} exists")

        return True
    except Exception as e:
        print(f"✗ Some tables don't exist: {e}")
        return False


def main():
    """Execute the Supabase test data setup workflow."""
    # Load environment variables
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return 1

    # Create Supabase client
    supabase: Client = create_client(url, key)

    print("=== Supabase Test Data Setup ===\n")

    # Check if tables exist
    if not check_tables_exist(supabase):
        print("\nTables don't exist. Please create them manually:")
        print("1. Go to your Supabase Dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy contents from migrations/000_create_test_tables.sql")
        print("4. Run the SQL")
        print("\nAlternatively, you can run this SQL file directly.")

        # Show the SQL file location
        sql_file = (
            Path(__file__).parent.parent / "migrations" / "000_create_test_tables.sql"
        )
        print(f"\nSQL file location: {sql_file}")

        return 1

    print("\n✓ All test tables exist")

    # Populate test data
    print("\nPopulating test data...")
    try:
        create_test_data()
        print("\n✓ Test data populated successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Error populating data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
