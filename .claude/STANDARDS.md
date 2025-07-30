# STANDARDS.md - OR-Tools Model Development Standards

## 1. Coding Standards

### Variable Naming Conventions
```python
# Decision Variables - Always use descriptive dictionaries
task_starts[(job_id, task_id)]              # IntVar: when task starts
task_ends[(job_id, task_id)]                # IntVar: when task ends
task_intervals[(job_id, task_id)]           # IntervalVar: task duration interval
task_assigned[(job_id, task_id, machine_id)] # BoolVar: assignment to machine
task_presences[(job_id, task_id)]           # BoolVar: whether task is scheduled
machine_intervals[(machine_id)]             # List[IntervalVar]: all intervals on machine

# Constants - UPPER_CASE
MAX_HORIZON = 10000
MIN_TASK_DURATION = 1

# Helper structures - lowercase with underscores
task_to_machines = {}  # Mapping of eligible machines per task
```

### Function Standards
```python
def add_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[int, int], IntVar],
    task_ends: Dict[Tuple[int, int], IntVar],
    precedences: List[Tuple[Tuple[int, int], Tuple[int, int]]]
) -> None:
    """Add precedence constraints between tasks.
    
    Args:
        model: The CP-SAT model
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables  
        precedences: List of ((job1, task1), (job2, task2)) tuples
        
    Constraints Added:
        - task2 must start after task1 ends
    """
    for (job1, task1), (job2, task2) in precedences:
        model.Add(task_starts[(job2, task2)] >= task_ends[(job1, task1)])
```

### Constraint Function Rules
1. Each function adds ONE type of constraint
2. Function name starts with `add_` followed by constraint type
3. Always type hint all parameters and return None
4. Docstring must list what constraints are added
5. Maximum 30 lines of actual code (excluding docstring)

## 2. Development Workflow

### Phase Implementation Process
```
1. PLAN
   - Document all constraints for the phase in detail
   - Identify variable dependencies
   - Sketch constraint formulations
   
2. IMPLEMENT
   - Create variables first
   - Add constraints in dependency order
   - Add solver hints/redundant constraints
   
3. TEST
   - Unit test each constraint function
   - Integration test the phase
   - Performance test with realistic data
   
4. VALIDATE
   - Check solution feasibility
   - Verify all constraints are satisfied
   - Compare against expected results
```

### Before Starting Each Phase
- [ ] Review data model completeness
- [ ] Document expected behavior
- [ ] Create test cases FIRST
- [ ] Identify solver efficiency opportunities

## 3. Testing Standards

### Unit Test Structure
```python
def test_precedence_constraints():
    """Test that precedence constraints are correctly enforced."""
    # GIVEN: A model with two tasks
    model = cp_model.CpModel()
    task_starts = {
        (1, 1): model.NewIntVar(0, 100, 'start_1_1'),
        (1, 2): model.NewIntVar(0, 100, 'start_1_2')
    }
    task_ends = {
        (1, 1): model.NewIntVar(0, 100, 'end_1_1'),
        (1, 2): model.NewIntVar(0, 100, 'end_1_2')
    }
    
    # WHEN: Adding precedence constraint
    add_precedence_constraints(model, task_starts, task_ends, [((1, 1), (1, 2))])
    
    # THEN: Solver finds valid solution where task 2 starts after task 1
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL
    assert solver.Value(task_starts[(1, 2)]) >= solver.Value(task_ends[(1, 1)])
```

### Integration Test Pattern
```python
def test_phase_1_integration():
    """Test Phase 1 constraints work together correctly."""
    # Load minimal test data
    # Create all Phase 1 variables
    # Add all Phase 1 constraints
    # Solve and validate solution meets all requirements
```

## 4. Review Procedures

### Self-Review Checklist (Before Each Commit)
- [ ] All variables follow naming convention
- [ ] All functions have complete docstrings
- [ ] No function exceeds 30 lines
- [ ] All constraints have unit tests
- [ ] Integration test passes
- [ ] No hardcoded values (use constants)

### Phase Completion Review
- [ ] All planned constraints implemented
- [ ] Performance meets targets (solve time < 60s for test data)
- [ ] Solution quality validated
- [ ] Edge cases handled
- [ ] Documentation complete

## 5. Solver Efficiency Standards

### Variable Bounds
```python
# ALWAYS set tight bounds
horizon = calculate_minimum_horizon(tasks)  # Not arbitrary large number
task_start = model.NewIntVar(
    earliest_start,  # Based on precedences
    latest_start,    # Based on due dates
    f'start_{job_id}_{task_id}'
)
```

### Redundant Constraints
```python
# Add constraints that help solver prune search space
if task1_precedes_task2 and task2_precedes_task3:
    # Add transitive constraint
    model.Add(task_starts[(job, task3)] >= task_ends[(job, task1)])
```

### Search Strategies
```python
# Define search strategy for better performance
model.AddDecisionStrategy(
    task_starts.values(),
    cp_model.CHOOSE_FIRST,
    cp_model.SELECT_MIN_VALUE
)
```

## 6. Error Handling

### Data Validation
```python
# Validate in data model, not in solver
@dataclass
class Task:
    duration: int
    
    def __post_init__(self):
        if self.duration <= 0:
            raise ValueError(f"Task duration must be positive: {self.duration}")
```

### Solver Status Handling
```python
status = solver.Solve(model)
if status == cp_model.OPTIMAL:
    return extract_solution(solver, variables)
elif status == cp_model.FEASIBLE:
    logger.warning("Found feasible but not optimal solution")
    return extract_solution(solver, variables)
elif status == cp_model.INFEASIBLE:
    raise ValueError("Problem is infeasible - check constraints")
else:
    raise RuntimeError(f"Solver failed with status: {solver.StatusName(status)}")
```

## 7. Documentation Standards

### Inline Comments
```python
# Use sparingly - code should be self-documenting
# Only for non-obvious solver tricks
model.Add(task_end == task_start + duration).OnlyEnforceIf(task_present)  # Optional task
```

### Constraint Documentation
Each constraint function must document:
1. Mathematical formulation
2. Business logic explanation  
3. Variable dependencies
4. Performance considerations

## 8. Performance Targets

### By Dataset Size
- **Tiny** (2 jobs, 10 tasks): < 1 second
- **Small** (5 jobs, 50 tasks): < 10 seconds  
- **Medium** (20 jobs, 500 tasks): < 60 seconds
- **Large** (50 jobs, 5000 tasks): < 48 hours

### Memory Usage
- Keep variable count minimal
- Use interval variables where possible
- Avoid creating unnecessary intermediate variables