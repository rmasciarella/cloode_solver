#!/usr/bin/env python3
"""Apply RLS migration to Supabase database."""

from pathlib import Path


def apply_migration():
    """Apply RLS migration using Supabase CLI."""
    print("🔐 Applying RLS Migration")
    print("=" * 50)

    # Check for migration files
    migration_files = [
        "migrations/001_initial_rls_setup.sql",
        "migrations/003_add_auth_and_rls_foundation.sql",
        "schema/auth_and_rls_foundation.sql",
    ]

    print("\n📁 Available migration files:")
    for file in migration_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (not found)")

    print("\n📝 Migration Instructions:")
    print("-" * 50)
    print("Since the API keys appear to be invalid, please:")
    print()
    print("1. Visit your Supabase project dashboard:")
    print("   https://hnrysjrydbhrnqqkrqir.supabase.co")
    print()
    print("2. Navigate to Settings → API")
    print()
    print("3. Copy the fresh API keys and update .env file:")
    print("   - SUPABASE_ANON_KEY")
    print("   - SUPABASE_SERVICE_ROLE_KEY")
    print()
    print("4. In SQL Editor, run the migration:")
    print("   - Open SQL Editor in Supabase dashboard")
    print("   - Copy contents of migrations/003_add_auth_and_rls_foundation.sql")
    print("   - Execute the SQL")
    print()
    print("5. Verify RLS is enabled:")
    print("   - Check Authentication → Policies")
    print("   - Confirm policies exist for all tables")
    print()
    print("Alternative: Use Supabase CLI if installed:")
    print("   supabase db push")
    print("-" * 50)


if __name__ == "__main__":
    apply_migration()
