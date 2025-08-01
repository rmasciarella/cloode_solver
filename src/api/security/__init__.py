"""API Security Layer for Fresh OR-Tools Solver.

Provides authentication, authorization, and input validation middleware
with backward compatibility for existing GUI integration.
"""

from .auth import AuthConfig, AuthenticatedRequest, SecurityLevel
from .config import get_security_config, get_security_config_manager
from .middleware import (
    AuthenticationMiddleware,
    InputValidationMiddleware,
    SecurityMiddleware,
)
from .service_role import ServiceRoleManager

__all__ = [
    "AuthConfig",
    "AuthenticatedRequest", 
    "SecurityLevel",
    "AuthenticationMiddleware",
    "InputValidationMiddleware",
    "SecurityMiddleware",
    "ServiceRoleManager",
    "get_security_config",
    "get_security_config_manager",
]