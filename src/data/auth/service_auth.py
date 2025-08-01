"""Service layer authentication handling for OR-Tools solver operations.
Maintains API functionality with proper service role access.
"""

import os
from dataclasses import dataclass
from typing import Any

from supabase import Client, create_client


@dataclass
class ServiceAuthConfig:
    """Configuration for service authentication"""

    supabase_url: str
    service_role_key: str
    enable_auth_bypass: bool = False
    security_level: str = "development"


class ServiceAuthManager:
    """Manages authentication for service operations"""

    def __init__(self, config: ServiceAuthConfig | None = None):
        self.config = config or self._load_config()
        self._client: Client | None = None

    def _load_config(self) -> ServiceAuthConfig:
        """Load configuration from environment variables"""
        return ServiceAuthConfig(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            enable_auth_bypass=os.getenv("NODE_ENV") == "development"
            and os.getenv("NEXT_PUBLIC_DISABLE_AUTH") == "true",
            security_level=os.getenv("NEXT_PUBLIC_SECURITY_LEVEL", "development"),
        )

    @property
    def client(self) -> Client:
        """Get authenticated Supabase client with service role access"""
        if not self._client:
            self._client = create_client(
                self.config.supabase_url, self.config.service_role_key
            )
        return self._client

    def execute_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute SQL query with service role privileges (bypasses RLS)"""
        try:
            result = self.client.rpc(
                "execute_sql", {"query": query, "params": params or {}}
            )

            return {"success": True, "data": result.data, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def get_table_data(
        self, table: str, filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get table data with service role access"""
        try:
            query = self.client.table(table).select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            result = query.execute()

            return {"success": True, "data": result.data, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def insert_data(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """Insert data with service role access"""
        try:
            result = self.client.table(table).insert(data).execute()

            return {"success": True, "data": result.data, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def update_data(
        self, table: str, data: dict[str, Any], filters: dict[str, Any]
    ) -> dict[str, Any]:
        """Update data with service role access"""
        try:
            query = self.client.table(table).update(data)

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()

            return {"success": True, "data": result.data, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def delete_data(self, table: str, filters: dict[str, Any]) -> dict[str, Any]:
        """Delete data with service role access"""
        try:
            query = self.client.table(table).delete()

            for key, value in filters.items():
                query = query.eq(key, value)

            result = query.execute()

            return {"success": True, "data": result.data, "error": None}

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def is_authenticated(self) -> bool:
        """Check if service is properly authenticated"""
        if self.config.enable_auth_bypass:
            return True

        try:
            # Test connection with a simple query
            result = self.client.table("departments").select("count").limit(1).execute()
            return True
        except Exception:
            return False


# Global service auth manager instance
service_auth = ServiceAuthManager()


# Compatibility functions for existing code
def get_authenticated_client() -> Client:
    """Get authenticated Supabase client for service operations"""
    return service_auth.client


def execute_service_query(
    query: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute query with service authentication"""
    return service_auth.execute_query(query, params)


def is_service_authenticated() -> bool:
    """Check if service authentication is working"""
    return service_auth.is_authenticated()
