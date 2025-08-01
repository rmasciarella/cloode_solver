"""Authentication configuration and models for API security.

Provides configurable authentication with graceful degradation
for backward compatibility with existing GUI endpoints.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security enforcement levels for different operations."""

    # No authentication required - for health checks, docs
    NONE = "none"

    # Optional authentication - log but don't block
    OPTIONAL = "optional"

    # Required for read operations - allow service role fallback
    READ = "read"

    # Required for write operations - strict enforcement
    WRITE = "write"

    # Administrative operations - service role only
    ADMIN = "admin"


class AuthConfig(BaseModel):
    """Configuration for authentication and security settings."""

    # Enable/disable authentication globally
    enabled: bool = Field(default=False, description="Enable authentication middleware")

    # Default security level for unspecified endpoints
    default_level: SecurityLevel = Field(
        default=SecurityLevel.OPTIONAL,
        description="Default security level for endpoints",
    )

    # Service role escalation settings
    allow_service_role_escalation: bool = Field(
        default=True, description="Allow service role for elevated operations"
    )

    # Graceful degradation settings
    fail_gracefully: bool = Field(
        default=True, description="Continue operation if auth fails (with logging)"
    )

    # Rate limiting settings
    enable_rate_limiting: bool = Field(
        default=True, description="Enable rate limiting middleware"
    )

    requests_per_minute: int = Field(
        default=60, ge=1, le=1000, description="Requests per minute per client"
    )

    # Input validation settings
    enable_input_validation: bool = Field(
        default=True, description="Enable input sanitization"
    )

    max_request_size_mb: float = Field(
        default=10.0, ge=0.1, le=100.0, description="Maximum request size in MB"
    )


class AuthenticatedRequest(BaseModel):
    """Enhanced request information with authentication context."""

    # Original request information
    path: str
    method: str
    client_ip: str

    # Authentication context
    authenticated: bool = False
    user_id: str | None = None
    role: str | None = None

    # Security metadata
    security_level: SecurityLevel = SecurityLevel.OPTIONAL
    service_role_used: bool = False
    validation_errors: list[str] = Field(default_factory=list)

    # Performance tracking
    auth_duration_ms: float = 0.0

    def is_authorized_for_level(self, required_level: SecurityLevel) -> bool:
        """Check if request is authorized for the required security level."""
        if required_level == SecurityLevel.NONE:
            return True

        if required_level == SecurityLevel.OPTIONAL:
            return True  # Optional always passes

        if required_level == SecurityLevel.READ:
            return self.authenticated or self.service_role_used

        if required_level == SecurityLevel.WRITE:
            return self.authenticated or self.service_role_used

        if required_level == SecurityLevel.ADMIN:
            return self.service_role_used or (
                self.authenticated and self.role == "admin"
            )

        return False

    def to_log_dict(self) -> dict[str, Any]:
        """Convert to dictionary for structured logging."""
        return {
            "path": self.path,
            "method": self.method,
            "client_ip": self.client_ip,
            "authenticated": self.authenticated,
            "user_id": self.user_id,
            "role": self.role,
            "security_level": self.security_level.value,
            "service_role_used": self.service_role_used,
            "validation_errors": self.validation_errors,
            "auth_duration_ms": self.auth_duration_ms,
        }


class SecurityContext:
    """Global security context for the application."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self._request_counts: dict[str, int] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited."""
        if not self.config.enable_rate_limiting:
            return False

        current_count = self._request_counts.get(client_ip, 0)
        return current_count >= self.config.requests_per_minute

    def increment_request_count(self, client_ip: str) -> None:
        """Increment request count for client IP."""
        if not self.config.enable_rate_limiting:
            return

        self._request_counts[client_ip] = self._request_counts.get(client_ip, 0) + 1

    def reset_rate_limits(self) -> None:
        """Reset rate limit counters (called periodically)."""
        self._request_counts.clear()
        logger.debug("Rate limit counters reset")


def extract_client_ip(request: Request) -> str:
    """Extract client IP address from request headers."""
    # Check for forwarded headers (behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct connection IP
    if hasattr(request, "client") and request.client:
        return request.client.host

    return "unknown"
