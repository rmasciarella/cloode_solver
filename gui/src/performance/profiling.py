"""Performance Profiling System for OR-Tools solver optimization.

This module provides detailed profiling capabilities for constraint-level performance
analysis, solver behavior monitoring, and memory usage optimization.
"""

import builtins
import contextlib
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import psutil
from ortools.sat.python import cp_model

logger = logging.getLogger(__name__)


@dataclass
class ConstraintProfile:
    """Performance profile for a specific constraint type."""

    constraint_name: str
    creation_time: float
    variable_count: int
    constraint_count_added: int
    memory_delta_mb: float
    solver_impact_factor: float = 1.0  # Estimated impact on solve time

    @property
    def efficiency_score(self) -> float:
        """Calculate constraint efficiency score (higher is better)."""
        if self.creation_time <= 0:
            return 0.0

        # Score based on constraints added per unit time, adjusted by solver impact
        base_score = self.constraint_count_added / self.creation_time
        return base_score / max(1.0, self.solver_impact_factor)


@dataclass
class SolverProfile:
    """Comprehensive solver performance profile."""

    template_id: str
    model_creation_time: float
    variable_creation_time: float
    constraint_creation_time: float
    solving_time: float
    total_time: float

    # Solver statistics
    variable_count: int
    constraint_count: int
    decisions_count: int
    conflicts_count: int
    branches_count: int

    # Memory statistics
    peak_memory_mb: float
    final_memory_mb: float

    # Solution quality
    objective_value: float | None = None
    solver_status: str = "UNKNOWN"
    first_solution_time: float = 0.0

    @property
    def model_setup_time(self) -> float:
        """Get total model setup time (variables + constraints)."""
        return self.variable_creation_time + self.constraint_creation_time

    @property
    def solve_efficiency(self) -> float:
        """Calculate solve efficiency (decisions per second)."""
        if self.solving_time <= 0:
            return 0.0
        return self.decisions_count / self.solving_time

    @property
    def memory_efficiency(self) -> float:
        """Calculate memory efficiency (variables per MB)."""
        if self.peak_memory_mb <= 0:
            return 0.0
        return self.variable_count / self.peak_memory_mb


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a specific point."""

    timestamp: datetime
    process_memory_mb: float
    system_memory_available_mb: float
    memory_percent: float
    operation: str = ""  # Description of what was happening

    @property
    def memory_pressure(self) -> str:
        """Assess memory pressure level."""
        if self.memory_percent < 50:
            return "low"
        elif self.memory_percent < 75:
            return "medium"
        elif self.memory_percent < 90:
            return "high"
        else:
            return "critical"


class ConstraintProfiler:
    """Detailed profiling system for constraint performance analysis."""

    def __init__(self) -> None:
        """Initialize constraint profiler."""
        self.profiles: dict[str, list[ConstraintProfile]] = {}
        self.current_profiles: dict[str, ConstraintProfile] = {}

    def start_constraint_profiling(self, constraint_name: str) -> None:
        """Start profiling a constraint creation process.

        Args:
            constraint_name: Name of the constraint being profiled

        """
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        self.current_profiles[constraint_name] = ConstraintProfile(
            constraint_name=constraint_name,
            creation_time=time.time(),
            variable_count=0,
            constraint_count_added=0,
            memory_delta_mb=-initial_memory,  # Will be adjusted when finishing
        )

        logger.debug(f"Started profiling constraint: {constraint_name}")

    def finish_constraint_profiling(
        self,
        constraint_name: str,
        variables_involved: int,
        constraints_added: int,
        solver_impact_estimate: float = 1.0,
    ) -> ConstraintProfile:
        """Finish profiling a constraint and calculate final metrics.

        Args:
            constraint_name: Name of the constraint being profiled
            variables_involved: Number of variables involved in constraint
            constraints_added: Number of constraints actually added to model
            solver_impact_estimate: Estimated impact on solver performance

        Returns:
            ConstraintProfile with complete profiling data

        """
        if constraint_name not in self.current_profiles:
            logger.warning(
                f"No active profiling found for constraint: {constraint_name}"
            )
            return ConstraintProfile(
                constraint_name=constraint_name,
                creation_time=0.0,
                variable_count=0,
                constraint_count_added=0,
                memory_delta_mb=0.0,
            )

        profile = self.current_profiles[constraint_name]

        # Calculate final metrics
        end_time = time.time()
        profile.creation_time = end_time - profile.creation_time
        profile.variable_count = variables_involved
        profile.constraint_count_added = constraints_added
        profile.solver_impact_factor = solver_impact_estimate

        # Calculate memory delta
        process = psutil.Process()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        profile.memory_delta_mb += final_memory

        # Store in history
        if constraint_name not in self.profiles:
            self.profiles[constraint_name] = []
        self.profiles[constraint_name].append(profile)

        # Keep only last 20 profiles per constraint
        if len(self.profiles[constraint_name]) > 20:
            self.profiles[constraint_name] = self.profiles[constraint_name][-20:]

        # Clean up current profile
        del self.current_profiles[constraint_name]

        logger.info(
            f"Constraint profiling complete for {constraint_name}: "
            f"{profile.creation_time:.3f}s, {constraints_added} constraints, "
            f"{profile.memory_delta_mb:.1f}MB delta"
        )

        return profile

    def get_constraint_performance_summary(self) -> dict[str, Any]:
        """Get performance summary across all profiled constraints."""
        if not self.profiles:
            return {"total_constraints": 0, "profiles": []}

        summaries: list[dict[str, Any]] = []

        for constraint_name, profiles in self.profiles.items():
            if profiles:
                latest = profiles[-1]
                avg_creation_time = sum(p.creation_time for p in profiles) / len(
                    profiles
                )
                avg_efficiency = sum(p.efficiency_score for p in profiles) / len(
                    profiles
                )

                summaries.append(
                    {
                        "constraint_name": constraint_name,
                        "total_profiles": len(profiles),
                        "latest_creation_time": latest.creation_time,
                        "average_creation_time": avg_creation_time,
                        "average_efficiency_score": avg_efficiency,
                        "latest_constraints_added": latest.constraint_count_added,
                        "latest_memory_delta": latest.memory_delta_mb,
                    }
                )

        # Sort by efficiency (most efficient first)
        summaries.sort(key=lambda x: x["average_efficiency_score"], reverse=True)

        return {
            "total_constraints": len(self.profiles),
            "total_profiles": sum(len(profiles) for profiles in self.profiles.values()),
            "most_efficient": summaries[0]["constraint_name"] if summaries else None,
            "least_efficient": summaries[-1]["constraint_name"] if summaries else None,
            "profiles": summaries,
        }

    def identify_performance_bottlenecks(self) -> list[dict[str, Any]]:
        """Identify constraint performance bottlenecks."""
        bottlenecks = []

        for constraint_name, profiles in self.profiles.items():
            if not profiles:
                continue

            latest = profiles[-1]

            # Identify bottlenecks
            if latest.creation_time > 1.0:  # More than 1 second
                bottlenecks.append(
                    {
                        "constraint_name": constraint_name,
                        "issue": "slow_creation",
                        "creation_time": latest.creation_time,
                        "recommendation": "Consider optimizing constraint formulation",
                    }
                )

            if latest.memory_delta_mb > 100:  # More than 100MB
                bottlenecks.append(
                    {
                        "constraint_name": constraint_name,
                        "issue": "high_memory_usage",
                        "memory_delta": latest.memory_delta_mb,
                        "recommendation": "Review variable creation patterns",
                    }
                )

            if latest.solver_impact_factor > 3.0:  # High solver impact
                bottlenecks.append(
                    {
                        "constraint_name": constraint_name,
                        "issue": "high_solver_impact",
                        "impact_factor": latest.solver_impact_factor,
                        "recommendation": (
                            "Consider adding redundant constraints or search hints"
                        ),
                    }
                )

        return bottlenecks


class SolverProfiler:
    """Comprehensive solver performance profiling system."""

    def __init__(self) -> None:
        """Initialize solver profiler."""
        self.profiles: dict[str, list[SolverProfile]] = {}
        self.current_profile: SolverProfile | None = None
        self._phase_start_time: float = 0.0
        self._initial_memory: float = 0.0

    def start_solver_profiling(self, template_id: str) -> None:
        """Start profiling solver performance.

        Args:
            template_id: Template being solved

        """
        process = psutil.Process()
        self._initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        self.current_profile = SolverProfile(
            template_id=template_id,
            model_creation_time=0.0,
            variable_creation_time=0.0,
            constraint_creation_time=0.0,
            solving_time=0.0,
            total_time=time.time(),
            variable_count=0,
            constraint_count=0,
            decisions_count=0,
            conflicts_count=0,
            branches_count=0,
            peak_memory_mb=self._initial_memory,
            final_memory_mb=0.0,
        )

        logger.debug(f"Started solver profiling for template: {template_id}")

    def mark_phase_start(self, phase: str) -> None:
        """Mark the start of a solver phase.

        Args:
            phase: Phase name ('model_creation', 'variable_creation',
                  'constraint_creation', 'solving')

        """
        self._phase_start_time = time.time()
        logger.debug(f"Started solver phase: {phase}")

    def mark_phase_end(self, phase: str) -> None:
        """Mark the end of a solver phase.

        Args:
            phase: Phase name that's ending

        """
        if not self.current_profile:
            return

        phase_time = time.time() - self._phase_start_time

        if phase == "model_creation":
            self.current_profile.model_creation_time = phase_time
        elif phase == "variable_creation":
            self.current_profile.variable_creation_time = phase_time
        elif phase == "constraint_creation":
            self.current_profile.constraint_creation_time = phase_time
        elif phase == "solving":
            self.current_profile.solving_time = phase_time

        logger.debug(f"Completed solver phase {phase}: {phase_time:.3f}s")

    def update_solver_statistics(
        self, solver: cp_model.CpSolver, model: cp_model.CpModel
    ) -> None:
        """Update solver statistics from CP-SAT solver.

        Args:
            solver: CP-SAT solver instance
            model: CP-SAT model

        """
        if not self.current_profile:
            return

        # Get model statistics
        self.current_profile.variable_count = len(model.Proto().variables)
        self.current_profile.constraint_count = len(model.Proto().constraints)

        # Get solver statistics (if available)
        try:
            self.current_profile.decisions_count = solver.NumBranches()
            self.current_profile.conflicts_count = solver.NumConflicts()
            self.current_profile.branches_count = solver.NumBranches()
        except Exception:
            # Some statistics may not be available
            pass

        # Update solver status and objective
        self.current_profile.solver_status = solver.StatusName()
        if solver.StatusName() in ["OPTIMAL", "FEASIBLE"]:
            with contextlib.suppress(builtins.BaseException):
                self.current_profile.objective_value = solver.ObjectiveValue()

    def finish_solver_profiling(self) -> SolverProfile | None:
        """Finish solver profiling and return complete profile.

        Returns:
            SolverProfile with complete profiling data

        """
        if not self.current_profile:
            return None

        # Calculate total time
        end_time = time.time()
        self.current_profile.total_time = end_time - self.current_profile.total_time

        # Get final memory usage
        process = psutil.Process()
        self.current_profile.final_memory_mb = process.memory_info().rss / 1024 / 1024

        # Calculate peak memory (use current as approximation)
        self.current_profile.peak_memory_mb = max(
            self.current_profile.peak_memory_mb, self.current_profile.final_memory_mb
        )

        # Store in history
        template_id = self.current_profile.template_id
        if template_id not in self.profiles:
            self.profiles[template_id] = []

        self.profiles[template_id].append(self.current_profile)

        # Keep only last 10 profiles per template
        if len(self.profiles[template_id]) > 10:
            self.profiles[template_id] = self.profiles[template_id][-10:]

        profile = self.current_profile
        self.current_profile = None

        logger.info(
            f"Solver profiling complete for {template_id}: "
            f"total={profile.total_time:.2f}s, solving={profile.solving_time:.2f}s, "
            f"memory={profile.peak_memory_mb:.1f}MB"
        )

        return profile

    def get_solver_performance_trends(self, template_id: str) -> dict[str, Any]:
        """Analyze solver performance trends for a template."""
        profiles = self.profiles.get(template_id, [])
        if not profiles:
            return {"error": "No solver profiles available"}

        # Extract trends
        total_times = [p.total_time for p in profiles]
        solving_times = [p.solving_time for p in profiles]
        memory_usage = [p.peak_memory_mb for p in profiles]
        efficiency_scores = [p.solve_efficiency for p in profiles]

        latest = profiles[-1]

        return {
            "template_id": template_id,
            "total_profiles": len(profiles),
            "latest_performance": {
                "total_time": latest.total_time,
                "solving_time": latest.solving_time,
                "peak_memory_mb": latest.peak_memory_mb,
                "solve_efficiency": latest.solve_efficiency,
                "solver_status": latest.solver_status,
            },
            "trends": {
                "average_total_time": sum(total_times) / len(total_times),
                "average_solving_time": sum(solving_times) / len(solving_times),
                "average_memory_usage": sum(memory_usage) / len(memory_usage),
                "average_efficiency": sum(efficiency_scores) / len(efficiency_scores),
                "performance_stability": self._calculate_stability(solving_times),
            },
        }

    def _calculate_stability(self, values: list[float]) -> str:
        """Calculate performance stability assessment."""
        if len(values) < 3:
            return "insufficient_data"

        # Calculate coefficient of variation
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance**0.5

        if mean_val == 0:
            return "unstable"

        cv = std_dev / mean_val

        if cv < 0.1:
            return "very_stable"
        elif cv < 0.2:
            return "stable"
        elif cv < 0.4:
            return "moderate"
        else:
            return "unstable"


class MemoryProfiler:
    """Memory usage profiling and optimization system."""

    def __init__(self, sampling_interval: float = 1.0):
        """Initialize memory profiler.

        Args:
            sampling_interval: How often to sample memory (seconds)

        """
        self.sampling_interval = sampling_interval
        self.snapshots: list[MemorySnapshot] = []
        self.is_profiling = False
        self._baseline_memory: float = 0.0

    def start_memory_profiling(self) -> None:
        """Start continuous memory profiling."""
        process = psutil.Process()
        self._baseline_memory = process.memory_info().rss / 1024 / 1024
        self.snapshots.clear()
        self.is_profiling = True

        # Take initial snapshot
        self.take_memory_snapshot("profiling_start")

        logger.info("Started memory profiling")

    def take_memory_snapshot(self, operation: str = "") -> MemorySnapshot:
        """Take a memory usage snapshot.

        Args:
            operation: Description of current operation

        Returns:
            MemorySnapshot with current memory state

        """
        process = psutil.Process()
        virtual_memory = psutil.virtual_memory()

        snapshot = MemorySnapshot(
            timestamp=datetime.now(UTC),
            process_memory_mb=process.memory_info().rss / 1024 / 1024,
            system_memory_available_mb=virtual_memory.available / 1024 / 1024,
            memory_percent=virtual_memory.percent,
            operation=operation,
        )

        if self.is_profiling:
            self.snapshots.append(snapshot)

        return snapshot

    def stop_memory_profiling(self) -> dict[str, Any]:
        """Stop memory profiling and return analysis.

        Returns:
            Dictionary with memory usage analysis

        """
        if not self.is_profiling:
            return {"error": "Memory profiling not active"}

        # Take final snapshot
        final_snapshot = self.take_memory_snapshot("profiling_end")
        self.is_profiling = False

        if not self.snapshots:
            return {"error": "No memory snapshots collected"}

        # Analyze memory usage
        memory_values = [s.process_memory_mb for s in self.snapshots]
        peak_memory = max(memory_values)
        final_memory = final_snapshot.process_memory_mb
        memory_growth = final_memory - self._baseline_memory

        # Find memory pressure periods
        high_pressure_periods = [
            s for s in self.snapshots if s.memory_pressure in ["high", "critical"]
        ]

        # Memory growth rate analysis
        if len(self.snapshots) > 1:
            duration = (
                self.snapshots[-1].timestamp - self.snapshots[0].timestamp
            ).total_seconds()
            growth_rate = memory_growth / max(1, duration)  # MB per second
        else:
            growth_rate = 0.0

        analysis = {
            "profiling_duration": duration if len(self.snapshots) > 1 else 0,
            "baseline_memory_mb": self._baseline_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_growth_mb": memory_growth,
            "growth_rate_mb_per_sec": growth_rate,
            "snapshots_collected": len(self.snapshots),
            "high_pressure_periods": len(high_pressure_periods),
            "memory_efficiency": "good" if memory_growth < 100 else "poor",
            "recommendations": self._generate_memory_recommendations(
                memory_growth, peak_memory, high_pressure_periods
            ),
        }

        logger.info(
            f"Memory profiling complete: {memory_growth:.1f}MB growth, "
            f"{peak_memory:.1f}MB peak"
        )

        return analysis

    def _generate_memory_recommendations(
        self,
        memory_growth: float,
        peak_memory: float,
        high_pressure_periods: list[MemorySnapshot],
    ) -> list[str]:
        """Generate memory optimization recommendations."""
        recommendations = []

        if memory_growth > 200:  # More than 200MB growth
            recommendations.append(
                "High memory growth detected - review variable creation patterns"
            )

        if peak_memory > 2000:  # More than 2GB
            recommendations.append(
                "High peak memory usage - consider batch processing or "
                "model decomposition"
            )

        if high_pressure_periods:
            recommendations.append(
                f"System memory pressure detected in {len(high_pressure_periods)} "
                f"snapshots - monitor system resources during solving"
            )

        if memory_growth < 10:  # Very low growth
            recommendations.append(
                "Excellent memory efficiency - current patterns are optimal"
            )

        return recommendations

    def get_memory_snapshots(
        self, operation_filter: str | None = None
    ) -> list[MemorySnapshot]:
        """Get memory snapshots, optionally filtered by operation.

        Args:
            operation_filter: Filter snapshots by operation name

        Returns:
            List of matching memory snapshots

        """
        if operation_filter:
            return [s for s in self.snapshots if operation_filter in s.operation]
        return self.snapshots.copy()
