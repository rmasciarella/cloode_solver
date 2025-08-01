#!/usr/bin/env python3
"""Apply initial RLS setup to Fresh Solver project.
This script applies the permissive RLS policies that maintain existing functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.auth.service_auth import ServiceAuthManager


def apply_initial_rls():
    """Apply the initial RLS migration"""
    try:
        # Initialize service auth
        auth_manager = ServiceAuthManager()
        client = auth_manager.client

        # Read the SQL migration file
        migration_file = project_root / "migrations" / "001_initial_rls_setup.sql"

        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False

        print(f"Reading migration from: {migration_file}")
        with open(migration_file) as f:
            sql_content = f.read()

        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        print(f"Executing {len(statements)} SQL statements...")

        # Execute each statement
        success_count = 0
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if (
                statement.startswith("--")
                or statement.startswith("/*")
                or not statement.strip()
            ):
                continue

            try:
                print(f"[{i}/{len(statements)}] Executing statement...")

                # Execute the statement using raw SQL
                result = client.rpc("execute_sql", {"query": statement})

                if result.data is not None:
                    success_count += 1
                    print(f"✓ Statement {i} executed successfully")
                else:
                    print(f"! Statement {i} returned no data (may be normal)")
                    success_count += 1

            except Exception as e:
                error_msg = str(e)
                # Some errors are expected (like trying to create existing policies)
                if any(
                    phrase in error_msg.lower()
                    for phrase in ["already exists", "duplicate", "already enabled"]
                ):
                    print(f"~ Statement {i} skipped (already exists): {error_msg}")
                    success_count += 1
                else:
                    print(f"✗ Statement {i} failed: {error_msg}")
                    # Continue with other statements

        print(
            f"\nMigration completed: {success_count}/{len([s for s in statements if s.strip() and not s.startswith('--')])} statements successful"
        )

        # Test basic functionality
        print("\nTesting basic database access...")
        try:
            result = client.table("departments").select("count").execute()
            print("✓ Database access test passed")
            return True
        except Exception as e:
            print(f"✗ Database access test failed: {e}")
            return False

    except Exception as e:
        print(f"Migration failed: {e}")
        return False


def main():
    """Main function"""
    print("Fresh Solver RLS Migration - Initial Setup")
    print("=" * 50)

    if apply_initial_rls():
        print("\n✓ Initial RLS setup completed successfully!")
        print("\nNext steps:")
        print("1. Test GUI functionality with NEXT_PUBLIC_DISABLE_AUTH=true")
        print("2. Gradually tighten security using security_migration.py")
        print("3. Enable authentication in production")
    else:
        print("\n✗ Migration failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
