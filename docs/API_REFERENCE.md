# API Reference - Production Enhancement Systems

## Template Parameter Management API

### ParameterManager

#### Methods

##### `validate_parameters(template_id: str, parameters: dict[str, Any]) -> ValidationResult`
Validate solver parameters for a template.

**Parameters:**
- `template_id`: Template identifier
- `parameters`: Dictionary of CP-SAT solver parameters

**Returns:** `ValidationResult` with validation status and speedup estimation

**Example:**
```python
param_manager = ParameterManager()
result = param_manager.validate_parameters("template_v1", {
    "num_search_workers": 8,
    "max_time_in_seconds": 60
})
```

##### `promote_parameters(template_id: str, validation_result: ValidationResult) -> BlessedParameters`
Promote validated parameters to blessed status.

##### `get_solver_parameters(template_id: str) -> dict[str, Any]`
Get blessed parameters for production use.

##### `list_blessed_parameters() -> list[BlessedParameters]`
List all blessed parameter configurations.

### TemplateOptimizer

#### Methods

##### `optimize_parameters(template_id: str, instance_counts: list[int], time_limit_seconds: int) -> OptimizationResult`
Run systematic parameter optimization.

##### `add_symmetry_breaking_constraints(model: cp_model.CpModel, variables: dict, config: SymmetryBreakingConfig)`
Add symmetry breaking constraints for performance optimization.

### TemplateValidator

#### Methods

##### `validate_template_comprehensive(template_id: str, job_template: Any, test_instances: int = 5) -> TemplateValidationReport`
Perform comprehensive template validation.

##### `validate_template_regression(template_id: str, current_performance: float, tolerance: float = 0.2) -> TemplateValidationReport`
Validate performance against historical baseline.

## Performance Infrastructure API

### BenchmarkRunner

#### Methods

##### `run_template_benchmark(config: TemplateBenchmark) -> BenchmarkSuite`
Execute comprehensive template benchmarking.

**Parameters:**
- `config`: Benchmark configuration with template ID, instance counts, time limits

**Returns:** `BenchmarkSuite` with detailed performance results

**Example:**
```python
config = TemplateBenchmark(
    template_id="manufacturing_v1",
    instance_counts=[1, 3, 5, 10],
    time_limit_seconds=60
)
suite = benchmark_runner.run_template_benchmark(config)
```

##### `get_performance_trends(template_id: str) -> dict[str, Any]`
Get performance trends for template.

### RegressionDetector

#### Methods

##### `establish_baseline(template_id: str, baseline_time: float, baseline_date: datetime = None)`
Establish performance baseline.

##### `check_regression(template_id: str, current_time: float, threshold: float = 0.2) -> PerformanceRegression | None`
Check for performance regression.

##### `get_regression_alerts() -> list[RegressionAlert]`
Get active regression alerts.

### Profiling APIs

#### ConstraintProfiler

##### `profile_constraint_performance(model: cp_model.CpModel, constraint_functions: list[Callable]) -> ConstraintProfile`
Profile constraint-level performance.

#### SolverProfiler

##### `profile_solver_performance(model: cp_model.CpModel, solver: cp_model.CpSolver, variables: dict) -> SolverProfile`
Profile overall solver performance.

#### MemoryProfiler

##### `profile_memory_usage(model: cp_model.CpModel, variables: dict) -> MemorySnapshot`
Profile memory usage patterns.

## Production Monitoring API

### PerformanceMonitor

#### Methods

##### `record_solve_performance(template_id: str, solve_time: float, instance_count: int, solver_status: str, **kwargs)`
Record solver performance metrics.

**Parameters:**
- `template_id`: Template identifier
- `solve_time`: Solve time in seconds
- `instance_count`: Number of instances solved
- `solver_status`: Solver status (OPTIMAL, FEASIBLE, etc.)
- `memory_usage_mb`: Optional memory usage in MB
- `objective_value`: Optional solution objective value

**Example:**
```python
perf_monitor.record_solve_performance(
    template_id="production_template",
    solve_time=2.3,
    instance_count=5,
    solver_status="OPTIMAL",
    memory_usage_mb=150
)
```

##### `record_system_metrics(cpu_percent: float, memory_percent: float, disk_usage_percent: float, **kwargs)`
Record system resource metrics.

##### `get_current_health() -> SystemHealthMetrics`
Get current system health assessment.

##### `get_template_performance_summary(template_id: str, hours: int = 1) -> dict[str, Any]`
Get performance summary for specific template.

##### `get_performance_trends(hours: int = 24) -> dict[str, Any]`
Get performance trends over time.

##### `export_metrics(template_id: str = None, hours: int = 1) -> list[dict[str, Any]]`
Export metrics for external monitoring systems.

### HealthChecker

#### Methods

##### `run_all_checks() -> list[HealthCheckResult]`
Run all health checks and return results.

**Returns:** List of `HealthCheckResult` objects with individual check results

**Example:**
```python
health_checker = HealthChecker()
results = health_checker.run_all_checks()
passed = sum(1 for r in results if r.is_healthy)
```

##### `register_custom_check(name: str, check_function: Callable[[], HealthCheckResult])`
Register custom health check function.

##### `get_overall_health_status(results: list[HealthCheckResult] = None) -> str`
Get overall system health status.

##### `generate_health_report() -> dict[str, Any]`
Generate comprehensive health report.

##### `get_health_history(hours: int = 24) -> list[HealthCheckResult]`
Get health check history.

### AlertManager

#### Methods

##### `create_performance_alert(template_id: str, current_time: float, baseline_time: float, threshold_percent: float) -> Alert | None`
Create performance degradation alert.

**Parameters:**
- `template_id`: Template identifier
- `current_time`: Current performance time
- `baseline_time`: Baseline performance time
- `threshold_percent`: Degradation threshold percentage

**Returns:** Created `Alert` object or None if not triggered

**Example:**
```python
alert = alert_manager.create_performance_alert(
    template_id="critical_template",
    current_time=15.2,
    baseline_time=3.1,
    threshold_percent=50.0
)
```

##### `add_channel(channel: AlertChannel)`
Add notification channel.

##### `add_rule(rule: AlertRule)`
Add alert rule.

##### `get_alert_statistics() -> dict[str, int]`
Get alert statistics.

##### `get_active_alerts() -> list[Alert]`
Get currently active alerts.

##### `resolve_alert(alert_id: str, resolution_note: str = "")`
Resolve an active alert.

## Data Classes

### BlessedParameters
```python
@dataclass
class BlessedParameters:
    template_id: str
    parameters: dict[str, Any]
    performance_baseline: float
    validation_date: datetime
    approved_by: str
    speedup_factor: float = 1.0
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    is_valid: bool
    speedup_factor: float
    validation_errors: list[str]
    validation_warnings: list[str]
    estimated_solve_time: float
```

### BenchmarkResult
```python
@dataclass
class BenchmarkResult:
    template_id: str
    instance_count: int
    solve_time: float
    memory_usage_mb: float
    objective_value: float | None
    solver_status: str
```

### BenchmarkSuite
```python
@dataclass
class BenchmarkSuite:
    template_id: str
    results: list[BenchmarkResult]
    average_speedup: float
    scalability_factor: float
    successful_results: list[BenchmarkResult]
```

### PerformanceMetric
```python
@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    template_id: str | None = None
    instance_count: int | None = None
    tags: dict[str, str] = field(default_factory=dict)
```

### SystemHealthMetrics
```python
@dataclass
class SystemHealthMetrics:
    status: SystemHealthStatus
    timestamp: datetime
    solver_performance: dict[str, float] = field(default_factory=dict)
    resource_utilization: dict[str, float] = field(default_factory=dict)
    error_rates: dict[str, float] = field(default_factory=dict)
    active_templates: int = 0
    recent_failures: int = 0
```

### HealthCheckResult
```python
@dataclass
class HealthCheckResult:
    name: str
    severity: HealthCheckSeverity  # INFO, WARNING, CRITICAL
    status: str  # "pass", "warning", "fail"
    message: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
```

### Alert
```python
@dataclass
class Alert:
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity  # LOW, MEDIUM, HIGH, CRITICAL
    template_id: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
```

## Enums

### SystemHealthStatus
```python
class SystemHealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
```

### HealthCheckSeverity
```python
class HealthCheckSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
```

### AlertSeverity
```python
class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

## Configuration Classes

### TemplateBenchmark
```python
@dataclass
class TemplateBenchmark:
    template_id: str
    instance_counts: list[int]
    time_limit_seconds: int = 60
    repetitions: int = 3
    parameters: dict[str, Any] = field(default_factory=dict)
```

### AlertChannel
```python
@dataclass
class AlertChannel:
    name: str
    type: str  # "email", "slack", "webhook"
    config: dict[str, Any]
    enabled: bool = True
```

### AlertRule
```python
@dataclass
class AlertRule:
    name: str
    condition: str
    severity: AlertSeverity
    channels: list[str]
    cooldown_minutes: int = 60
    enabled: bool = True
```

## Usage Examples

### Complete Integration Example
```python
def production_workflow_example():
    # 1. Parameter Management
    param_manager = ParameterManager()
    solver_params = param_manager.get_solver_parameters("production_template")
    
    # 2. Performance Monitoring
    perf_monitor = PerformanceMonitor()
    
    # 3. Health Checks
    health_checker = HealthChecker()
    health_results = health_checker.run_all_checks()
    
    if any(r.is_critical for r in health_results):
        raise SystemError("Critical health check failure")
    
    # 4. Solver execution with monitoring
    start_time = time.time()
    # ... solver execution ...
    solve_time = time.time() - start_time
    
    # 5. Record performance
    perf_monitor.record_solve_performance(
        template_id="production_template",
        solve_time=solve_time,
        instance_count=10,
        solver_status="OPTIMAL"
    )
    
    # 6. Check for regressions
    detector = RegressionDetector()
    regression = detector.check_regression("production_template", solve_time)
    
    # 7. Alert if needed
    if regression and regression.is_significant:
        alert_manager = AlertManager()
        alert_manager.create_performance_alert(
            "production_template", solve_time, regression.baseline_time, 50.0
        )
```

This API reference provides complete documentation for all three enhancement systems, enabling developers to integrate production-grade monitoring and optimization capabilities into their OR-Tools constraint programming solutions.