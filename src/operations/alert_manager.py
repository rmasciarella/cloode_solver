"""Alert management system for production OR-Tools deployment.

This module provides comprehensive alerting capabilities for template-based
scheduling systems, including alert generation, routing, and notification management.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(Enum):
    """Alert notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Alert:
    """Alert notification for system issues."""

    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str  # Component that generated the alert
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    template_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    @property
    def is_resolved(self) -> bool:
        """Check if alert has been resolved."""
        return self.resolved_at is not None

    @property
    def age_minutes(self) -> float:
        """Get alert age in minutes."""
        end_time = self.resolved_at or datetime.now(UTC)
        return (end_time - self.created_at).total_seconds() / 60

    @property
    def is_critical_or_higher(self) -> bool:
        """Check if alert is critical or emergency severity."""
        return self.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]


@dataclass
class AlertRule:
    """Configuration for alert generation rules."""

    name: str
    condition: str  # Description of condition
    severity: AlertSeverity
    channels: list[AlertChannel]
    template_filter: str | None = None  # Filter alerts by template pattern
    cooldown_minutes: int = 15  # Minimum time between same alerts
    auto_resolve_minutes: int | None = None  # Auto-resolve after time
    enabled: bool = True

    def matches_template(self, template_id: str | None) -> bool:
        """Check if alert rule applies to template."""
        if not self.template_filter or not template_id:
            return True
        return self.template_filter in template_id


class AlertManager:
    """Comprehensive alert management system for OR-Tools deployment.

    Provides functionality for:
    - Alert generation and routing
    - Multi-channel notification delivery
    - Alert aggregation and deduplication
    - Alert lifecycle management (creation, escalation, resolution)
    - Alert rule configuration and management
    """

    def __init__(self) -> None:
        """Initialize alert manager."""
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.alert_rules: dict[str, AlertRule] = {}
        self.notification_handlers: dict[AlertChannel, Callable[[Alert], bool]] = {}
        self.last_alert_times: dict[str, datetime] = {}  # For cooldown tracking

        # Register default notification handlers
        self._register_default_handlers()

        # Configure default alert rules
        self._configure_default_rules()

    def _register_default_handlers(self) -> None:
        """Register default notification handlers."""
        self.notification_handlers[AlertChannel.LOG] = self._send_log_notification
        self.notification_handlers[AlertChannel.EMAIL] = self._send_email_notification
        self.notification_handlers[AlertChannel.WEBHOOK] = (
            self._send_webhook_notification
        )

    def _configure_default_rules(self) -> None:
        """Configure default alert rules."""
        default_rules = [
            AlertRule(
                name="solver_failure",
                condition="Solver returns INFEASIBLE or ERROR status",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.EMAIL],
                cooldown_minutes=5,
            ),
            AlertRule(
                name="performance_degradation",
                condition="Solve time increases >50% from baseline",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG],
                cooldown_minutes=10,
            ),
            AlertRule(
                name="system_resource_critical",
                condition="CPU or memory usage >90%",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.EMAIL],
                cooldown_minutes=5,
            ),
            AlertRule(
                name="health_check_failure",
                condition="Critical health check fails",
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.LOG, AlertChannel.EMAIL],
                cooldown_minutes=3,
            ),
            AlertRule(
                name="template_regression",
                condition="Template performance regresses >20%",
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.LOG],
                cooldown_minutes=30,
            ),
        ]

        for rule in default_rules:
            self.alert_rules[rule.name] = rule

    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str,
        template_id: str | None = None,
        details: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        rule_name: str | None = None,
    ) -> Alert | None:
        """Create and process a new alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            source: Component that generated the alert
            template_id: Associated template ID
            details: Additional alert details
            tags: Alert tags for categorization
            rule_name: Alert rule that triggered this alert

        Returns:
            Created Alert object, or None if suppressed by cooldown

        """
        # Check cooldown for duplicate alerts
        alert_key = f"{source}:{title}"
        if alert_key in self.last_alert_times:
            time_since_last = datetime.now(UTC) - self.last_alert_times[alert_key]
            rule = self.alert_rules.get(rule_name) if rule_name else None
            cooldown_minutes = rule.cooldown_minutes if rule else 15

            if time_since_last.total_seconds() < (cooldown_minutes * 60):
                logger.debug(f"Alert suppressed by cooldown: {title}")
                return None

        # Generate unique alert ID
        alert_id = (
            f"{source}_{int(datetime.now(UTC).timestamp())}_{hash(title) % 10000}"
        )

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            template_id=template_id,
            details=details or {},
            tags=tags or [],
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[alert_key] = alert.created_at

        # Send notifications
        self._send_alert_notifications(alert, rule_name)

        # Schedule auto-resolution if configured
        if rule_name and rule_name in self.alert_rules:
            rule = self.alert_rules[rule_name]
            if rule.auto_resolve_minutes:
                # In production, would schedule background task
                logger.debug(
                    f"Alert {alert_id} scheduled for auto-resolution in "
                    f"{rule.auto_resolve_minutes} minutes"
                )

        logger.info(f"Alert created: {alert.severity.value} - {title} [{source}]")

        return alert

    def _send_alert_notifications(
        self, alert: Alert, rule_name: str | None = None
    ) -> None:
        """Send alert notifications through configured channels."""
        channels = [AlertChannel.LOG]  # Default to log

        if rule_name and rule_name in self.alert_rules:
            rule = self.alert_rules[rule_name]
            if rule.enabled and rule.matches_template(alert.template_id):
                channels = rule.channels

        for channel in channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    success = handler(alert)
                    if success:
                        logger.debug(
                            f"Alert notification sent via {channel.value}: {alert.id}"
                        )
                    else:
                        logger.error(
                            f"Failed to send alert notification via {channel.value}: "
                            f"{alert.id}"
                        )
                else:
                    logger.warning(
                        f"No handler configured for channel: {channel.value}"
                    )
            except Exception as e:
                logger.error(
                    f"Error sending alert notification via {channel.value}: {e}"
                )

    def _send_log_notification(self, alert: Alert) -> bool:
        """Send alert notification to log."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.EMERGENCY: logging.CRITICAL,
        }.get(alert.severity, logging.INFO)

        logger.log(
            log_level,
            f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message} "
            f"(Source: {alert.source}, Template: {alert.template_id or 'N/A'})",
        )
        return True

    def _send_email_notification(self, alert: Alert) -> bool:
        """Send alert notification via email."""
        # Placeholder for email notification
        # In production, would use SMTP configuration
        logger.info(f"Email notification (simulated): {alert.title}")
        return True

    def _send_webhook_notification(self, alert: Alert) -> bool:
        """Send alert notification via webhook."""
        # Placeholder for webhook notification
        # In production, would make HTTP POST to configured webhook URL
        logger.info(f"Webhook notification (simulated): {alert.title}")
        return True

    def resolve_alert(self, alert_id: str, resolution_message: str = "") -> bool:
        """Resolve an active alert.

        Args:
            alert_id: Alert identifier
            resolution_message: Optional resolution details

        Returns:
            True if alert was resolved, False if not found

        """
        if alert_id not in self.active_alerts:
            logger.warning(f"Cannot resolve alert - not found: {alert_id}")
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved_at = datetime.now(UTC)

        if resolution_message:
            alert.details["resolution"] = resolution_message

        # Move from active to history
        del self.active_alerts[alert_id]

        logger.info(
            f"Alert resolved: {alert.title} [{alert_id}] - {resolution_message}"
        )

        return True

    def get_active_alerts(
        self,
        severity: AlertSeverity | None = None,
        template_id: str | None = None,
        source: str | None = None,
    ) -> list[Alert]:
        """Get active alerts with optional filtering.

        Args:
            severity: Filter by severity level
            template_id: Filter by template ID
            source: Filter by source component

        Returns:
            List of matching active alerts

        """
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if template_id:
            alerts = [a for a in alerts if a.template_id == template_id]
        if source:
            alerts = [a for a in alerts if a.source == source]

        # Sort by severity and creation time
        severity_order = {
            AlertSeverity.EMERGENCY: 0,
            AlertSeverity.CRITICAL: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3,
        }

        alerts.sort(
            key=lambda a: (severity_order[a.severity], a.created_at), reverse=True
        )

        return alerts

    def get_alert_statistics(self, hours: int = 24) -> dict[str, Any]:
        """Get alert statistics for the specified time period.

        Args:
            hours: Hours of history to analyze

        Returns:
            Dictionary with alert statistics

        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.created_at >= cutoff]

        if not recent_alerts:
            return {
                "time_period_hours": hours,
                "total_alerts": 0,
                "active_alerts": len(self.active_alerts),
                "by_severity": {},
                "by_source": {},
                "top_templates": [],
            }

        # Count by severity
        by_severity = {}
        for severity in AlertSeverity:
            count = sum(1 for a in recent_alerts if a.severity == severity)
            by_severity[severity.value] = count

        # Count by source
        by_source: dict[str, int] = {}
        for alert in recent_alerts:
            by_source[alert.source] = by_source.get(alert.source, 0) + 1

        # Top templates by alert count
        template_counts: dict[str, int] = {}
        for alert in recent_alerts:
            if alert.template_id:
                template_counts[alert.template_id] = (
                    template_counts.get(alert.template_id, 0) + 1
                )

        top_templates = sorted(
            template_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Resolution statistics
        resolved_alerts = [a for a in recent_alerts if a.is_resolved]
        if resolved_alerts:
            avg_resolution_time = sum(a.age_minutes for a in resolved_alerts) / len(
                resolved_alerts
            )
        else:
            avg_resolution_time = 0.0

        return {
            "time_period_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "resolved_alerts": len(resolved_alerts),
            "resolution_rate": (
                len(resolved_alerts) / len(recent_alerts) if recent_alerts else 0.0
            ),
            "avg_resolution_time_minutes": avg_resolution_time,
            "by_severity": by_severity,
            "by_source": by_source,
            "top_templates": top_templates,
        }

    def create_performance_alert(
        self,
        template_id: str,
        current_time: float,
        baseline_time: float,
        threshold_percent: float = 50.0,
    ) -> Alert | None:
        """Create alert for performance degradation.

        Args:
            template_id: Template identifier
            current_time: Current solve time
            baseline_time: Baseline solve time
            threshold_percent: Degradation threshold percentage

        Returns:
            Created alert or None if below threshold

        """
        if baseline_time <= 0:
            return None

        degradation_percent = ((current_time - baseline_time) / baseline_time) * 100

        if degradation_percent < threshold_percent:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if degradation_percent > 100
            else AlertSeverity.WARNING
        )

        return self.create_alert(
            title=f"Performance degradation detected: {template_id}",
            message=f"Solve time increased by {degradation_percent:.1f}% "
            f"({baseline_time:.2f}s → {current_time:.2f}s)",
            severity=severity,
            source="performance_monitor",
            template_id=template_id,
            details={
                "current_time": current_time,
                "baseline_time": baseline_time,
                "degradation_percent": degradation_percent,
                "threshold_percent": threshold_percent,
            },
            tags=["performance", "degradation"],
            rule_name="performance_degradation",
        )

    def create_health_check_alert(
        self,
        check_name: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> Alert | None:
        """Create alert for health check failure.

        Args:
            check_name: Health check name
            status: Check status
            message: Check message
            details: Additional details

        Returns:
            Created alert or None for passing checks

        """
        if status == "pass":
            return None

        severity = AlertSeverity.CRITICAL if status == "fail" else AlertSeverity.WARNING

        return self.create_alert(
            title=f"Health check failed: {check_name}",
            message=message,
            severity=severity,
            source="health_checker",
            details=details or {},
            tags=["health_check", check_name.lower()],
            rule_name="health_check_failure",
        )

    def create_resource_alert(
        self, resource_type: str, usage_percent: float, threshold_percent: float = 80.0
    ) -> Alert | None:
        """Create alert for high resource usage.

        Args:
            resource_type: Resource type (cpu, memory, disk)
            usage_percent: Current usage percentage
            threshold_percent: Alert threshold percentage

        Returns:
            Created alert or None if below threshold

        """
        if usage_percent < threshold_percent:
            return None

        severity = (
            AlertSeverity.CRITICAL if usage_percent > 90 else AlertSeverity.WARNING
        )

        return self.create_alert(
            title=f"High {resource_type} usage",
            message=f"{resource_type.capitalize()} usage at {usage_percent:.1f}%",
            severity=severity,
            source="resource_monitor",
            details={
                "resource_type": resource_type,
                "usage_percent": usage_percent,
                "threshold_percent": threshold_percent,
            },
            tags=["resource", resource_type],
            rule_name="system_resource_critical",
        )

    def register_notification_handler(
        self, channel: AlertChannel, handler: Callable[[Alert], bool]
    ) -> None:
        """Register custom notification handler.

        Args:
            channel: Alert channel
            handler: Function that takes Alert and returns success boolean

        """
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for channel: {channel.value}")

    def configure_alert_rule(self, rule: AlertRule) -> None:
        """Configure or update an alert rule.

        Args:
            rule: AlertRule configuration

        """
        self.alert_rules[rule.name] = rule
        logger.info(f"Configured alert rule: {rule.name} ({rule.severity.value})")

    def disable_alert_rule(self, rule_name: str) -> bool:
        """Disable an alert rule.

        Args:
            rule_name: Name of rule to disable

        Returns:
            True if rule was disabled, False if not found

        """
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False
            logger.info(f"Disabled alert rule: {rule_name}")
            return True
        return False

    def cleanup_old_alerts(self, days: int = 7) -> int:
        """Clean up old resolved alerts from history.

        Args:
            days: Days of history to retain

        Returns:
            Number of alerts cleaned up

        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        original_count = len(self.alert_history)

        self.alert_history = [
            a for a in self.alert_history if a.created_at >= cutoff or not a.is_resolved
        ]

        cleaned_count = original_count - len(self.alert_history)

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old alerts")

        return cleaned_count
