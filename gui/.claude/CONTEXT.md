# Project Context - Fresh Solver OR-Tools

## Domain Overview

### Problem Type
- **Category**: Job-shop scheduling with resource constraints
- **Framework**: Google OR-Tools CP-SAT solver
- **Scale**: Supporting from 2 to 5000+ tasks
- **Industry**: Manufacturing/Production scheduling (adaptable to logistics, healthcare)

### Time Representation
- **CRITICAL**: All durations stored as 15-minute intervals (quarters)
- **Conversion**: 60 minutes = 4 time units
- **Example**: 2.5 hours = 150 minutes = 10 time units
- **Horizon**: Always includes 20% buffer beyond minimum required

## Core Business Rules

### Immutable Constraints
1. **No Task Overlap**: Tasks cannot share a machine at the same time
2. **Precedence Respect**: Dependent tasks must wait for predecessors
3. **Machine Assignment**: Each task must be assigned to exactly one capable machine
4. **Duration Enforcement**: Task durations are fixed once mode is selected

### Mode Selection Rules
1. Each task can have multiple execution modes
2. Each mode specifies a machine and duration
3. Exactly one mode must be selected per task
4. Mode selection affects both machine assignment and task duration

### Scheduling Boundaries
1. All tasks must complete within the horizon
2. Tasks cannot start before time 0
3. Once started, tasks run to completion (no preemption in Phase 1)

## Common Edge Cases

### Data Issues
1. **Empty Jobs**: Jobs with no tasks (should be handled gracefully)
2. **Isolated Tasks**: Tasks with no valid machine modes
3. **Circular Dependencies**: Task A depends on B, B depends on A
4. **Zero Duration**: Tasks with 0 duration (convert to minimum 1 time unit)

### Solver Challenges
1. **Tight Horizons**: When minimal horizon barely fits all tasks
2. **Machine Bottlenecks**: Single machine required by many tasks
3. **Long Precedence Chains**: Deep dependency trees limiting parallelism
4. **Symmetric Solutions**: Multiple equivalent optimal solutions

## Performance Insights

### Variable Creation
- **Minimize Count**: Use interval variables where possible
- **Tight Bounds**: Calculate earliest/latest start times from precedences
- **Named Variables**: Always use descriptive names for debugging

### Constraint Ordering
1. Add duration constraints first (establish task intervals)
2. Then precedence constraints (order tasks)
3. Then no-overlap constraints (prevent conflicts)
4. Finally objective function (optimize solution)

### Solver Strategies
- **Small Problems** (< 50 tasks): Default search works well
- **Medium Problems** (50-500 tasks): Use CHOOSE_FIRST with SELECT_MIN_VALUE
- **Large Problems** (500+ tasks): Consider domain-specific heuristics

### Type Safety Impact
- **Development Speed**: mypy catches OR-Tools API misuse early, preventing runtime errors
- **Refactoring Safety**: Type annotations enable confident refactoring of complex constraint logic
- **IDE Support**: Proper typing enables better autocomplete and error detection
- **Code Documentation**: Type hints serve as self-documenting interface contracts
- **Performance**: Zero runtime impact, all benefits during development time

## Known Performance Bottlenecks

### Variable Explosion
- **Issue**: Creating BoolVar for every task-machine-time combination
- **Solution**: Use IntervalVar with optional presence instead

### Loose Bounds
- **Issue**: Variables with bounds 0 to MAX_HORIZON
- **Solution**: Calculate tight bounds from business constraints

### Missing Redundancy
- **Issue**: Solver explores obviously bad solutions
- **Solution**: Add redundant constraints (transitive precedence, total duration)

### Poor Search Order
- **Issue**: Solver tries unlikely assignments first
- **Solution**: Order variables by criticality, use domain knowledge

### Type Safety Considerations
- **mypy Integration**: Essential for OR-Tools development due to C++ binding complexity
- **ortools-stubs**: Required dependency for proper CP-SAT type checking
- **Centralized Type Aliases**: Prevent inconsistencies and improve refactoring safety
- **Line Length Management**: Type annotations can cause line length violations, use `ruff format`

## Implementation Patterns

### Variable Dictionaries
```python
# Good: Tuple keys for easy lookup
task_starts[(job_id, task_id)] = model.NewIntVar(...)

# Bad: Nested dictionaries
task_starts[job_id][task_id] = model.NewIntVar(...)
```

### Constraint Functions
```python
# Good: Single responsibility
def add_precedence_constraints(model, starts, ends, precedences):
    # Only handles precedence logic

# Bad: Mixed concerns
def add_all_constraints(model, problem):
    # Handles everything - hard to test/debug
```

### Time Calculations
```python
# Good: Use utility functions
duration_units = minutes_to_time_units(duration_minutes)

# Bad: Inline calculations
duration_units = duration_minutes // 15
```

## Testing Considerations

### Dataset Scales
- **Tiny**: 2 jobs, 10 tasks (unit tests, < 1 second)
- **Small**: 5 jobs, 50 tasks (integration tests, < 10 seconds)
- **Medium**: 20 jobs, 500 tasks (performance tests, < 60 seconds)
- **Large**: 50 jobs, 5000 tasks (stress tests, < 48 hours)

### Critical Test Cases
1. Single task job (edge case)
2. Linear precedence chain (worst case for parallelism)
3. All tasks on one machine (bottleneck test)
4. No precedences (maximum parallelism)
5. Infeasible problems (proper error handling)

## Database Integration

### Supabase Schema
- Jobs table: id, name, created_at
- Tasks table: id, job_id, name, position
- Machines table: id, name, capacity
- TaskModes table: task_id, machine_id, duration_minutes
- Precedences table: predecessor_task_id, successor_task_id

### Data Validation Requirements
1. Verify foreign keys exist before loading
2. Ensure positive durations
3. Check for precedence cycles
4. Validate machine-task compatibility

## Common Mistakes to Avoid

### Solver Modeling
1. **Don't** create variables in loops without bounds
2. **Don't** use big-M constraints when intervals work
3. **Don't** forget to set solution limit for large problems
4. **Don't** ignore solver status (might be FEASIBLE not OPTIMAL)

### Code Structure
1. **Don't** mix constraint logic with data loading
2. **Don't** hardcode time units (always use utilities)
3. **Don't** create monolithic constraint functions
4. **Don't** skip validation in data models

### Performance
1. **Don't** use loose variable bounds
2. **Don't** create unnecessary intermediate variables
3. **Don't** ignore symmetry breaking opportunities
4. **Don't** forget to add redundant constraints

## Future Considerations (Phases 2-3)

### Phase 2 Additions
- Resource capacity (machines have limited capacity)
- Skill matching (workers with specific skills)
- Variable task durations based on worker skill

### Phase 3 Additions
- Shift constraints (business hours, breaks)
- Setup times between different task types
- Parallel task execution on single machine
- Soft constraints with penalties

## Debugging Strategies

### When Infeasible
1. Remove objective function first
2. Disable constraints one by one
3. Start with no-overlap (often most restrictive)
4. Check data for impossible requirements

### When Slow
1. Print variable count and bounds
2. Log constraint creation time
3. Use SolutionCallback to see progress
4. Check for accidental cartesian products

### When Wrong Solution
1. Verify constraint formulation matches intent
2. Check unit conversions (minutes vs time units)
3. Validate data loaded correctly
4. Ensure all constraints added to model