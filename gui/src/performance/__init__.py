"""Performance infrastructure for OR-Tools solver optimization.

This module provides comprehensive performance monitoring, benchmarking,
and regression detection capabilities for template-based scheduling optimization.
"""

from .benchmarks import BenchmarkResult, BenchmarkRunner, TemplateBenchmark
from .profiling import ConstraintProfiler, MemoryProfiler, SolverProfiler
from .regression import PerformanceRegression, RegressionAlert, RegressionDetector

__all__ = [
    # Benchmarking
    "TemplateBenchmark",
    "BenchmarkRunner",
    "BenchmarkResult",
    # Profiling
    "ConstraintProfiler",
    "SolverProfiler",
    "MemoryProfiler",
    # Regression Detection
    "RegressionDetector",
    "RegressionAlert",
    "PerformanceRegression",
]
