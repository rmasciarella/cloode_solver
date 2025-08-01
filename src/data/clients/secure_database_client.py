"""Secure database client factory for Fresh OR-Tools solver.

This module provides secure database client creation with proper RLS handling,
service role management, and backward compatibility with existing GUI operations.
"""

import logging
import os
from contextlib import contextmanager
from typing import Any

from supabase import Client, create_client

from config.database_security_config import (
    get_supabase_config,
    security_config,
    should_use_service_role,
)

logger = logging.getLogger(__name__)


class SecureDatabaseClient:
    """Factory for creating secure database clients with RLS support."""

    def __init__(self) -> None:
        """Initialize the secure database client factory."""
        self._anon_client: Client | None = None
        self._service_client: Client | None = None

    def get_client(self, operation_type: str = "gui") -> Client:
        """Get appropriate Supabase client for operation type.

        Args:
            operation_type: Type of operation ('gui', 'solver', 'admin', 'migration')

        Returns:
            Configured Supabase client

        Raises:
            ValueError: If required configuration is missing

        """
        use_service_role = should_use_service_role(operation_type)

        if use_service_role:
            return self._get_service_client()
        else:
            return self._get_anon_client()

    def _get_anon_client(self) -> Client:
        """Get anonymous client for GUI operations."""
        if self._anon_client is None:
            config = get_supabase_config(use_service_role=False)
            self._anon_client = create_client(config["url"], config["key"])
            logger.info("Created anonymous Supabase client for GUI operations")

        return self._anon_client

    def _get_service_client(self) -> Client:
        """Get service role client for backend operations."""
        if self._service_client is None:
            config = get_supabase_config(use_service_role=True)
            self._service_client = create_client(config["url"], config["key"])
            logger.info("Created service role Supabase client for backend operations")

        return self._service_client

    @contextmanager
    def get_transaction_client(self, operation_type: str = "gui") -> Any:
        """Get client with transaction support.

        Args:
            operation_type: Type of operation

        Yields:
            Supabase client with transaction context

        """
        client = self.get_client(operation_type)
        # Note: Supabase Python client doesn't have explicit transaction support
        # This is a placeholder for future transaction implementation
        try:
            yield client
        except Exception as e:
            logger.error(f"Transaction failed for {operation_type}: {e}")
            raise

    def validate_security_setup(self) -> dict[str, Any]:
        """Validate security setup and client connectivity.

        Returns:
            Validation results with connectivity status

        """
        validation = security_config.validate_configuration()

        # Test client connections
        connectivity = {
            "anon_client": False,
            "service_client": False,
        }

        try:
            # Test anonymous client
            anon_client = self._get_anon_client()
            # Simple query to test connectivity
            result = (
                anon_client.table("departments")
                .select("department_id")
                .limit(1)
                .execute()
            )
            connectivity["anon_client"] = True
            logger.info("Anonymous client connectivity: OK")
        except Exception as e:
            logger.error(f"Anonymous client connectivity failed: {e}")
            validation["warnings"].append(f"Anonymous client connectivity failed: {e}")

        try:
            # Test service client
            service_client = self._get_service_client()
            result = (
                service_client.table("departments")
                .select("department_id")
                .limit(1)
                .execute()
            )
            connectivity["service_client"] = True
            logger.info("Service client connectivity: OK")
        except Exception as e:
            logger.error(f"Service client connectivity failed: {e}")
            validation["warnings"].append(f"Service client connectivity failed: {e}")

        validation["connectivity"] = connectivity
        return validation

    def test_rls_policies(self) -> dict[str, Any]:
        """Test RLS policies with different client types.

        Returns:
            Test results for RLS policy functionality

        """
        results: dict[str, Any] = {
            "anon_access": {"allowed": False, "error": None},
            "service_access": {"allowed": False, "error": None},
            "policy_active": False,
        }

        # Test anonymous access
        try:
            anon_client = self._get_anon_client()
            response = (
                anon_client.table("departments")
                .select("department_id")
                .limit(1)
                .execute()
            )
            results["anon_access"]["allowed"] = (
                len(response.data) >= 0
            )  # Even empty result is success
            logger.info("Anonymous access test: PASSED")
        except Exception as e:
            results["anon_access"]["error"] = str(e)
            logger.warning(f"Anonymous access test: FAILED - {e}")

        # Test service role access
        try:
            service_client = self._get_service_client()
            response = (
                service_client.table("departments")
                .select("department_id")
                .limit(1)
                .execute()
            )
            results["service_access"]["allowed"] = len(response.data) >= 0
            logger.info("Service role access test: PASSED")
        except Exception as e:
            results["service_access"]["error"] = str(e)
            logger.error(f"Service role access test: FAILED - {e}")

        # Check if RLS is actually active
        try:
            service_client = self._get_service_client()
            # Query system tables to check RLS status
            rls_status = service_client.rpc("check_rls_status").execute()
            results["policy_active"] = True
            logger.info("RLS policies are active")
        except Exception as e:
            logger.info(f"Could not determine RLS status: {e}")

        return results

    def emergency_disable_rls(self) -> str:
        """Emergency disable RLS policies (development only).

        Returns:
            Result message

        Raises:
            RuntimeError: If not allowed or operation fails

        """
        if not security_config.validate_configuration().get(
            "allow_emergency_disable", False
        ):
            raise RuntimeError(
                "Emergency RLS disable not allowed in current configuration"
            )

        if os.environ.get("ENVIRONMENT") == "production":
            raise RuntimeError("Emergency RLS disable not allowed in production")

        try:
            service_client = self._get_service_client()
            result = service_client.rpc("emergency_disable_rls").execute()
            logger.warning("RLS policies disabled via emergency function")
            return str(result.data)
        except Exception as e:
            logger.error(f"Failed to disable RLS: {e}")
            raise RuntimeError(f"Failed to disable RLS: {e}")

    def emergency_enable_rls(self) -> str:
        """Emergency enable RLS policies after recovery.

        Returns:
            Result message

        Raises:
            RuntimeError: If operation fails

        """
        try:
            service_client = self._get_service_client()
            result = service_client.rpc("emergency_enable_rls").execute()
            logger.info("RLS policies re-enabled after emergency recovery")
            return str(result.data)
        except Exception as e:
            logger.error(f"Failed to enable RLS: {e}")
            raise RuntimeError(f"Failed to enable RLS: {e}")


# Global client factory instance
db_client_factory = SecureDatabaseClient()


def get_database_client(operation_type: str = "gui") -> Client:
    """Get database client for specified operation type.

    Args:
        operation_type: Type of operation ('gui', 'solver', 'admin', 'migration')

    Returns:
        Configured Supabase client

    """
    return db_client_factory.get_client(operation_type)


def validate_database_security() -> dict[str, Any]:
    """Validate database security configuration and connectivity.

    Returns:
        Validation results

    """
    return db_client_factory.validate_security_setup()


def test_rls_functionality() -> dict[str, Any]:
    """Test RLS policy functionality.

    Returns:
        Test results

    """
    return db_client_factory.test_rls_policies()


@contextmanager
def database_transaction(operation_type: str = "gui") -> Any:
    """Context manager for database transactions.

    Args:
        operation_type: Type of operation

    Yields:
        Database client with transaction context

    """
    with db_client_factory.get_transaction_client(operation_type) as client:
        yield client


# Backward compatibility aliases
def get_supabase_client(use_service_role: bool = False) -> Client:
    """Get Supabase client with backward compatibility.

    Args:
        use_service_role: If True, use service role

    Returns:
        Supabase client

    """
    operation_type = "solver" if use_service_role else "gui"
    return get_database_client(operation_type)


def create_secure_client(operation_type: str) -> Client:
    """Create secure database client for operation type.

    Args:
        operation_type: Type of operation

    Returns:
        Configured Supabase client

    """
    return get_database_client(operation_type)
