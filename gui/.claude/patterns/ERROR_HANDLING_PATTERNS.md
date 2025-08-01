# Error Handling Patterns for OR-Tools

## Overview

Comprehensive error handling strategies for OR-Tools applications, covering prevention, detection, recovery, and user communication.

## Error Classification

```
┌─────────────────────────────────────────────┐
│           Error Categories                  │
├──────────┬───────────┬──────────┬──────────┤
│   Data   │  Solver   │ Constraint│ System  │
│  Errors  │ Failures  │ Conflicts │ Errors  │
└──────────┴───────────┴──────────┴──────────┘
```

## Error Type Hierarchy

### 1. Data Validation Errors

```python
# src/solver/errors/data_errors.py
from typing import List, Dict, Optional

class DataValidationError(Exception):
    """Base class for data validation errors."""
    
    def __init__(self, message: str, field: str = None, value: any = None):
        self.field = field
        self.value = value
        super().__init__(message)
    
    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        if self.field:
            return f"Invalid {self.field}: {self.args[0]}"
        return str(self.args[0])

class MissingDataError(DataValidationError):
    """Required data is missing."""
    pass

class InvalidDurationError(DataValidationError):
    """Task duration is invalid."""
    
    def __init__(self, task_id: int, duration: int):
        super().__init__(
            f"Duration must be positive, got {duration}",
            field="duration",
            value=duration
        )
        self.task_id = task_id

class CircularDependencyError(DataValidationError):
    """Circular dependency detected in precedences."""
    
    def __init__(self, cycle: List[int]):
        self.cycle = cycle
        message = f"Circular dependency: {' -> '.join(map(str, cycle))}"
        super().__init__(message, field="precedences")
```

### 2. Solver Errors

```python
class SolverError(Exception):
    """Base class for solver-related errors."""
    
    def __init__(self, message: str, status: str = None):
        self.status = status
        self.timestamp = datetime.now()
        super().__init__(message)

class InfeasibleProblemError(SolverError):
    """Problem has no feasible solution."""
    
    def __init__(self, conflicts: List[str] = None):
        self.conflicts = conflicts or []
        message = "No feasible solution exists"
        if conflicts:
            message += f". Conflicts: {', '.join(conflicts)}"
        super().__init__(message, status="INFEASIBLE")
    
    def get_diagnostic_info(self) -> Dict:
        """Get detailed diagnostic information."""
        return {
            'status': self.status,
            'conflicts': self.conflicts,
            'suggestions': self._get_suggestions()
        }
    
    def _get_suggestions(self) -> List[str]:
        """Suggest potential fixes."""
        suggestions = []
        if 'time window' in str(self.conflicts):
            suggestions.append("Try relaxing time window constraints")
        if 'capacity' in str(self.conflicts):
            suggestions.append("Consider increasing resource capacity")
        return suggestions

class SolverTimeoutError(SolverError):
    """Solver exceeded time limit."""
    
    def __init__(self, time_limit: float, best_solution: Optional[Dict] = None):
        self.time_limit = time_limit
        self.best_solution = best_solution
        message = f"Solver timeout after {time_limit}s"
        if best_solution:
            message += f" (found solution with objective {best_solution['objective']})"
        super().__init__(message, status="TIMEOUT")
```

### 3. Constraint Conflicts

```python
class ConstraintConflictError(Exception):
    """Constraint conflict detected."""
    
    def __init__(
        self, 
        constraint_type: str,
        conflicting_items: List[str],
        details: Dict = None
    ):
        self.constraint_type = constraint_type
        self.conflicting_items = conflicting_items
        self.details = details or {}
        
        message = f"{constraint_type} conflict: {', '.join(conflicting_items)}"
        super().__init__(message)

class ResourceOverflowError(ConstraintConflictError):
    """Resource capacity exceeded."""
    
    def __init__(
        self,
        resource_id: int,
        time_point: int,
        required: int,
        available: int
    ):
        super().__init__(
            "Resource capacity",
            [f"Resource {resource_id} at time {time_point}"],
            {
                'resource_id': resource_id,
                'time_point': time_point,
                'required': required,
                'available': available,
                'overflow': required - available
            }
        )
```

## Error Handling Strategies

### Strategy 1: Preventive Validation

```python
# src/solver/validation/preventive.py
class PreventiveValidator:
    """Validate before attempting to solve."""
    
    def validate_before_solve(self, problem: SchedulingProblem) -> None:
        """Run all validations before solving."""
        validators = [
            self._validate_data_integrity,
            self._validate_constraint_compatibility,
            self._validate_feasibility_bounds,
            self._validate_resource_availability
        ]
        
        errors = []
        warnings = []
        
        for validator in validators:
            try:
                validator(problem)
            except DataValidationError as e:
                errors.append(e)
            except Warning as w:
                warnings.append(w)
        
        if errors:
            raise ValidationBatchError(errors, warnings)
        
        if warnings:
            logger.warning(f"Validation warnings: {warnings}")
    
    def _validate_feasibility_bounds(self, problem: SchedulingProblem) -> None:
        """Check if problem has feasible bounds."""
        # Check if total duration fits in horizon
        total_duration = sum(t.duration for t in problem.tasks)
        min_horizon = total_duration // problem.num_machines
        
        if problem.horizon < min_horizon:
            raise DataValidationError(
                f"Horizon {problem.horizon} too small for workload. "
                f"Need at least {min_horizon}",
                field="horizon"
            )
        
        # Check time windows
        for task in problem.tasks:
            if hasattr(task, 'latest_end') and hasattr(task, 'earliest_start'):
                if task.latest_end - task.earliest_start < task.duration:
                    raise InvalidTimeWindowError(
                        task.id,
                        task.earliest_start,
                        task.latest_end,
                        task.duration
                    )
```

### Strategy 2: Graceful Degradation

```python
class GracefulSolver:
    """Solver with graceful degradation."""
    
    def solve_with_fallback(
        self,
        problem: SchedulingProblem
    ) -> Solution:
        """Solve with multiple fallback strategies."""
        strategies = [
            (self._solve_optimal, "optimal"),
            (self._solve_relaxed, "relaxed"),
            (self._solve_heuristic, "heuristic"),
            (self._solve_greedy, "greedy")
        ]
        
        last_error = None
        
        for solve_func, strategy_name in strategies:
            try:
                logger.info(f"Attempting {strategy_name} strategy")
                solution = solve_func(problem)
                
                if solution:
                    solution.metadata['strategy'] = strategy_name
                    if strategy_name != "optimal":
                        logger.warning(
                            f"Used fallback strategy: {strategy_name}"
                        )
                    return solution
                    
            except SolverError as e:
                logger.warning(f"{strategy_name} failed: {e}")
                last_error = e
                continue
        
        # All strategies failed
        raise SolverExhaustionError(
            "All solving strategies failed",
            last_error=last_error,
            attempted_strategies=[s[1] for s in strategies]
        )
    
    def _solve_relaxed(self, problem: SchedulingProblem) -> Solution:
        """Solve with relaxed constraints."""
        relaxed_problem = problem.copy()
        
        # Relax time windows by 20%
        for task in relaxed_problem.tasks:
            if hasattr(task, 'earliest_start'):
                task.earliest_start = int(task.earliest_start * 0.8)
            if hasattr(task, 'latest_end'):
                task.latest_end = int(task.latest_end * 1.2)
        
        # Increase solver time limit
        solver = FreshSolver(time_limit=300)
        return solver.solve(relaxed_problem)
```

### Strategy 3: Error Recovery

```python
class ErrorRecoveryHandler:
    """Handle and recover from errors."""
    
    def __init__(self):
        self.recovery_strategies = {
            InfeasibleProblemError: self._recover_from_infeasible,
            SolverTimeoutError: self._recover_from_timeout,
            ResourceOverflowError: self._recover_from_resource_overflow
        }
    
    def handle_error(
        self,
        error: Exception,
        problem: SchedulingProblem,
        context: Dict
    ) -> Optional[Solution]:
        """Attempt to recover from error."""
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            recovery_func = self.recovery_strategies[error_type]
            return recovery_func(error, problem, context)
        
        # Log unhandled error
        logger.error(f"Unhandled error type: {error_type}")
        raise error
    
    def _recover_from_infeasible(
        self,
        error: InfeasibleProblemError,
        problem: SchedulingProblem,
        context: Dict
    ) -> Optional[Solution]:
        """Recover from infeasible problem."""
        # Try to identify conflicting constraints
        conflict_analyzer = ConflictAnalyzer()
        conflicts = conflict_analyzer.analyze(problem)
        
        if conflicts:
            # Remove least important conflicts
            relaxed_problem = self._relax_conflicts(problem, conflicts)
            
            # Retry with relaxed problem
            solver = FreshSolver()
            solution = solver.solve(relaxed_problem)
            
            if solution:
                solution.metadata['relaxed_constraints'] = conflicts
                return solution
        
        return None
```

## Logging and Monitoring

### Structured Logging

```python
# src/solver/logging/structured.py
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class SolverLogger:
    """Structured logging for solver operations."""
    
    def __init__(self, problem_id: str):
        self.logger = logger.bind(problem_id=problem_id)
    
    def log_validation_error(
        self,
        error: DataValidationError,
        context: Dict[str, Any]
    ) -> None:
        """Log validation error with context."""
        self.logger.error(
            "validation_failed",
            error_type=type(error).__name__,
            field=error.field,
            value=error.value,
            message=str(error),
            context=context,
            timestamp=datetime.now().isoformat()
        )
    
    def log_solver_attempt(
        self,
        strategy: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Log solver attempt."""
        self.logger.info(
            "solver_attempt",
            strategy=strategy,
            parameters=parameters,
            timestamp=datetime.now().isoformat()
        )
    
    def log_solver_result(
        self,
        status: str,
        solve_time: float,
        objective: Optional[float] = None
    ) -> None:
        """Log solver result."""
        self.logger.info(
            "solver_result",
            status=status,
            solve_time_seconds=solve_time,
            objective_value=objective,
            timestamp=datetime.now().isoformat()
        )
```

### Error Tracking

```python
class ErrorTracker:
    """Track and analyze errors."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def track_error(
        self,
        error: Exception,
        problem_id: str,
        context: Dict
    ) -> str:
        """Track error in database."""
        error_data = {
            'problem_id': problem_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_details': self._extract_error_details(error),
            'context': context,
            'stack_trace': traceback.format_exc(),
            'created_at': datetime.now()
        }
        
        response = self.client.table('solver_errors')\
            .insert(error_data)\
            .execute()
            
        return response.data[0]['id']
    
    def get_error_patterns(self, days: int = 7) -> Dict:
        """Analyze error patterns."""
        cutoff = datetime.now() - timedelta(days=days)
        
        response = self.client.rpc(
            'analyze_error_patterns',
            {'cutoff_date': cutoff.isoformat()}
        ).execute()
        
        return response.data
```

## User Communication

### Error Message Templates

```python
class UserErrorFormatter:
    """Format errors for user display."""
    
    ERROR_TEMPLATES = {
        InvalidDurationError: "Task {task_id} has an invalid duration. Duration must be positive.",
        CircularDependencyError: "Tasks have circular dependencies: {cycle}. Please review task ordering.",
        InfeasibleProblemError: "Unable to find a valid schedule. {suggestions}",
        SolverTimeoutError: "Scheduling is taking longer than expected. {status}",
        ResourceOverflowError: "Not enough {resource_type} available at {time}."
    }
    
    def format_for_user(self, error: Exception) -> Dict[str, Any]:
        """Format error for user display."""
        error_type = type(error)
        
        # Get template
        template = self.ERROR_TEMPLATES.get(
            error_type,
            "An error occurred: {message}"
        )
        
        # Format message
        message = self._format_template(template, error)
        
        # Get severity
        severity = self._get_severity(error_type)
        
        # Get suggestions
        suggestions = self._get_suggestions(error)
        
        return {
            'message': message,
            'severity': severity,
            'suggestions': suggestions,
            'error_code': error_type.__name__,
            'can_retry': self._is_retryable(error_type)
        }
    
    def _get_suggestions(self, error: Exception) -> List[str]:
        """Get actionable suggestions for user."""
        suggestions = []
        
        if isinstance(error, InfeasibleProblemError):
            suggestions.extend([
                "Try extending the scheduling horizon",
                "Review task dependencies for conflicts",
                "Check resource availability"
            ])
        elif isinstance(error, SolverTimeoutError):
            suggestions.extend([
                "Consider breaking the problem into smaller parts",
                "Reduce the number of constraints",
                "Accept a near-optimal solution"
            ])
        
        return suggestions
```

### Progressive Error Detail

```python
class ProgressiveErrorDisplay:
    """Show error details progressively."""
    
    def get_error_display(
        self,
        error: Exception,
        detail_level: str = "basic"
    ) -> Dict:
        """Get error display based on detail level."""
        levels = {
            "basic": self._get_basic_info,
            "detailed": self._get_detailed_info,
            "debug": self._get_debug_info
        }
        
        if detail_level not in levels:
            detail_level = "basic"
            
        return levels[detail_level](error)
    
    def _get_basic_info(self, error: Exception) -> Dict:
        """Basic user-friendly info."""
        formatter = UserErrorFormatter()
        return formatter.format_for_user(error)
    
    def _get_detailed_info(self, error: Exception) -> Dict:
        """Detailed information for power users."""
        basic = self._get_basic_info(error)
        
        basic['technical_details'] = {
            'error_type': type(error).__name__,
            'attributes': {
                k: v for k, v in error.__dict__.items()
                if not k.startswith('_')
            }
        }
        
        if hasattr(error, 'get_diagnostic_info'):
            basic['diagnostics'] = error.get_diagnostic_info()
            
        return basic
    
    def _get_debug_info(self, error: Exception) -> Dict:
        """Full debug information."""
        detailed = self._get_detailed_info(error)
        
        detailed['debug'] = {
            'stack_trace': traceback.format_exc(),
            'locals': self._safe_extract_locals(),
            'system_info': self._get_system_info()
        }
        
        return detailed
```

## Debugging Workflows

### Interactive Debugger

```python
class InteractiveSolverDebugger:
    """Interactive debugging for solver issues."""
    
    def debug_infeasible_problem(
        self,
        problem: SchedulingProblem
    ) -> None:
        """Interactively debug infeasible problem."""
        print("Starting infeasibility analysis...")
        
        # Step 1: Check individual constraint types
        constraint_checks = [
            ("Duration constraints", self._check_duration_feasibility),
            ("Precedence constraints", self._check_precedence_feasibility),
            ("Resource constraints", self._check_resource_feasibility),
            ("Time window constraints", self._check_time_window_feasibility)
        ]
        
        for name, check_func in constraint_checks:
            print(f"\nChecking {name}...")
            result = check_func(problem)
            
            if not result['feasible']:
                print(f"❌ {name} are infeasible!")
                print(f"   Reason: {result['reason']}")
                print(f"   Affected items: {result['items']}")
                
                if self._prompt_fix(name):
                    self._apply_fix(problem, result['fix'])
            else:
                print(f"✅ {name} are feasible")
        
        # Step 2: Check constraint interactions
        print("\nChecking constraint interactions...")
        interactions = self._check_constraint_interactions(problem)
        
        if interactions:
            print("Found problematic interactions:")
            for interaction in interactions:
                print(f"  - {interaction}")
    
    def _prompt_fix(self, constraint_name: str) -> bool:
        """Prompt user for fix decision."""
        response = input(f"Attempt to fix {constraint_name}? (y/n): ")
        return response.lower() == 'y'
```

### Error Reproduction

```python
class ErrorReproducer:
    """Reproduce errors for debugging."""
    
    def save_error_context(
        self,
        error: Exception,
        problem: SchedulingProblem,
        solver_state: Dict
    ) -> str:
        """Save complete error context."""
        context_id = str(uuid.uuid4())
        
        # Serialize problem
        problem_data = problem.to_dict()
        
        # Save to file
        error_context = {
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            },
            'problem': problem_data,
            'solver_state': solver_state,
            'timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info()
        }
        
        filename = f"error_context_{context_id}.json"
        with open(filename, 'w') as f:
            json.dump(error_context, f, indent=2)
            
        return filename
    
    def reproduce_from_file(self, filename: str) -> None:
        """Reproduce error from saved context."""
        with open(filename, 'r') as f:
            context = json.load(f)
        
        # Recreate problem
        problem = SchedulingProblem.from_dict(context['problem'])
        
        # Recreate solver with same parameters
        solver = FreshSolver(**context['solver_state'])
        
        # Attempt to reproduce
        try:
            solution = solver.solve(problem)
            print("Error not reproduced - got solution!")
        except Exception as e:
            print(f"Reproduced error: {type(e).__name__}: {e}")
```

## Best Practices

### 1. Error Prevention

```python
# Always validate input data
def process_problem(data: Dict) -> Solution:
    # Validate first
    validator = DataValidator()
    validation_result = validator.validate(data)
    
    if not validation_result.is_valid:
        raise ValidationError(validation_result.errors)
    
    # Then process
    problem = create_problem(validation_result.cleaned_data)
    return solve_problem(problem)
```

### 2. Fail Fast

```python
# Check preconditions early
def add_constraint(model, constraint_data):
    # Fail fast on invalid input
    if not constraint_data:
        raise ValueError("Constraint data cannot be empty")
    
    if 'type' not in constraint_data:
        raise KeyError("Constraint must have a type")
    
    # Process valid data
    return _add_constraint_internal(model, constraint_data)
```

### 3. Rich Error Context

```python
# Provide context for debugging
try:
    solution = solver.solve(problem)
except SolverError as e:
    # Add context
    e.problem_size = len(problem.tasks)
    e.constraint_count = model.NumConstraints()
    e.time_elapsed = time.time() - start_time
    
    # Log with context
    logger.error("Solver failed", exc_info=e, extra={
        'problem_id': problem.id,
        'problem_size': e.problem_size,
        'constraint_count': e.constraint_count
    })
    
    raise
```

### 4. Graceful User Experience

```python
# Handle errors gracefully in API
@app.route('/solve', methods=['POST'])
def solve_problem():
    try:
        data = request.json
        solution = solve_scheduling_problem(data)
        return jsonify({'success': True, 'solution': solution})
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid input data',
            'details': e.errors,
            'suggestions': e.suggestions
        }), 400
        
    except InfeasibleProblemError as e:
        return jsonify({
            'success': False,
            'error': 'No valid schedule found',
            'conflicts': e.conflicts,
            'suggestions': [
                'Try extending the time horizon',
                'Review resource availability'
            ]
        }), 422
        
    except Exception as e:
        # Log unexpected errors
        error_id = str(uuid.uuid4())
        logger.error(f"Unexpected error {error_id}", exc_info=True)
        
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'error_id': error_id,
            'message': 'Please contact support with this error ID'
        }), 500
```

This comprehensive error handling system ensures robust operation and excellent debugging capabilities!