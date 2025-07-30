#!/usr/bin/env python3
"""Setup test data by running migration and populating data.

This script can be run without package installation.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def check_dependencies():
    """Check if required packages are available."""
    required = ["supabase", "dotenv", "ortools"]
    missing = []

    for pkg in required:
        try:
            if pkg == "dotenv":
                __import__("dotenv")
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Missing packages: {missing}")
        print("Installing required packages...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "supabase",
                "python-dotenv",
                "ortools",
            ],
            check=True,
        )
        print("Packages installed successfully!")


def run_migration():
    """Apply the database migration."""
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False

    print("Connecting to Supabase...")
    supabase = create_client(url, key)

    # Read migration file
    migration_path = Path(__file__).parent / "migrations" / "000_create_test_tables.sql"
    with open(migration_path) as f:
        sql = f.read()

    print("Running migration to create test tables...")

    # Split SQL into individual statements and execute
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    for i, statement in enumerate(statements):
        if statement:
            try:
                # Use RPC to execute raw SQL
                supabase.rpc("execute_sql", {"query": statement + ";"}).execute()
                print(f"  Statement {i+1}/{len(statements)} executed")
            except Exception as e:
                # If RPC doesn't exist, we'll note it but continue
                if "execute_sql" in str(e):
                    print(
                        "  Note: Cannot execute raw SQL via Supabase client. "
                        "Tables may need to be created manually."
                    )
                    print(
                        "  You can run the migration manually in Supabase SQL Editor."
                    )
                    return False
                else:
                    print(f"  Error on statement {i+1}: {e}")

    print("Migration completed!")
    return True


def populate_test_data():
    """Run the populate test data script."""
    print("\nPopulating test data...")
    script_path = Path(__file__).parent / "scripts" / "populate_test_data.py"

    result = subprocess.run(
        [sys.executable, str(script_path)], capture_output=True, text=True
    )

    if result.returncode == 0:
        print(result.stdout)
        print("Test data populated successfully!")
        return True
    else:
        print("Error populating test data:")
        print(result.stderr)
        return False


def verify_data():
    """Verify the test data was created."""
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    supabase = create_client(url, key)

    print("\nVerifying test data...")

    tables = [
        "test_work_cells",
        "test_resources",
        "test_jobs",
        "test_tasks",
        "test_task_modes",
        "test_task_precedences",
    ]

    for table in tables:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            count = len(result.data)
            print(f"  {table}: {count} records")
        except Exception as e:
            print(f"  {table}: Error - {e}")


def main():
    """Execute the main test data setup workflow."""
    print("Fresh Solver Test Data Setup")
    print("=" * 40)

    # Check dependencies
    check_dependencies()

    # Run migration (note: this might need manual execution)
    print(
        "\nNOTE: Database migrations typically need to be run manually "
        "in Supabase SQL Editor."
    )
    print("Please ensure the tables are created before proceeding.")
    print("Migration file: migrations/000_create_test_tables.sql")

    input("\nPress Enter when tables are created...")

    # Populate test data
    if populate_test_data():
        # Verify
        verify_data()
        print("\nSetup complete!")
    else:
        print("\nSetup failed. Please check the errors above.")


if __name__ == "__main__":
    main()
