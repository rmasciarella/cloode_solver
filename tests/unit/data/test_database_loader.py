"""Unit tests for DatabaseLoader."""

import os
from datetime import UTC
from unittest.mock import MagicMock, patch

import pytest

from src.data.loaders.database import DatabaseLoader, load_test_problem
from src.solver.models.problem import (
    SchedulingProblem,
)


class TestDatabaseLoader:
    """Test DatabaseLoader class."""

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_init_with_test_tables(self, mock_create_client):
        """Test initialization with test tables."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        loader = DatabaseLoader(use_test_tables=True)

        assert loader.supabase == mock_client
        assert loader.table_prefix == "test_"
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co", "test_key"
        )

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://prod.supabase.co", "SUPABASE_ANON_KEY": "prod_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_init_with_production_tables(self, mock_create_client):
        """Test initialization with production tables."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        loader = DatabaseLoader(use_test_tables=False)

        assert loader.table_prefix == ""

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.data.loaders.database.load_dotenv")
    def test_init_missing_env_vars(self, mock_load_dotenv):
        """Test initialization fails with missing environment variables."""
        # Ensure load_dotenv doesn't load anything
        mock_load_dotenv.return_value = None

        with pytest.raises(
            ValueError, match="SUPABASE_URL and SUPABASE_ANON_KEY must be set"
        ):
            DatabaseLoader()

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_work_cells(self, mock_create_client):
        """Test loading work cells from database."""
        # Mock Supabase client
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {"cell_id": "cell1", "name": "Cell 1", "capacity": 2},
            {"cell_id": "cell2", "name": "Cell 2", "capacity": 1},
        ]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        loader = DatabaseLoader()
        cells = loader._load_work_cells()

        assert len(cells) == 2
        assert cells[0].cell_id == "cell1"
        assert cells[0].name == "Cell 1"
        assert cells[0].capacity == 2
        assert cells[1].cell_id == "cell2"

        mock_client.table.assert_called_with("test_work_cells")

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_machines(self, mock_create_client):
        """Test loading machines from database."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "resource_id": "m1",
                "cell_id": "cell1",
                "name": "Machine 1",
                "capacity": 1,
                "cost_per_hour": "50.5",
                "resource_type": "machine",
            }
        ]
        mock_eq = mock_client.table.return_value.select.return_value.eq
        mock_eq.return_value.execute.return_value = mock_response

        loader = DatabaseLoader()
        machines = loader._load_machines()

        assert len(machines) == 1
        assert machines[0].resource_id == "m1"
        assert machines[0].cell_id == "cell1"
        assert machines[0].cost_per_hour == 50.5

        mock_eq.assert_called_with("resource_type", "machine")

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_jobs(self, mock_create_client):
        """Test loading jobs from database."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "job_id": "j1",
                "description": "Test Job",
                "due_date": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        ]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        loader = DatabaseLoader()
        jobs = loader._load_jobs()

        assert len(jobs) == 1
        assert jobs[0].job_id == "j1"
        assert jobs[0].description == "Test Job"
        assert jobs[0].due_date.tzinfo == UTC

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_tasks(self, mock_create_client):
        """Test loading tasks from database."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "task_id": "t1",
                "job_id": "j1",
                "name": "Task 1",
                "department_id": "dept1",
                "is_unattended": True,
                "is_setup": False,
            }
        ]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        loader = DatabaseLoader()
        tasks = loader._load_tasks()

        assert len(tasks) == 1
        assert tasks[0].task_id == "t1"
        assert tasks[0].is_unattended
        assert not tasks[0].is_setup

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_task_modes(self, mock_create_client):
        """Test loading task modes from database."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "task_mode_id": "tm1",
                "task_id": "t1",
                "machine_resource_id": "m1",
                "duration_minutes": 60,
            }
        ]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        loader = DatabaseLoader()
        modes = loader._load_task_modes()

        assert len(modes) == 1
        assert modes[0].task_mode_id == "tm1"
        assert modes[0].duration_minutes == 60
        assert modes[0].duration_time_units == 4  # 60 minutes = 4 time units

    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.database.create_client")
    def test_load_precedences(self, mock_create_client):
        """Test loading precedences from database."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [{"predecessor_task_id": "t1", "successor_task_id": "t2"}]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        loader = DatabaseLoader()
        precedences = loader._load_precedences()

        assert len(precedences) == 1
        assert precedences[0].predecessor_task_id == "t1"
        assert precedences[0].successor_task_id == "t2"

    @patch("builtins.print")
    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.template_database.create_client")
    @patch("src.data.loaders.database.create_client")
    def test_load_problem_complete(
        self, mock_create_client, mock_template_create_client, _mock_print
    ):
        """Test loading complete problem with associations."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock template client to return empty templates (use legacy mode)
        mock_template_client = MagicMock()
        mock_template_create_client.return_value = mock_template_client
        mock_template_table = MagicMock()
        mock_template_client.table.return_value = mock_template_table
        mock_template_table.select.return_value = mock_template_table
        mock_template_table.limit.return_value = mock_template_table
        mock_template_table.execute.return_value = MagicMock(data=[])

        # Mock all table responses
        mock_table = mock_client.table

        # Work cells
        mock_cells_response = MagicMock()
        mock_cells_response.data = [
            {"cell_id": "cell1", "name": "Cell 1", "capacity": 2}
        ]

        # Machines
        mock_machines_response = MagicMock()
        mock_machines_response.data = [
            {
                "resource_id": "m1",
                "cell_id": "cell1",
                "name": "Machine 1",
                "capacity": 1,
                "cost_per_hour": "50",
                "resource_type": "machine",
            }
        ]

        # Jobs
        mock_jobs_response = MagicMock()
        mock_jobs_response.data = [
            {
                "job_id": "j1",
                "description": "Job 1",
                "due_date": "2024-01-01T12:00:00Z",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            }
        ]

        # Tasks
        mock_tasks_response = MagicMock()
        mock_tasks_response.data = [
            {
                "task_id": "t1",
                "job_id": "j1",
                "name": "Task 1",
                "department_id": None,
                "is_unattended": False,
                "is_setup": False,
            }
        ]

        # Task modes
        mock_modes_response = MagicMock()
        mock_modes_response.data = [
            {
                "task_mode_id": "tm1",
                "task_id": "t1",
                "machine_resource_id": "m1",
                "duration_minutes": 60,
            }
        ]

        # Precedences
        mock_precedences_response = MagicMock()
        mock_precedences_response.data = []

        # Set up mock chain for each table
        def mock_table_side_effect(table_name):
            mock_chain = MagicMock()
            if table_name == "test_work_cells":
                mock_chain.select.return_value.execute.return_value = (
                    mock_cells_response
                )
            elif table_name == "test_resources":
                mock_chain.select.return_value.eq.return_value.execute.return_value = (
                    mock_machines_response
                )
            elif table_name == "test_jobs":
                mock_chain.select.return_value.execute.return_value = mock_jobs_response
            elif table_name == "test_tasks":
                mock_chain.select.return_value.execute.return_value = (
                    mock_tasks_response
                )
            elif table_name == "test_task_modes":
                mock_chain.select.return_value.execute.return_value = (
                    mock_modes_response
                )
            elif table_name == "test_task_precedences":
                mock_chain.select.return_value.execute.return_value = (
                    mock_precedences_response
                )
            return mock_chain

        mock_table.side_effect = mock_table_side_effect

        loader = DatabaseLoader()
        problem = loader.load_problem()

        # Verify associations
        assert len(problem.jobs) == 1
        assert len(problem.jobs[0].tasks) == 1
        assert len(problem.jobs[0].tasks[0].modes) == 1
        assert len(problem.work_cells) == 1
        assert len(problem.work_cells[0].machines) == 1
        assert problem.total_task_count == 1

    @patch("src.data.loaders.database.logger")
    @patch.dict(
        os.environ,
        {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test_key"},
    )
    @patch("src.data.loaders.template_database.create_client")
    @patch("src.data.loaders.database.create_client")
    def test_load_problem_with_validation_issues(
        self, mock_create_client, mock_template_create_client, mock_logger
    ):
        """Test loading problem with validation issues."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock template client to return empty templates (use legacy mode)
        mock_template_client = MagicMock()
        mock_template_create_client.return_value = mock_template_client
        mock_template_table = MagicMock()
        mock_template_client.table.return_value = mock_template_table
        mock_template_table.select.return_value = mock_template_table
        mock_template_table.limit.return_value = mock_template_table
        mock_template_table.execute.return_value = MagicMock(data=[])

        # Set up minimal mock data that will cause validation issues
        mock_table = mock_client.table

        def mock_table_side_effect(table_name):
            mock_chain = MagicMock()
            mock_response = MagicMock()

            if table_name == "test_work_cells" or table_name == "test_resources":
                mock_response.data = []
            elif table_name == "test_jobs":
                mock_response.data = [
                    {
                        "job_id": "j1",
                        "description": None,  # Will use default
                        "due_date": "2024-01-01T12:00:00Z",
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-01T10:00:00Z",
                    }
                ]
            elif table_name == "test_tasks":
                mock_response.data = [
                    {
                        "task_id": "t1",
                        "job_id": "j1",
                        "name": "Task 1",
                        "department_id": None,
                        "is_unattended": False,
                        "is_setup": False,
                    }
                ]
            elif table_name == "test_task_modes":
                mock_response.data = []  # No modes - will cause validation issue
            elif table_name == "test_task_precedences":
                mock_response.data = []

            # Set up chain: table -> select -> execute
            mock_chain.select.return_value.execute.return_value = mock_response
            # For resources table, also handle: table -> select -> eq -> execute
            if hasattr(mock_chain.select.return_value, "eq"):
                mock_chain.select.return_value.eq.return_value.execute.return_value = (
                    mock_response
                )

            return mock_chain

        mock_table.side_effect = mock_table_side_effect

        loader = DatabaseLoader()
        problem = loader.load_problem()

        # Should still return a problem, but with issues printed
        assert problem is not None
        # Check that warning was logged
        mock_logger.warning.assert_any_call("Problem validation issues found:")


def test_load_test_problem():
    """Test convenience function for loading test problem."""
    with patch("src.data.loaders.database.DatabaseLoader") as mock_loader_class:
        mock_loader = MagicMock()
        mock_problem = MagicMock(spec=SchedulingProblem)
        mock_loader.load_problem.return_value = mock_problem
        mock_loader_class.return_value = mock_loader

        result = load_test_problem()

        assert result == mock_problem
        mock_loader_class.assert_called_once_with(use_test_tables=True)
        mock_loader.load_problem.assert_called_once()
