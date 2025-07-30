#!/usr/bin/env python3
"""Populate template-based test data for Fresh OR-Tools solver.

Week 3 Implementation: Creates realistic template-based test data
for performance testing and development.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from supabase import Client, create_client

from src.data.loaders.template_database import TemplateDatabaseLoader


def setup_database_connection() -> Client:
    """Setup Supabase connection."""
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    return create_client(url, key)


def create_manufacturing_template(supabase: Client) -> str:
    """Create the standard manufacturing job template."""
    # Insert job template
    template_data = {
        "name": "Standard Manufacturing Job",
        "description": "Complete manufacturing process from setup to packaging",
        "task_count": 7,  # Will be updated by trigger
        "total_min_duration_minutes": 0,  # Will be calculated by trigger
        "critical_path_length_minutes": 0,  # Will be calculated by trigger
    }

    template_response = supabase.table("job_templates").insert(template_data).execute()
    template_id = template_response.data[0]["template_id"]

    print(f"Created manufacturing template: {template_id}")

    # Define template tasks
    template_tasks = [
        {
            "template_id": template_id,
            "name": "Machine Setup",
            "department_id": "production",
            "is_setup": True,
            "position": 1,
        },
        {
            "template_id": template_id,
            "name": "Load Raw Material",
            "department_id": "production",
            "is_setup": False,
            "position": 2,
        },
        {
            "template_id": template_id,
            "name": "Primary Manufacturing Operation",
            "department_id": "production",
            "is_setup": False,
            "position": 3,
        },
        {
            "template_id": template_id,
            "name": "Secondary Manufacturing Operation",
            "department_id": "production",
            "is_setup": False,
            "position": 4,
        },
        {
            "template_id": template_id,
            "name": "Quality Control Inspection",
            "department_id": "quality",
            "is_setup": False,
            "position": 5,
        },
        {
            "template_id": template_id,
            "name": "Package Finished Product",
            "department_id": "packaging",
            "is_setup": False,
            "position": 6,
        },
        {
            "template_id": template_id,
            "name": "Machine Cleanup",
            "department_id": "production",
            "is_setup": True,
            "position": 7,
        },
    ]

    tasks_response = supabase.table("template_tasks").insert(template_tasks).execute()
    task_ids = {task["name"]: task["template_task_id"] for task in tasks_response.data}

    print(f"Created {len(task_ids)} template tasks")

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
        return template_id

    # Define task modes (machine + duration combinations)
    task_modes = []

    # Machine Setup modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Machine Setup"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 30,
                "mode_name": "setup_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Machine Setup"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 45,
                "mode_name": "setup_cnc2",
            }
        )

    # Load Material modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Load Raw Material"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 15,
                "mode_name": "load_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Load Raw Material"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 20,
                "mode_name": "load_cnc2",
            }
        )

    # Primary Operation modes
    if "CNC Machine #1" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #1"],
                "duration_minutes": 90,
                "mode_name": "primary_cnc1",
            }
        )
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 75,
                "mode_name": "primary_cnc2",
            }
        )
    if "Manual Assembly Station" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Primary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["Manual Assembly Station"],
                "duration_minutes": 120,
                "mode_name": "primary_manual",
            }
        )

    # Secondary Operation modes
    if "CNC Machine #2" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Secondary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["CNC Machine #2"],
                "duration_minutes": 60,
                "mode_name": "secondary_cnc2",
            }
        )
    if "Manual Assembly Station" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Secondary Manufacturing Operation"],
                "machine_resource_id": machine_lookup["Manual Assembly Station"],
                "duration_minutes": 45,
                "mode_name": "secondary_manual",
            }
        )

    # Quality Control modes
    if "Quality Control Station" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Quality Control Inspection"],
                "machine_resource_id": machine_lookup["Quality Control Station"],
                "duration_minutes": 30,
                "mode_name": "qc_station",
            }
        )

    # Packaging modes
    if "Packaging Station" in machine_lookup:
        task_modes.append(
            {
                "template_task_id": task_ids["Package Finished Product"],
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
                    "template_task_id": task_ids["Machine Cleanup"],
                    "machine_resource_id": machine_lookup[machine_name],
                    "duration_minutes": duration,
                    "mode_name": f"cleanup_{machine_name.lower().replace(' ', '_').replace('#', '')}",
                }
            )

    if task_modes:
        supabase.table("template_task_modes").insert(task_modes).execute()
        print(f"Created {len(task_modes)} task modes")
    else:
        print("WARNING: No task modes created. Check machine names in test_resources.")

    # Define template precedences (linear workflow)
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
                "template_id": template_id,
                "predecessor_template_task_id": pred_id,
                "successor_template_task_id": succ_id,
                "lag_minutes": 0,
            }
        )

    supabase.table("template_precedences").insert(precedence_data).execute()
    print(f"Created {len(precedence_data)} precedence constraints")

    return template_id


def create_assembly_template(supabase: Client) -> str:
    """Create a simpler assembly job template for variety."""
    template_data = {
        "name": "Simple Assembly Job",
        "description": "Basic assembly process with minimal setup",
        "task_count": 4,
    }

    template_response = supabase.table("job_templates").insert(template_data).execute()
    template_id = template_response.data[0]["template_id"]

    print(f"Created assembly template: {template_id}")

    # Define simpler template tasks
    template_tasks = [
        {
            "template_id": template_id,
            "name": "Assembly Setup",
            "department_id": "production",
            "is_setup": True,
            "position": 1,
        },
        {
            "template_id": template_id,
            "name": "Component Assembly",
            "department_id": "production",
            "is_setup": False,
            "position": 2,
        },
        {
            "template_id": template_id,
            "name": "Quality Check",
            "department_id": "quality",
            "is_setup": False,
            "position": 3,
        },
        {
            "template_id": template_id,
            "name": "Final Packaging",
            "department_id": "packaging",
            "is_setup": False,
            "position": 4,
        },
    ]

    tasks_response = supabase.table("template_tasks").insert(template_tasks).execute()
    task_ids = {task["name"]: task["template_task_id"] for task in tasks_response.data}

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
                    "template_task_id": task_ids[task_name],
                    "machine_resource_id": machine_lookup[machine_name],
                    "duration_minutes": duration,
                    "mode_name": f"{task_name.lower().replace(' ', '_')}",
                }
            )

    if task_modes:
        supabase.table("template_task_modes").insert(task_modes).execute()
        print(f"Created {len(task_modes)} task modes for assembly template")

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
                "template_id": template_id,
                "predecessor_template_task_id": pred_id,
                "successor_template_task_id": succ_id,
                "lag_minutes": 0,
            }
        )

    supabase.table("template_precedences").insert(precedence_data).execute()
    print(
        f"Created {len(precedence_data)} precedence constraints for assembly template"
    )

    return template_id


def create_job_instances(
    supabase: Client, template_id: str, count: int, base_description: str
) -> list[str]:
    """Create job instances for a template."""
    now = datetime.now()
    base_due_date = now + timedelta(hours=24)  # Start 24 hours from now

    instances = []
    for i in range(count):
        due_date = base_due_date + timedelta(hours=2 * i)  # 2 hours apart
        instances.append(
            {
                "template_id": template_id,
                "description": f"{base_description} {i + 1:03d}",
                "due_date": due_date.isoformat(),
                "status": "scheduled",
                "priority": 100 + (i % 50),  # Vary priority slightly
                "customer_id": f"CUST_{(i % 5) + 1:03d}",  # 5 different customers
                "order_number": f"ORD_{template_id[:8]}_{i + 1:04d}",
            }
        )

    response = supabase.table("job_instances").insert(instances).execute()
    instance_ids = [row["instance_id"] for row in response.data]

    print(f"Created {len(instance_ids)} instances for template {template_id}")
    return instance_ids


def populate_template_statistics(supabase: Client, template_id: str):
    """Populate template statistics for optimization."""
    # Get template info
    template_response = (
        supabase.table("job_templates")
        .select("*")
        .eq("template_id", template_id)
        .execute()
    )

    if not template_response.data:
        return

    template = template_response.data[0]

    # Create sample statistics
    stats_data = {
        "template_id": template_id,
        "variable_density": 2.5,  # Variables per constraint ratio
        "constraint_complexity": 1.8,  # Average constraint complexity
        "parallelism_factor": 0.6,  # 60% of tasks can be parallel
        "longest_chain_length": template["task_count"],  # Assuming linear chain
        "bottleneck_machine_count": 2,  # Estimated bottlenecks
        "last_solve_time_ms": None,  # Will be updated after solving
        "typical_instances_solved": 10,  # Typical problem size
    }

    # Upsert statistics
    existing = (
        supabase.table("template_statistics")
        .select("template_id")
        .eq("template_id", template_id)
        .execute()
    )

    if existing.data:
        supabase.table("template_statistics").update(stats_data).eq(
            "template_id", template_id
        ).execute()
    else:
        supabase.table("template_statistics").insert(stats_data).execute()

    print(f"Updated statistics for template {template_id}")


def main():
    """Main population script."""
    print("Populating template-based test data...")

    supabase = setup_database_connection()

    try:
        # Check if templates already exist
        existing_templates = supabase.table("job_templates").select("name").execute()
        if existing_templates.data:
            print(f"Found {len(existing_templates.data)} existing templates:")
            for template in existing_templates.data:
                print(f"  - {template['name']}")

            response = input("Clear existing templates and recreate? (y/N): ")
            if response.lower() == "y":
                # Clear existing data
                supabase.table("instance_task_assignments").delete().neq(
                    "assignment_id", ""
                ).execute()
                supabase.table("job_instances").delete().neq(
                    "instance_id", ""
                ).execute()
                supabase.table("template_statistics").delete().neq(
                    "template_id", ""
                ).execute()
                supabase.table("template_machine_requirements").delete().neq(
                    "template_id", ""
                ).execute()
                supabase.table("template_precedences").delete().neq(
                    "template_id", ""
                ).execute()
                supabase.table("template_task_modes").delete().neq(
                    "template_task_mode_id", ""
                ).execute()
                supabase.table("template_tasks").delete().neq(
                    "template_task_id", ""
                ).execute()
                supabase.table("job_templates").delete().neq(
                    "template_id", ""
                ).execute()
                print("Cleared existing template data")
            else:
                print("Keeping existing templates")
                return

        # Create templates
        manufacturing_template_id = create_manufacturing_template(supabase)
        assembly_template_id = create_assembly_template(supabase)

        # Create job instances
        print("\nCreating job instances...")

        # Manufacturing jobs - create different sized batches for testing
        create_job_instances(
            supabase, manufacturing_template_id, 5, "Manufacturing Job"
        )  # Small batch
        create_job_instances(
            supabase, manufacturing_template_id, 15, "Production Run"
        )  # Medium batch

        # Assembly jobs
        create_job_instances(supabase, assembly_template_id, 8, "Assembly Job")

        # Populate statistics
        print("\nPopulating template statistics...")
        populate_template_statistics(supabase, manufacturing_template_id)
        populate_template_statistics(supabase, assembly_template_id)

        print("\n" + "=" * 60)
        print("Template test data population completed successfully!")
        print("=" * 60)

        # Verify data
        templates = supabase.table("job_templates").select("name, task_count").execute()
        instances = supabase.table("job_instances").select("template_id").execute()

        print(f"\nCreated {len(templates.data)} templates:")
        for template in templates.data:
            print(f"  - {template['name']}: {template['task_count']} tasks")

        print(f"Created {len(instances.data)} total job instances")

        # Test loading
        print("\nTesting template loading...")
        loader = TemplateDatabaseLoader()
        available_templates = loader.load_available_templates()

        print(f"Successfully loaded {len(available_templates)} templates:")
        for template in available_templates:
            print(
                f"  - {template.name}: {template.task_count} tasks, {len(template.template_precedences)} precedences"
            )

        # Test problem loading
        if available_templates:
            test_template = available_templates[0]
            problem = loader.load_template_problem(
                test_template.template_id, max_instances=3
            )
            print(
                f"\nTest problem loaded: {len(problem.jobs)} jobs, {problem.total_task_count} tasks"
            )

        print("\nTemplate system ready for use!")

    except Exception as e:
        print(f"Error during population: {e}")
        raise


if __name__ == "__main__":
    main()
