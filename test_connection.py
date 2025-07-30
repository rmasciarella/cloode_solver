#!/usr/bin/env python3
"""Simple connectivity test for debugging database issues."""

import os

from dotenv import load_dotenv
from supabase import create_client


def test_connection():
    """Test database connectivity."""
    print("Testing database connectivity...")

    # Load environment variables
    load_dotenv()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    print(f"SUPABASE_URL: {url}")
    print(f"SUPABASE_ANON_KEY: {'*' * 20 if key else 'None'}")

    if not url or not key:
        print("❌ Missing environment variables")
        return False

    try:
        # Create client
        supabase = create_client(url, key)
        print("✅ Client created successfully")

        # Test query
        result = supabase.table("test_work_cells").select("*").limit(1).execute()
        print(f"✅ Query successful: {len(result.data)} rows returned")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
