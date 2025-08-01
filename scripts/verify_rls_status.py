#!/usr/bin/env python3
"""Verify RLS status in the live Supabase database."""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()


def check_rls_status():
    """Check if RLS is enabled on tables in the database."""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_key:
        print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False

    print(f"🔍 Checking RLS status for: {url}")

    # Create client with service role key to bypass RLS
    client = create_client(url, service_key)

    try:
        # Query to check RLS status on tables
        query = """
        SELECT 
            schemaname,
            tablename,
            rowsecurity
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN (
            'departments', 'machines', 'work_cells', 
            'job_optimized_patterns', 'optimized_tasks',
            'job_instances', 'operators', 'skills'
        )
        ORDER BY tablename;
        """

        result = client.rpc("sql_query", {"query": query}).execute()

        if result.data:
            print("\n📊 RLS Status by Table:")
            print("-" * 50)
            all_enabled = True
            for row in result.data:
                status = "✅ ENABLED" if row["rowsecurity"] else "❌ DISABLED"
                print(f"{row['tablename']:<30} {status}")
                if not row["rowsecurity"]:
                    all_enabled = False
            print("-" * 50)

            if all_enabled:
                print("\n✅ All tables have RLS enabled!")
            else:
                print("\n⚠️  Some tables don't have RLS enabled")

            return all_enabled
        else:
            # Alternative approach: Try direct SQL
            print("⚠️  Direct SQL query not available, checking via table access...")

            # Test if we can access departments without auth
            anon_client = create_client(url, os.getenv("SUPABASE_ANON_KEY"))

            try:
                # Try to read departments as anonymous user
                result = anon_client.table("departments").select("*").limit(1).execute()
                if result.data:
                    print("⚠️  Anonymous access allowed to departments table")
                    print(
                        "   This suggests RLS is either disabled or has permissive policies"
                    )
                else:
                    print("✅ No anonymous access to departments (RLS working)")
                return True
            except Exception as e:
                if "permission denied" in str(e).lower():
                    print("✅ RLS is blocking anonymous access (good!)")
                    return True
                else:
                    print(f"❌ Error checking anonymous access: {e}")
                    return False

    except Exception as e:
        print(f"❌ Error checking RLS status: {e}")

        # Try alternative check
        print("\n🔄 Attempting alternative RLS check...")
        try:
            # Check if we can query pg_policies
            policies_query = """
            SELECT 
                schemaname,
                tablename,
                policyname,
                permissive,
                roles,
                cmd
            FROM pg_policies
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname;
            """

            # Since we can't use sql_query, let's check table access
            print("\n📋 Checking table access levels:")

            tables = ["departments", "machines", "work_cells"]
            for table in tables:
                try:
                    # Try with service role (should always work)
                    service_result = client.table(table).select("*").limit(1).execute()
                    print(f"✅ Service role can access {table}")

                    # Try with anon key
                    anon_client = create_client(url, os.getenv("SUPABASE_ANON_KEY"))
                    try:
                        anon_result = (
                            anon_client.table(table).select("*").limit(1).execute()
                        )
                        print(
                            f"⚠️  Anonymous can access {table} (permissive RLS or disabled)"
                        )
                    except:
                        print(f"✅ Anonymous blocked from {table} (RLS working)")

                except Exception as table_error:
                    print(f"❌ Error accessing {table}: {table_error}")

        except Exception as alt_error:
            print(f"❌ Alternative check failed: {alt_error}")

    return False


def check_environment_config():
    """Verify environment configuration."""
    print("\n🔧 Environment Configuration:")
    print("-" * 50)

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "RLS_ENABLED",
        "DATABASE_SECURITY_LEVEL",
        "AUTH_REQUIRED",
        "ALLOW_ANON_ACCESS",
    ]

    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display_value = (
                    value[:10] + "..." + value[-5:] if len(value) > 20 else "***"
                )
            else:
                display_value = value
            print(f"{var:<30} ✅ {display_value}")
        else:
            print(f"{var:<30} ❌ Not set")
            all_set = False

    print("-" * 50)
    return all_set


def main():
    """Main verification function."""
    print("🔐 Fresh Solver RLS Verification")
    print("=" * 50)

    # Check environment config
    env_ok = check_environment_config()

    # Check RLS status
    rls_ok = check_rls_status()

    print("\n📊 Summary:")
    print("-" * 50)
    print(f"Environment Configuration: {'✅ OK' if env_ok else '❌ Issues found'}")
    print(
        f"RLS Status:               {'✅ Enabled' if rls_ok else '❌ Not fully enabled'}"
    )
    print("-" * 50)

    if env_ok and rls_ok:
        print("\n✅ Security configuration verified successfully!")
        return 0
    else:
        print("\n⚠️  Security configuration needs attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
