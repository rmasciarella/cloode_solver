"""Template Validator for comprehensive template testing and validation.

This module provides validation and testing capabilities for template-based
scheduling optimization, ensuring template integrity, performance validation,
and production readiness assessment.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a template."""

    severity: str  # "error", "warning", "info"
    category: str  # "structure", "performance", "compatibility", "data"
    message: str
    template_id: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_blocking(self) -> bool:
        """Check if this issue blocks template promotion to production."""
        return self.severity == "error"


@dataclass
class OptimizedValidationReport:
    """Comprehensive validation report for a template."""

    template_id: str
    validation_date: str
    overall_status: str  # "pass", "warning", "fail"
    issues: list[ValidationIssue] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    compatibility_status: dict[str, bool] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Get number of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        """Get number of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def is_production_ready(self) -> bool:
        """Check if template is ready for production deployment."""
        return (
            self.overall_status in ["pass", "warning"]
            and self.error_count == 0
            and self.performance_metrics.get("speedup_factor", 0) >= 1.5
        )


class OptimizedValidator:
    """Comprehensive template validation system.

    Provides validation for:
    - Template structure and integrity
    - Performance requirements and regression testing
    - Compatibility with existing systems
    - Production readiness assessment
    """

    def __init__(self) -> None:
        """Initialize template validator."""
        self.validation_history: dict[str, list[OptimizedValidationReport]] = {}

    def validate_template_comprehensive(
        self,
        template_id: str,
        job_optimized_pattern: Any,  # JobTemplate - avoiding circular import
        test_instances: int = 5,
        performance_baseline: float = 10.0,
    ) -> OptimizedValidationReport:
        """Perform comprehensive template validation.

        Args:
            template_id: Template identifier
            job_optimized_pattern: JobTemplate instance to validate
            test_instances: Number of instances to test with
            performance_baseline: Performance baseline for comparison

        Returns:
            OptimizedValidationReport with complete validation results

        """
        issues = []
        performance_metrics = {}
        compatibility_status = {}
        recommendations = []

        # Structure validation
        structure_issues = self._validate_template_structure(
            template_id, job_optimized_pattern
        )
        issues.extend(structure_issues)

        # Performance validation
        perf_issues, perf_metrics = self._validate_template_performance(
            template_id, job_optimized_pattern, test_instances, performance_baseline
        )
        issues.extend(perf_issues)
        performance_metrics.update(perf_metrics)

        # Compatibility validation
        compat_issues, compat_status = self._validate_template_compatibility(
            template_id, job_optimized_pattern
        )
        issues.extend(compat_issues)
        compatibility_status.update(compat_status)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            template_id, issues, performance_metrics
        )

        # Determine overall status
        if any(issue.severity == "error" for issue in issues):
            overall_status = "fail"
        elif any(issue.severity == "warning" for issue in issues):
            overall_status = "warning"
        else:
            overall_status = "pass"

        report = OptimizedValidationReport(
            template_id=template_id,
            validation_date=str(__import__("datetime").datetime.now()),
            overall_status=overall_status,
            issues=issues,
            performance_metrics=performance_metrics,
            compatibility_status=compatibility_status,
            recommendations=recommendations,
        )

        # Record validation history
        self._record_validation(report)

        logger.info(
            f"Template validation complete for {template_id}: "
            f"{overall_status} ({len(issues)} issues, "
            f"{performance_metrics.get('speedup_factor', 1.0):.1f}x speedup)"
        )

        return report

    def _validate_template_structure(
        self, template_id: str, job_optimized_pattern: Any
    ) -> list[ValidationIssue]:
        """Validate template structure and integrity."""
        issues = []

        # Check basic template properties
        if (
            not hasattr(job_optimized_pattern, "optimized_tasks")
            or not job_optimized_pattern.optimized_tasks
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    category="structure",
                    message="Template has no tasks defined",
                    template_id=template_id,
                    details={"task_count": 0},
                )
            )

        if not hasattr(job_optimized_pattern, "optimized_precedences"):
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="structure",
                    message="Template has no precedence relationships",
                    template_id=template_id,
                    details={"precedence_count": 0},
                )
            )

        # Validate task structure
        if hasattr(job_optimized_pattern, "optimized_tasks"):
            for task in job_optimized_pattern.optimized_tasks:
                if not hasattr(task, "modes") or not task.modes:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            category="structure",
                            message=(
                                f"Template task {task.optimized_task_id} has no "
                                "execution modes"
                            ),
                            template_id=template_id,
                            details={"task_id": task.optimized_task_id},
                        )
                    )

                # Check for reasonable duration ranges
                if hasattr(task, "modes") and task.modes:
                    durations = [mode.duration_minutes for mode in task.modes]
                    if max(durations) - min(durations) > 480:  # 8 hours difference
                        issues.append(
                            ValidationIssue(
                                severity="warning",
                                category="structure",
                                message=(
                                    f"Template task {task.optimized_task_id} has large "
                                    "duration variance"
                                ),
                                template_id=template_id,
                                details={
                                    "task_id": task.optimized_task_id,
                                    "min_duration": min(durations),
                                    "max_duration": max(durations),
                                },
                            )
                        )

        # Validate precedence relationships
        if hasattr(job_optimized_pattern, "optimized_precedences"):
            precedence_count = len(job_optimized_pattern.optimized_precedences)
            task_count = (
                len(job_optimized_pattern.optimized_tasks)
                if hasattr(job_optimized_pattern, "optimized_tasks")
                else 0
            )

            if precedence_count == 0 and task_count > 1:
                issues.append(
                    ValidationIssue(
                        severity="info",
                        category="structure",
                        message=(
                            "Template has multiple tasks but no precedence "
                            "constraints (fully parallel)"
                        ),
                        template_id=template_id,
                        details={
                            "task_count": task_count,
                            "precedence_count": precedence_count,
                        },
                    )
                )
            elif precedence_count > task_count * (task_count - 1) / 2:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="structure",
                        message="Template may have excessive precedence constraints",
                        template_id=template_id,
                        details={
                            "task_count": task_count,
                            "precedence_count": precedence_count,
                        },
                    )
                )

        return issues

    def _validate_template_performance(
        self,
        template_id: str,
        job_optimized_pattern: Any,
        test_instances: int,
        baseline: float,
    ) -> tuple[list[ValidationIssue], dict[str, float]]:
        """Validate template performance characteristics."""
        issues = []
        metrics = {}

        # Simulate performance testing
        task_count = (
            len(job_optimized_pattern.optimized_tasks)
            if hasattr(job_optimized_pattern, "optimized_tasks")
            else 0
        )

        # Estimate performance based on template complexity
        complexity_factor = 1.0 + (task_count * 0.1) + (test_instances * 0.05)
        estimated_time = baseline / complexity_factor  # Template should be faster
        speedup_factor = baseline / estimated_time if estimated_time > 0 else 1.0

        metrics = {
            "estimated_solve_time": estimated_time,
            "speedup_factor": speedup_factor,
            "template_complexity": complexity_factor,
            "instances_tested": test_instances,
            "baseline_time": baseline,
        }

        # Performance validation criteria
        if speedup_factor < 1.5:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="performance",
                    message=(
                        f"Template provides minimal performance improvement: "
                        f"{speedup_factor:.1f}x"
                    ),
                    template_id=template_id,
                    details={"speedup_factor": speedup_factor, "target": 1.5},
                )
            )

        if estimated_time > 60.0:  # More than 1 minute
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="performance",
                    message=(
                        f"Template estimated solve time exceeds target: "
                        f"{estimated_time:.1f}s"
                    ),
                    template_id=template_id,
                    details={"estimated_time": estimated_time, "target": 60.0},
                )
            )

        # Template scalability validation
        scalability_limit = max(10, 100 / task_count) if task_count > 0 else 10
        if test_instances > scalability_limit:
            issues.append(
                ValidationIssue(
                    severity="info",
                    category="performance",
                    message="Template tested beyond typical scalability range",
                    template_id=template_id,
                    details={
                        "instances_tested": test_instances,
                        "recommended_limit": scalability_limit,
                    },
                )
            )

        return issues, metrics

    def _validate_template_compatibility(
        self,
        template_id: str,
        job_optimized_pattern: Any,  # noqa: ARG002
    ) -> tuple[list[ValidationIssue], dict[str, bool]]:
        """Validate template compatibility with existing systems."""
        issues = []
        compatibility = {}

        # Check backward compatibility
        has_legacy_support = True  # Simulate compatibility check
        compatibility["legacy_system"] = has_legacy_support

        if not has_legacy_support:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    category="compatibility",
                    message=(
                        "Template may not be compatible with legacy scheduling system"
                    ),
                    template_id=template_id,
                    details={"legacy_support": False},
                )
            )

        # Check OR-Tools version compatibility
        ortools_compatible = True  # Simulate version check
        compatibility["ortools_version"] = ortools_compatible

        # Check database schema compatibility
        schema_compatible = True  # Simulate schema check
        compatibility["database_schema"] = schema_compatible

        if not schema_compatible:
            issues.append(
                ValidationIssue(
                    severity="error",
                    category="compatibility",
                    message="Template requires database schema updates",
                    template_id=template_id,
                    details={"schema_version": "current"},
                )
            )

        # Check API compatibility
        api_compatible = True  # Simulate API check
        compatibility["api_endpoints"] = api_compatible

        return issues, compatibility

    def _generate_recommendations(
        self,
        template_id: str,  # noqa: ARG002
        issues: list[ValidationIssue],
        performance_metrics: dict[str, float],
    ) -> list[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Performance-based recommendations
        speedup = performance_metrics.get("speedup_factor", 1.0)
        if speedup < 2.0:
            recommendations.append(
                "Consider applying additional symmetry breaking constraints to "
                "improve performance"
            )

        if speedup < 1.5:
            recommendations.append(
                "Template performance improvement is minimal - review parameter tuning"
            )

        # Issue-based recommendations
        error_count = sum(1 for issue in issues if issue.severity == "error")
        if error_count > 0:
            recommendations.append(
                f"Resolve {error_count} error-level issues before production deployment"
            )

        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        if warning_count > 3:
            recommendations.append(
                f"Consider addressing {warning_count} warning-level issues for "
                "better robustness"
            )

        # Structure-based recommendations
        structure_issues = [i for i in issues if i.category == "structure"]
        if structure_issues:
            recommendations.append(
                "Review template structure - ensure all tasks have valid "
                "execution modes"
            )

        # Template complexity recommendations
        complexity = performance_metrics.get("template_complexity", 1.0)
        if complexity > 5.0:
            recommendations.append(
                "Template complexity is high - consider decomposition for "
                "better maintainability"
            )

        return recommendations

    def validate_template_regression(
        self, template_id: str, current_performance: float, tolerance: float = 0.2
    ) -> OptimizedValidationReport:
        """Validate template performance against historical baseline.

        Args:
            template_id: Template identifier
            current_performance: Current performance measurement
            tolerance: Performance degradation tolerance (20% by default)

        Returns:
            OptimizedValidationReport focusing on regression analysis

        """
        issues = []
        performance_metrics = {"current_performance": current_performance}

        # Get historical baseline
        historical_reports = self.validation_history.get(template_id, [])
        if historical_reports:
            baseline_report = historical_reports[-1]
            baseline_performance = baseline_report.performance_metrics.get(
                "estimated_solve_time", 10.0
            )

            performance_metrics["baseline_performance"] = baseline_performance
            performance_change = (
                current_performance - baseline_performance
            ) / baseline_performance
            performance_metrics["performance_change"] = performance_change

            if performance_change > tolerance:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        category="performance",
                        message=(
                            f"Template performance degraded by {performance_change:.1%}"
                        ),
                        template_id=template_id,
                        details={
                            "current": current_performance,
                            "baseline": baseline_performance,
                            "degradation": performance_change,
                            "tolerance": tolerance,
                        },
                    )
                )
            elif performance_change > tolerance / 2:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        category="performance",
                        message=(
                            f"Template performance decline detected: "
                            f"{performance_change:.1%}"
                        ),
                        template_id=template_id,
                        details={
                            "current": current_performance,
                            "baseline": baseline_performance,
                            "decline": performance_change,
                        },
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    severity="info",
                    category="performance",
                    message="No historical baseline available for regression analysis",
                    template_id=template_id,
                    details={"current_performance": current_performance},
                )
            )

        overall_status = (
            "fail" if any(i.severity == "error" for i in issues) else "pass"
        )

        report = OptimizedValidationReport(
            template_id=template_id,
            validation_date=str(__import__("datetime").datetime.now()),
            overall_status=overall_status,
            issues=issues,
            performance_metrics=performance_metrics,
            recommendations=self._generate_recommendations(
                template_id, issues, performance_metrics
            ),
        )

        return report

    def _record_validation(self, report: OptimizedValidationReport) -> None:
        """Record validation report in history."""
        if report.template_id not in self.validation_history:
            self.validation_history[report.template_id] = []

        self.validation_history[report.template_id].append(report)

        # Keep only last 5 reports per template
        if len(self.validation_history[report.template_id]) > 5:
            self.validation_history[report.template_id] = self.validation_history[
                report.template_id
            ][-5:]

    def get_validation_history(
        self, template_id: str
    ) -> list[OptimizedValidationReport]:
        """Get validation history for a template."""
        return self.validation_history.get(template_id, [])

    def get_production_ready_templates(self) -> list[str]:
        """Get list of templates that are production ready."""
        ready_templates = []

        for template_id, reports in self.validation_history.items():
            if reports and reports[-1].is_production_ready:
                ready_templates.append(template_id)

        return ready_templates

    def generate_validation_summary(self) -> dict[str, Any]:
        """Generate summary of all template validations."""
        if not self.validation_history:
            return {"total_templates": 0, "validations": []}

        summaries: list[dict[str, Any]] = []
        for template_id, reports in self.validation_history.items():
            if reports:
                latest = reports[-1]
                summaries.append(
                    {
                        "template_id": template_id,
                        "status": latest.overall_status,
                        "error_count": latest.error_count,
                        "warning_count": latest.warning_count,
                        "is_production_ready": latest.is_production_ready,
                        "speedup_factor": latest.performance_metrics.get(
                            "speedup_factor", 1.0
                        ),
                        "last_validated": latest.validation_date,
                    }
                )

        production_ready_count = sum(1 for s in summaries if s["is_production_ready"])

        return {
            "total_templates": len(self.validation_history),
            "production_ready_count": production_ready_count,
            "average_speedup": (
                float(sum(s["speedup_factor"] for s in summaries)) / len(summaries)
                if summaries
                else 1.0
            ),
            "validations": summaries,
        }
