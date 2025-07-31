#!/usr/bin/env python3
"""Populate optimized pattern test data for Fresh OR-Tools solver.

Week 3 Implementation: Creates realistic optimized pattern test data
for performance testing and development with 5-8x performance improvements.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from supabase import Client, create_client

from src.data.loaders.optimized_database import OptimizedDatabaseLoader


def setup_database_connection() -> Client:
    """Set up Supabase connection."""
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    return create_client(url, key)


def create_manufacturing_pattern(supabase: Client) -> str:
    """Create the standard manufacturing job optimized pattern."""
    # Insert job optimized pattern
    pattern_data = {
        "name": "Standard Manufacturing Job",
        "description": "Complete manufacturing process from setup to packaging",
        "task_count": 7,  # Will be updated by trigger
        "total_min_duration_minutes": 0,  # Will be calculated by trigger
        "critical_path_length_minutes": 0,  # Will be calculated by trigger
    }

    pattern_response = (
        supabase.table("job_optimized_patterns").insert(pattern_data).execute()
    )
    pattern_id = pattern_response.data[0]["pattern_id"]

    print(f"Created manufacturing pattern: {pattern_id}")

    # Define optimized tasks
    optimized_tasks = [
        {
            "pattern_id": pattern_id,
            "name": "Machine Setup",
            "department_id": "production",
            "is_setup": True,
            "position": 1,
        },
        {
            "pattern_id": pattern_id,
            "name": "Load Raw Material",
            "department_id": "production",
            "is_setup": False,
            "position": 2,
        },
        {
            "pattern_id": pattern_id,
            "name": "Primary Manufacturing Operation",
            "department_id": "production",
            "is_setup": False,
            "position": 3,
        },
        {
            "pattern_id": pattern_id,
            "name": "Secondary Manufacturing Operation",
            "department_id": "production",
            "is_setup": False,
            "position": 4,
        },
        {
            "pattern_id": pattern_id,
            "name": "Quality Control Inspection",
            "department_id": "quality",
            "is_setup": False,
            "position": 5,
        },
        {
            "pattern_id": pattern_id,
            "name": "Package Finished Product",
            "department_id": "packaging",
            "is_setup": False,
            "position": 6,
        },
        {
            "pattern_id": pattern_id,
            "name": "Machine Cleanup",
            "department_id": "production",
            "is_setup": True,
            "position": 7,
        },
    ]

    tasks_response = supabase.table("optimized_tasks").insert(optimized_tasks).execute()
    task_ids = {task["name"]: task["optimized_task_id"] for task in tasks_response.data}

    print(f"Created {len(task_ids)} optimized tasks")

    # Get machine IDs from test resources
    machines_response = (
        supabase.table("test_resources")
        .select("resource_id, name")
        .eq("resource_type", "machine")
        .execute()
    )

    machine_lookup = {
        machine["name"]: machine["resource_id"] for machine in machines_response.data
    }

    if not machine_lookup:
        print("WARNING: No machines found in test_resources. Create machines first.")
        return pattern_id

    # Define task modes (machine + duration combinations)
    task_modes = []

    # Machine Setup modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Machine Setup"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 30,
                "mode_name": "setup_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Machine Setup"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 45,
                "mode_name": "setup_cnc2",
            }
        )

    # Load Material modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Load Raw Material"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 15,
                "mode_name": "load_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Load Raw Material"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 20,
                "mode_name": "load_cnc2",
            }
        )

    # Primary Operation modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 90,
                "mode_name": "primary_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 75,
                "mode_name": "primary_cnc2",
            }
        )
    if "Manual Assembly Station" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["Manual Assembly Station"],
                "duration_minutes": 120,
                "mode_name": "primary_manual",
            }
        )

    # Secondary Operation modes
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Secondary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 60,
                "mode_name": "secondary_cnc2",
            }
        )
    if "Manual Assembly Station" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Secondary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["Manual Assembly Station"],
                "duration_minutes": 45,
                "mode_name": "secondary_manual",
            }
        )

    # Quality Control modes
    if "Quality Control Station" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Quality Control Inspection"],
                "machine_resource_id": machine_lookup["Quality Control Station"],
                "duration_minutes": 30,
                "mode_name": "qc_station",
            }
        )

    # Packaging modes
    if "Packaging Station" in machine_lookup:
        task_modes.append(
            {
                "optimized_task_id": task_ids["Package Finished Product"],
                "machine_resource_id": machine_lookup["Packaging Station"],
                "duration_minutes": 20,
                "mode_name": "pack_station",
            }
        )

    # Cleanup modes
    for machine_name in ["CNC Machine #1", "CNC Machine #2", "Manual Assembly Station"]:
        if machine_name in machine_lookup:
            duration = 20 if "CNC" in machine_name else 15
            task_modes.append(
                {
                    "optimized_task_id": task_ids["Machine Cleanup"],
                    "machine_resource_id": machine_lookup[machine_name],
                    "duration_minutes": duration,
                    "mode_name": (
                        f"cleanup_"
                        f"{machine_name.lower().replace(' ', '_').replace('#', '')}"
                    ),
                }
            )

    if task_modes:
        supabase.table("optimized_task_modes").insert(task_modes).execute()
        print(f"Created {len(task_modes)} task modes")
    else:
        print("WARNING: No task modes created. Check machine names in test_resources.")

    # Define optimized precedences (linear workflow)
    precedences = [
        (task_ids["Machine Setup"], task_ids["Load Raw Material"]),
        (task_ids["Load Raw Material"], task_ids["Primary Manufacturing Operation"]),
        (
            task_ids["Primary Manufacturing Operation"],
            task_ids["Secondary Manufacturing Operation"],
        ),
        (
            task_ids["Secondary Manufacturing Operation"],
            task_ids["Quality Control Inspection"],
        ),
        (task_ids["Quality Control Inspection"], task_ids["Package Finished Product"]),
        (task_ids["Package Finished Product"], task_ids["Machine Cleanup"]),
    ]

    precedence_data = []
    for pred_id, succ_id in precedences:
        precedence_data.append(
            {
                "pattern_id": pattern_id,
                "predecessor_optimized_task_id": pred_id,
                "successor_optimized_task_id": succ_id,
            }
        )

    supabase.table("optimized_precedences").insert(precedence_data).execute()
    print(f"Created {len(precedence_data)} precedence constraints")

    return pattern_id


def create_assembly_pattern(supabase: Client) -> str:
    """Create a simpler assembly job optimized pattern for variety."""
    pattern_data = {
        "name": "Simple Assembly Job",
        "description": "Basic assembly process with minimal setup",
        "task_count": 4,
    }

    pattern_response = (
        supabase.table("job_optimized_patterns").insert(pattern_data).execute()
    )
    pattern_id = pattern_response.data[0]["pattern_id"]

    print(f"Created assembly pattern: {pattern_id}")

    # Define simpler optimized tasks
    optimized_tasks = [
        {
            "pattern_id": pattern_id,
            "name": "Assembly Setup",
            "department_id": "production",
            "is_setup": True,
            "position": 1,
        },
        {
            "pattern_id": pattern_id,
            "name": "Component Assembly",
            "department_id": "production",
            "is_setup": False,
            "position": 2,
        },
        {
            "pattern_id": pattern_id,
            "name": "Quality Check",
            "department_id": "quality",
            "is_setup": False,
            "position": 3,
        },
        {
            "pattern_id": pattern_id,
            "name": "Final Packaging",
            "department_id": "packaging",
            "is_setup": False,
            "position": 4,
        },
    ]

    tasks_response = supabase.table("optimized_tasks").insert(optimized_tasks).execute()
    task_ids = {task["name"]: task["optimized_task_id"] for task in tasks_response.data}

    # Get machine IDs
    machines_response = (
        supabase.table("test_resources")
        .select("resource_id, name")
        .eq("resource_type", "machine")
        .execute()
    )

    machine_lookup = {
        machine["name"]: machine["resource_id"] for machine in machines_response.data
    }

    # Define task modes for assembly
    task_modes = []

    # Assembly modes (using manual station primarily)
    for task_name, machine_name, duration in [
        ("Assembly Setup", "Manual Assembly Station", 10),
        ("Component Assembly", "Manual Assembly Station", 60),
        ("Quality Check", "Quality Control Station", 15),
        ("Final Packaging", "Packaging Station", 10),
    ]:
        if machine_name in machine_lookup:
            task_modes.append(
                {
                    "optimized_task_id": task_ids[task_name],
                    "machine_resource_id": machine_lookup[machine_name],
                    "duration_minutes": duration,
                    "mode_name": f"{task_name.lower().replace(' ', '_')}",
                }
            )

    if task_modes:
        supabase.table("optimized_task_modes").insert(task_modes).execute()
        print(f"Created {len(task_modes)} task modes for assembly pattern")

    # Define precedences
    precedences = [
        (task_ids["Assembly Setup"], task_ids["Component Assembly"]),
        (task_ids["Component Assembly"], task_ids["Quality Check"]),
        (task_ids["Quality Check"], task_ids["Final Packaging"]),
    ]

    precedence_data = []
    for pred_id, succ_id in precedences:
        precedence_data.append(
            {
                "pattern_id": pattern_id,
                "predecessor_optimized_task_id": pred_id,
                "successor_optimized_task_id": succ_id,
            }
        )

    supabase.table("optimized_precedences").insert(precedence_data).execute()
    print(f"Created {len(precedence_data)} precedence constraints for assembly pattern")

    return pattern_id


def create_job_instances(
    supabase: Client, pattern_id: str, count: int, base_description: str
) -> list[str]:
    """Create job instances for an optimized pattern."""
    now = datetime.now()
    base_due_date = now + timedelta(hours=24)  # Start 24 hours from now

    instances = []
    for i in range(count):
        due_date = base_due_date + timedelta(hours=2 * i)  # 2 hours apart
        instances.append(
            {
                "pattern_id": pattern_id,
                "description": f"{base_description} {i + 1:03d}",
                "due_date": due_date.isoformat(),
                "status": "scheduled",
                "priority": 100 + (i % 50),  # Vary priority slightly
                "customer_id": f"CUST_{(i % 5) + 1:03d}",  # 5 different customers
                "order_number": f"ORD_{pattern_id[:8]}_{i + 1:04d}",
            }
        )

    response = supabase.table("job_instances").insert(instances).execute()
    instance_ids = [row["instance_id"] for row in response.data]

    print(f"Created {len(instance_ids)} instances for pattern {pattern_id}")
    return instance_ids


def main():
    """Run main population script."""
    print("Populating optimized pattern test data...")

    supabase = setup_database_connection()

    try:
        # Check if patterns already exist
        existing_patterns = (
            supabase.table("job_optimized_patterns").select("name").execute()
        )
        if existing_patterns.data:
            print(f"Found {len(existing_patterns.data)} existing patterns:")
            for pattern in existing_patterns.data:
                print(f"  - {pattern['name']}")

            response = input("Clear existing patterns and recreate? (y/N): ")
            if response.lower() == "y":
                # Clear existing data
                supabase.table("instance_task_assignments").delete().neq(
                    "assignment_id", ""
                ).execute()
                supabase.table("job_instances").delete().neq(
                    "instance_id", ""
                ).execute()
                supabase.table("optimized_precedences").delete().neq(
                    "pattern_id", ""
                ).execute()
                supabase.table("optimized_task_modes").delete().neq(
                    "optimized_task_mode_id", ""
                ).execute()
                supabase.table("optimized_tasks").delete().neq(
                    "optimized_task_id", ""
                ).execute()
                supabase.table("job_optimized_patterns").delete().neq(
                    "pattern_id", ""
                ).execute()
                print("Cleared existing pattern data")
            else:
                print("Keeping existing patterns")
                return

        # Create patterns
        manufacturing_pattern_id = create_manufacturing_pattern(supabase)
        assembly_pattern_id = create_assembly_pattern(supabase)

        # Create job instances
        print("\nCreating job instances...")

        # Manufacturing jobs - create different sized batches for testing
        create_job_instances(
            supabase, manufacturing_pattern_id, 5, "Manufacturing Job"
        )  # Small batch
        create_job_instances(
            supabase, manufacturing_pattern_id, 15, "Production Run"
        )  # Medium batch

        # Assembly jobs
        create_job_instances(supabase, assembly_pattern_id, 8, "Assembly Job")

        print("\n" + "=" * 60)
        print("Optimized pattern test data population completed successfully!")
        print("=" * 60)

        # Verify data
        patterns = (
            supabase.table("job_optimized_patterns")
            .select("name, task_count")
            .execute()
        )
        instances = supabase.table("job_instances").select("pattern_id").execute()

        print(f"\nCreated {len(patterns.data)} patterns:")
        for pattern in patterns.data:
            print(f"  - {pattern['name']}: {pattern['task_count']} tasks")

        print(f"Created {len(instances.data)} total job instances")

        # Test loading
        print("\nTesting pattern loading...")
        loader = OptimizedDatabaseLoader()
        available_patterns = loader.load_available_patterns()

        print(f"Successfully loaded {len(available_patterns)} patterns:")
        for pattern in available_patterns:
            print(
                f"  - {pattern.name}: {pattern.task_count} tasks, "
                f"{len(pattern.optimized_precedences)} precedences"
            )

        # Test problem loading
        if available_patterns:
            test_pattern = available_patterns[0]
            problem = loader.load_optimized_problem(
                test_pattern.optimized_pattern_id, max_instances=3
            )
            print(
                f"\nTest problem loaded: {len(problem.jobs)} jobs, "
                f"{problem.total_task_count} tasks"
            )

        print("\nOptimized pattern system ready for use!")

    except Exception as e:
        print(f"Error during population: {e}")
        raise


if __name__ == "__main__":
    main()
