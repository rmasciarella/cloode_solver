"""Unit tests for the visualization module."""

import json

import pytest

from src.solver.models.problem import (
    Job,
    Machine,
    Precedence,
    SchedulingProblem,
    Task,
    TaskMode,
)

# Import is already at the top
from src.visualization.schedule_exporter import (
    ScheduleExporter,
    TaskVisualization,
)


@pytest.fixture
def sample_problem():
    """Create a sample scheduling problem with high-capacity machines."""
    from datetime import UTC, datetime, timedelta

    machines = [
        Machine(resource_id="1", cell_id="cell1", name="Machine 1", capacity=1),
        Machine(
            resource_id="2", cell_id="cell1", name="Machine 2", capacity=3
        ),  # High capacity
    ]

    # Create task modes
    task_modes1 = [
        TaskMode(
            task_mode_id="tm1",
            task_id="1",
            machine_resource_id="1",
            duration_minutes=60,
        ),
    ]
    task_modes2 = [
        TaskMode(
            task_mode_id="tm2",
            task_id="2",
            machine_resource_id="2",
            duration_minutes=90,
        ),
    ]
    task_modes3 = [
        TaskMode(
            task_mode_id="tm3",
            task_id="3",
            machine_resource_id="2",
            duration_minutes=60,
        ),
    ]
    task_modes4 = [
        TaskMode(
            task_mode_id="tm4",
            task_id="4",
            machine_resource_id="2",
            duration_minutes=45,
        ),
    ]

    # Create tasks with modes
    tasks1 = [
        Task(task_id="1", job_id="1", name="Task 1", modes=task_modes1),
        Task(task_id="2", job_id="1", name="Task 2", modes=task_modes2),
    ]
    tasks2 = [
        Task(task_id="3", job_id="2", name="Task 3", modes=task_modes3),
        Task(task_id="4", job_id="2", name="Task 4", modes=task_modes4),
    ]

    jobs = [
        Job(
            job_id="1",
            description="Job A",
            due_date=datetime.now(UTC) + timedelta(hours=24),
            tasks=tasks1,
        ),
        Job(
            job_id="2",
            description="Job B",
            due_date=datetime.now(UTC) + timedelta(hours=24),
            tasks=tasks2,
        ),
    ]

    precedences = [
        Precedence(predecessor_task_id="1", successor_task_id="2"),
        Precedence(predecessor_task_id="3", successor_task_id="4"),
    ]

    return SchedulingProblem(
        jobs=jobs,
        machines=machines,
        work_cells=[],  # Empty list for work cells
        precedences=precedences,
    )


@pytest.fixture
def sample_solution():
    """Create a sample solution with concurrent tasks."""
    # ScheduleExporter expects a solution dictionary with a 'schedule' key
    return {
        "schedule": [
            {
                "task_id": "1",
                "job_id": "1",
                "machine_id": "1",
                "start_time": 0,
                "end_time": 4,
            },
            {
                "task_id": "2",
                "job_id": "1",
                "machine_id": "2",
                "start_time": 4,
                "end_time": 10,
            },
            {
                "task_id": "3",
                "job_id": "2",
                "machine_id": "2",
                "start_time": 5,
                "end_time": 9,
            },  # Concurrent with task 2
            {
                "task_id": "4",
                "job_id": "2",
                "machine_id": "2",
                "start_time": 9,
                "end_time": 12,
            },
        ],
        "objective": 12,  # makespan
        "solve_time": 0.5,
        "status": "OPTIMAL",
    }


def test_schedule_exporter_init(sample_problem, sample_solution):
    """Test ScheduleExporter initialization."""
    exporter = ScheduleExporter(sample_problem, sample_solution)
    assert len(exporter.color_palette) >= 10
    assert all(color.startswith("#") for color in exporter.color_palette)


def test_export_to_json(sample_problem, sample_solution, tmp_path):
    """Test JSON export functionality."""
    exporter = ScheduleExporter(sample_problem, sample_solution)

    # Export to string
    json_str = exporter.to_json()
    data = json.loads(json_str)

    # Check structure
    assert "tasks" in data
    assert "machines" in data
    assert "metadata" in data
    assert "capacity_warnings" in data

    # Check tasks
    assert len(data["tasks"]) == 4
    task1 = data["tasks"][0]
    assert task1["job_id"] == "1"
    assert task1["id"] == "1"  # 'id' not 'task_id' in TaskVisualization
    assert task1["machine"] == "1"  # 'machine' not 'machine_id'
    assert task1["start"] == 0  # 'start' not 'start_time'
    assert task1["end"] == 4  # 'end' not 'end_time'
    assert task1["duration"] == 4
    assert "color" in task1

    # Check machines
    assert len(data["machines"]) == 2
    machine2 = next(m for m in data["machines"] if m["id"] == "2")
    assert machine2["capacity"] == 3
    assert machine2["utilization"] > 0

    # Check metadata
    assert data["metadata"]["total_jobs"] == 2
    assert data["metadata"]["total_tasks"] == 4
    assert data["metadata"]["makespan"] == 12
    assert data["metadata"]["solve_time"] == 0.5

    # Export to file
    output_path = tmp_path / "test_schedule.json"
    exporter.to_file(output_path)
    assert output_path.exists()


def test_capacity_validation(sample_problem):
    """Test capacity validation warnings."""
    # Create solution that exceeds capacity on Machine 2 (capacity=3)
    solution = {
        "schedule": [
            {
                "task_id": "1",
                "job_id": "1",
                "machine_id": "2",
                "start_time": 0,
                "end_time": 4,
            },
            {
                "task_id": "2",
                "job_id": "1",
                "machine_id": "2",
                "start_time": 2,
                "end_time": 6,
            },
            {
                "task_id": "3",
                "job_id": "2",
                "machine_id": "2",
                "start_time": 3,
                "end_time": 7,
            },
            {
                "task_id": "4",
                "job_id": "2",
                "machine_id": "2",
                "start_time": 3,
                "end_time": 8,
            },  # 4 tasks at time 3-4, exceeds capacity
        ],
        "objective": 8,
        "solve_time": 0.1,
        "status": "OPTIMAL",
    }

    exporter = ScheduleExporter(sample_problem, solution)
    visualization = exporter._create_visualization()

    # Should have warnings
    assert len(visualization.capacity_warnings) > 0
    # Check that machine 2 appears in capacity warnings
    assert any(warning["machine"] == "2" for warning in visualization.capacity_warnings)


def test_task_visualization_creation(sample_problem, sample_solution):
    """Test TaskVisualization dataclass creation."""
    exporter = ScheduleExporter(sample_problem, sample_solution)
    visualization = exporter._create_visualization()

    # Check task visualizations
    assert len(visualization.tasks) == 4

    task1_viz = visualization.tasks[0]
    assert isinstance(task1_viz, TaskVisualization)
    # Check TaskVisualization attributes
    assert task1_viz.id == "1"
    assert task1_viz.name == "Task 1"
    assert task1_viz.machine == "1"
    assert task1_viz.job_id == "1"


def test_machine_stats_calculation(sample_problem, sample_solution):
    """Test machine utilization statistics."""
    exporter = ScheduleExporter(sample_problem, sample_solution)
    visualization = exporter._create_visualization()

    # Check machine stats
    assert len(visualization.machines) == 2

    machine1_stats = next(m for m in visualization.machines if m.id == "1")
    # Machine 1: task duration 4, makespan 12, capacity 1
    # Utilization = (4 / (12 * 1)) * 100 = 33.33%
    assert machine1_stats.utilization == pytest.approx(33.33, 0.1)

    machine2_stats = next(m for m in visualization.machines if m.id == "2")
    # Machine 2: task durations 6+4+3=13, makespan 12, capacity 3
    # Utilization = (13 / (12 * 3)) * 100 = 36.11%
    assert machine2_stats.utilization == pytest.approx(36.11, 0.1)


# CSV export test removed - not implemented in current version
# def test_export_to_csv(sample_problem, sample_solution, tmp_path):


def test_color_assignment(sample_problem, sample_solution):
    """Test that jobs get consistent colors."""
    exporter = ScheduleExporter(sample_problem, sample_solution)
    visualization = exporter._create_visualization()

    # Get colors for each job
    job1_colors = [t.color for t in visualization.tasks if t.job_id == "1"]
    job2_colors = [t.color for t in visualization.tasks if t.job_id == "2"]

    # All tasks from same job should have same color
    assert len(set(job1_colors)) == 1
    assert len(set(job2_colors)) == 1

    # Different jobs should have different colors
    assert job1_colors[0] != job2_colors[0]


def test_empty_solution(sample_problem):
    """Test handling of empty solution."""
    empty_solution = {
        "schedule": [],
        "objective": 0,
        "solve_time": 0.0,
        "status": "NO_SOLUTION",
    }

    exporter = ScheduleExporter(sample_problem, empty_solution)
    json_str = exporter.to_json()
    data = json.loads(json_str)

    assert len(data["tasks"]) == 0
    assert data["metadata"]["total_tasks"] == 4  # Total tasks in problem, not solution
    assert data["metadata"]["makespan"] == 0


def test_concurrent_task_detection(sample_problem, sample_solution):
    """Test that concurrent tasks are properly identified."""
    exporter = ScheduleExporter(sample_problem, sample_solution)
    visualization = exporter._create_visualization()

    # Tasks 2 and 3 are concurrent on machine 2 (time 5-9)
    task2 = next(t for t in visualization.tasks if t.id == "2")
    task3 = next(t for t in visualization.tasks if t.id == "3")

    # They overlap in time
    assert task2.start < task3.end
    assert task3.start < task2.end
    assert task2.machine == task3.machine == "2"
