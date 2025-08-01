"""Database security configuration for Fresh OR-Tools solver.

This module provides configuration management for RLS policies, authentication,
and security features while preserving backward compatibility.
"""

import os
from enum import Enum
from typing import Any

from dotenv import load_dotenv


class SecurityLevel(Enum):
    """Security levels for progressive RLS policy implementation."""

    PERMISSIVE = "permissive"  # Phase 1: Allow all access (GUI compatibility)
    AUTHENTICATED = (
        "authenticated"  # Phase 2: Require authentication but allow all data
    )
    DEPARTMENT = "department"  # Phase 3: Restrict by department
    TENANT = "tenant"  # Phase 4: Multi-tenant isolation


class DatabaseSecurityConfig:
    """Configuration for database security features."""

    def __init__(self):
        """Initialize security configuration from environment."""
        load_dotenv()

        # Core Supabase configuration
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        # Security configuration
        self.security_level = SecurityLevel(
            os.environ.get("DATABASE_SECURITY_LEVEL", "permissive")
        )
        self.rls_enabled = os.environ.get("RLS_ENABLED", "true").lower() == "true"
        self.audit_enabled = os.environ.get("AUDIT_ENABLED", "true").lower() == "true"

        # Authentication configuration
        self.auth_required = os.environ.get("AUTH_REQUIRED", "false").lower() == "true"
        self.allow_anon_access = (
            os.environ.get("ALLOW_ANON_ACCESS", "true").lower() == "true"
        )

        # Performance monitoring
        self.monitor_rls_performance = (
            os.environ.get("MONITOR_RLS_PERFORMANCE", "true").lower() == "true"
        )
        self.log_security_events = (
            os.environ.get("LOG_SECURITY_EVENTS", "true").lower() == "true"
        )

    def get_client_config(self, use_service_role: bool = False) -> dict[str, Any]:
        """Get Supabase client configuration.

        Args:
            use_service_role: If True, use service role key (bypasses RLS)

        Returns:
            Configuration dictionary for Supabase client

        """
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL must be set in environment")

        if use_service_role:
            if not self.supabase_service_role_key:
                raise ValueError(
                    "SUPABASE_SERVICE_ROLE_KEY must be set for service role access"
                )
            key = self.supabase_service_role_key
        else:
            if not self.supabase_anon_key:
                raise ValueError("SUPABASE_ANON_KEY must be set for client access")
            key = self.supabase_anon_key

        return {
            "url": self.supabase_url,
            "key": key,
            "options": {
                "db": {"schema": "public"},
                "auth": {
                    "auto_refresh_token": True,
                    "persist_session": True,
                    "detect_session_in_url": True,
                },
            },
        }

    def should_use_service_role(self, operation_type: str) -> bool:
        """Determine if service role should be used for operation.

        Args:
            operation_type: Type of operation ('solver', 'migration', 'admin', 'gui')

        Returns:
            True if service role should be used

        """
        service_role_operations = {
            "solver",  # Backend solver operations
            "migration",  # Database migrations
            "admin",  # Administrative operations
            "batch",  # Batch processing
            "performance",  # Performance monitoring
        }

        return operation_type in service_role_operations

    def get_rls_policy_config(self) -> dict[str, Any]:
        """Get RLS policy configuration based on security level.

        Returns:
            Policy configuration for current security level

        """
        base_config = {
            "enabled": self.rls_enabled,
            "audit_enabled": self.audit_enabled,
            "monitor_performance": self.monitor_rls_performance,
        }

        if self.security_level == SecurityLevel.PERMISSIVE:
            return {
                **base_config,
                "allow_anon": True,
                "check_department": False,
                "check_tenant": False,
                "policy_type": "permissive",
                "description": "Allow all access - preserves GUI compatibility",
            }

        elif self.security_level == SecurityLevel.AUTHENTICATED:
            return {
                **base_config,
                "allow_anon": self.allow_anon_access,
                "check_department": False,
                "check_tenant": False,
                "policy_type": "authenticated",
                "description": "Require authentication but allow all data access",
            }

        elif self.security_level == SecurityLevel.DEPARTMENT:
            return {
                **base_config,
                "allow_anon": False,
                "check_department": True,
                "check_tenant": False,
                "policy_type": "department",
                "description": "Restrict access by user department",
            }

        elif self.security_level == SecurityLevel.TENANT:
            return {
                **base_config,
                "allow_anon": False,
                "check_department": True,
                "check_tenant": True,
                "policy_type": "tenant",
                "description": "Full multi-tenant isolation",
            }

    def validate_configuration(self) -> dict[str, Any]:
        """Validate current security configuration.

        Returns:
            Validation result with status and issues

        """
        issues = []
        warnings = []
        
        # Development bypass
        if (
            os.environ.get("ENVIRONMENT") == "development"
            and os.environ.get("DEVELOPMENT_BYPASS_AUTH", "false").lower() == "true"
        ):
            return {
                "valid": True,
                "issues": [],
                "warnings": ["Development mode - authentication bypassed"],
                "security_level": self.security_level.value,
                "rls_enabled": self.rls_enabled,
                "config": self.get_rls_policy_config(),
                "config_valid": True,
                "development_bypass": True,
            }

        # Check required environment variables
        if not self.supabase_url:
            issues.append("SUPABASE_URL is required")
        if not self.supabase_anon_key:
            issues.append("SUPABASE_ANON_KEY is required")
        if not self.supabase_service_role_key:
            warnings.append(
                "SUPABASE_SERVICE_ROLE_KEY not set - backend operations may fail"
            )

        # Check security level compatibility
        if self.security_level != SecurityLevel.PERMISSIVE and not self.auth_required:
            warnings.append(
                f"Security level {self.security_level.value} requires authentication"
            )

        if (
            self.security_level == SecurityLevel.PERMISSIVE
            and not self.allow_anon_access
        ):
            issues.append("Permissive security level requires ALLOW_ANON_ACCESS=true")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "security_level": self.security_level.value,
            "rls_enabled": self.rls_enabled,
            "config": self.get_rls_policy_config(),
        }

    def get_migration_sql(
        self, target_security_level: SecurityLevel | None = None
    ) -> str:
        """Generate SQL for updating RLS policies to target security level.

        Args:
            target_security_level: Target security level (default: current level)

        Returns:
            SQL commands to update policies

        """
        level = target_security_level or self.security_level

        if level == SecurityLevel.PERMISSIVE:
            return self._get_permissive_policies_sql()
        elif level == SecurityLevel.AUTHENTICATED:
            return self._get_authenticated_policies_sql()
        elif level == SecurityLevel.DEPARTMENT:
            return self._get_department_policies_sql()
        elif level == SecurityLevel.TENANT:
            return self._get_tenant_policies_sql()

    def _get_permissive_policies_sql(self) -> str:
        """Get SQL for permissive policies (Phase 1)."""
        return """
-- PERMISSIVE POLICIES: Allow all access (Phase 1)
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- PERMISSIVE: Allow all access including anon
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

    def _get_authenticated_policies_sql(self) -> str:
        """Get SQL for authenticated policies (Phase 2)."""
        return """
-- AUTHENTICATED POLICIES: Require authentication (Phase 2)
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- Require authentication
    RETURN auth.uid() IS NOT NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

    def _get_department_policies_sql(self) -> str:
        """Get SQL for department-restricted policies (Phase 3)."""
        return """
-- DEPARTMENT POLICIES: Restrict by department (Phase 3)
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
DECLARE
    user_dept_id UUID;
    record_dept_id UUID;
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- Must be authenticated
    IF auth.uid() IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Admins can access all departments
    IF EXISTS (
        SELECT 1 FROM public.user_profiles 
        WHERE id = auth.uid() AND role = 'admin'
    ) THEN
        RETURN TRUE;
    END IF;
    
    -- Check department match (implementation depends on context)
    RETURN TRUE; -- Simplified for this example
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

    def _get_tenant_policies_sql(self) -> str:
        """Get SQL for tenant-isolated policies (Phase 4)."""
        return """
-- TENANT POLICIES: Multi-tenant isolation (Phase 4)
CREATE OR REPLACE FUNCTION auth.is_authenticated_or_service_role()
RETURNS BOOLEAN AS $$
DECLARE
    user_tenant_id UUID;
    record_tenant_id UUID;
BEGIN
    -- Service role bypasses all RLS
    IF current_setting('role') = 'service_role' THEN
        RETURN TRUE;
    END IF;
    
    -- Must be authenticated
    IF auth.uid() IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Super admins can access all tenants
    IF EXISTS (
        SELECT 1 FROM public.user_profiles 
        WHERE id = auth.uid() AND role = 'admin' AND permissions ? 'super_admin'
    ) THEN
        RETURN TRUE;
    END IF;
    
    -- Check tenant isolation (implementation depends on context)
    RETURN TRUE; -- Simplified for this example
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""


# Global configuration instance
security_config = DatabaseSecurityConfig()


def get_supabase_config(use_service_role: bool = False) -> dict[str, Any]:
    """Get Supabase client configuration.

    Args:
        use_service_role: If True, use service role key

    Returns:
        Configuration for Supabase client

    """
    return security_config.get_client_config(use_service_role)


def should_use_service_role(operation_type: str) -> bool:
    """Check if service role should be used for operation type.

    Args:
        operation_type: Type of operation

    Returns:
        True if service role should be used

    """
    return security_config.should_use_service_role(operation_type)


def validate_security_config() -> dict[str, Any]:
    """Validate current security configuration.

    Returns:
        Validation results

    """
    return security_config.validate_configuration()


def get_rls_policy_config() -> dict[str, Any]:
    """Get current RLS policy configuration.

    Returns:
        RLS policy configuration

    """
    return security_config.get_rls_policy_config()
