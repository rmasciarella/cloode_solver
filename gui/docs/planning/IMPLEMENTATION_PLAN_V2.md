# Revised Implementation Plan for OR-Tools Scheduling Solver

## Current State Assessment (Moving into Phase 1)

The codebase has already implemented significant functionality:

### ✅ Completed Features
1. **Core Data Models** (`src/solver/models/problem.py`)
   - Machine, Task, TaskMode, Job, WorkCell, Precedence models
   - Multiple modes per task with machine-specific durations
   - Time unit conversion (15-minute intervals)
   - Comprehensive validation

2. **Basic Solver Architecture** (`src/solver/core/solver.py`)
   - Interval variables (start, duration, end)
   - Boolean assignment variables for machine selection
   - Optional intervals for no-overlap constraints
   - Search strategies and parallel solver configuration
   - Makespan minimization objective

3. **Constraint Implementation**
   - Task duration constraints
   - Precedence constraints (with redundant constraints)
   - Machine assignment (exactly one mode per task)
   - No-overlap constraints using optional intervals
   - **✅ Setup time constraints (Phase 1.2 - COMPLETED)**
     - Sequence-dependent setup times
     - Conditional constraints based on machine assignment
     - Unit tests implemented

4. **Database Integration**
   - Supabase loader with test/production table switching
   - Complete data loading pipeline
   - Environment-based configuration

5. **Project Structure**
   - Well-organized constraint modules
   - Test framework setup
   - Utility functions for time calculations

## Phase 0: Cleanup and Stabilization (1-2 days) - PARTIALLY COMPLETE

### 0.1 Code Review and Refactoring
- [x] Review existing constraint implementations for correctness
- [x] Ensure all constraint functions follow the 30-line rule
- [x] Add missing type hints where needed
- [x] Verify test coverage for existing features (constraints tested)

### 0.2 Performance Baseline
- [ ] Create performance benchmarks for current implementation
- [ ] Document current solve times for different dataset sizes
- [ ] Identify any immediate performance bottlenecks

### 0.3 Documentation Update
- [x] Update CLAUDE.md with current architecture
- [x] Document existing constraint patterns (CONSTRAINT_PATTERNS.md)
- [x] Create examples of current capabilities (extensive .claude/ documentation)

## Phase 1: Enhanced Machine Constraints (3-5 days)

### 1.1 Machine Capacity Constraints
```python
# Multiple tasks can run on high-capacity machines
# Example: Machine with capacity=3 can run 3 tasks simultaneously
def add_machine_capacity_constraints(
    model: cp_model.CpModel,
    machine_intervals: Dict[str, List[IntervalVar]],
    machine_demands: Dict[Tuple[str, str, str], IntVar],
    machines: List[Machine]
) -> None:
    """Add cumulative constraints for machine capacity."""
```

### 1.2 Setup Time Constraints ✅ COMPLETED
```python
# Add setup times between different task types
def add_setup_time_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[str, str], cp_model.IntVar],
    task_ends: Dict[Tuple[str, str], cp_model.IntVar],
    task_assigned: Dict[Tuple[str, str, str], cp_model.BoolVar],
    setup_times: Dict[Tuple[str, str, str], int],
    problem: SchedulingProblem
) -> None:
    """Add sequence-dependent setup times."""
```

**Implementation Details:**
- Located in `src/solver/constraints/phase1/setup_times.py`
- Uses conditional constraints with big-M method
- Optimized by grouping tasks by machine
- Unit tests in `tests/unit/constraints/test_setup_times.py`
- Integrated into `FreshSolver` with optional `setup_times` parameter

### 1.3 Machine Availability Windows
```python
# Machines may have maintenance windows or shifts
def add_machine_availability_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict,
    machine_availability: Dict[str, List[Tuple[int, int]]]
) -> None:
    """Ensure tasks only run when machines are available."""
```

## Phase 2: Resource and Skill Constraints (5-7 days)

### 2.1 Worker/Operator Constraints
```python
# Tasks may require operators with specific skills
def add_operator_assignment_constraints(
    model: cp_model.CpModel,
    task_operators: Dict[Tuple[str, str, str], BoolVar],
    operator_skills: Dict[str, List[str]],
    task_skill_requirements: Dict[str, List[str]]
) -> None:
    """Assign operators with required skills to tasks."""
```

### 2.2 Tool/Fixture Constraints
```python
# Shared tools that move between machines
def add_tool_constraints(
    model: cp_model.CpModel,
    task_tools: Dict[Tuple[str, str, str], BoolVar],
    tool_inventory: Dict[str, int]
) -> None:
    """Ensure tool availability for tasks."""
```

### 2.3 Material Flow Constraints
```python
# Material availability and consumption
def add_material_constraints(
    model: cp_model.CpModel,
    task_starts: Dict,
    material_availability: Dict[str, List[Tuple[int, int, int]]]
) -> None:
    """Ensure materials are available when needed."""
```

## Phase 3: Advanced Scheduling Features (7-10 days)

### 3.1 Multi-Objective Optimization
```python
# Balance makespan, cost, and resource utilization
def create_hierarchical_objectives(
    model: cp_model.CpModel,
    makespan: IntVar,
    total_cost: IntVar,
    resource_utilization: IntVar,
    priorities: List[Tuple[str, int]]
) -> None:
    """Implement lexicographic multi-objective optimization."""
```

### 3.2 Preemptive Scheduling
```python
# Allow task interruption for higher priority jobs
def add_preemption_constraints(
    model: cp_model.CpModel,
    task_segments: Dict[Tuple[str, str, int], IntervalVar],
    task_priorities: Dict[str, int]
) -> None:
    """Enable task preemption based on priorities."""
```

### 3.3 Due Date and Tardiness
```python
# Minimize tardiness and handle soft/hard due dates
def add_due_date_constraints(
    model: cp_model.CpModel,
    task_ends: Dict,
    job_due_dates: Dict[str, int],
    tardiness_vars: Dict[str, IntVar]
) -> None:
    """Track and minimize job tardiness."""
```

## Phase 4: Production Features (5-7 days)

### 4.1 Solution Persistence
- [ ] Save solutions to database
- [ ] Solution versioning and comparison
- [ ] Audit trail for schedule changes

### 4.2 Incremental Solving
```python
# Re-solve with fixed partial schedule
def add_partial_schedule_constraints(
    model: cp_model.CpModel,
    fixed_assignments: Dict[Tuple[str, str], Tuple[str, int, int]]
) -> None:
    """Fix already-started tasks in place."""
```

### 4.3 Real-time Updates
- [ ] Handle new job arrivals
- [ ] Machine breakdowns
- [ ] Rush orders and priority changes

### 4.4 Solution Quality Metrics
- [ ] Resource utilization reports
- [ ] Bottleneck analysis
- [ ] Schedule stability metrics

## Phase 5: API and Integration (5-7 days)

### 5.1 REST API
```python
# FastAPI endpoints
POST   /solve              # Submit scheduling problem
GET    /solutions/{id}     # Retrieve solution
POST   /solutions/{id}/fix # Fix partial schedule
DELETE /solutions/{id}     # Delete solution
```

### 5.2 GraphQL API
```graphql
type Solution {
  id: ID!
  status: SolverStatus!
  makespan: Int
  tasks: [ScheduledTask!]!
  metrics: SolutionMetrics!
}
```

### 5.3 Webhook Integration
- [ ] Solution ready notifications
- [ ] Progress updates for long-running solves
- [ ] Schedule change alerts

## Phase 6: Advanced Solver Strategies (3-5 days)

### 6.1 Custom Search Strategies
```python
def create_adaptive_search_strategy(
    model: cp_model.CpModel,
    problem_characteristics: Dict[str, float]
) -> None:
    """Adapt search based on problem structure."""
```

### 6.2 Constraint Learning
- [ ] Learn patterns from historical schedules
- [ ] Add learned constraints for common scenarios
- [ ] Adaptive bound tightening

### 6.3 Distributed Solving
- [ ] Problem decomposition strategies
- [ ] Parallel neighborhood search
- [ ] Solution pool management

## Testing Strategy

### Unit Tests (Each Phase)
- Test each constraint function independently
- Verify constraint propagation
- Check solution feasibility

### Integration Tests
- Phase-by-phase integration tests
- Cross-constraint interaction tests
- End-to-end scheduling scenarios

### Performance Tests
- Scaling tests (10, 100, 1000, 10000 tasks)
- Memory usage profiling
- Solver statistics analysis

### Property-Based Tests
```python
# Use hypothesis for generative testing
@given(valid_scheduling_problem())
def test_solution_satisfies_all_constraints(problem):
    solution = solver.solve(problem)
    assert all_constraints_satisfied(solution)
```

## Success Metrics

### Performance Targets
- **Small** (50 tasks, 10 machines): < 5 seconds
- **Medium** (500 tasks, 50 machines): < 60 seconds  
- **Large** (5000 tasks, 200 machines): < 10 minutes
- **XLarge** (50000 tasks, 500 machines): < 2 hours

### Quality Targets
- Optimality gap < 5% for small problems
- Feasible solutions for all valid problems
- Meaningful progress on partial solutions

### Code Quality
- 90%+ test coverage
- All functions < 30 lines
- Comprehensive error handling
- Clear constraint documentation

## Implementation Order Recommendation

1. **Week 1**: Phase 0 (Cleanup) + Phase 1.1 (Machine Capacity)
2. **Week 2**: Phase 1.2-1.3 (Setup Times, Availability)
3. **Week 3**: Phase 2.1 (Operators) + Phase 3.3 (Due Dates)
4. **Week 4**: Phase 4.1-4.2 (Persistence, Incremental)
5. **Week 5**: Phase 5.1 (REST API) + Testing
6. **Week 6**: Remaining features based on priority

## Risk Mitigation

1. **Performance Risk**: Profile early and often
2. **Complexity Risk**: Incremental feature addition
3. **Integration Risk**: Database transaction handling
4. **Scalability Risk**: Test with production-size data

## Next Immediate Steps

1. Run existing tests to verify current state
2. Create performance benchmark suite
3. Implement machine capacity constraints (Phase 1.1)
4. Add integration tests for capacity constraints
5. Update documentation with new capabilities

This plan builds incrementally on the existing solid foundation, avoiding rewrites while systematically adding production-ready features.