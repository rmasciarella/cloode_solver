#!/usr/bin/env python3
"""Check what tables exist in Supabase."""

import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    exit(1)

print("Connecting to Supabase...")
print(f"URL: {url}")

supabase = create_client(url, key)

# Try to list tables using a simple query
test_tables = [
    "test_work_cells",
    "test_resources",
    "test_jobs",
    "test_tasks",
    "test_task_modes",
    "test_task_precedences",
]

print("\nChecking for test tables:")
for table in test_tables:
    try:
        result = supabase.table(table).select("*").limit(1).execute()
        print(f"✓ {table} exists")
    except Exception as e:
        print(f"✗ {table} - {str(e)[:100]}")

print("\nIf tables are missing, please run the migration in Supabase SQL Editor:")
print("File: migrations/000_create_test_tables.sql")
