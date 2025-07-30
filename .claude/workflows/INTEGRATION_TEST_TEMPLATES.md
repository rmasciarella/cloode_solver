# Integration Test Templates for OR-Tools

## Overview

Templates and patterns for testing multiple OR-Tools components working together, ensuring system-wide correctness and performance.

## Integration Test Hierarchy

```
┌────────────────────────────────────────────┐
│         Integration Test Levels            │
├──────────┬──────────┬──────────┬──────────┤
│Component │ Feature  │  Phase   │  System  │
│  Pairs   │  Groups  │ Complete │   E2E    │
└──────────┴──────────┴──────────┴──────────┘
```

## Level 1: Component Integration Tests

### Template: Constraint Pair Integration

```python
# tests/integration/constraints/test_constraint_pairs.py
import pytest
from ortools.sat.python import cp_model
from src.solver.constraints import (
    add_duration_constraints,
    add_precedence_constraints,
    add_assignment_constraints,
    add_no_overlap_constraints
)

class TestConstraintPairIntegration:
    """Test pairs of constraints working together."""
    
    @pytest.fixture
    def base_problem(self):
        """Create base problem for integration testing."""
        return SchedulingProblem(
            jobs=[Job(id=1), Job(id=2)],
            tasks=[
                Task(id=1, job_id=1, duration=30),
                Task(id=2, job_id=1, duration=45),
                Task(id=3, job_id=2, duration=60),
                Task(id=4, job_id=2, duration=30)
            ],
            machines=[Machine(id=1), Machine(id=2)],
            precedences=[(1, 2), (3, 4)]
        )
    
    def test_precedence_with_assignment(self, base_problem):
        """Test precedence constraints with assignment constraints."""
        # GIVEN: Model with both constraint types
        model = cp_model.CpModel()
        variables = create_all_variables(model, base_problem)
        
        # WHEN: Adding both constraints
        add_precedence_constraints(
            model, 
            variables['task_starts'],
            variables['task_ends'],
            base_problem.precedences
        )
        
        add_assignment_constraints(
            model,
            variables['task_assigned'],
            base_problem.tasks
        )
        
        # THEN: Both constraints should be satisfied
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        
        assert status == cp_model.OPTIMAL
        
        # Verify precedence
        for (pred, succ) in base_problem.precedences:
            pred_end = solver.Value(variables['task_ends'][(1, pred)])
            succ_start = solver.Value(variables['task_starts'][(1, succ)])
            assert pred_end <= succ_start
        
        # Verify assignment
        for task in base_problem.tasks:
            assigned_count = sum(
                solver.Value(variables['task_assigned'][(1, task.id, m)])
                for m in [1, 2]
            )
            assert assigned_count == 1  # Exactly one machine
    
    def test_assignment_with_no_overlap(self, base_problem):
        """Test assignment with no-overlap constraints."""
        # Template for testing machine conflicts
        # ... implementation ...
```

### Template: Data Flow Integration

```python
class TestDataFlowIntegration:
    """Test data flow from loader to solver to storage."""
    
    def test_database_to_solver_flow(self, test_db):
        """Test complete flow from database to solver."""
        # GIVEN: Data in database
        loader = DatabaseLoader(test_db)
        problem = loader.load_problem(problem_id=1)
        
        # WHEN: Solving
        solver = FreshSolver()
        solution = solver.solve(problem)
        
        # THEN: Solution should be valid
        assert solution is not None
        assert validate_solution(solution, problem)
        
        # AND: Should be storable
        storage = SolutionStorage(test_db)
        stored_id = storage.store_solution(solution)
        assert stored_id is not None
        
        # AND: Should be retrievable
        retrieved = storage.get_solution(stored_id)
        assert retrieved.objective_value == solution.objective_value
```

## Level 2: Feature Integration Tests

### Template: Complete Feature Test

```python
# tests/integration/features/test_resource_capacity.py
class TestResourceCapacityFeature:
    """Test complete resource capacity feature."""
    
    def test_capacity_feature_end_to_end(self):
        """Test resource capacity from problem definition to solution."""
        # GIVEN: Problem with resource capacity requirements
        problem = SchedulingProblem()
        
        # Add tasks with resource needs
        task1 = Task(id=1, duration=60, resource_requirement=2)
        task2 = Task(id=2, duration=45, resource_requirement=3)
        task3 = Task(id=3, duration=30, resource_requirement=1)
        problem.add_tasks([task1, task2, task3])
        
        # Add resource with limited capacity
        resource = Resource(
            id=1,
            capacity=3,  # Max 3 units
            available_windows=[(0, 200)]
        )
        problem.add_resource(resource)
        
        # Add machine assignments requiring resource
        problem.set_task_resource_requirement(1, 1, 2)  # Task 1 needs 2 units
        problem.set_task_resource_requirement(2, 1, 3)  # Task 2 needs 3 units
        problem.set_task_resource_requirement(3, 1, 1)  # Task 3 needs 1 unit
        
        # WHEN: Solving with capacity constraints
        solver = FreshSolver()
        solution = solver.solve(problem)
        
        # THEN: Capacity should never be exceeded
        resource_usage = calculate_resource_usage_timeline(solution, problem)
        
        for time_point, usage in resource_usage.items():
            assert usage <= resource.capacity, \
                f"Capacity exceeded at time {time_point}: {usage} > {resource.capacity}"
        
        # AND: Tasks should be scheduled to respect capacity
        # Task 1 and 2 cannot run simultaneously (2+3 > 3)
        task1_interval = (solution.task_starts[1], solution.task_ends[1])
        task2_interval = (solution.task_starts[2], solution.task_ends[2])
        
        assert not intervals_overlap(task1_interval, task2_interval), \
            "Tasks 1 and 2 overlap despite capacity constraint"
```

### Template: Multi-Constraint Feature

```python
class TestMultiConstraintIntegration:
    """Test features requiring multiple constraint types."""
    
    @pytest.mark.integration
    def test_maintenance_window_feature(self):
        """Test maintenance windows affecting multiple constraints."""
        # GIVEN: Problem with maintenance windows
        problem = create_problem_with_maintenance()
        
        # Maintenance window blocks all machines 100-150
        maintenance = MaintenanceWindow(
            start=100,
            end=150,
            machines=[1, 2, 3]
        )
        problem.add_maintenance_window(maintenance)
        
        # WHEN: Solving
        solver = FreshSolver()
        solution = solver.solve(problem)
        
        # THEN: No tasks during maintenance
        for task_id, start in solution.task_starts.items():
            end = solution.task_ends[task_id]
            
            # Task should not overlap maintenance
            assert end <= maintenance.start or start >= maintenance.end, \
                f"Task {task_id} scheduled during maintenance"
        
        # AND: Precedence still respected
        verify_precedence_constraints(solution, problem)
        
        # AND: Assignments still valid
        verify_assignment_constraints(solution, problem)
```

## Level 3: Phase Integration Tests

### Template: Complete Phase Test

```python
# tests/integration/phases/test_phase_integration.py
class TestPhaseIntegration:
    """Test complete phase implementations."""
    
    def create_phase_test_problem(self, phase: int) -> SchedulingProblem:
        """Create problem with all features for given phase."""
        problem = SchedulingProblem()
        
        if phase >= 1:
            # Phase 1 features
            add_basic_scheduling_data(problem)
            add_precedence_data(problem)
            add_machine_assignment_data(problem)
            
        if phase >= 2:
            # Phase 2 features
            add_resource_capacity_data(problem)
            add_skill_matching_data(problem)
            add_variable_duration_data(problem)
            
        if phase >= 3:
            # Phase 3 features
            add_shift_constraint_data(problem)
            add_setup_time_data(problem)
            add_parallel_execution_data(problem)
            
        return problem
    
    @pytest.mark.phase1
    def test_phase_1_complete(self):
        """Test all Phase 1 features together."""
        # GIVEN: Phase 1 problem
        problem = self.create_phase_test_problem(phase=1)
        
        # WHEN: Solving with Phase 1 solver
        solver = FreshSolver(phase=1)
        solution = solver.solve(problem)
        
        # THEN: All Phase 1 requirements met
        assert solution is not None
        assert solution.status in ['OPTIMAL', 'FEASIBLE']
        
        # Verify all constraints
        self.verify_phase_1_constraints(solution, problem)
        
        # Check performance
        assert solution.solve_time < 10.0  # Phase 1 performance target
        
    def verify_phase_1_constraints(self, solution, problem):
        """Verify all Phase 1 constraints satisfied."""
        # Duration constraints
        for task_id in solution.task_starts:
            duration = problem.get_task(task_id).duration
            assert solution.task_ends[task_id] == \
                   solution.task_starts[task_id] + duration
        
        # Precedence constraints
        for (pred, succ) in problem.precedences:
            assert solution.task_ends[pred] <= solution.task_starts[succ]
        
        # Assignment constraints
        for task_id in solution.task_assignments:
            assert solution.task_assignments[task_id] in problem.valid_machines[task_id]
        
        # No overlap constraints
        self.verify_no_overlap(solution, problem)
```

## Level 4: System Integration Tests

### Template: End-to-End Test

```python
# tests/integration/system/test_end_to_end.py
class TestEndToEnd:
    """Complete system integration tests."""
    
    @pytest.mark.e2e
    def test_complete_workflow(self, test_database):
        """Test complete workflow from input to output."""
        # GIVEN: Input data in multiple formats
        
        # 1. Load from database
        db_loader = DatabaseLoader(test_database)
        db_problem = db_loader.load_problem(1)
        
        # 2. Load from file
        file_loader = FileLoader()
        file_problem = file_loader.load_from_json("test_data/problem.json")
        
        # 3. Create programmatically
        api_problem = create_problem_via_api()
        
        # WHEN: Solving all three
        solver = FreshSolver()
        
        db_solution = solver.solve(db_problem)
        file_solution = solver.solve(file_problem)
        api_solution = solver.solve(api_problem)
        
        # THEN: All should solve successfully
        assert all(s.status in ['OPTIMAL', 'FEASIBLE'] 
                  for s in [db_solution, file_solution, api_solution])
        
        # AND: Solutions should be exportable
        exporters = [
            JsonExporter(),
            CsvExporter(),
            DatabaseExporter(test_database)
        ]
        
        for solution in [db_solution, file_solution, api_solution]:
            for exporter in exporters:
                exported = exporter.export(solution)
                assert exported is not None
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_concurrent_solving(self):
        """Test multiple solvers running concurrently."""
        import concurrent.futures
        
        # GIVEN: Multiple different problems
        problems = [
            create_small_problem(),
            create_medium_problem(),
            create_large_problem()
        ]
        
        # WHEN: Solving concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i, problem in enumerate(problems):
                solver = FreshSolver()
                future = executor.submit(solver.solve, problem)
                futures.append((i, future))
            
            # THEN: All should complete
            results = {}
            for i, future in futures:
                try:
                    solution = future.result(timeout=300)
                    results[i] = solution
                except concurrent.futures.TimeoutError:
                    pytest.fail(f"Problem {i} timed out")
        
        # Verify all solved
        assert len(results) == len(problems)
        for solution in results.values():
            assert solution.status in ['OPTIMAL', 'FEASIBLE']
```

## Integration Test Patterns

### Pattern 1: State Verification

```python
class StateVerificationPattern:
    """Verify system state at integration points."""
    
    def verify_model_state_after_constraints(self, model, expected):
        """Verify model state after adding constraints."""
        actual = {
            'variables': model.NumVariables(),
            'constraints': model.NumConstraints(),
            'objectives': model.HasObjective()
        }
        
        for key, expected_value in expected.items():
            assert actual[key] == expected_value, \
                f"Model {key}: expected {expected_value}, got {actual[key]}"
    
    def verify_solution_completeness(self, solution, problem):
        """Verify solution contains all required data."""
        # All tasks scheduled
        assert len(solution.task_starts) == len(problem.tasks)
        assert len(solution.task_ends) == len(problem.tasks)
        
        # All assignments made
        assert len(solution.task_assignments) == len(problem.tasks)
        
        # Objective calculated
        assert solution.objective_value is not None
```

### Pattern 2: Error Propagation

```python
class ErrorPropagationPattern:
    """Test error handling across components."""
    
    def test_invalid_data_propagation(self):
        """Test how invalid data propagates through system."""
        # GIVEN: Invalid problem data
        problem = SchedulingProblem()
        problem.add_task(Task(id=1, duration=-10))  # Invalid duration
        
        # WHEN: Attempting to solve
        solver = FreshSolver()
        
        # THEN: Should get meaningful error
        with pytest.raises(ValueError) as exc_info:
            solver.solve(problem)
        
        assert "duration must be positive" in str(exc_info.value)
        assert "Task id=1" in str(exc_info.value)
```

### Pattern 3: Performance Under Load

```python
class LoadTestingPattern:
    """Test integration under various load conditions."""
    
    @pytest.mark.load
    def test_memory_stability(self):
        """Test memory doesn't leak across multiple solves."""
        import gc
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Solve many problems
        for i in range(100):
            problem = create_random_problem(size='small')
            solver = FreshSolver()
            solution = solver.solve(problem)
            
            # Cleanup
            del problem, solver, solution
            if i % 10 == 0:
                gc.collect()
        
        # Check memory
        final_memory = process.memory_info().rss
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        assert memory_growth < 100, f"Memory grew by {memory_growth}MB"
```

## Integration Test Organization

### Directory Structure

```
tests/integration/
├── __init__.py
├── conftest.py              # Shared fixtures
├── constraints/             # Constraint integration
│   ├── test_pairs.py
│   └── test_groups.py
├── features/               # Feature integration
│   ├── test_resources.py
│   ├── test_skills.py
│   └── test_maintenance.py
├── phases/                 # Phase integration
│   ├── test_phase1.py
│   ├── test_phase2.py
│   └── test_phase3.py
├── system/                 # System integration
│   ├── test_end_to_end.py
│   ├── test_performance.py
│   └── test_error_handling.py
└── scenarios/              # Real-world scenarios
    ├── test_manufacturing.py
    ├── test_logistics.py
    └── test_healthcare.py
```

### Fixture Hierarchy

```python
# conftest.py
@pytest.fixture(scope='session')
def test_database():
    """Database for integration tests."""
    db = create_test_database()
    populate_test_data(db)
    yield db
    cleanup_database(db)

@pytest.fixture(scope='function')
def solver():
    """Fresh solver instance."""
    return FreshSolver()

@pytest.fixture(scope='function')
def problem_generator():
    """Generate test problems."""
    def _generate(size='small', features=None):
        problem = create_base_problem(size)
        if features:
            for feature in features:
                add_feature_to_problem(problem, feature)
        return problem
    return _generate
```

## Test Execution Strategy

### Run Levels

```bash
# Quick integration tests (< 1 min)
pytest tests/integration -m "not slow"

# Full integration suite
pytest tests/integration

# Specific feature tests
pytest tests/integration/features/test_resources.py

# Phase-specific tests
pytest tests/integration/phases -k "phase1"

# End-to-end tests only
pytest tests/integration/system -m "e2e"
```

### CI/CD Integration

```yaml
# .github/workflows/integration-tests.yml
integration-tests:
  strategy:
    matrix:
      test-level: [quick, features, phases, e2e]
  
  steps:
    - name: Run integration tests
      run: |
        if [ "${{ matrix.test-level }}" = "quick" ]; then
          pytest tests/integration -m "not slow" --maxfail=3
        elif [ "${{ matrix.test-level }}" = "features" ]; then
          pytest tests/integration/features -v
        elif [ "${{ matrix.test-level }}" = "phases" ]; then
          pytest tests/integration/phases -v
        elif [ "${{ matrix.test-level }}" = "e2e" ]; then
          pytest tests/integration/system -m "e2e" -v
        fi
```

## Best Practices

1. **Test Independence**
   - Each test should set up its own data
   - No shared mutable state
   - Clean up after tests

2. **Realistic Data**
   - Use production-like problem sizes
   - Include edge cases from real scenarios
   - Test with actual constraint combinations

3. **Performance Awareness**
   - Mark slow tests appropriately
   - Set timeouts for long-running tests
   - Monitor test execution time

4. **Clear Failure Messages**
   - Include context in assertions
   - Log intermediate states
   - Provide debugging information

5. **Incremental Testing**
   - Test component pairs before groups
   - Test features before phases
   - Build up to full system tests