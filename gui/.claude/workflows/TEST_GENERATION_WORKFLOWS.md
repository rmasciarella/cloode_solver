# Test Generation Workflows for OR-Tools

## Overview

Systematic workflows for generating comprehensive tests at unit, integration, and performance levels for OR-Tools components.

## Test Generation Philosophy

```
┌─────────────────────────────────────────┐
│         Test Generation Flow            │
├──────────┬───────────┬─────────────────┤
│  Analyze │  Generate │    Validate     │
│   Code   │   Tests   │   Coverage      │
└──────────┴───────────┴─────────────────┘
```

## Workflow 1: Unit Test Generation

### Step 1: Analyze Target Function

```python
# Target: src/solver/constraints/capacity.py
def add_capacity_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[int, int], IntVar],
    resources: Dict[int, ResourceCapacity]
) -> None:
    """Add resource capacity constraints."""
    # Function implementation
```

**Analysis Checklist:**
- [ ] Input parameters and types
- [ ] Expected outputs/side effects
- [ ] Edge cases and boundaries
- [ ] Error conditions
- [ ] Dependencies

### Step 2: Generate Test Structure

```python
# Generated: tests/unit/constraints/test_capacity.py
import pytest
from ortools.sat.python import cp_model
from src.solver.constraints.capacity import add_capacity_constraints
from src.solver.models.problem import ResourceCapacity

class TestCapacityConstraints:
    """Test suite for capacity constraints."""
    
    @pytest.fixture
    def basic_model(self):
        """Create basic model for testing."""
        model = cp_model.CpModel()
        return model
    
    @pytest.fixture
    def task_variables(self, basic_model):
        """Create task variables for testing."""
        starts = {
            (1, 1): basic_model.NewIntVar(0, 100, 'start_1_1'),
            (1, 2): basic_model.NewIntVar(0, 100, 'start_1_2')
        }
        return starts
```

### Step 3: Generate Test Cases

```python
def test_basic_capacity_constraint(self, basic_model, task_variables):
    """Test basic capacity constraint enforcement."""
    # GIVEN: Model with tasks and resource capacity
    resources = {
        1: ResourceCapacity(id=1, capacity=2, time_windows=[(0, 50)])
    }
    
    # WHEN: Adding capacity constraints
    add_capacity_constraints(basic_model, task_variables, resources)
    
    # THEN: Model should have capacity constraints
    assert basic_model.NumConstraints() > 0
    
def test_capacity_exceeded(self, basic_model, task_variables):
    """Test behavior when capacity would be exceeded."""
    # GIVEN: Limited capacity resource
    resources = {
        1: ResourceCapacity(id=1, capacity=1, time_windows=[(0, 20)])
    }
    
    # WHEN: Multiple tasks need same resource
    add_capacity_constraints(basic_model, task_variables, resources)
    solver = cp_model.CpSolver()
    status = solver.Solve(basic_model)
    
    # THEN: Tasks should not overlap
    if status == cp_model.OPTIMAL:
        start1 = solver.Value(task_variables[(1, 1)])
        start2 = solver.Value(task_variables[(1, 2)])
        assert abs(start1 - start2) >= 10  # Assuming duration 10

def test_empty_resources(self, basic_model, task_variables):
    """Test with no resources defined."""
    # GIVEN: Empty resources
    resources = {}
    
    # WHEN: Adding constraints
    add_capacity_constraints(basic_model, task_variables, resources)
    
    # THEN: Should not fail
    assert basic_model.NumConstraints() == 0
```

### Step 4: Generate Edge Case Tests

```python
def test_zero_capacity(self, basic_model, task_variables):
    """Test resource with zero capacity."""
    # Edge case: resource exists but has no capacity
    resources = {
        1: ResourceCapacity(id=1, capacity=0, time_windows=[(0, 50)])
    }
    
    # Should make model infeasible if tasks require this resource
    add_capacity_constraints(basic_model, task_variables, resources)
    solver = cp_model.CpSolver()
    status = solver.Solve(basic_model)
    
    # Expecting infeasible or no tasks assigned to this resource
    assert status != cp_model.OPTIMAL or not tasks_use_resource(solver, 1)

def test_overlapping_time_windows(self, basic_model, task_variables):
    """Test resource with overlapping availability windows."""
    resources = {
        1: ResourceCapacity(
            id=1, 
            capacity=2, 
            time_windows=[(0, 30), (20, 50)]  # Overlap 20-30
        )
    }
    
    # Should handle overlapping windows correctly
    add_capacity_constraints(basic_model, task_variables, resources)
    # Verify constraints properly handle the overlap
```

## Workflow 2: Integration Test Generation

### Step 1: Identify Integration Points

```python
# Integration test for complete constraint system
class TestPhaseIntegration:
    """Test multiple constraints working together."""
    
    def test_capacity_with_precedence(self):
        """Test capacity constraints with precedence constraints."""
        # GIVEN: Problem with both precedence and capacity requirements
        problem = create_test_problem(
            tasks_with_precedence=True,
            resources_with_capacity=True
        )
        
        # WHEN: Solving with all constraints
        solver = FreshSolver()
        solution = solver.solve(problem)
        
        # THEN: Both constraint types should be satisfied
        assert_precedence_satisfied(solution)
        assert_capacity_satisfied(solution)
        assert solution.status == 'OPTIMAL'
```

### Step 2: Generate Interaction Tests

```python
def test_capacity_forces_precedence_delay(self):
    """Test when capacity constraints delay precedence tasks."""
    # GIVEN: Task B must follow A, but resource is busy
    problem = SchedulingProblem()
    problem.add_task(Task(id=1, duration=20))  # A
    problem.add_task(Task(id=2, duration=20))  # B
    problem.add_task(Task(id=3, duration=30))  # C (blocks resource)
    problem.add_precedence(task_a=1, task_b=2)
    
    # Resource available 0-100, capacity 1
    problem.add_resource(ResourceCapacity(
        id=1, capacity=1, time_windows=[(0, 100)]
    ))
    
    # All tasks need same resource
    problem.assign_task_to_resource(1, 1)
    problem.assign_task_to_resource(2, 1)
    problem.assign_task_to_resource(3, 1)
    
    # WHEN: Solving
    solution = solver.solve(problem)
    
    # THEN: Tasks should be sequenced
    assert solution.task_starts[3] >= 0
    assert solution.task_starts[1] >= 30  # After C
    assert solution.task_starts[2] >= 50  # After A
```

## Workflow 3: Performance Test Generation

### Step 1: Define Performance Scenarios

```python
# Performance test template
class TestPerformance:
    """Performance benchmarks for solver components."""
    
    @pytest.mark.benchmark
    @pytest.mark.parametrize("size", [
        ("tiny", 2, 10),
        ("small", 5, 50), 
        ("medium", 20, 500),
        ("large", 50, 5000)
    ])
    def test_solve_time(self, benchmark, size):
        """Benchmark solve time for different problem sizes."""
        name, num_jobs, num_tasks = size
        
        # GIVEN: Problem of specified size
        problem = generate_problem(num_jobs, num_tasks)
        solver = FreshSolver()
        
        # WHEN: Timing the solve
        result = benchmark(solver.solve, problem)
        
        # THEN: Should meet performance targets
        assert result.status in ['OPTIMAL', 'FEASIBLE']
        assert benchmark.stats['mean'] < PERFORMANCE_TARGETS[name]
```

### Step 2: Generate Stress Tests

```python
def test_memory_usage_large_problem(self):
    """Test memory usage doesn't explode with problem size."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create large problem
    problem = generate_problem(num_jobs=100, num_tasks=10000)
    solver = FreshSolver()
    
    # Solve and measure memory
    solution = solver.solve(problem)
    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    memory_increase = peak_memory - initial_memory
    assert memory_increase < 1000  # Less than 1GB increase
    print(f"Memory used: {memory_increase:.1f} MB")
```

## Test Generation Commands

### Using /test-constraint Command

```bash
/test-constraint capacity

# Generates:
- Unit tests for add_capacity_constraints
- Edge case tests
- Integration test stubs
- Performance test template
```

### Test Generation Checklist

```python
def generate_test_checklist(function_name: str) -> dict:
    """Generate comprehensive test checklist."""
    return {
        'unit_tests': [
            'happy_path',
            'empty_input',
            'single_element', 
            'maximum_size',
            'invalid_input',
            'edge_boundaries'
        ],
        'integration_tests': [
            'with_other_constraints',
            'full_pipeline',
            'error_propagation'
        ],
        'performance_tests': [
            'small_scale',
            'medium_scale', 
            'large_scale',
            'stress_test'
        ],
        'property_tests': [
            'invariants',
            'symmetry',
            'monotonicity'
        ]
    }
```

## Test Patterns

### Pattern 1: Constraint Test Pattern

```python
def test_{constraint_type}_pattern(self):
    """Standard pattern for testing constraints."""
    # GIVEN: Model and problem setup
    model, variables = setup_test_model()
    constraint_data = create_constraint_data()
    
    # WHEN: Adding constraint
    add_{constraint_type}_constraints(model, variables, constraint_data)
    
    # THEN: Verify constraint behavior
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    # Check feasibility
    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    
    # Check constraint is satisfied
    assert verify_{constraint_type}_satisfied(solver, variables)
    
    # Check expected properties
    assert check_{constraint_type}_properties(solver, variables)
```

### Pattern 2: Solver Test Pattern

```python
def test_solver_with_{scenario}(self):
    """Test solver with specific scenario."""
    # GIVEN: Specific problem scenario
    problem = create_{scenario}_problem()
    
    # WHEN: Solving
    solver = FreshSolver()
    with time_limit(60):  # Timeout protection
        solution = solver.solve(problem)
    
    # THEN: Verify solution quality
    assert solution is not None
    assert solution.status in ACCEPTABLE_STATUSES
    assert validate_solution(solution, problem)
    assert solution.objective_value <= EXPECTED_BOUNDS[scenario]
```

## Test Data Generation

### Dynamic Test Data

```python
class TestDataGenerator:
    """Generate test data for OR-Tools tests."""
    
    @staticmethod
    def generate_tasks(num_tasks: int, seed: int = 42) -> List[Task]:
        """Generate random but reproducible tasks."""
        random.seed(seed)
        tasks = []
        
        for i in range(num_tasks):
            duration = random.randint(1, 20) * 15  # 15-min intervals
            tasks.append(Task(
                id=i,
                name=f"task_{i}",
                duration_minutes=duration
            ))
            
        return tasks
    
    @staticmethod 
    def generate_precedence_chain(tasks: List[Task]) -> List[Tuple]:
        """Generate linear precedence chain."""
        precedences = []
        for i in range(len(tasks) - 1):
            precedences.append((tasks[i].id, tasks[i+1].id))
        return precedences
```

### Fixture Library

```python
# conftest.py - Shared test fixtures
@pytest.fixture
def simple_problem():
    """Simple 2-job, 10-task problem."""
    return create_test_problem(jobs=2, tasks_per_job=5)

@pytest.fixture
def complex_problem():
    """Complex problem with all constraint types."""
    problem = create_test_problem(jobs=10, tasks_per_job=10)
    add_resource_constraints(problem)
    add_precedence_constraints(problem)
    add_maintenance_windows(problem)
    return problem

@pytest.fixture
def infeasible_problem():
    """Problem designed to be infeasible."""
    problem = create_test_problem(jobs=5, tasks_per_job=5)
    # Add conflicting constraints
    add_impossible_precedence(problem)
    return problem
```

## Coverage Requirements

### Minimum Coverage Targets

```yaml
coverage:
  unit_tests:
    target: 90%
    exclude:
      - "*/test_*.py"
      - "*/__init__.py"
  
  integration_tests:
    target: 80%
    focus_on:
      - "solver/core/*"
      - "solver/constraints/*"
  
  performance_tests:
    scenarios:
      - tiny: < 1s
      - small: < 10s
      - medium: < 60s
      - large: < 48h
```

### Coverage Report Integration

```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Check specific module
pytest tests/unit/constraints/test_capacity.py --cov=src/solver/constraints/capacity

# Fail if below threshold
pytest --cov=src --cov-fail-under=85
```

## Test Maintenance

### Test Review Checklist

Before committing tests:
- [ ] Tests follow GIVEN-WHEN-THEN pattern
- [ ] All edge cases covered
- [ ] Performance tests included for new features
- [ ] Integration with existing constraints tested
- [ ] Tests are deterministic (use fixed seeds)
- [ ] Clear test names and descriptions
- [ ] No hardcoded paths or values
- [ ] Cleanup after tests (no side effects)

### Test Refactoring Triggers

Refactor tests when:
1. Test setup > 20 lines → Extract fixtures
2. Duplicate test logic → Create test utilities
3. Slow tests > 5s → Add @pytest.mark.slow
4. Flaky tests → Fix or mark @pytest.mark.flaky