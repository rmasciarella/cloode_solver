"""Unit tests for database loader.

Tests data loading, conversion, and error handling with mocked Supabase.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.data.loaders.database import DatabaseLoader, load_test_problem


class TestDatabaseLoader:
    """Test DatabaseLoader class."""

    @patch("src.data.loaders.database.create_client")
    def test_loader_initialization_success(self, mock_create_client):
        """Test successful loader initialization."""
        # GIVEN: Environment variables are set
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Creating loader
            loader = DatabaseLoader(use_test_tables=True)

            # THEN: Client created with correct params
            mock_create_client.assert_called_once_with(
                "https://test.supabase.co", "test-key"
            )
            assert loader.table_prefix == "test_"

    @patch("src.data.loaders.database.load_dotenv")
    def test_loader_missing_env_vars(self, mock_load_dotenv):
        """Test that missing env vars raise error."""
        # GIVEN: Missing environment variables
        mock_load_dotenv.return_value = None  # Don't load from .env

        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(
                ValueError, match="SUPABASE_URL and SUPABASE_ANON_KEY must be set"
            ),
        ):
            # WHEN/THEN: Creating loader raises ValueError
            DatabaseLoader()

    @patch("src.data.loaders.database.create_client")
    def test_loader_production_tables(self, _mock_create_client):
        """Test loader uses production tables when specified."""
        # GIVEN: Environment variables set
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Creating loader with production tables
            loader = DatabaseLoader(use_test_tables=False)

            # THEN: No table prefix
            assert loader.table_prefix == ""

    @patch("src.data.loaders.database.create_client")
    def test_load_problem_success(self, mock_create_client):
        """Test successful problem loading."""
        # GIVEN: Mock Supabase responses
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Setup mock responses for each table
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        # Mock data responses
        mock_responses = {
            "test_work_cells": [{"cell_id": "c1", "name": "Cell 1", "capacity": 2}],
            "test_resources": [
                {
                    "resource_id": "m1",
                    "cell_id": "c1",
                    "name": "Machine 1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "10.0",
                }
            ],
            "test_jobs": [
                {
                    "job_id": "j1",
                    "description": "Job 1",
                    "due_date": "2024-01-15T10:00:00Z",
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-10T10:00:00Z",
                }
            ],
            "test_tasks": [
                {
                    "task_id": "t1",
                    "job_id": "j1",
                    "name": "Task 1",
                    "department_id": "d1",
                    "is_unattended": False,
                    "is_setup": False,
                }
            ],
            "test_task_modes": [
                {
                    "task_mode_id": "tm1",
                    "task_id": "t1",
                    "machine_resource_id": "m1",
                    "duration_minutes": 30,
                }
            ],
            "test_task_precedences": [
                {"predecessor_task_id": "t1", "successor_task_id": "t2"}
            ],
        }

        def mock_execute(*_args, **_kwargs):
            # Get the table name from the most recent table() call
            table_name = mock_client.table.call_args[0][0]
            return MagicMock(data=mock_responses.get(table_name, []))

        mock_table.execute.side_effect = mock_execute

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading problem
            loader = DatabaseLoader()
            problem = loader.load_problem()

            # THEN: Problem loaded correctly
            assert len(problem.jobs) == 1
            assert len(problem.machines) == 1
            assert len(problem.work_cells) == 1
            assert len(problem.precedences) == 1
            assert problem.jobs[0].job_id == "j1"

    @patch("src.data.loaders.database.create_client")
    def test_load_problem_empty_database(self, mock_create_client):
        """Test loading from empty database."""
        # GIVEN: Empty database responses
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading problem
            loader = DatabaseLoader()
            problem = loader.load_problem()

            # THEN: Empty problem created
            assert len(problem.jobs) == 0
            assert len(problem.machines) == 0
            assert problem.total_task_count == 0

    @patch("src.data.loaders.database.create_client")
    @patch("builtins.print")
    def test_load_problem_validation_warnings(self, mock_print, mock_create_client):
        """Test that validation warnings are printed."""
        # GIVEN: Data that will cause validation warnings
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        # Create task with no modes
        mock_responses = {
            "test_work_cells": [],
            "test_resources": [],
            "test_jobs": [
                {
                    "job_id": "j1",
                    "description": "Job 1",
                    "due_date": "2024-01-15T10:00:00Z",
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-10T10:00:00Z",
                }
            ],
            "test_tasks": [{"task_id": "t1", "job_id": "j1", "name": "Task 1"}],
            "test_task_modes": [],  # No modes for task
            "test_task_precedences": [],
        }

        def mock_execute(*_args, **_kwargs):
            table_name = mock_client.table.call_args[0][0]
            return MagicMock(data=mock_responses.get(table_name, []))

        mock_table.execute.side_effect = mock_execute

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading problem
            loader = DatabaseLoader()
            loader.load_problem()

            # THEN: Warning printed
            warning_printed = False
            all_prints = []

            for call in mock_print.call_args_list:
                if call[0]:  # Check if there are arguments
                    message = str(call[0][0])
                    all_prints.append(message)
                    if "WARNING" in message:
                        warning_printed = True

            # Debug: Show all print calls if assertion fails
            if not warning_printed:
                print(f"DEBUG: All print calls: {all_prints}")

            assert warning_printed, f"Expected WARNING but got: {all_prints}"

    @patch("src.data.loaders.database.create_client")
    def test_data_associations(self, mock_create_client):
        """Test that data associations are correctly built."""
        # GIVEN: Related data
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        mock_responses = {
            "test_work_cells": [{"cell_id": "c1", "name": "Cell 1", "capacity": 2}],
            "test_resources": [
                {
                    "resource_id": "m1",
                    "cell_id": "c1",
                    "name": "M1",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "10",
                },
                {
                    "resource_id": "m2",
                    "cell_id": "c1",
                    "name": "M2",
                    "resource_type": "machine",
                    "capacity": 1,
                    "cost_per_hour": "15",
                },
            ],
            "test_jobs": [
                {
                    "job_id": "j1",
                    "description": "Job 1",
                    "due_date": "2024-01-15T10:00:00Z",
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-10T10:00:00Z",
                }
            ],
            "test_tasks": [
                {"task_id": "t1", "job_id": "j1", "name": "Task 1"},
                {"task_id": "t2", "job_id": "j1", "name": "Task 2"},
            ],
            "test_task_modes": [
                {
                    "task_mode_id": "tm1",
                    "task_id": "t1",
                    "machine_resource_id": "m1",
                    "duration_minutes": 30,
                },
                {
                    "task_mode_id": "tm2",
                    "task_id": "t1",
                    "machine_resource_id": "m2",
                    "duration_minutes": 45,
                },
            ],
            "test_task_precedences": [],
        }

        def mock_execute(*_args, **_kwargs):
            table_name = mock_client.table.call_args[0][0]
            return MagicMock(data=mock_responses.get(table_name, []))

        mock_table.execute.side_effect = mock_execute

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading problem
            loader = DatabaseLoader()
            problem = loader.load_problem()

            # THEN: Associations are correct
            # Machines associated with cells
            assert len(problem.work_cells[0].machines) == 2

            # Tasks associated with jobs
            assert len(problem.jobs[0].tasks) == 2

            # Modes associated with tasks
            assert len(problem.jobs[0].tasks[0].modes) == 2
            assert problem.jobs[0].tasks[1].modes == []  # No modes for t2

    @patch("src.data.loaders.database.create_client")
    def test_timezone_handling(self, mock_create_client):
        """Test that datetimes are properly converted to timezone-aware."""
        # GIVEN: Date strings from database
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table

        mock_responses = {
            "test_work_cells": [],
            "test_resources": [],
            "test_jobs": [
                {
                    "job_id": "j1",
                    "description": "Job 1",
                    "due_date": "2024-01-15T10:00:00Z",
                    "created_at": "2024-01-10T10:00:00Z",
                    "updated_at": "2024-01-10T10:00:00Z",
                }
            ],
            "test_tasks": [],
            "test_task_modes": [],
            "test_task_precedences": [],
        }

        def mock_execute(*_args, **_kwargs):
            table_name = mock_client.table.call_args[0][0]
            return MagicMock(data=mock_responses.get(table_name, []))

        mock_table.execute.side_effect = mock_execute

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_ANON_KEY": "test-key",
            },
        ):
            # WHEN: Loading problem
            loader = DatabaseLoader()
            problem = loader.load_problem()

            # THEN: Dates are timezone-aware
            job = problem.jobs[0]
            assert job.due_date.tzinfo is not None
            assert job.created_at.tzinfo is not None
            assert job.updated_at.tzinfo is not None


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch("src.data.loaders.database.DatabaseLoader")
    def test_load_test_problem(self, mock_loader_class):
        """Test load_test_problem convenience function."""
        # GIVEN: Mock loader
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        mock_problem = MagicMock()
        mock_loader.load_problem.return_value = mock_problem

        # WHEN: Using convenience function
        result = load_test_problem()

        # THEN: Loader created with test tables
        mock_loader_class.assert_called_once_with(use_test_tables=True)
        mock_loader.load_problem.assert_called_once()
        assert result == mock_problem
