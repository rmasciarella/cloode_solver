"""Centralized logging configuration for Fresh Solver OR-Tools.

This module provides standardized logging configuration for the Fresh Solver
constraint programming project, enabling structured logging across all components
while maintaining appropriate log levels for different contexts.
"""

import logging
import logging.config
from pathlib import Path
from typing import Any


def setup_logging(
    level: str = "INFO",
    enable_file_logging: bool = True,
    log_dir: Path | None = None,
    enable_performance_logging: bool = False,
) -> None:
    """Configure standardized logging for Fresh Solver.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_file_logging: Whether to write logs to files
        log_dir: Directory for log files (default: project_root/logs)
        enable_performance_logging: Enable detailed performance logging

    """
    if log_dir is None:
        log_dir = Path.cwd() / "logs"

    log_dir.mkdir(exist_ok=True)

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d: %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "performance": {
                "format": "%(asctime)s [PERF] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S.%f",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "solver": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "data": {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": level, "handlers": ["console"]},
    }

    # Add file logging if enabled
    if enable_file_logging:
        config["handlers"].update(
            {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": level,
                    "formatter": "detailed",
                    "filename": str(log_dir / "fresh_solver.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(log_dir / "errors.log"),
                    "maxBytes": 10485760,
                    "backupCount": 3,
                },
            }
        )

        # Add file handlers to loggers
        for logger_name in ["solver", "data", "root"]:
            config["loggers"][logger_name]["handlers"].extend(["file", "error_file"])

    # Add performance logging if enabled
    if enable_performance_logging:
        config["handlers"]["performance"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "performance",
            "filename": str(log_dir / "performance.log"),
            "maxBytes": 10485760,
            "backupCount": 3,
        }

        config["loggers"]["performance"] = {
            "level": "INFO",
            "handlers": ["performance"],
            "propagate": False,
        }

    logging.config.dictConfig(config)


def get_performance_logger() -> logging.Logger:
    """Get specialized logger for performance metrics."""
    return logging.getLogger("performance")


def get_solver_logger(name: str) -> logging.Logger:
    """Get standardized logger for solver components."""
    return logging.getLogger(f"solver.{name}")


def get_data_logger(name: str) -> logging.Logger:
    """Get standardized logger for data components."""
    return logging.getLogger(f"data.{name}")


class SolverLogContext:
    """Context manager for solver-specific logging levels.

    Enables detailed logging for specific solver operations like
    constraint debugging or variable analysis.
    """

    def __init__(
        self,
        solver_name: str,
        debug_constraints: bool = False,
        debug_variables: bool = False,
        performance_tracking: bool = False,
    ):
        """Initialize solver logging context.

        Args:
            solver_name: Name of the solver for identification
            debug_constraints: Enable constraint debugging logs
            debug_variables: Enable variable creation debugging
            performance_tracking: Enable performance tracking

        """
        self.solver_name = solver_name
        self.debug_constraints = debug_constraints
        self.debug_variables = debug_variables
        self.performance_tracking = performance_tracking
        self.original_levels: dict[str, int] = {}

    def __enter__(self) -> "SolverLogContext":
        """Enable appropriate logging levels for solver context."""
        if self.debug_constraints:
            constraint_logger = logging.getLogger("solver.constraints")
            self.original_levels["solver.constraints"] = constraint_logger.level
            constraint_logger.setLevel(logging.DEBUG)

        if self.debug_variables:
            core_logger = logging.getLogger("solver.core")
            self.original_levels["solver.core"] = core_logger.level
            core_logger.setLevel(logging.DEBUG)

        if self.performance_tracking:
            perf_logger = get_performance_logger()
            perf_logger.info("Starting performance tracking: %s", self.solver_name)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore original logging levels."""
        for logger_name, original_level in self.original_levels.items():
            logging.getLogger(logger_name).setLevel(original_level)

        if self.performance_tracking:
            perf_logger = get_performance_logger()
            perf_logger.info("Completed performance tracking: %s", self.solver_name)


# Convenience functions for common logging patterns
def log_solver_progress(
    logger: logging.Logger, operation: str, details: str | None = None
) -> None:
    """Log solver progress with consistent formatting."""
    if details:
        logger.info("Solver %s: %s", operation, details)
    else:
        logger.info("Solver %s", operation)


def log_template_performance(
    template_id: str, instances: int, solve_time: float, speedup: float
) -> None:
    """Log template performance metrics in structured format."""
    perf_logger = get_performance_logger()
    perf_logger.info(
        "template_performance template_id=%s instances=%d "
        "solve_time=%.3fs speedup=%.1fx",
        template_id,
        instances,
        solve_time,
        speedup,
    )


def log_constraint_application(
    logger: logging.Logger, constraint_name: str, count: int
) -> None:
    """Log constraint application with consistent formatting."""
    logger.info("Applied %s constraints: %d constraints added", constraint_name, count)


def log_validation_issues(logger: logging.Logger, issues: list[str]) -> None:
    """Log validation issues in structured format."""
    if issues:
        logger.warning(
            "Validation issues found (%d): %s", len(issues), "; ".join(issues)
        )
    else:
        logger.info("Validation completed successfully")
