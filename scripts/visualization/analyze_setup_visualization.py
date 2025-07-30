#!/usr/bin/env python3
"""Analyze the setup time visualization data to verify correctness."""

import json
from pathlib import Path


def analyze_visualization():
    """Analyze the schedule.json to verify visualization elements."""
    # Load the schedule data
    json_path = Path("output/setup_time_demo/schedule.json")
    with open(json_path) as f:
        data = json.load(f)

    print("=== Setup Time Visualization Analysis ===\n")

    # 1. Machine Information
    print("1. MACHINES:")
    for machine in data["machines"]:
        print(f"   - {machine['name']} (ID: {machine['id']})")
        print(f"     Capacity: {machine['capacity']}")
        print(f"     Utilization: {machine['utilization']}%")

    # 2. Task Schedule
    print("\n2. TASK SCHEDULE:")
    print("   Machine 1 (CNC Mill - capacity 1):")
    m1_tasks = [t for t in data["tasks"] if t["machine"] == "machine_1"]
    for task in sorted(m1_tasks, key=lambda x: x["start"]):
        print(
            f"     {task['name']}: {task['start']} -> {task['end']} "
            f"(lane {task['lane']})"
        )

    print("\n   Machine 2 (3D Printer - capacity 2):")
    m2_tasks = [t for t in data["tasks"] if t["machine"] == "machine_2"]
    for task in sorted(m2_tasks, key=lambda x: x["start"]):
        print(
            f"     {task['name']}: {task['start']} -> {task['end']} "
            f"(lane {task['lane']})"
        )

    # 3. Setup Times
    print("\n3. SETUP TIME BLOCKS (Gold blocks):")
    for setup in data["setups"]:
        print(f"   - From {setup['from_task']} to {setup['to_task']}")
        print(f"     Machine: {setup['machine']}")
        print(
            f"     Time: {setup['start']} -> {setup['end']} "
            f"(duration: {setup['duration']})"
        )

    # 4. Setup Metrics
    print("\n4. SETUP TIME STATISTICS:")
    metrics = data["metadata"]["setup_time_metrics"]
    print(
        f"   - Total Setup Time: {metrics['total_setup_time']} units "
        f"({metrics['total_setup_minutes']} min)"
    )
    print(f"   - Number of Setups: {metrics['num_setups']}")
    print(
        f"   - Average Setup Time: {metrics['average_setup_time']} units "
        f"({metrics['average_setup_minutes']} min)"
    )

    # 5. Concurrent Execution Check
    print("\n5. CONCURRENT EXECUTION CHECK:")
    print("   Checking for overlapping tasks on Machine 2 (capacity 2):")

    # Find overlapping tasks
    overlaps = []
    for i, t1 in enumerate(m2_tasks):
        for t2 in m2_tasks[i + 1 :]:
            if t1["start"] < t2["end"] and t2["start"] < t1["end"]:
                overlaps.append(
                    (
                        t1["name"],
                        t2["name"],
                        max(t1["start"], t2["start"]),
                        min(t1["end"], t2["end"]),
                    )
                )

    if overlaps:
        print("   ✓ Found concurrent tasks:")
        for t1, t2, start, end in overlaps:
            print(f"     - {t1} and {t2} overlap from time {start} to {end}")
    else:
        print("   ✗ No concurrent tasks found (unexpected!)")

    # 6. Visual Elements Expected
    print("\n6. EXPECTED VISUAL ELEMENTS:")
    print("   - Header: 'Schedule Visualization'")
    print("   - Metadata panel: Shows 4 jobs, 8 tasks, makespan 11 units, solve time")
    print("   - Gantt chart with:")
    print("     * 8 colored task rectangles")
    print("     * 2 gold setup time blocks")
    print("     * Tasks in lane 0 and lane 1 on Machine 2 (showing concurrency)")
    print("   - Machine stats panel (right side):")
    print("     * CNC Mill: 800% utilization (error in calculation)")
    print("     * 3D Printer: 600% utilization (error in calculation)")
    print("   - Setup stats panel (right side):")
    print("     * Total setup time: 2 units (30 minutes)")
    print("     * Number of setups: 2")
    print("     * Average setup time: 1.0 units (15.0 minutes)")
    print("     * Per-machine breakdown")

    # 7. Color Coding
    print("\n7. COLOR CODING:")
    jobs = {}
    for task in data["tasks"]:
        if task["job_id"] not in jobs:
            jobs[task["job_id"]] = task["color"]

    for job_id, color in sorted(jobs.items()):
        print(f"   - {job_id}: {color}")
    print("   - Setup blocks: #FFD700 (gold)")


if __name__ == "__main__":
    analyze_visualization()
