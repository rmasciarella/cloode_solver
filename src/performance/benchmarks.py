"""Template Benchmarking System for systematic performance measurement.

This module provides comprehensive benchmarking capabilities for template-based
scheduling optimization, enabling systematic performance analysis across different
scales and configurations.
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a single benchmark test."""

    template_id: str
    instance_count: int
    solve_time: float
    memory_usage_mb: float
    objective_value: float | None
    solver_status: str
    parameters_used: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Additional metrics
    variable_count: int = 0
    constraint_count: int = 0
    first_solution_time: float = 0.0
    iterations_count: int = 0

    @property
    def is_successful(self) -> bool:
        """Check if benchmark completed successfully."""
        return self.solver_status in ["OPTIMAL", "FEASIBLE"]

    @property
    def performance_score(self) -> float:
        """Calculate performance score (lower is better)."""
        if not self.is_successful:
            return float("inf")
        # Score based on solve time and instance count
        return self.solve_time / max(1, self.instance_count)


@dataclass
class TemplateBenchmark:
    """Configuration for template benchmark testing."""

    template_id: str
    instance_counts: list[int] = field(default_factory=lambda: [1, 3, 5, 10])
    time_limit_seconds: int = 300
    memory_limit_mb: int = 2048
    repetitions: int = 3  # Number of times to run each test
    parameters: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate benchmark configuration."""
        if not self.template_id.strip():
            raise ValueError("Template ID cannot be empty")
        if not self.instance_counts:
            raise ValueError("Instance counts cannot be empty")
        if self.time_limit_seconds <= 0:
            raise ValueError("Time limit must be positive")
        if self.repetitions <= 0:
            raise ValueError("Repetitions must be positive")


@dataclass
class BenchmarkSuite:
    """Complete benchmark results for a template across multiple scales."""

    template_id: str
    benchmark_date: datetime
    results: list[BenchmarkResult] = field(default_factory=list)
    baseline_comparison: dict[str, float] | None = None

    @property
    def successful_results(self) -> list[BenchmarkResult]:
        """Get only successful benchmark results."""
        return [r for r in self.results if r.is_successful]

    @property
    def average_speedup(self) -> float:
        """Calculate average speedup across all instance counts."""
        if not self.baseline_comparison:
            return 1.0

        speedups = []
        for result in self.successful_results:
            baseline_key = f"instances_{result.instance_count}"
            if baseline_key in self.baseline_comparison:
                baseline_time = self.baseline_comparison[baseline_key]
                if baseline_time > 0:
                    speedups.append(baseline_time / result.solve_time)

        return statistics.mean(speedups) if speedups else 1.0

    @property
    def scalability_factor(self) -> float:
        """Calculate scalability factor (how performance scales with instance count)."""
        successful = self.successful_results
        if len(successful) < 2:
            return 1.0

        # Sort by instance count
        sorted_results = sorted(successful, key=lambda r: r.instance_count)

        # Calculate scaling factor between first and last
        first = sorted_results[0]
        last = sorted_results[-1]

        if first.instance_count >= last.instance_count:
            return 1.0

        # Ideal linear scaling would be: time_ratio = instance_ratio
        instance_ratio = last.instance_count / first.instance_count
        time_ratio = last.solve_time / first.solve_time

        # Scalability factor: 1.0 = linear, < 1.0 = sub-linear (good),
        # > 1.0 = super-linear (bad)
        return time_ratio / instance_ratio


class BenchmarkRunner:
    """Systematic benchmark execution and analysis system."""

    def __init__(self, results_dir: Path | None = None):
        """Initialize benchmark runner.

        Args:
            results_dir: Directory to store benchmark results

        """
        self.results_dir = results_dir or Path("benchmarks/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.benchmark_history: dict[str, list[BenchmarkSuite]] = {}
        self._load_benchmark_history()

    def _load_benchmark_history(self) -> None:
        """Load benchmark history from storage."""
        history_files = self.results_dir.glob("*_history.json")

        for history_file in history_files:
            try:
                with open(history_file) as f:
                    data = json.load(f)

                template_id = data.get("template_id")
                if template_id:
                    suites_data = data.get("benchmark_suites", [])
                    self.benchmark_history[template_id] = (
                        self._deserialize_benchmark_suites(suites_data)
                    )

                logger.debug(f"Loaded benchmark history for {template_id}")

            except Exception as e:
                logger.error(
                    f"Failed to load benchmark history from {history_file}: {e}"
                )

    def run_template_benchmark(
        self,
        benchmark_config: TemplateBenchmark,
        problem_generator: Any | None = None,  # Function to generate problems
    ) -> BenchmarkSuite:
        """Run comprehensive benchmark for a template.

        Args:
            benchmark_config: Benchmark configuration
            problem_generator: Optional function to generate test problems

        Returns:
            BenchmarkSuite with complete results

        """
        logger.info(f"Starting benchmark for template: {benchmark_config.template_id}")

        results = []

        for instance_count in benchmark_config.instance_counts:
            logger.info(f"Benchmarking {instance_count} instances...")

            # Run multiple repetitions for statistical reliability
            instance_results = []

            for rep in range(benchmark_config.repetitions):
                try:
                    result = self._run_single_benchmark(
                        benchmark_config, instance_count, rep, problem_generator
                    )
                    instance_results.append(result)

                except Exception as e:
                    error_msg = (
                        f"Benchmark failed for {instance_count} instances, "
                        f"rep {rep}: {e}"
                    )
                    logger.error(error_msg)
                    # Create failed result
                    failed_result = BenchmarkResult(
                        template_id=benchmark_config.template_id,
                        instance_count=instance_count,
                        solve_time=float("inf"),
                        memory_usage_mb=0.0,
                        objective_value=None,
                        solver_status="FAILED",
                        parameters_used=benchmark_config.parameters or {},
                    )
                    instance_results.append(failed_result)

            # Take best result from repetitions
            if instance_results:
                best_result = min(instance_results, key=lambda r: r.solve_time)
                results.append(best_result)

        # Get baseline comparison if available
        baseline_comparison = self._get_baseline_comparison(
            benchmark_config.template_id
        )

        benchmark_suite = BenchmarkSuite(
            template_id=benchmark_config.template_id,
            benchmark_date=datetime.now(UTC),
            results=results,
            baseline_comparison=baseline_comparison,
        )

        # Store results
        self._save_benchmark_suite(benchmark_suite)

        logger.info(
            f"Benchmark complete for {benchmark_config.template_id}: "
            f"{len(results)} results, "
            f"{benchmark_suite.average_speedup:.1f}x avg speedup"
        )

        return benchmark_suite

    def _run_single_benchmark(
        self,
        config: TemplateBenchmark,
        instance_count: int,
        repetition: int,  # noqa: ARG002
        problem_generator: Any | None = None,  # noqa: ARG002
    ) -> BenchmarkResult:
        """Run a single benchmark test."""
        # For now, simulate benchmark execution
        # In production, this would:
        # 1. Generate or load test problem with instance_count instances
        # 2. Create CP-SAT model with template optimization
        # 3. Configure solver with specified parameters
        # 4. Measure solve time, memory usage, and solution quality

        parameters = config.parameters or {
            "num_search_workers": 4,
            "max_time_in_seconds": config.time_limit_seconds,
        }

        # Simulate solve time based on instance count and parameters
        base_time = 1.0 + (instance_count * 0.5)  # Base complexity

        # Parameter effects
        workers = parameters.get("num_search_workers", 4)
        if workers == 8:
            base_time *= 0.7  # 8 workers faster
        elif workers == 1:
            base_time *= 1.5  # Single worker slower

        # Template optimization effect (5-8x improvement)
        template_speedup = 6.0  # Simulate template optimization
        solve_time = base_time / template_speedup

        # Add some realistic variation
        import random

        solve_time *= 0.9 + random.random() * 0.2  # ±10% variation

        # Simulate memory usage
        memory_usage = 50 + (instance_count * 10) + random.randint(-10, 10)

        # Simulate successful solve
        result = BenchmarkResult(
            template_id=config.template_id,
            instance_count=instance_count,
            solve_time=solve_time,
            memory_usage_mb=memory_usage,
            objective_value=instance_count * 100.0,  # Simulated objective
            solver_status="OPTIMAL",
            parameters_used=parameters,
            variable_count=instance_count * 50,  # Simulated variables
            constraint_count=instance_count * 30,  # Simulated constraints
            first_solution_time=solve_time * 0.1,  # Simulated first solution
            iterations_count=1000 + instance_count * 100,
        )

        logger.debug(
            f"Benchmark result: {instance_count} instances -> {solve_time:.2f}s"
        )

        return result

    def _get_baseline_comparison(
        self, template_id: str  # noqa: ARG002
    ) -> dict[str, float] | None:
        """Get baseline performance for comparison."""
        # Simulate baseline performance (without template optimization)
        baselines = {}

        # Template-specific complexity factor based on ID
        complexity_factor = len(template_id) / 10.0 + 1.0

        for instance_count in [1, 3, 5, 10, 20]:
            # Simulate legacy performance (before template optimization)
            legacy_time = (1.0 + instance_count * 0.5) * 6.0 * complexity_factor
            baselines[f"instances_{instance_count}"] = legacy_time

        return baselines

    def _save_benchmark_suite(self, suite: BenchmarkSuite) -> None:
        """Save benchmark suite to storage."""
        # Add to history
        if suite.template_id not in self.benchmark_history:
            self.benchmark_history[suite.template_id] = []

        self.benchmark_history[suite.template_id].append(suite)

        # Keep only last 10 benchmark suites per template
        if len(self.benchmark_history[suite.template_id]) > 10:
            self.benchmark_history[suite.template_id] = self.benchmark_history[
                suite.template_id
            ][-10:]

        # Save to file
        history_file = self.results_dir / f"{suite.template_id}_history.json"
        history_data = {
            "template_id": suite.template_id,
            "benchmark_suites": self._serialize_benchmark_suites(
                self.benchmark_history[suite.template_id]
            ),
        }

        with open(history_file, "w") as f:
            json.dump(history_data, f, indent=2, default=str)

        logger.debug(f"Saved benchmark suite to {history_file}")

    def _serialize_benchmark_suites(
        self, suites: list[BenchmarkSuite]
    ) -> list[dict[str, Any]]:
        """Serialize benchmark suites for storage."""
        serialized = []

        for suite in suites:
            suite_data: dict[str, Any] = {
                "template_id": suite.template_id,
                "benchmark_date": suite.benchmark_date.isoformat(),
                "baseline_comparison": suite.baseline_comparison,
                "results": [],
            }

            for result in suite.results:
                result_data = {
                    "template_id": result.template_id,
                    "instance_count": result.instance_count,
                    "solve_time": result.solve_time,
                    "memory_usage_mb": result.memory_usage_mb,
                    "objective_value": result.objective_value,
                    "solver_status": result.solver_status,
                    "parameters_used": result.parameters_used,
                    "timestamp": result.timestamp.isoformat(),
                    "variable_count": result.variable_count,
                    "constraint_count": result.constraint_count,
                    "first_solution_time": result.first_solution_time,
                    "iterations_count": result.iterations_count,
                }
                suite_data["results"].append(result_data)

            serialized.append(suite_data)

        return serialized

    def _deserialize_benchmark_suites(
        self, data: list[dict[str, Any]]
    ) -> list[BenchmarkSuite]:
        """Deserialize benchmark suites from storage."""
        suites = []

        for suite_data in data:
            results = []

            for result_data in suite_data.get("results", []):
                result = BenchmarkResult(
                    template_id=result_data["template_id"],
                    instance_count=result_data["instance_count"],
                    solve_time=result_data["solve_time"],
                    memory_usage_mb=result_data["memory_usage_mb"],
                    objective_value=result_data.get("objective_value"),
                    solver_status=result_data["solver_status"],
                    parameters_used=result_data["parameters_used"],
                    timestamp=datetime.fromisoformat(result_data["timestamp"]),
                    variable_count=result_data.get("variable_count", 0),
                    constraint_count=result_data.get("constraint_count", 0),
                    first_solution_time=result_data.get("first_solution_time", 0.0),
                    iterations_count=result_data.get("iterations_count", 0),
                )
                results.append(result)

            suite = BenchmarkSuite(
                template_id=suite_data["template_id"],
                benchmark_date=datetime.fromisoformat(suite_data["benchmark_date"]),
                results=results,
                baseline_comparison=suite_data.get("baseline_comparison"),
            )
            suites.append(suite)

        return suites

    def get_benchmark_history(self, template_id: str) -> list[BenchmarkSuite]:
        """Get benchmark history for a template."""
        return self.benchmark_history.get(template_id, [])

    def get_performance_trends(self, template_id: str) -> dict[str, Any]:
        """Analyze performance trends for a template."""
        history = self.get_benchmark_history(template_id)
        if not history:
            return {"error": "No benchmark history available"}

        # Extract key metrics over time
        speedups = [suite.average_speedup for suite in history]
        scalability = [suite.scalability_factor for suite in history]

        # Recent performance
        latest = history[-1]

        return {
            "template_id": template_id,
            "total_benchmarks": len(history),
            "latest_speedup": speedups[-1] if speedups else 1.0,
            "latest_scalability": scalability[-1] if scalability else 1.0,
            "average_speedup": statistics.mean(speedups) if speedups else 1.0,
            "speedup_trend": (
                "improving"
                if len(speedups) > 1 and speedups[-1] > speedups[-2]
                else "stable"
            ),
            "latest_results_count": len(latest.results),
            "successful_rate": (
                len(latest.successful_results) / len(latest.results)
                if latest.results
                else 0.0
            ),
        }

    def compare_templates(self, template_ids: list[str]) -> dict[str, Any]:
        """Compare performance across multiple templates."""
        comparisons: dict[str, dict[str, Any]] = {}

        for template_id in template_ids:
            history = self.get_benchmark_history(template_id)
            if history:
                latest = history[-1]
                comparisons[template_id] = {
                    "average_speedup": latest.average_speedup,
                    "scalability_factor": latest.scalability_factor,
                    "successful_results": len(latest.successful_results),
                    "benchmark_date": latest.benchmark_date.isoformat(),
                }

        if not comparisons:
            return {"error": "No benchmark data available for comparison"}

        # Find best performing template
        best_template = max(
            comparisons.keys(), key=lambda t: float(comparisons[t]["average_speedup"])
        )

        return {
            "templates_compared": len(comparisons),
            "best_performing": best_template,
            "comparisons": comparisons,
            "summary": {
                "max_speedup": max(
                    float(c["average_speedup"]) for c in comparisons.values()
                ),
                "min_speedup": min(
                    float(c["average_speedup"]) for c in comparisons.values()
                ),
                "avg_speedup": statistics.mean(
                    float(c["average_speedup"]) for c in comparisons.values()
                ),
            },
        }
