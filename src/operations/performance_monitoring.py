"""Production Performance Monitoring for OR-Tools solver systems.

This module provides real-time performance monitoring, metric collection,
and system health assessment for production template-based scheduling deployments.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SystemHealthStatus(Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PerformanceMetric:
    """Performance metric measurement."""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    template_id: str | None = None
    instance_count: int | None = None
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def age_seconds(self) -> float:
        """Get metric age in seconds."""
        return (datetime.now(UTC) - self.timestamp).total_seconds()

    @property
    def is_stale(self) -> bool:
        """Check if metric is older than 5 minutes."""
        return self.age_seconds > 300


@dataclass
class SystemHealthMetrics:
    """Comprehensive system health metrics."""

    status: SystemHealthStatus
    timestamp: datetime
    solver_performance: dict[str, float] = field(default_factory=dict)
    resource_utilization: dict[str, float] = field(default_factory=dict)
    error_rates: dict[str, float] = field(default_factory=dict)
    active_templates: int = 0
    recent_failures: int = 0

    @property
    def overall_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Penalize for high error rates
        total_error_rate = sum(self.error_rates.values())
        score -= min(50, total_error_rate * 10)

        # Penalize for poor performance
        avg_solve_time = self.solver_performance.get("avg_solve_time", 0)
        if avg_solve_time > 60:  # More than 1 minute
            score -= min(30, (avg_solve_time - 60) / 10)

        # Penalize for high resource usage
        cpu_usage = self.resource_utilization.get("cpu_percent", 0)
        memory_usage = self.resource_utilization.get("memory_percent", 0)
        if cpu_usage > 80:
            score -= min(20, (cpu_usage - 80) / 2)
        if memory_usage > 80:
            score -= min(20, (memory_usage - 80) / 2)

        # Penalize for recent failures
        score -= min(20, self.recent_failures * 2)

        return max(0, score)


class PerformanceMonitor:
    """Production performance monitoring system.

    Provides comprehensive monitoring of:
    - Solver performance metrics
    - Resource utilization
    - Error rates and failure patterns
    - Template performance trends
    - System health assessment
    """

    def __init__(self, retention_hours: int = 24):
        """Initialize performance monitor.

        Args:
            retention_hours: How long to retain metrics (default: 24 hours)

        """
        self.retention_hours = retention_hours
        self.metrics: list[PerformanceMetric] = []
        self.health_history: list[SystemHealthMetrics] = []
        self.failure_count = 0
        self.last_health_check = datetime.now(UTC)

    def record_solve_performance(
        self,
        template_id: str,
        solve_time: float,
        instance_count: int,
        solver_status: str,
        memory_usage_mb: float = 0,
        objective_value: float | None = None,
    ) -> None:
        """Record solver performance metrics.

        Args:
            template_id: Template identifier
            solve_time: Solve time in seconds
            instance_count: Number of instances solved
            solver_status: Solver status (OPTIMAL, FEASIBLE, etc.)
            memory_usage_mb: Memory usage in MB
            objective_value: Solution objective value

        """
        timestamp = datetime.now(UTC)

        # Core performance metrics
        self.metrics.extend(
            [
                PerformanceMetric(
                    name="solve_time",
                    value=solve_time,
                    unit="seconds",
                    timestamp=timestamp,
                    template_id=template_id,
                    instance_count=instance_count,
                    tags={"status": solver_status},
                ),
                PerformanceMetric(
                    name="memory_usage",
                    value=memory_usage_mb,
                    unit="mb",
                    timestamp=timestamp,
                    template_id=template_id,
                    instance_count=instance_count,
                ),
                PerformanceMetric(
                    name="instances_solved",
                    value=instance_count,
                    unit="count",
                    timestamp=timestamp,
                    template_id=template_id,
                ),
            ]
        )

        # Performance per instance
        if instance_count > 0:
            self.metrics.append(
                PerformanceMetric(
                    name="solve_time_per_instance",
                    value=solve_time / instance_count,
                    unit="seconds/instance",
                    timestamp=timestamp,
                    template_id=template_id,
                    instance_count=instance_count,
                )
            )

        # Success/failure tracking
        is_success = solver_status in ["OPTIMAL", "FEASIBLE"]
        self.metrics.append(
            PerformanceMetric(
                name="solve_success",
                value=1.0 if is_success else 0.0,
                unit="boolean",
                timestamp=timestamp,
                template_id=template_id,
                tags={"status": solver_status},
            )
        )

        if not is_success:
            self.failure_count += 1
            logger.warning(f"Solver failure recorded: {template_id} - {solver_status}")

        # Objective value if available
        if objective_value is not None:
            self.metrics.append(
                PerformanceMetric(
                    name="objective_value",
                    value=objective_value,
                    unit="units",
                    timestamp=timestamp,
                    template_id=template_id,
                    instance_count=instance_count,
                )
            )

        # Clean up old metrics
        self._cleanup_old_metrics()

        logger.debug(
            f"Recorded performance: {template_id} - {solve_time:.2f}s, "
            f"{instance_count} instances, {solver_status}"
        )

    def record_system_metrics(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_usage_percent: float,
        active_connections: int = 0,
    ) -> None:
        """Record system resource metrics.

        Args:
            cpu_percent: CPU usage percentage (0-100)
            memory_percent: Memory usage percentage (0-100)
            disk_usage_percent: Disk usage percentage (0-100)
            active_connections: Number of active connections

        """
        timestamp = datetime.now(UTC)

        self.metrics.extend(
            [
                PerformanceMetric(
                    name="cpu_usage",
                    value=cpu_percent,
                    unit="percent",
                    timestamp=timestamp,
                ),
                PerformanceMetric(
                    name="memory_usage",
                    value=memory_percent,
                    unit="percent",
                    timestamp=timestamp,
                ),
                PerformanceMetric(
                    name="disk_usage",
                    value=disk_usage_percent,
                    unit="percent",
                    timestamp=timestamp,
                ),
                PerformanceMetric(
                    name="active_connections",
                    value=active_connections,
                    unit="count",
                    timestamp=timestamp,
                ),
            ]
        )

        logger.debug(
            f"Recorded system metrics: CPU {cpu_percent:.1f}%, "
            f"Memory {memory_percent:.1f}%, Disk {disk_usage_percent:.1f}%"
        )

    def get_current_health(self) -> SystemHealthMetrics:
        """Get current system health assessment.

        Returns:
            SystemHealthMetrics with current health status

        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=10)  # Last 10 minutes

        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        # Calculate solver performance
        solve_times = [m.value for m in recent_metrics if m.name == "solve_time"]
        success_metrics = [m.value for m in recent_metrics if m.name == "solve_success"]

        solver_performance = {}
        if solve_times:
            solver_performance = {
                "avg_solve_time": statistics.mean(solve_times),
                "max_solve_time": max(solve_times),
                "min_solve_time": min(solve_times),
                "solve_count": len(solve_times),
            }

        # Calculate resource utilization
        cpu_metrics = [m.value for m in recent_metrics if m.name == "cpu_usage"]
        memory_metrics = [m.value for m in recent_metrics if m.name == "memory_usage"]

        resource_utilization = {}
        if cpu_metrics:
            resource_utilization["cpu_percent"] = statistics.mean(cpu_metrics)
        if memory_metrics:
            resource_utilization["memory_percent"] = statistics.mean(memory_metrics)

        # Calculate error rates
        total_solves = len(success_metrics)
        failed_solves = sum(1 for s in success_metrics if s == 0.0)
        error_rate = (failed_solves / total_solves) if total_solves > 0 else 0.0

        error_rates = {"solve_failure_rate": error_rate}

        # Count active templates
        template_ids = {m.template_id for m in recent_metrics if m.template_id}
        active_templates = len(template_ids)

        # Recent failures (last hour)
        hour_cutoff = now - timedelta(hours=1)
        recent_failures = sum(
            1
            for m in self.metrics
            if m.name == "solve_success"
            and m.value == 0.0
            and m.timestamp >= hour_cutoff
        )

        # Determine overall health status
        health_score = self._calculate_health_score(
            solver_performance, resource_utilization, error_rates, recent_failures
        )

        if health_score >= 80:
            status = SystemHealthStatus.HEALTHY
        elif health_score >= 60:
            status = SystemHealthStatus.WARNING
        else:
            status = SystemHealthStatus.CRITICAL

        health_metrics = SystemHealthMetrics(
            status=status,
            timestamp=now,
            solver_performance=solver_performance,
            resource_utilization=resource_utilization,
            error_rates=error_rates,
            active_templates=active_templates,
            recent_failures=recent_failures,
        )

        # Store health history
        self.health_history.append(health_metrics)
        if len(self.health_history) > 100:  # Keep last 100 health checks
            self.health_history = self.health_history[-100:]

        self.last_health_check = now

        logger.info(
            f"Health check: {status.value} (score: {health_score:.1f}) - "
            f"{active_templates} templates, {recent_failures} recent failures"
        )

        return health_metrics

    def _calculate_health_score(
        self,
        solver_performance: dict[str, float],
        resource_utilization: dict[str, float],
        error_rates: dict[str, float],
        recent_failures: int,
    ) -> float:
        """Calculate health score (0-100)."""
        score = 100.0

        # Performance penalties
        avg_solve_time = solver_performance.get("avg_solve_time", 0)
        if avg_solve_time > 30:  # More than 30 seconds
            score -= min(25, (avg_solve_time - 30) / 2)

        # Resource utilization penalties
        cpu_usage = resource_utilization.get("cpu_percent", 0)
        memory_usage = resource_utilization.get("memory_percent", 0)

        if cpu_usage > 70:
            score -= min(20, (cpu_usage - 70) / 2)
        if memory_usage > 70:
            score -= min(20, (memory_usage - 70) / 2)

        # Error rate penalties
        error_rate = error_rates.get("solve_failure_rate", 0)
        if error_rate > 0.1:  # More than 10% failure rate
            score -= min(30, error_rate * 100)

        # Recent failure penalties
        if recent_failures > 0:
            score -= min(25, recent_failures * 5)

        return max(0, score)

    def get_template_performance_summary(
        self, template_id: str, hours: int = 1
    ) -> dict[str, Any]:
        """Get performance summary for a specific template.

        Args:
            template_id: Template identifier
            hours: Hours of history to analyze

        Returns:
            Dictionary with performance summary

        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        template_metrics = [
            m
            for m in self.metrics
            if m.template_id == template_id and m.timestamp >= cutoff
        ]

        if not template_metrics:
            return {"error": f"No metrics found for template {template_id}"}

        # Solve times
        solve_times = [m.value for m in template_metrics if m.name == "solve_time"]
        success_count = sum(
            1 for m in template_metrics if m.name == "solve_success" and m.value == 1.0
        )
        total_solves = len([m for m in template_metrics if m.name == "solve_success"])

        # Instance counts
        instance_counts = [
            m.instance_count for m in template_metrics if m.instance_count
        ]

        summary = {
            "template_id": template_id,
            "time_period_hours": hours,
            "total_solves": total_solves,
            "successful_solves": success_count,
            "success_rate": success_count / total_solves if total_solves > 0 else 0.0,
        }

        if solve_times:
            summary.update(
                {
                    "avg_solve_time": statistics.mean(solve_times),
                    "max_solve_time": max(solve_times),
                    "min_solve_time": min(solve_times),
                    "median_solve_time": statistics.median(solve_times),
                }
            )

        if instance_counts:
            summary.update(
                {
                    "avg_instances": statistics.mean(instance_counts),
                    "max_instances": max(instance_counts),
                    "total_instances": sum(instance_counts),
                }
            )

        return summary

    def get_performance_trends(self, hours: int = 24) -> dict[str, Any]:
        """Get performance trends over time.

        Args:
            hours: Hours of history to analyze

        Returns:
            Dictionary with trend analysis

        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        if not recent_metrics:
            return {"error": "No metrics available for trend analysis"}

        # Group metrics by hour
        hourly_data: dict[str, list[PerformanceMetric]] = {}
        for metric in recent_metrics:
            hour_key = metric.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            hourly_data[hour_key].append(metric)

        # Calculate trends
        hourly_stats: list[dict[str, Any]] = []
        for hour, metrics in sorted(hourly_data.items()):
            solve_times = [m.value for m in metrics if m.name == "solve_time"]
            successes = [m.value for m in metrics if m.name == "solve_success"]

            hour_stats: dict[str, Any] = {
                "hour": hour,
                "solve_count": len(solve_times),
                "avg_solve_time": statistics.mean(solve_times) if solve_times else 0.0,
                "success_rate": statistics.mean(successes) if successes else 0.0,
            }
            hourly_stats.append(hour_stats)

        # Calculate overall trends
        if len(hourly_stats) >= 2:
            first_half = hourly_stats[: len(hourly_stats) // 2]
            second_half = hourly_stats[len(hourly_stats) // 2 :]

            first_avg_time = statistics.mean(
                h["avg_solve_time"] for h in first_half if h["avg_solve_time"] > 0
            )
            second_avg_time = statistics.mean(
                h["avg_solve_time"] for h in second_half if h["avg_solve_time"] > 0
            )

            time_trend = (
                "improving" if second_avg_time < first_avg_time else "degrading"
            )
        else:
            time_trend = "insufficient_data"

        return {
            "time_period_hours": hours,
            "hourly_stats": hourly_stats,
            "performance_trend": time_trend,
            "total_metrics": len(recent_metrics),
            "unique_templates": len(
                {m.template_id for m in recent_metrics if m.template_id}
            ),
        }

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        cutoff = datetime.now(UTC) - timedelta(hours=self.retention_hours)
        original_count = len(self.metrics)

        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        removed_count = original_count - len(self.metrics)
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old metrics")

    def reset_metrics(self) -> None:
        """Reset all collected metrics (for testing/development)."""
        self.metrics.clear()
        self.health_history.clear()
        self.failure_count = 0
        logger.info("All performance metrics reset")

    def export_metrics(
        self, template_id: str | None = None, hours: int = 1
    ) -> list[dict[str, Any]]:
        """Export metrics for external monitoring systems.

        Args:
            template_id: Filter by template ID (optional)
            hours: Hours of history to export

        Returns:
            List of metric dictionaries

        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        filtered_metrics = [
            m
            for m in self.metrics
            if m.timestamp >= cutoff
            and (not template_id or m.template_id == template_id)
        ]

        exported = []
        for metric in filtered_metrics:
            exported.append(
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "template_id": metric.template_id,
                    "instance_count": metric.instance_count,
                    "tags": metric.tags,
                }
            )

        return exported
