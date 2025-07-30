# Performance Benchmarking Process for OR-Tools

## Overview

Systematic approach to measuring, tracking, and optimizing solver performance across different problem scales and configurations.

## Benchmarking Framework

```
┌─────────────────────────────────────────────┐
│        Performance Benchmarking Flow         │
├─────────┬──────────┬───────────┬───────────┤
│ Baseline│ Measure  │  Analyze  │ Optimize  │
│  Setup  │ Execute  │  Results  │  & Verify │
└─────────┴──────────┴───────────┴───────────┘
```

## Performance Metrics

### Primary Metrics
1. **Solve Time** - Time to find optimal/feasible solution
2. **Memory Usage** - Peak memory consumption
3. **Model Building Time** - Time to construct CP-SAT model
4. **Solution Quality** - Objective value achieved
5. **Time to First Solution** - For anytime algorithms

### Secondary Metrics
1. **Variables Created** - Total decision variables
2. **Constraints Added** - Total constraints in model
3. **Search Nodes Explored** - Solver search space
4. **CPU Utilization** - Multi-core efficiency
5. **Iterations/Second** - Solver throughput

## Benchmark Implementation

### 1. Benchmark Suite Structure

```python
# benchmarks/performance_suite.py
import pytest
import time
import psutil
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class BenchmarkResult:
    """Performance benchmark result."""
    name: str
    size: str
    solve_time: float
    memory_mb: float
    model_build_time: float
    solution_status: str
    objective_value: Optional[float]
    variables_count: int
    constraints_count: int
    first_solution_time: Optional[float]
    
    def meets_target(self, targets: Dict[str, float]) -> bool:
        """Check if result meets performance targets."""
        size_target = targets.get(self.size, float('inf'))
        return self.solve_time <= size_target

class PerformanceBenchmark:
    """Base class for OR-Tools performance benchmarks."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process(os.getpid())
        
    def measure_memory(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
        
    def run_benchmark(self, name: str, problem_generator, solver_func):
        """Run a single benchmark."""
        # Measure initial state
        initial_memory = self.measure_memory()
        
        # Generate problem
        start_time = time.time()
        problem = problem_generator()
        
        # Build model
        model_start = time.time()
        model, variables = build_model(problem)
        model_build_time = time.time() - model_start
        
        # Track first solution
        first_solution_time = None
        
        def solution_callback(solver):
            nonlocal first_solution_time
            if first_solution_time is None:
                first_solution_time = time.time() - solve_start
        
        # Solve
        solve_start = time.time()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300  # 5 min timeout
        
        # Add callback for first solution
        solver.solve_with_solution_callback(model, solution_callback)
        
        solve_time = time.time() - solve_start
        peak_memory = self.measure_memory()
        
        # Create result
        result = BenchmarkResult(
            name=name,
            size=problem.size_category,
            solve_time=solve_time,
            memory_mb=peak_memory - initial_memory,
            model_build_time=model_build_time,
            solution_status=solver.StatusName(),
            objective_value=solver.ObjectiveValue() if solver.StatusName() in ['OPTIMAL', 'FEASIBLE'] else None,
            variables_count=len(variables),
            constraints_count=model.NumConstraints(),
            first_solution_time=first_solution_time
        )
        
        self.results.append(result)
        return result
```

### 2. Problem Size Definitions

```python
# benchmarks/problem_sizes.py
PROBLEM_SIZES = {
    'tiny': {
        'jobs': 2,
        'tasks_per_job': 5,
        'machines': 3,
        'time_horizon': 100,
        'target_time': 1.0  # seconds
    },
    'small': {
        'jobs': 5,
        'tasks_per_job': 10,
        'machines': 5,
        'time_horizon': 500,
        'target_time': 10.0
    },
    'medium': {
        'jobs': 20,
        'tasks_per_job': 25,
        'machines': 10,
        'time_horizon': 2000,
        'target_time': 60.0
    },
    'large': {
        'jobs': 50,
        'tasks_per_job': 100,
        'machines': 20,
        'time_horizon': 10000,
        'target_time': 172800.0  # 48 hours
    }
}

def generate_problem_for_size(size: str) -> SchedulingProblem:
    """Generate problem of specified size."""
    config = PROBLEM_SIZES[size]
    return generate_random_problem(**config)
```

### 3. Benchmark Test Suite

```python
# benchmarks/test_performance.py
import pytest
from benchmarks.performance_suite import PerformanceBenchmark
from benchmarks.problem_sizes import PROBLEM_SIZES, generate_problem_for_size

class TestSolverPerformance(PerformanceBenchmark):
    """Performance benchmarks for solver."""
    
    @pytest.mark.benchmark
    @pytest.mark.parametrize("size", ["tiny", "small", "medium"])
    def test_basic_scheduling_performance(self, size):
        """Benchmark basic scheduling performance."""
        result = self.run_benchmark(
            name=f"basic_scheduling_{size}",
            problem_generator=lambda: generate_problem_for_size(size),
            solver_func=lambda p: FreshSolver().solve(p)
        )
        
        # Assert performance targets
        target = PROBLEM_SIZES[size]['target_time']
        assert result.solve_time < target, \
            f"{size} solve time {result.solve_time}s exceeds target {target}s"
        
    @pytest.mark.benchmark
    @pytest.mark.slow  # Mark slow tests
    def test_large_problem_performance(self):
        """Benchmark large problem (run with --slow flag)."""
        result = self.run_benchmark(
            name="large_scheduling",
            problem_generator=lambda: generate_problem_for_size("large"),
            solver_func=lambda p: FreshSolver().solve(p)
        )
        
        # More lenient target for large problems
        assert result.solve_time < 172800  # 48 hours
        assert result.first_solution_time < 3600  # First solution within 1 hour
```

### 4. Constraint-Specific Benchmarks

```python
# benchmarks/constraint_benchmarks.py
class ConstraintBenchmarks(PerformanceBenchmark):
    """Benchmark individual constraint performance."""
    
    def benchmark_precedence_scaling(self):
        """Test how precedence constraints scale."""
        results = []
        
        for num_precedences in [10, 100, 1000, 10000]:
            problem = create_problem_with_precedences(num_precedences)
            
            start = time.time()
            model = cp_model.CpModel()
            variables = create_variables(model, problem)
            add_precedence_constraints(model, variables, problem.precedences)
            elapsed = time.time() - start
            
            results.append({
                'precedences': num_precedences,
                'time': elapsed,
                'constraints': model.NumConstraints()
            })
            
        # Check scaling is linear or better
        self._verify_scaling(results)
    
    def benchmark_resource_capacity(self):
        """Test resource capacity constraint performance."""
        for num_resources in [5, 50, 500]:
            for num_time_windows in [1, 10, 100]:
                problem = create_capacity_problem(
                    num_resources, num_time_windows
                )
                result = self.run_benchmark(
                    f"capacity_r{num_resources}_w{num_time_windows}",
                    lambda: problem,
                    solve_with_capacity
                )
```

## Performance Profiling

### 1. Solver Profiling

```python
def profile_solver_execution(problem: SchedulingProblem) -> Dict:
    """Detailed profiling of solver execution."""
    
    profiler = SolverProfiler()
    
    # Profile model building
    with profiler.measure("model_building"):
        model = cp_model.CpModel()
        variables = create_all_variables(model, problem)
    
    # Profile each constraint type
    with profiler.measure("duration_constraints"):
        add_duration_constraints(model, variables)
        
    with profiler.measure("precedence_constraints"):
        add_precedence_constraints(model, variables)
        
    with profiler.measure("assignment_constraints"):
        add_assignment_constraints(model, variables)
        
    with profiler.measure("no_overlap_constraints"):
        add_no_overlap_constraints(model, variables)
    
    # Profile solving
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    
    with profiler.measure("solving"):
        status = solver.Solve(model)
    
    # Analyze results
    return {
        'profile': profiler.get_results(),
        'solver_stats': {
            'status': solver.StatusName(),
            'time': solver.WallTime(),
            'branches': solver.NumBranches(),
            'conflicts': solver.NumConflicts(),
            'solutions': solver.SolutionCount()
        }
    }
```

### 2. Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_solve(problem_size: str):
    """Profile memory usage during solve."""
    problem = generate_problem_for_size(problem_size)
    
    # Track memory at each stage
    model = cp_model.CpModel()  # Line 1
    variables = create_variables(model, problem)  # Line 2
    add_all_constraints(model, variables, problem)  # Line 3
    
    solver = cp_model.CpSolver()  # Line 4
    status = solver.Solve(model)  # Line 5
    
    solution = extract_solution(solver, variables)  # Line 6
    return solution
```

### 3. Bottleneck Analysis

```python
def analyze_bottlenecks(profile_data: Dict) -> Dict:
    """Identify performance bottlenecks."""
    
    total_time = sum(profile_data['profile'].values())
    bottlenecks = []
    
    for component, time_spent in profile_data['profile'].items():
        percentage = (time_spent / total_time) * 100
        
        if percentage > 20:  # Component takes >20% of time
            bottlenecks.append({
                'component': component,
                'time': time_spent,
                'percentage': percentage,
                'severity': 'high' if percentage > 40 else 'medium'
            })
    
    return {
        'bottlenecks': bottlenecks,
        'recommendations': generate_optimization_recommendations(bottlenecks)
    }
```

## Continuous Performance Tracking

### 1. Performance Database

```python
# benchmarks/tracking.py
import sqlite3
from datetime import datetime

class PerformanceTracker:
    """Track performance over time."""
    
    def __init__(self, db_path: str = "benchmarks.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        
    def _create_tables(self):
        """Create performance tracking tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                git_commit TEXT,
                test_name TEXT,
                problem_size TEXT,
                solve_time REAL,
                memory_mb REAL,
                objective_value REAL,
                status TEXT
            )
        """)
        
    def record_benchmark(self, result: BenchmarkResult, git_commit: str):
        """Record benchmark result."""
        self.conn.execute("""
            INSERT INTO benchmarks 
            (timestamp, git_commit, test_name, problem_size, 
             solve_time, memory_mb, objective_value, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(), git_commit, result.name, result.size,
            result.solve_time, result.memory_mb, 
            result.objective_value, result.solution_status
        ))
        self.conn.commit()
        
    def get_performance_trend(self, test_name: str, days: int = 30):
        """Get performance trend for specific test."""
        query = """
            SELECT timestamp, solve_time, git_commit
            FROM benchmarks
            WHERE test_name = ? 
            AND timestamp > datetime('now', '-{} days')
            ORDER BY timestamp
        """.format(days)
        
        return self.conn.execute(query, (test_name,)).fetchall()
```

### 2. Performance Regression Detection

```python
def detect_performance_regression(
    current: BenchmarkResult,
    history: List[BenchmarkResult],
    threshold: float = 0.2  # 20% regression threshold
) -> Optional[str]:
    """Detect if current result is a regression."""
    
    if not history:
        return None
        
    # Calculate baseline (median of last 10 runs)
    recent_times = sorted([r.solve_time for r in history[-10:]])
    baseline = recent_times[len(recent_times) // 2]
    
    # Check for regression
    if current.solve_time > baseline * (1 + threshold):
        regression_percent = ((current.solve_time - baseline) / baseline) * 100
        return f"Performance regression detected: {regression_percent:.1f}% slower than baseline"
        
    return None
```

### 3. Automated Performance Reports

```python
def generate_performance_report(results: List[BenchmarkResult]) -> str:
    """Generate performance report."""
    
    report = """
# Performance Benchmark Report
Generated: {timestamp}

## Summary
Total benchmarks run: {total}
Passed targets: {passed}
Failed targets: {failed}

## Results by Size
{size_results}

## Bottleneck Analysis
{bottlenecks}

## Recommendations
{recommendations}
"""
    
    # Analyze results
    passed = sum(1 for r in results if r.meets_target(PROBLEM_SIZES))
    failed = len(results) - passed
    
    # Group by size
    by_size = {}
    for result in results:
        by_size.setdefault(result.size, []).append(result)
    
    size_results = []
    for size, size_results in by_size.items():
        avg_time = sum(r.solve_time for r in size_results) / len(size_results)
        size_results.append(f"- {size}: avg {avg_time:.2f}s")
    
    return report.format(
        timestamp=datetime.now(),
        total=len(results),
        passed=passed,
        failed=failed,
        size_results="\n".join(size_results),
        bottlenecks=analyze_bottlenecks(results),
        recommendations=generate_recommendations(results)
    )
```

## Integration with CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/performance.yml
name: Performance Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest-benchmark memory-profiler
        
    - name: Run benchmarks
      run: |
        pytest benchmarks/test_performance.py \
          --benchmark-only \
          --benchmark-json=benchmark_results.json
          
    - name: Check for regression
      run: |
        python scripts/check_regression.py benchmark_results.json
        
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: benchmark-results
        path: |
          benchmark_results.json
          performance_report.html
```

## Performance Optimization Workflow

### 1. Identify Bottleneck

```bash
# Profile specific test
/profile-solver --test medium_scheduling

# Output shows bottleneck
> no_overlap_constraints: 45% of total time
```

### 2. Optimize

```python
# Before: O(n²) no-overlap implementation
def add_no_overlap_naive(model, tasks):
    for i, task1 in enumerate(tasks):
        for j, task2 in enumerate(tasks[i+1:], i+1):
            # Disjunctive constraint
            model.AddNoOverlap([task1, task2])

# After: O(n) using global constraint
def add_no_overlap_optimized(model, tasks):
    # Group by machine
    by_machine = defaultdict(list)
    for task in tasks:
        by_machine[task.machine].append(task.interval)
    
    # One no-overlap per machine
    for machine, intervals in by_machine.items():
        model.AddNoOverlap(intervals)
```

### 3. Verify Improvement

```bash
# Re-run benchmark
/profile-solver --test medium_scheduling

# Compare results
> no_overlap_constraints: 12% of total time (was 45%)
> Total speedup: 3.2x
```

## Best Practices

1. **Benchmark Early and Often**
   - Run benchmarks in CI/CD
   - Track trends over time
   - Set performance budgets

2. **Profile Before Optimizing**
   - Identify actual bottlenecks
   - Measure impact of changes
   - Avoid premature optimization

3. **Test Realistic Scenarios**
   - Use production-like data
   - Test various problem structures
   - Include edge cases

4. **Monitor Production Performance**
   - Log solve times
   - Track memory usage
   - Alert on degradation