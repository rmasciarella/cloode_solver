"""Performance Regression Detection System for OR-Tools solver optimization.

This module provides automated regression detection, alerting, and performance
monitoring capabilities to ensure template-based optimization maintains
consistent performance improvements.
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PerformanceBaseline:
    """Performance baseline for regression detection."""

    template_id: str
    baseline_date: datetime
    solve_time: float
    speedup_factor: float
    instance_count: int
    parameters_used: dict[str, Any]
    confidence_interval: tuple[float, float]  # (lower, upper) bounds

    @property
    def is_current(self, days_threshold: int = 30) -> bool:
        """Check if baseline is recent enough to be current."""
        age = datetime.now(UTC) - self.baseline_date
        return age.days <= days_threshold


@dataclass
class PerformanceRegression:
    """Detected performance regression."""

    template_id: str
    detection_date: datetime
    regression_type: str  # "degradation", "timeout", "failure", "memory"
    severity: str  # "low", "medium", "high", "critical"

    # Performance metrics
    baseline_performance: float
    current_performance: float
    performance_change: float  # Percentage change (negative = worse)

    # Context information
    instance_count: int
    parameters_changed: bool = False
    system_changes: list[str] = field(default_factory=list)

    # Analysis
    root_cause_analysis: str = ""
    recommended_actions: list[str] = field(default_factory=list)

    @property
    def performance_impact(self) -> str:
        """Describe the performance impact."""
        if self.performance_change < -50:
            return "severe_degradation"
        elif self.performance_change < -25:
            return "significant_degradation"
        elif self.performance_change < -10:
            return "moderate_degradation"
        else:
            return "minor_degradation"


@dataclass
class RegressionAlert:
    """Alert for performance regression detection."""

    template_id: str
    alert_date: datetime
    alert_type: str  # "regression", "warning", "info"
    message: str
    regression: PerformanceRegression | None = None
    acknowledged: bool = False
    acknowledged_by: str = ""
    acknowledged_date: datetime | None = None

    @property
    def alert_age_hours(self) -> float:
        """Get alert age in hours."""
        return (datetime.now(UTC) - self.alert_date).total_seconds() / 3600

    def acknowledge(self, acknowledged_by: str) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_by = acknowledged_by
        self.acknowledged_date = datetime.now(UTC)


class RegressionDetector:
    """Automated performance regression detection and alerting system."""

    def __init__(self, storage_path: Path | None = None):
        """Initialize regression detector.

        Args:
            storage_path: Directory to store baselines and alerts

        """
        self.storage_path = storage_path or Path("performance/regression")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.baselines: dict[str, PerformanceBaseline] = {}
        self.regressions: list[PerformanceRegression] = []
        self.alerts: list[RegressionAlert] = []

        self._load_baselines()
        self._load_regression_history()

    def _load_baselines(self) -> None:
        """Load performance baselines from storage."""
        baseline_file = self.storage_path / "baselines.json"

        if not baseline_file.exists():
            return

        try:
            with open(baseline_file) as f:
                data = json.load(f)

            for template_id, baseline_data in data.items():
                baseline = PerformanceBaseline(
                    template_id=template_id,
                    baseline_date=datetime.fromisoformat(
                        baseline_data["baseline_date"]
                    ),
                    solve_time=baseline_data["solve_time"],
                    speedup_factor=baseline_data["speedup_factor"],
                    instance_count=baseline_data["instance_count"],
                    parameters_used=baseline_data["parameters_used"],
                    confidence_interval=tuple(baseline_data["confidence_interval"]),
                )
                self.baselines[template_id] = baseline

            logger.info(f"Loaded {len(self.baselines)} performance baselines")

        except Exception as e:
            logger.error(f"Failed to load performance baselines: {e}")

    def _load_regression_history(self) -> None:
        """Load regression history from storage."""
        regression_file = self.storage_path / "regressions.json"
        alerts_file = self.storage_path / "alerts.json"

        # Load regressions
        if regression_file.exists():
            try:
                with open(regression_file) as f:
                    data = json.load(f)

                for regression_data in data:
                    regression = PerformanceRegression(
                        template_id=regression_data["template_id"],
                        detection_date=datetime.fromisoformat(
                            regression_data["detection_date"]
                        ),
                        regression_type=regression_data["regression_type"],
                        severity=regression_data["severity"],
                        baseline_performance=regression_data["baseline_performance"],
                        current_performance=regression_data["current_performance"],
                        performance_change=regression_data["performance_change"],
                        instance_count=regression_data["instance_count"],
                        parameters_changed=regression_data.get(
                            "parameters_changed", False
                        ),
                        system_changes=regression_data.get("system_changes", []),
                        root_cause_analysis=regression_data.get(
                            "root_cause_analysis", ""
                        ),
                        recommended_actions=regression_data.get(
                            "recommended_actions", []
                        ),
                    )
                    self.regressions.append(regression)

                logger.debug(f"Loaded {len(self.regressions)} regression records")

            except Exception as e:
                logger.error(f"Failed to load regression history: {e}")

        # Load alerts
        if alerts_file.exists():
            try:
                with open(alerts_file) as f:
                    data = json.load(f)

                for alert_data in data:
                    alert = RegressionAlert(
                        template_id=alert_data["template_id"],
                        alert_date=datetime.fromisoformat(alert_data["alert_date"]),
                        alert_type=alert_data["alert_type"],
                        message=alert_data["message"],
                        acknowledged=alert_data.get("acknowledged", False),
                        acknowledged_by=alert_data.get("acknowledged_by", ""),
                        acknowledged_date=(
                            datetime.fromisoformat(alert_data["acknowledged_date"])
                            if alert_data.get("acknowledged_date")
                            else None
                        ),
                    )
                    self.alerts.append(alert)

                logger.debug(f"Loaded {len(self.alerts)} alert records")

            except Exception as e:
                logger.error(f"Failed to load alert history: {e}")

    def establish_baseline(
        self,
        template_id: str,
        solve_time: float,
        speedup_factor: float,
        instance_count: int,
        parameters: dict[str, Any],
        confidence_margin: float = 0.2,
    ) -> PerformanceBaseline:
        """Establish performance baseline for a template.

        Args:
            template_id: Template identifier
            solve_time: Baseline solve time in seconds
            speedup_factor: Template speedup factor vs legacy
            instance_count: Number of instances tested
            parameters: Solver parameters used
            confidence_margin: Confidence interval margin (20% by default)

        Returns:
            PerformanceBaseline established for the template

        """
        # Calculate confidence interval
        lower_bound = solve_time * (1 - confidence_margin)
        upper_bound = solve_time * (1 + confidence_margin)

        baseline = PerformanceBaseline(
            template_id=template_id,
            baseline_date=datetime.now(UTC),
            solve_time=solve_time,
            speedup_factor=speedup_factor,
            instance_count=instance_count,
            parameters_used=parameters.copy(),
            confidence_interval=(lower_bound, upper_bound),
        )

        self.baselines[template_id] = baseline
        self._save_baselines()

        logger.info(
            f"Established baseline for {template_id}: {solve_time:.2f}s "
            f"({speedup_factor:.1f}x speedup) with {instance_count} instances"
        )

        return baseline

    def detect_regression(
        self,
        template_id: str,
        current_solve_time: float,
        instance_count: int,
        parameters: dict[str, Any] | None = None,
        tolerance_factor: float = 1.3,  # 30% performance degradation threshold
    ) -> PerformanceRegression | None:
        """Detect performance regression for a template.

        Args:
            template_id: Template identifier
            current_solve_time: Current solve time in seconds
            instance_count: Number of instances tested
            parameters: Current solver parameters
            tolerance_factor: Performance degradation tolerance (1.3 = 30% slower)

        Returns:
            PerformanceRegression if detected, None otherwise

        """
        baseline = self.baselines.get(template_id)
        if not baseline:
            logger.warning(f"No baseline available for template {template_id}")
            return None

        if not baseline.is_current:
            logger.warning(f"Baseline for {template_id} is outdated")

        # Adjust baseline for instance count differences
        if instance_count != baseline.instance_count:
            # Simple scaling assumption - may need more sophisticated modeling
            scaling_factor = instance_count / baseline.instance_count
            adjusted_baseline = baseline.solve_time * scaling_factor
        else:
            adjusted_baseline = baseline.solve_time

        # Calculate performance change
        performance_change = (
            (current_solve_time - adjusted_baseline) / adjusted_baseline
        ) * 100

        # Check if regression occurred
        regression_detected = current_solve_time > (
            adjusted_baseline * tolerance_factor
        )

        if not regression_detected:
            return None

        # Determine regression severity
        severity = self._determine_regression_severity(performance_change)

        # Check if parameters changed
        parameters_changed = (
            parameters is not None and parameters != baseline.parameters_used
        )

        # Create regression record
        regression = PerformanceRegression(
            template_id=template_id,
            detection_date=datetime.now(UTC),
            regression_type="degradation",
            severity=severity,
            baseline_performance=adjusted_baseline,
            current_performance=current_solve_time,
            performance_change=performance_change,
            instance_count=instance_count,
            parameters_changed=parameters_changed,
            root_cause_analysis=self._analyze_root_cause(
                template_id, current_solve_time, adjusted_baseline, parameters_changed
            ),
            recommended_actions=self._generate_recommendations(
                template_id, performance_change, parameters_changed
            ),
        )

        # Record regression
        self.regressions.append(regression)
        self._save_regressions()

        # Create alert
        alert = RegressionAlert(
            template_id=template_id,
            alert_date=datetime.now(UTC),
            alert_type="regression",
            message=(
                f"Performance regression detected for {template_id}: "
                f"{performance_change:+.1f}% change ({current_solve_time:.2f}s vs "
                f"{adjusted_baseline:.2f}s baseline)"
            ),
            regression=regression,
        )

        self.alerts.append(alert)
        self._save_alerts()

        logger.warning(
            f"Performance regression detected for {template_id}: "
            f"{performance_change:+.1f}% change, severity: {severity}"
        )

        return regression

    def _determine_regression_severity(self, performance_change: float) -> str:
        """Determine regression severity based on performance change."""
        if performance_change > 100:  # More than 100% slower
            return "critical"
        elif performance_change > 50:  # More than 50% slower
            return "high"
        elif performance_change > 25:  # More than 25% slower
            return "medium"
        else:
            return "low"

    def _analyze_root_cause(
        self,
        template_id: str,
        current_time: float,
        baseline_time: float,
        parameters_changed: bool,
    ) -> str:
        """Analyze potential root cause of regression."""
        analysis_points = []

        if parameters_changed:
            analysis_points.append("Solver parameters were modified")

        performance_ratio = current_time / baseline_time
        if performance_ratio > 3.0:
            analysis_points.append(
                "Severe performance degradation suggests algorithmic changes"
            )
        elif performance_ratio > 2.0:
            analysis_points.append(
                "Significant degradation may indicate constraint or data changes"
            )

        # Check recent regression history
        recent_regressions = [
            r
            for r in self.regressions
            if r.template_id == template_id
            and (datetime.now(UTC) - r.detection_date).days <= 7
        ]

        if len(recent_regressions) > 1:
            analysis_points.append(
                "Multiple recent regressions indicate systematic issues"
            )

        if not analysis_points:
            analysis_points.append(
                "Performance regression detected - investigate recent changes"
            )

        return " | ".join(analysis_points)

    def _generate_recommendations(
        self, template_id: str, performance_change: float, parameters_changed: bool
    ) -> list[str]:
        """Generate recommendations for addressing regression."""
        recommendations = []

        if parameters_changed:
            recommendations.append("Revert to blessed parameters and re-test")
            recommendations.append(
                "Re-run parameter optimization if changes were intentional"
            )

        if performance_change > 50:
            recommendations.append("Investigate recent constraint or model changes")
            recommendations.append("Review system resource availability")
            recommendations.append("Consider rolling back recent code changes")

        recommendations.append(
            f"Re-establish baseline for {template_id} once issue is resolved"
        )
        recommendations.append("Monitor template performance for 24-48 hours")

        return recommendations

    def check_template_health(self, template_id: str) -> dict[str, Any]:
        """Check overall health status for a template.

        Args:
            template_id: Template identifier

        Returns:
            Dictionary with health status and metrics

        """
        baseline = self.baselines.get(template_id)

        # Get recent regressions
        recent_regressions = [
            r
            for r in self.regressions
            if r.template_id == template_id
            and (datetime.now(UTC) - r.detection_date).days <= 30
        ]

        # Get unacknowledged alerts
        unack_alerts = [
            a
            for a in self.alerts
            if a.template_id == template_id and not a.acknowledged
        ]

        # Determine health status
        if not baseline:
            health_status = "no_baseline"
        elif (
            len([r for r in recent_regressions if r.severity in ["critical", "high"]])
            > 0
        ):
            health_status = "critical"
        elif len(recent_regressions) > 3:
            health_status = "degraded"
        elif len(unack_alerts) > 0:
            health_status = "warning"
        else:
            health_status = "healthy"

        return {
            "template_id": template_id,
            "health_status": health_status,
            "baseline_age_days": (
                (datetime.now(UTC) - baseline.baseline_date).days if baseline else None
            ),
            "recent_regressions": len(recent_regressions),
            "unacknowledged_alerts": len(unack_alerts),
            "last_regression_date": (
                max(r.detection_date for r in recent_regressions).isoformat()
                if recent_regressions
                else None
            ),
            "baseline_performance": baseline.solve_time if baseline else None,
            "baseline_speedup": baseline.speedup_factor if baseline else None,
        }

    def generate_regression_report(self, days_back: int = 30) -> dict[str, Any]:
        """Generate comprehensive regression report.

        Args:
            days_back: Number of days to include in report

        Returns:
            Dictionary with regression analysis and trends

        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_back)

        # Filter recent data
        recent_regressions = [
            r for r in self.regressions if r.detection_date >= cutoff_date
        ]

        recent_alerts = [a for a in self.alerts if a.alert_date >= cutoff_date]

        # Analyze by template
        template_stats = {}
        for template_id in self.baselines:
            template_regressions = [
                r for r in recent_regressions if r.template_id == template_id
            ]
            template_alerts = [a for a in recent_alerts if a.template_id == template_id]

            template_stats[template_id] = {
                "regressions": len(template_regressions),
                "alerts": len(template_alerts),
                "health_status": self.check_template_health(template_id)[
                    "health_status"
                ],
                "avg_performance_change": (
                    statistics.mean(r.performance_change for r in template_regressions)
                    if template_regressions
                    else 0.0
                ),
            }

        # Calculate overall metrics
        total_regressions = len(recent_regressions)
        critical_regressions = len(
            [r for r in recent_regressions if r.severity == "critical"]
        )
        unack_alerts = len([a for a in recent_alerts if not a.acknowledged])

        return {
            "report_period_days": days_back,
            "total_templates": len(self.baselines),
            "total_regressions": total_regressions,
            "critical_regressions": critical_regressions,
            "unacknowledged_alerts": unack_alerts,
            "regression_rate": total_regressions
            / max(1, len(self.baselines))
            / days_back
            * 30,  # per month
            "template_stats": template_stats,
            "severity_breakdown": {
                "critical": len(
                    [r for r in recent_regressions if r.severity == "critical"]
                ),
                "high": len([r for r in recent_regressions if r.severity == "high"]),
                "medium": len(
                    [r for r in recent_regressions if r.severity == "medium"]
                ),
                "low": len([r for r in recent_regressions if r.severity == "low"]),
            },
        }

    def acknowledge_alerts(
        self, template_id: str | None = None, acknowledged_by: str = "system"
    ) -> int:
        """Acknowledge alerts for a template or all templates.

        Args:
            template_id: Template to acknowledge (None for all)
            acknowledged_by: Who acknowledged the alerts

        Returns:
            Number of alerts acknowledged

        """
        alerts_to_ack = [
            a
            for a in self.alerts
            if not a.acknowledged
            and (template_id is None or a.template_id == template_id)
        ]

        for alert in alerts_to_ack:
            alert.acknowledge(acknowledged_by)

        if alerts_to_ack:
            self._save_alerts()

        logger.info(f"Acknowledged {len(alerts_to_ack)} alerts")
        return len(alerts_to_ack)

    def _save_baselines(self) -> None:
        """Save performance baselines to storage."""
        baseline_file = self.storage_path / "baselines.json"

        data = {}
        for template_id, baseline in self.baselines.items():
            data[template_id] = {
                "baseline_date": baseline.baseline_date.isoformat(),
                "solve_time": baseline.solve_time,
                "speedup_factor": baseline.speedup_factor,
                "instance_count": baseline.instance_count,
                "parameters_used": baseline.parameters_used,
                "confidence_interval": list(baseline.confidence_interval),
            }

        with open(baseline_file, "w") as f:
            json.dump(data, f, indent=2)

    def _save_regressions(self) -> None:
        """Save regression history to storage."""
        regression_file = self.storage_path / "regressions.json"

        data = []
        for regression in self.regressions[-100:]:  # Keep last 100 regressions
            data.append(
                {
                    "template_id": regression.template_id,
                    "detection_date": regression.detection_date.isoformat(),
                    "regression_type": regression.regression_type,
                    "severity": regression.severity,
                    "baseline_performance": regression.baseline_performance,
                    "current_performance": regression.current_performance,
                    "performance_change": regression.performance_change,
                    "instance_count": regression.instance_count,
                    "parameters_changed": regression.parameters_changed,
                    "system_changes": regression.system_changes,
                    "root_cause_analysis": regression.root_cause_analysis,
                    "recommended_actions": regression.recommended_actions,
                }
            )

        with open(regression_file, "w") as f:
            json.dump(data, f, indent=2)

    def _save_alerts(self) -> None:
        """Save alert history to storage."""
        alerts_file = self.storage_path / "alerts.json"

        data = []
        for alert in self.alerts[-200:]:  # Keep last 200 alerts
            data.append(
                {
                    "template_id": alert.template_id,
                    "alert_date": alert.alert_date.isoformat(),
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "acknowledged": alert.acknowledged,
                    "acknowledged_by": alert.acknowledged_by,
                    "acknowledged_date": (
                        alert.acknowledged_date.isoformat()
                        if alert.acknowledged_date
                        else None
                    ),
                }
            )

        with open(alerts_file, "w") as f:
            json.dump(data, f, indent=2)
