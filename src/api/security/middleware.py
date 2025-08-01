"""Security middleware for FastAPI application.

Provides authentication, input validation, and rate limiting
with backward compatibility and graceful degradation.
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .auth import (
    AuthConfig,
    AuthenticatedRequest,
    SecurityContext,
    SecurityLevel,
    extract_client_ip,
)
from .service_role import get_service_role_manager

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Main security middleware that orchestrates all security features."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.context = SecurityContext(config)
        self.service_role_manager = get_service_role_manager()

        # Endpoint security level mappings
        self._endpoint_security_levels = {
            # Public endpoints
            "/": SecurityLevel.NONE,
            "/docs": SecurityLevel.NONE,
            "/redoc": SecurityLevel.NONE,
            "/openapi.json": SecurityLevel.NONE,
            # Health and monitoring
            "/api/v1/health": SecurityLevel.OPTIONAL,
            "/api/v1/status": SecurityLevel.OPTIONAL,
            # Read operations
            "/api/v1/patterns": SecurityLevel.READ,
            # Write operations
            "/api/v1/solve": SecurityLevel.WRITE,
            "/api/v1/validate": SecurityLevel.WRITE,
            # Admin operations
            "/api/v1/admin": SecurityLevel.ADMIN,
        }

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Main middleware execution."""
        start_time = time.time()

        try:
            # Create authenticated request context
            auth_request = await self._create_auth_context(request)

            # Apply security checks
            security_result = await self._apply_security_checks(auth_request)

            if not security_result["allowed"]:
                return self._create_security_response(security_result)

            # Add security context to request for downstream use
            request.state.auth = auth_request
            request.state.security = security_result

            # Execute the request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response, auth_request)

            # Log successful request
            self._log_request(
                auth_request, response.status_code, time.time() - start_time
            )

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")

            # In graceful degradation mode, continue with warning
            if self.config.fail_gracefully:
                logger.warning("Continuing request with security bypass due to error")
                response = await call_next(request)
                response.headers["X-Security-Warning"] = (
                    "Security check bypassed due to error"
                )
                return response
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": "Security system error",
                        "detail": "Contact administrator",
                    },
                )

    async def _create_auth_context(self, request: Request) -> AuthenticatedRequest:
        """Create authentication context for the request."""
        auth_start = time.time()

        auth_request = AuthenticatedRequest(
            path=str(request.url.path),
            method=request.method,
            client_ip=extract_client_ip(request),
            security_level=self._get_endpoint_security_level(str(request.url.path)),
        )

        if self.config.enabled:
            # Check for authentication token
            auth_token = request.headers.get("Authorization")
            if auth_token and auth_token.startswith("Bearer "):
                token = auth_token[7:]  # Remove "Bearer " prefix
                auth_result = await self._validate_auth_token(token)

                auth_request.authenticated = auth_result["valid"]
                auth_request.user_id = auth_result.get("user_id")
                auth_request.role = auth_result.get("role")

        auth_request.auth_duration_ms = (time.time() - auth_start) * 1000
        return auth_request

    async def _apply_security_checks(
        self, auth_request: AuthenticatedRequest
    ) -> dict[str, Any]:
        """Apply all security checks to the request."""
        result = {
            "allowed": True,
            "reason": "authorized",
            "escalation_used": False,
            "rate_limited": False,
        }

        # Rate limiting check
        if self.context.is_rate_limited(auth_request.client_ip):
            result.update(
                {
                    "allowed": False,
                    "reason": "rate_limited",
                    "rate_limited": True,
                }
            )
            return result

        # Security level authorization check
        required_level = auth_request.security_level

        if not auth_request.is_authorized_for_level(required_level):
            # Try service role escalation for system operations
            if self._can_use_service_role_escalation(auth_request):
                auth_request.service_role_used = True
                result["escalation_used"] = True
                logger.info(
                    f"Service role escalation used for {auth_request.path}",
                    extra=auth_request.to_log_dict(),
                )
            else:
                result.update(
                    {
                        "allowed": False,
                        "reason": "insufficient_authorization",
                    }
                )
                return result

        # Increment rate limit counter
        self.context.increment_request_count(auth_request.client_ip)

        return result

    def _can_use_service_role_escalation(
        self, auth_request: AuthenticatedRequest
    ) -> bool:
        """Check if service role escalation can be used for this request."""
        if not self.config.allow_service_role_escalation:
            return False

        if not self.service_role_manager.is_available():
            return False

        # Define paths that can use service role escalation
        escalation_paths = {
            "/api/v1/patterns",
            "/api/v1/solve",
            "/api/v1/validate",
            "/api/v1/health",
        }

        return any(auth_request.path.startswith(path) for path in escalation_paths)

    def _get_endpoint_security_level(self, path: str) -> SecurityLevel:
        """Get security level for an endpoint path."""
        # Exact match first
        if path in self._endpoint_security_levels:
            return self._endpoint_security_levels[path]

        # Pattern matching for parameterized paths
        for endpoint_pattern, level in self._endpoint_security_levels.items():
            if path.startswith(endpoint_pattern):
                return level

        # Default level
        return self.config.default_level

    async def _validate_auth_token(self, token: str) -> dict[str, Any]:
        """Validate Supabase JWT authentication token."""
        if not token:
            return {"valid": False, "error": "No token provided"}

        # Check basic JWT structure (header.payload.signature)
        if token.count(".") != 2:
            return {"valid": False, "error": "Invalid JWT format"}

        try:
            # Import JWT validation utilities
            import os

            import jwt
            from dotenv import load_dotenv

            load_dotenv()
            jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")

            if not jwt_secret:
                logger.warning(
                    "SUPABASE_JWT_SECRET not configured, using development mode"
                )
                # Development mode only - check JWT structure but don't validate signature
                try:
                    # Decode without verification for development
                    header, payload, signature = token.split(".")
                    import base64
                    import json

                    # Decode payload (add padding if needed)
                    payload_padded = payload + "=" * (4 - len(payload) % 4)
                    decoded_payload = base64.urlsafe_b64decode(payload_padded)
                    payload_data = json.loads(decoded_payload)

                    # Basic validation of payload structure
                    if "sub" in payload_data and "role" in payload_data:
                        return {
                            "valid": True,
                            "user_id": payload_data.get("sub"),
                            "role": payload_data.get("role", "anon"),
                            "email": payload_data.get("email"),
                            "development_mode": True,
                        }
                    else:
                        return {
                            "valid": False,
                            "error": "Invalid JWT payload structure",
                        }

                except Exception as decode_error:
                    logger.error(f"Development JWT decode error: {decode_error}")
                    return {"valid": False, "error": "Invalid JWT format"}

            # Production mode - proper JWT validation
            decoded = jwt.decode(
                token, jwt_secret, algorithms=["HS256"], options={"verify_exp": True}
            )

            return {
                "valid": True,
                "user_id": decoded.get("sub"),
                "role": decoded.get("role", "user"),
                "email": decoded.get("email"),
            }

        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": f"Invalid token: {str(e)}"}
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {"valid": False, "error": "Token validation failed"}

    async def _simulate_auth_delay(self) -> None:
        """Simulate realistic authentication delay."""
        import asyncio

        await asyncio.sleep(0.01)  # 10ms delay

    def _create_security_response(
        self, security_result: dict[str, Any]
    ) -> JSONResponse:
        """Create appropriate response for security check failure."""
        if security_result["reason"] == "rate_limited":
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests, please try again later",
                },
                headers={"Retry-After": "60"},
            )

        elif security_result["reason"] == "insufficient_authorization":
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Authentication required",
                    "detail": "Valid authentication token required for this operation",
                },
            )

        else:
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Access denied",
                    "detail": "Insufficient permissions for this operation",
                },
            )

    def _add_security_headers(
        self, response: Response, auth_request: AuthenticatedRequest
    ) -> None:
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if auth_request.service_role_used:
            response.headers["X-Service-Role-Used"] = "true"

        if auth_request.authenticated:
            response.headers["X-Authenticated"] = "true"

    def _log_request(
        self, auth_request: AuthenticatedRequest, status_code: int, duration: float
    ) -> None:
        """Log request with security context."""
        log_data = auth_request.to_log_dict()
        log_data.update(
            {
                "status_code": status_code,
                "total_duration_ms": duration * 1000,
            }
        )

        if status_code >= 400:
            logger.warning(
                f"Request failed: {auth_request.method} {auth_request.path}",
                extra=log_data,
            )
        else:
            logger.info(
                f"Request completed: {auth_request.method} {auth_request.path}",
                extra=log_data,
            )


class AuthenticationMiddleware:
    """Dedicated authentication middleware (legacy compatibility)."""

    def __init__(self, config: AuthConfig):
        self.security_middleware = SecurityMiddleware(config)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Execute authentication middleware."""
        return await self.security_middleware(request, call_next)


class InputValidationMiddleware:
    """Input validation and sanitization middleware."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.max_size_bytes = int(config.max_request_size_mb * 1024 * 1024)

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Execute input validation middleware."""
        if not self.config.enable_input_validation:
            return await call_next(request)

        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "success": False,
                        "error": "Request too large",
                        "detail": f"Request size exceeds {self.config.max_request_size_mb}MB limit",
                    },
                )

            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if not content_type.startswith(
                    ("application/json", "multipart/form-data")
                ):
                    return JSONResponse(
                        status_code=415,
                        content={
                            "success": False,
                            "error": "Unsupported media type",
                            "detail": "Only JSON and form data are supported",
                        },
                    )

            return await call_next(request)

        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Invalid request",
                    "detail": "Request validation failed",
                },
            )
