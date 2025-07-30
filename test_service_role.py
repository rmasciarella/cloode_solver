#!/usr/bin/env python3
"""Test connectivity using service role key."""

import os

from dotenv import load_dotenv
from supabase import create_client


def test_service_role():
    """Test database connectivity with service role."""
    print("Testing database connectivity with service role...")

    # Load environment variables
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    print(f"SUPABASE_URL: {url}")
    print(f"SERVICE_ROLE_KEY: {'*' * 20 if key else 'None'}")

    if not url or not key:
        print("❌ Missing environment variables")
        return False

    try:
        # Create client with service role
        supabase = create_client(url, key)
        print("✅ Client created successfully")

        # Test query
        result = supabase.table("test_work_cells").select("*").limit(1).execute()
        print(f"✅ Query successful: {len(result.data)} rows returned")

        if result.data:
            print(f"Sample data: {result.data[0]}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_service_role()
    exit(0 if success else 1)
