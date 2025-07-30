#!/usr/bin/env python3
"""Debug script to check table visibility with structured logging."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Add project root to path for logging config import
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.solver.utils.logging_config import get_data_logger, setup_logging  # noqa: E402


def debug_tables():
    """Check what tables are visible using structured logging."""
    # Setup logging for debugging
    setup_logging(level="INFO", enable_file_logging=True)
    logger = get_data_logger("debug_tables")

    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.error("Missing environment variables: SUPABASE_URL or SUPABASE_ANON_KEY")
        print("❌ Missing environment variables")
        return

    logger.info("Starting table visibility debug session")
    supabase = create_client(url, key)

    # Test 1: RPC query
    try:
        result = supabase.rpc("pg_tables_query", {}).execute()
        logger.info("RPC query successful: found %d tables", len(result.data))
        logger.debug("Available tables via RPC: %s", result.data)
        print("✅ RPC query successful")
    except Exception as e:
        logger.error("RPC query failed: %s", str(e))
        print(f"❌ RPC failed: {e}")

    # Test 2: Direct SQL query
    try:
        query = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        result = supabase.postgrest.rpc("sql", {"query": query}).execute()
        logger.info("SQL RPC query successful: found %d tables", len(result.data))
        logger.debug("Tables via SQL RPC: %s", result.data)
        print("✅ SQL RPC query successful")
    except Exception as e:
        logger.error("SQL RPC query failed: %s", str(e))
        print(f"❌ SQL RPC failed: {e}")

    # Test 3: Individual test table access
    test_tables = [
        "test_work_cells",
        "test_jobs",
        "test_tasks",
        "test_resources",
        "test_task_modes",
        "test_task_precedences",
    ]

    logger.info("Testing access to %d specific tables", len(test_tables))
    accessible_tables = []
    failed_tables = []

    for table in test_tables:
        try:
            result = supabase.table(table).select("count").execute()
            logger.debug("Table %s: accessible", table)
            accessible_tables.append(table)
            print(f"✅ {table}: accessible")
        except Exception as e:
            logger.warning("Table %s: access failed - %s", table, str(e))
            failed_tables.append((table, str(e)))
            print(f"❌ {table}: {e}")

    # Summary logging
    logger.info("Table access summary:")
    logger.info("  Accessible tables: %d", len(accessible_tables))
    logger.info("  Failed tables: %d", len(failed_tables))

    if accessible_tables:
        logger.info("  Accessible: %s", ", ".join(accessible_tables))

    if failed_tables:
        failed_summary = ", ".join([f"{t}({e})" for t, e in failed_tables])
        logger.warning("  Failed: %s", failed_summary)

    # Console summary
    accessible_count = len(accessible_tables)
    total_count = len(test_tables)
    print(f"\n📊 Summary: {accessible_count}/{total_count} tables accessible")
    print("See logs for detailed information")


if __name__ == "__main__":
    debug_tables()
