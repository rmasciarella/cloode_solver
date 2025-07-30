"""Schedule exporter for visualizing scheduling solutions.

This module provides functionality to export scheduling solutions
to various formats suitable for visualization, including JSON and CSV.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.solver.models.problem import SchedulingProblem


@dataclass
class TaskVisualization:
    """Task data prepared for visualization."""

    id: str
    job_id: str
    name: str
    machine: str
    start: int
    end: int
    duration: int
    color: str
    lane: int = 0  # For stacking on high-capacity machines


@dataclass
class MachineVisualization:
    """Machine data prepared for visualization."""

    id: str
    name: str
    capacity: int
    cell_id: str
    utilization: float = 0.0


@dataclass
class SetupVisualization:
    """Setup time data prepared for visualization."""

    from_task: str
    to_task: str
    machine: str
    start: int
    end: int
    duration: int
    color: str = "#808080"  # Gray color for setup times


@dataclass
class ScheduleVisualization:
    """Complete schedule data for visualization."""

    tasks: list[TaskVisualization]
    machines: list[MachineVisualization]
    metadata: dict[str, Any]
    capacity_warnings: list[dict[str, Any]]
    setups: list[SetupVisualization] = field(default_factory=list)


class ScheduleExporter:
    """Export scheduling solutions to various formats for visualization."""

    def __init__(self, problem: SchedulingProblem, solution: dict[str, Any]):
        """Initialize the schedule exporter.

        Args:
            problem: The scheduling problem
            solution: The solution dictionary from extract_solution

        """
        self.problem = problem
        self.solution = solution
        self.color_palette = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#FFA07A",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
            "#85C1E2",
            "#F8B7D3",
            "#82E0AA",
            "#F8C471",
            "#AED6F1",
            "#D7BDE2",
            "#A9DFBF",
            "#FAD7A0",
        ]

    def to_dict(self) -> dict[str, Any]:
        """Export schedule as a dictionary.

        Returns:
            Dictionary representation of the schedule

        """
        visualization = self._create_visualization()

        result = {
            "tasks": [asdict(task) for task in visualization.tasks],
            "machines": [asdict(machine) for machine in visualization.machines],
            "metadata": visualization.metadata,
            "capacity_warnings": visualization.capacity_warnings,
        }

        if visualization.setups:
            result["setups"] = [asdict(setup) for setup in visualization.setups]

        return result

    def to_json(self, indent: int | None = None) -> str:
        """Export schedule to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation of the schedule

        """
        return json.dumps(self.to_dict(), indent=indent)

    def to_file(self, output_path: Path, format: str = "json") -> None:
        """Export schedule to file.

        Args:
            output_path: Path to save the file
            format: Export format (currently only 'json' supported)

        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, "w") as f:
                f.write(self.to_json(indent=2))
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _create_visualization(self) -> ScheduleVisualization:
        """Create visualization data from solution.

        Returns:
            ScheduleVisualization object with all data prepared for rendering

        """
        tasks = []
        machines = []
        capacity_warnings: list[dict[str, Any]] = []

        # Extract schedule from solution
        schedule_list = self.solution.get("schedule", [])

        # Convert list to dict format if needed
        schedule = {}
        if isinstance(schedule_list, list):
            for item in schedule_list:
                task_id = item.get("task_id")
                if task_id:
                    schedule[task_id] = {
                        "job_id": item.get("job_id"),
                        "start": item.get("start_time", 0),
                        "end": item.get("end_time", 0),
                        "machine": item.get("machine_id", "unknown"),
                    }
        else:
            schedule = schedule_list

        # Create job color mapping
        job_colors = {}
        for color_index, job in enumerate(self.problem.jobs):
            job_colors[job.job_id] = self.color_palette[
                color_index % len(self.color_palette)
            ]

        # Process machines
        machine_dict = {m.resource_id: m for m in self.problem.machines}
        for machine in self.problem.machines:
            machines.append(
                MachineVisualization(
                    id=machine.resource_id,
                    name=machine.name,
                    capacity=machine.capacity,
                    cell_id=machine.cell_id,
                )
            )

        # Process tasks
        for task_key, task_info in schedule.items():
            # Extract task details
            if isinstance(task_key, tuple):
                job_id, task_id = task_key
            else:
                # Handle string keys - task_key is the task_id
                task_id = task_key
                # Get job_id from the task_info if available
                job_id = task_info.get("job_id")
                if not job_id:
                    # Find job_id from problem data
                    job_id = None
                    for job in self.problem.jobs:
                        for task in job.tasks:
                            if task.task_id == task_id:
                                job_id = job.job_id
                                break
                        if job_id:
                            break
                    if not job_id:
                        continue

            # Get task name from problem data
            task_name = task_id
            for job in self.problem.jobs:
                for task in job.tasks:
                    if task.task_id == task_id:
                        task_name = task.name
                        break

            # Store task data for lane assignment later
            machine_id = task_info["machine"]
            start = task_info["start"]
            end = task_info["end"]

            tasks.append(
                TaskVisualization(
                    id=task_id,
                    job_id=job_id or "unknown",
                    name=task_name,
                    machine=machine_id,
                    start=start,
                    end=end,
                    duration=end - start,
                    color=job_colors.get(job_id, "#999999"),
                    lane=0,  # Will be assigned later
                )
            )

        # Assign lanes to tasks for better visualization of concurrent execution
        self._assign_lanes_to_tasks(tasks, machine_dict)

        # Group tasks by machine for capacity checking
        tasks_by_machine: dict[str, list[TaskVisualization]] = {}
        task_viz: TaskVisualization
        for task_viz in tasks:
            if task_viz.machine not in tasks_by_machine:
                tasks_by_machine[task_viz.machine] = []
            tasks_by_machine[task_viz.machine].append(task_viz)

        # Check for capacity violations by analyzing concurrent tasks
        capacity_warnings = []
        for machine_id, machine_tasks in tasks_by_machine.items():
            if machine_id in machine_dict:
                capacity = machine_dict[machine_id].capacity

                # Find all unique time points
                time_points = set()
                task_viz2: TaskVisualization
                for task_viz2 in machine_tasks:
                    time_points.add(task_viz2.start)
                    time_points.add(task_viz2.end)

                # Check concurrent tasks at each time point
                for t in sorted(time_points):
                    concurrent_tasks = []
                    task_viz3: TaskVisualization
                    for task_viz3 in machine_tasks:
                        if task_viz3.start <= t < task_viz3.end:
                            concurrent_tasks.append(task_viz3)

                    if len(concurrent_tasks) > capacity:
                        capacity_warnings.append(
                            {
                                "machine": machine_id,
                                "time": t,
                                "capacity": capacity,
                                "concurrent": len(concurrent_tasks),
                                "tasks": [task_viz.id for task_viz in concurrent_tasks],
                            }
                        )

        # Calculate machine utilization
        makespan = self.solution.get("objective", 100)
        for i, machine_viz in enumerate(machines):
            total_task_time = sum(
                task_viz.duration
                for task_viz in tasks
                if task_viz.machine == machine_viz.id
            )
            if makespan > 0 and machine_viz.capacity > 0:
                machine_viz.utilization = (
                    total_task_time / (makespan * machine_viz.capacity)
                ) * 100
            machines[i] = machine_viz

        # Create metadata
        metadata = {
            "solution_status": self.solution.get("status", "UNKNOWN"),
            "makespan": makespan,
            "solve_time": self.solution.get("solve_time", 0),
            "total_jobs": len(self.problem.jobs),
            "total_tasks": sum(len(job.tasks) for job in self.problem.jobs),
            "total_machines": len(self.problem.machines),
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "machine_utilization": {
                    machine_viz.id: machine_viz.utilization for machine_viz in machines
                },
                "max_concurrent_per_machine": self._calculate_max_concurrent(
                    tasks_by_machine
                ),
            },
        }

        # Add setup time metrics if available
        if "setup_time_metrics" in self.solution:
            metadata["setup_time_metrics"] = self.solution["setup_time_metrics"]

        # Create setup visualizations if setup times are present
        setups: list[SetupVisualization] = []
        if "setup_time_metrics" in self.solution:
            setup_instances = self.solution["setup_time_metrics"].get(
                "setup_instances", []
            )
            for setup in setup_instances:
                setups.append(
                    SetupVisualization(
                        from_task=setup["from_task"],
                        to_task=setup["to_task"],
                        machine=setup["machine"],
                        start=setup["start_time"],
                        end=setup["end_time"],
                        duration=setup["setup_time"],
                    )
                )

        return ScheduleVisualization(
            tasks=tasks,
            machines=machines,
            metadata=metadata,
            capacity_warnings=capacity_warnings,
            setups=setups,
        )

    def _assign_lanes_to_tasks(
        self, tasks: list[TaskVisualization], machine_dict: dict[str, Any]
    ) -> None:
        """Assign visual lanes to tasks for concurrent execution display.

        Args:
            tasks: List of task visualizations to assign lanes to
            machine_dict: Dictionary mapping machine IDs to machine objects

        """
        # Group tasks by machine
        tasks_by_machine: dict[str, list[TaskVisualization]] = {}
        for task in tasks:
            if task.machine not in tasks_by_machine:
                tasks_by_machine[task.machine] = []
            tasks_by_machine[task.machine].append(task)

        # Assign lanes for each machine
        for machine_id, machine_tasks in tasks_by_machine.items():
            # Sort tasks by start time
            machine_tasks.sort(key=lambda t: t.start)

            # Get machine capacity
            machine = machine_dict.get(machine_id)
            capacity = machine.capacity if machine else 1

            # Track occupied lanes: list of lists of (start, end) tuples
            lanes: list[list[tuple[int, int]]] = []

            for task in machine_tasks:
                # Find first available lane
                assigned_lane = None

                for lane_idx, lane_intervals in enumerate(lanes):
                    # Check if this task overlaps with any interval in this lane
                    can_use_lane = True
                    for interval_start, interval_end in lane_intervals:
                        if not (
                            task.end <= interval_start or task.start >= interval_end
                        ):
                            # Overlap found, can't use this lane
                            can_use_lane = False
                            break

                    if can_use_lane:
                        # This lane is free, use it
                        lane_intervals.append((task.start, task.end))
                        assigned_lane = lane_idx
                        break

                if assigned_lane is None:
                    # Need a new lane
                    if len(lanes) < capacity:
                        # Create new lane
                        lanes.append([(task.start, task.end)])
                        assigned_lane = len(lanes) - 1
                    else:
                        # Capacity exceeded, force into lane 0
                        assigned_lane = 0
                        # Note: capacity warnings are handled separately

                # Update task with assigned lane
                task.lane = assigned_lane

    def _calculate_max_concurrent(
        self, tasks_by_machine: dict[str, list[TaskVisualization]]
    ) -> dict[str, int]:
        """Calculate maximum concurrent tasks for each machine.

        Args:
            tasks_by_machine: Dictionary mapping machine IDs to lists of tasks

        Returns:
            Dictionary mapping machine IDs to max concurrent task count

        """
        max_concurrent = {}

        for machine_id, machine_tasks in tasks_by_machine.items():
            if not machine_tasks:
                max_concurrent[machine_id] = 0
                continue

            # Find all unique time points
            time_points = set()
            for task in machine_tasks:
                time_points.add(task.start)
                time_points.add(task.end)

            # Check concurrent tasks at each time point
            max_count = 0
            for t in sorted(time_points):
                concurrent_count = sum(
                    1 for task in machine_tasks if task.start <= t < task.end
                )
                max_count = max(max_count, concurrent_count)

            max_concurrent[machine_id] = max_count

        return max_concurrent
