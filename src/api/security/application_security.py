"""Application-level security implementation for Fresh OR-Tools solver.

This module provides security enforcement at the application layer without requiring
database schema changes, enabling secure operation while preserving GUI functionality.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

from config.database_security_config import SecurityLevel, security_config

logger = logging.getLogger(__name__)


class SecurityAction(Enum):
    """Security actions for audit logging."""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"


class SecurityContext:
    """Security context for request processing."""

    def __init__(
        self,
        user_id: str | None = None,
        role: str = "anonymous",
        department_id: str | None = None,
        tenant_id: str | None = None,
        permissions: list[str] | None = None,
    ):
        self.user_id = user_id
        self.role = role
        self.department_id = department_id
        self.tenant_id = tenant_id
        self.permissions = permissions or []
        self.timestamp = datetime.utcnow()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.user_id is not None

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        if self.role == "admin":
            return True
        return permission in self.permissions

    def can_access_department(self, department_id: str) -> bool:
        """Check if user can access specific department."""
        if self.role == "admin":
            return True
        return self.department_id == department_id

    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if user can access specific tenant."""
        if self.role == "admin":
            return True
        return self.tenant_id == tenant_id


class ApplicationSecurityManager:
    """Manages application-level security enforcement."""

    def __init__(self):
        self.audit_log: list[dict[str, Any]] = []
        self.access_attempts: dict[str, list[datetime]] = {}

    def authenticate_request(self, headers: dict[str, str]) -> SecurityContext:
        """Authenticate incoming request and return security context.

        Args:
            headers: Request headers containing authentication info

        Returns:
            SecurityContext with user permissions

        """
        # In development/permissive mode, allow all access
        if security_config.security_level == SecurityLevel.PERMISSIVE:
            return SecurityContext(
                user_id="anonymous",
                role="admin",  # Grant admin access in permissive mode
                permissions=["read", "write", "delete", "admin"],
            )

        # Check for authorization header
        auth_header = headers.get("Authorization", "")
        if not auth_header:
            if security_config.allow_anon_access:
                return SecurityContext(
                    user_id=None, role="anonymous", permissions=["read"]
                )
            else:
                return SecurityContext()  # No permissions

        # Parse authorization token
        try:
            # In a real implementation, this would validate JWT tokens
            # For now, we'll simulate based on configuration
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user_context = self._validate_token(token)
                return user_context
            else:
                return SecurityContext()
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return SecurityContext()

    def _validate_token(self, token: str) -> SecurityContext:
        """Validate authentication token.

        Args:
            token: JWT or API token

        Returns:
            SecurityContext for authenticated user

        """
        # Simplified token validation for demonstration
        # In production, this would validate JWT signature, expiration, etc.

        if token == "demo_admin_token":
            return SecurityContext(
                user_id="admin_user",
                role="admin",
                permissions=["read", "write", "delete", "admin"],
            )
        elif token == "demo_user_token":
            return SecurityContext(
                user_id="regular_user",
                role="user",
                department_id="production",
                permissions=["read", "write"],
            )
        else:
            return SecurityContext()

    def authorize_action(
        self,
        context: SecurityContext,
        action: SecurityAction,
        resource: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Authorize user action on resource.

        Args:
            context: Security context for user
            action: Action being performed
            resource: Resource type (departments, machines, etc.)
            resource_id: Specific resource ID
            metadata: Additional context for authorization

        Returns:
            True if action is authorized

        """
        # Log the authorization attempt
        self._log_security_event(context, action, resource, resource_id, metadata)

        # Check security level requirements
        if security_config.security_level == SecurityLevel.PERMISSIVE:
            return True

        # Require authentication for authenticated level and above
        if security_config.security_level in [
            SecurityLevel.AUTHENTICATED,
            SecurityLevel.DEPARTMENT,
            SecurityLevel.TENANT,
        ]:
            if not context.is_authenticated() and not security_config.allow_anon_access:
                return False

        # Check department-level access
        if security_config.security_level in [
            SecurityLevel.DEPARTMENT,
            SecurityLevel.TENANT,
        ]:
            if metadata and "department_id" in metadata:
                if not context.can_access_department(metadata["department_id"]):
                    return False

        # Check tenant-level access
        if security_config.security_level == SecurityLevel.TENANT:
            if metadata and "tenant_id" in metadata:
                if not context.can_access_tenant(metadata["tenant_id"]):
                    return False

        # Check action permissions
        action_permissions = {
            SecurityAction.READ: "read",
            SecurityAction.CREATE: "write",
            SecurityAction.UPDATE: "write",
            SecurityAction.DELETE: "delete",
        }

        required_permission = action_permissions.get(action)
        if required_permission and not context.has_permission(required_permission):
            return False

        return True

    def _log_security_event(
        self,
        context: SecurityContext,
        action: SecurityAction,
        resource: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Log security event for audit purposes.

        Args:
            context: Security context
            action: Action performed
            resource: Resource accessed
            resource_id: Specific resource ID
            metadata: Additional context

        """
        if not security_config.log_security_events:
            return

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": context.user_id,
            "role": context.role,
            "action": action.value,
            "resource": resource,
            "resource_id": resource_id,
            "department_id": context.department_id,
            "tenant_id": context.tenant_id,
            "metadata": metadata or {},
            "security_level": security_config.security_level.value,
        }

        self.audit_log.append(event)

        # Keep only recent events to prevent memory issues
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]

        # Log security events
        logger.info(
            f"Security Event: {action.value} on {resource} by {context.user_id or 'anonymous'}"
        )

        # Log access denied events as warnings
        if action == SecurityAction.ACCESS_DENIED:
            logger.warning(
                f"Access denied: {context.user_id or 'anonymous'} attempted {action.value} on {resource}"
            )

    def get_audit_log(
        self, user_id: str | None = None, resource: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get audit log entries.

        Args:
            user_id: Filter by user ID
            resource: Filter by resource type
            limit: Maximum entries to return

        Returns:
            List of audit log entries

        """
        filtered_log = self.audit_log

        if user_id:
            filtered_log = [e for e in filtered_log if e["user_id"] == user_id]

        if resource:
            filtered_log = [e for e in filtered_log if e["resource"] == resource]

        return filtered_log[-limit:]

    def check_rate_limit(
        self, user_id: str, max_attempts: int = 100, window_minutes: int = 60
    ) -> bool:
        """Check if user is within rate limits.

        Args:
            user_id: User identifier
            max_attempts: Maximum attempts in window
            window_minutes: Time window in minutes

        Returns:
            True if within rate limits

        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old attempts
        if user_id in self.access_attempts:
            self.access_attempts[user_id] = [
                attempt
                for attempt in self.access_attempts[user_id]
                if attempt > window_start
            ]
        else:
            self.access_attempts[user_id] = []

        # Check current attempts
        current_attempts = len(self.access_attempts[user_id])

        if current_attempts >= max_attempts:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: {current_attempts} attempts"
            )
            return False

        # Record this attempt
        self.access_attempts[user_id].append(now)
        return True


# Global security manager instance
security_manager = ApplicationSecurityManager()


def require_authentication(f):
    """Decorator to require authentication for endpoint."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would be implemented in the actual API framework
        # For now, it's a placeholder for the security pattern
        return f(*args, **kwargs)

    return decorated_function


def require_permission(permission: str):
    """Decorator to require specific permission for endpoint."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would check the permission in the actual implementation
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_security_context(headers: dict[str, str]) -> SecurityContext:
    """Get security context for request.

    Args:
        headers: Request headers

    Returns:
        SecurityContext for request

    """
    return security_manager.authenticate_request(headers)


def authorize_action(
    context: SecurityContext,
    action: SecurityAction,
    resource: str,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Authorize action for security context.

    Args:
        context: Security context
        action: Action to authorize
        resource: Resource type
        resource_id: Specific resource ID
        metadata: Additional context

    Returns:
        True if authorized

    """
    return security_manager.authorize_action(
        context, action, resource, resource_id, metadata
    )


def log_security_event(
    context: SecurityContext,
    action: SecurityAction,
    resource: str,
    success: bool = True,
    metadata: dict[str, Any] | None = None,
):
    """Log security event.

    Args:
        context: Security context
        action: Action performed
        resource: Resource accessed
        success: Whether action succeeded
        metadata: Additional context

    """
    if not success:
        action = SecurityAction.ACCESS_DENIED

    security_manager._log_security_event(context, action, resource, None, metadata)


def get_audit_log(
    user_id: str | None = None, resource: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """Get audit log entries.

    Args:
        user_id: Filter by user ID
        resource: Filter by resource type
        limit: Maximum entries to return

    Returns:
        List of audit log entries

    """
    return security_manager.get_audit_log(user_id, resource, limit)
