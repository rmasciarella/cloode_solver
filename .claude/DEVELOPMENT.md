# DEVELOPMENT.md - Core Development Details

## Template Architecture Benefits

- **Memory Efficiency**: N jobs share 1 template structure
- **Constraint Reuse**: Template precedences expand to job precedences  
- **Complexity Reduction**: Theoretical improvements of 10-100x demonstrated
- **Performance**: O(template_tasks × instances) vs O(total_tasks³) complexity

## Core Components

### 1. Data Models (`data_models.py`)
Dataclasses for Job, Task, Machine, SchedulingProblem
- All time durations stored as 15-minute intervals
- Validation in `__post_init__` methods
- Template-aware data structures for 5-8x performance

### 2. Constraint Functions (`constraints.py`)
Modular functions adding single constraint types
- Naming: `add_<constraint_type>_constraints()`
- Maximum 30 lines per function
- Document constraints added in docstring
- Full type safety with centralized aliases

### 3. Solver (`solver.py`)
Main FreshSolver class orchestrating solving process
- Creates decision variables (task_starts, task_ends, task_assigned)
- Applies constraints in dependency order
- Uses search strategies for performance
- Template-aware optimization paths

### 4. Database Integration (`db_loader.py`)
Supabase client for loading/saving data
- Environment variables for connection
- Test data setup via SQL scripts
- Template structure persistence

### 5. Type Safety Integration
Comprehensive mypy coverage (100% compliance)
- 0 mypy errors across 34 source files
- Centralized type aliases for OR-Tools structures
- ortools-stubs for proper CP-SAT typing

## Key Design Patterns

### 1. Variable Naming Convention
```python
task_starts[(job_id, task_id)]                    # When task starts
task_ends[(job_id, task_id)]                      # When task ends  
task_assigned[(job_id, task_id, machine_id)]      # Boolean assignment
task_intervals[(job_id, task_id)]                 # IntervalVar for scheduling
```

### 2. Template-Specific Variables (Performance Optimized)
```python
# Template instance variables for 5-8x improvement
template_task_starts[(instance_id, template_task_id)]    # Template-aware starts
template_task_assigned[(instance_id, template_task_id, machine_id)]  # Template assignments
```

### 3. Time Handling
- All durations converted to 15-minute intervals
- Horizon includes 20% buffer beyond minimum required
- Use `solver_utils.py` for time calculations
- Template time calculations leverage shared structure

### 4. Performance Requirements
- Tiny dataset (2 jobs, 10 tasks): < 1 second
- Small dataset (5 jobs, 50 tasks): < 10 seconds
- Medium dataset (20 jobs, 500 tasks): < 60 seconds
- Template-based: 5-8x faster than legacy approach

## Template Optimization Workflow Detail

### 1. Model Structure Optimization (Highest Impact)

#### Symmetry Breaking Techniques
```python
# For identical job instances - lexicographical ordering
for i in range(len(instances) - 1):
    curr_instance = instances[i]
    next_instance = instances[i + 1]
    
    # First task of current <= first task of next
    model.Add(task_starts[curr_key] <= task_starts[next_key])
```

#### Template Reuse Patterns
- Exploit O(template_tasks × instances) complexity
- Share constraint structure across job instances
- Manual symmetry breaking for identical elements
- Decision strategies for parallel resource assignments

### 2. CP-SAT Parameter Tuning (Medium Impact)

#### Critical Parameters for Templates
```python
# Template-optimized solver configuration
solver.parameters.num_search_workers = 8        # Critical for parallel jobs
solver.parameters.max_time_in_seconds = 60      # Template-appropriate timeouts
solver.parameters.linearization_level = 1       # Start conservative, try 2
solver.parameters.search_branching = cp_model.FIXED_SEARCH  # Consistent behavior
solver.parameters.repair_hint = True            # Warm start scenarios
```

#### Parameter Testing Methodology
1. Baseline with default parameters
2. Grid search on key parameters
3. Statistical validation across instance counts
4. Robust parameter selection for production

### 3. Solution Hinting (Specialized Use)
```python
# Template re-solving with minor changes
for key, value in previous_solution.items():
    if key in current_variables:
        model.AddHint(current_variables[key], value)

solver.parameters.repair_hint = True
solver.parameters.hint_conflict_limit = 15  # Controlled repair effort
```

## Testing Strategy

### Unit Testing
- Each constraint function has comprehensive tests
- GIVEN-WHEN-THEN pattern mandatory
- Edge cases and integration scenarios
- Template-specific test patterns

### Integration Testing  
- Complete phases tested together
- Template vs legacy performance validation
- Cross-template compatibility tests
- Database integration validation

### Performance Benchmarking
- Different dataset sizes systematically tested
- Template performance regression detection
- Memory usage profiling for large instances
- Solver parameter optimization validation

### Test Fixtures
- `tests/conftest.py` provides shared fixtures
- Template test data generation utilities
- Performance baseline maintenance
- Database test data management

## Template Development Session Patterns

### Session Initialization
```
"Continue template optimization for {template_id}.
Last session performance: {baseline}s → {current}s.
Applied techniques: {optimization_list}
Current focus: {next_area}"
```

### Checkpoint Structure
```
"Template {template_id} checkpoint:
- Baseline: {original_time}s
- Current: {current_time}s  
- Improvement: {speedup}x
- Techniques: {applied_optimizations}
- Status: {blessed|experimental|testing}
- Next: {pending_strategies}"
```

### Session Documentation Format
Store in project for cross-session continuity:
```json
{
  "template_id": "manufacturing_job_v2",
  "optimization_history": [...],
  "current_performance": "3.2s for 10 instances",
  "target_performance": "< 2.0s for 10 instances", 
  "next_focus": ["linearization_tuning", "redundant_constraints"]
}
```