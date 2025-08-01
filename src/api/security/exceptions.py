"""Security-focused exception handling for API endpoints.

Provides structured error responses that don't leak sensitive information
while maintaining proper logging for security monitoring.
"""

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class SecurityException(HTTPException):
    """Base exception for security-related errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        security_context: dict[str, Any] | None = None,
        log_detail: str | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.security_context = security_context or {}
        self.log_detail = log_detail or detail


class AuthenticationFailedException(SecurityException):
    """Exception for authentication failures."""

    def __init__(
        self,
        detail: str = "Authentication required",
        security_context: dict[str, Any] | None = None,
        log_detail: str | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            security_context=security_context,
            log_detail=log_detail,
        )


class AuthorizationFailedException(SecurityException):
    """Exception for authorization failures."""

    def __init__(
        self,
        detail: str = "Insufficient permissions",
        security_context: dict[str, Any] | None = None,
        log_detail: str | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            security_context=security_context,
            log_detail=log_detail,
        )


class RateLimitExceededException(SecurityException):
    """Exception for rate limit violations."""

    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: int = 60,
        security_context: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            security_context=security_context,
        )
        self.retry_after = retry_after


class InputValidationException(SecurityException):
    """Exception for input validation failures."""

    def __init__(
        self,
        detail: str = "Invalid input",
        validation_errors: list[str] | None = None,
        security_context: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            security_context=security_context,
        )
        self.validation_errors = validation_errors or []


class ServiceRoleException(SecurityException):
    """Exception for service role escalation failures."""

    def __init__(
        self,
        detail: str = "Service role operation failed",
        operation: str | None = None,
        security_context: dict[str, Any] | None = None,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            security_context=security_context,
        )
        self.operation = operation


class SecurityExceptionHandler:
    """Centralized security exception handling with proper logging."""

    @staticmethod
    async def handle_security_exception(
        request: Request, exc: SecurityException
    ) -> JSONResponse:
        """Handle security exceptions with proper logging and response."""
        # Extract request context for logging
        request_context = {
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": getattr(request.state, "client_ip", "unknown"),
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        # Merge with security context
        full_context = {**request_context, **exc.security_context}

        # Log the security exception
        if isinstance(
            exc, (AuthenticationFailedException, AuthorizationFailedException)
        ):
            logger.warning(
                f"Security violation: {exc.log_detail or exc.detail}",
                extra={
                    "exception_type": type(exc).__name__,
                    "status_code": exc.status_code,
                    **full_context,
                },
            )
        elif isinstance(exc, RateLimitExceededException):
            logger.info(
                f"Rate limit exceeded: {exc.detail}",
                extra={
                    "exception_type": type(exc).__name__,
                    "retry_after": getattr(exc, "retry_after", 60),
                    **full_context,
                },
            )
        else:
            logger.error(
                f"Security exception: {exc.log_detail or exc.detail}",
                extra={
                    "exception_type": type(exc).__name__,
                    "status_code": exc.status_code,
                    **full_context,
                },
            )

        # Create response content (sanitized for client)
        response_content = {
            "success": False,
            "error": exc.detail,
            "type": "security_error",
        }

        # Add specific fields for certain exception types
        if isinstance(exc, RateLimitExceededException):
            response_content["retry_after"] = exc.retry_after
        elif isinstance(exc, InputValidationException) and exc.validation_errors:
            response_content["validation_errors"] = exc.validation_errors

        # Create response with appropriate headers
        headers = {}
        if isinstance(exc, RateLimitExceededException):
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=exc.status_code,
            content=response_content,
            headers=headers,
        )

    @staticmethod
    async def handle_generic_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle non-security exceptions with security-conscious logging."""
        # Extract request context
        request_context = {
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": getattr(request.state, "client_ip", "unknown"),
        }

        # Log the exception securely (avoid logging sensitive data)
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)[:200],  # Truncate to avoid log injection
                **request_context,
            },
            exc_info=True,
        )

        # Return sanitized error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": "An unexpected error occurred. Please contact support.",
                "type": "server_error",
            },
        )


def setup_security_exception_handlers(app) -> None:
    """Set up security exception handlers for the FastAPI app."""
    handler = SecurityExceptionHandler()

    # Security-specific exceptions
    app.add_exception_handler(SecurityException, handler.handle_security_exception)
    app.add_exception_handler(
        AuthenticationFailedException, handler.handle_security_exception
    )
    app.add_exception_handler(
        AuthorizationFailedException, handler.handle_security_exception
    )
    app.add_exception_handler(
        RateLimitExceededException, handler.handle_security_exception
    )
    app.add_exception_handler(
        InputValidationException, handler.handle_security_exception
    )
    app.add_exception_handler(ServiceRoleException, handler.handle_security_exception)

    # Override generic exception handler for security
    app.add_exception_handler(Exception, handler.handle_generic_exception)

    logger.info("Security exception handlers configured")
