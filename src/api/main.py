"""FastAPI application for Fresh OR-Tools Solver API.

Provides REST endpoints for GUI integration with the constraint solver.
Supports the 3-phase constraint system with proper error handling.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.rest.solver_endpoints import router as solver_router
from src.api.security import SecurityMiddleware
from src.api.security.config import get_security_config, get_security_config_manager
from src.api.security.exceptions import setup_security_exception_handlers
from src.data.loaders.optimized_database import OptimizedDatabaseLoader
from src.operations.performance_monitoring import PerformanceMonitor
from src.solver.utils.logging_config import setup_logging

# Global performance monitor and security config
performance_monitor = PerformanceMonitor()
security_config_manager = get_security_config_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting Fresh OR-Tools Solver API...")

    # Initialize performance monitoring
    performance_monitor.start_monitoring()

    # Validate system components
    try:
        # Test database connection
        loader = OptimizedDatabaseLoader(use_test_tables=True)
        patterns = loader.load_available_patterns()
        logger.info(
            f"Database connection successful - {len(patterns)} patterns available"
        )

        # Record startup performance
        performance_monitor.record_startup_metric("database_init", True)

        # Initialize security system
        security_config = get_security_config()
        logger.info(f"Security system initialized - enabled: {security_config.enabled}")
        performance_monitor.record_startup_metric("security_init", True)

    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        performance_monitor.record_startup_metric("database_init", False, str(e))
        performance_monitor.record_startup_metric("security_init", False, str(e))

    logger.info("API startup complete")
    yield

    # Shutdown
    logger.info("Shutting down Fresh OR-Tools Solver API...")
    performance_monitor.stop_monitoring()
    logger.info("API shutdown complete")


# Setup logging
setup_logging(level="INFO", enable_file_logging=True)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Fresh OR-Tools Solver API",
    description="REST API for constraint programming solver with GUI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add security middleware (before other middleware for proper ordering)
security_config = get_security_config()
if security_config.enabled:
    app.add_middleware(SecurityMiddleware, config=security_config)
    logger.info("Security middleware enabled")
else:
    logger.warning("Security middleware disabled - development mode")

# Add CORS middleware for GUI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # GUI dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup security exception handlers
setup_security_exception_handlers(app)


# Add performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor request performance and log metrics."""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    # Record performance metrics
    performance_monitor.record_request_metric(
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        response_time=process_time,
    )

    # Add performance headers
    response.headers["X-Process-Time"] = str(process_time)

    return response


# Include solver endpoints
app.include_router(solver_router)


# Add security management endpoint
@app.get("/api/v1/security")
async def get_security_status():
    """Get current security configuration and status."""
    return {"success": True, "security": security_config_manager.get_security_summary()}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    security_summary = security_config_manager.get_security_summary()

    return {
        "name": "Fresh OR-Tools Solver API",
        "version": "1.0.0",
        "status": "running",
        "security": {
            "enabled": security_summary["enabled"],
            "level": security_summary["default_level"],
            "service_role_available": security_summary["service_role_escalation"],
        },
        "endpoints": {
            "health": "/api/v1/health",
            "patterns": "/api/v1/patterns",
            "solve": "/api/v1/solve",
            "validate": "/api/v1/validate",
            "security": "/api/v1/security",
            "docs": "/docs",
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": (
                str(exc) if logger.level <= logging.DEBUG else "Contact administrator"
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Fresh OR-Tools Solver API server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
