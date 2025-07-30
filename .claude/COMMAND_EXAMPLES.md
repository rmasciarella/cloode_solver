# OR-Tools Command Examples

Real examples of using the custom OR-Tools commands with Claude.

## Constraint Development Examples

### Example 1: Adding a Shift Schedule Constraint

**Input:**
```
/ac shift_schedule
```

**Claude's Response:**
```python
def add_shift_schedule_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[int, int], IntVar],
    task_ends: Dict[Tuple[int, int], IntVar],
    shifts: List[Tuple[int, int]],
    task_shifts: Dict[Tuple[int, int], List[int]]
) -> None:
    """Add shift schedule constraints to ensure tasks run within shifts.
    
    Mathematical formulation:
        For each task t assigned to shift s:
        shift_start[s] <= task_start[t] AND task_end[t] <= shift_end[s]
    
    Business logic:
        Tasks must be scheduled entirely within their assigned shifts.
        No task can span across shift boundaries.
        
    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Dictionary mapping (job_id, task_id) to start time variables
        task_ends: Dictionary mapping (job_id, task_id) to end time variables
        shifts: List of (start_time, end_time) tuples defining shifts
        task_shifts: Dictionary mapping tasks to allowed shift indices
        
    Constraints added:
        - Task start must be after shift start
        - Task end must be before shift end
        - One constraint pair per task-shift assignment
    
    Performance considerations:
        - O(n*s) constraints where n=tasks, s=shifts per task
        - Pre-filter invalid task-shift combinations to reduce constraints
    """
    for (job_id, task_id), allowed_shifts in task_shifts.items():
        if not allowed_shifts:
            continue  # Skip tasks with no shift requirements
            
        start_var = task_starts[(job_id, task_id)]
        end_var = task_ends[(job_id, task_id)]
        
        # Create boolean variables for shift assignment
        shift_vars = []
        for shift_idx in allowed_shifts:
            shift_start, shift_end = shifts[shift_idx]
            shift_var = model.NewBoolVar(f'task_{job_id}_{task_id}_in_shift_{shift_idx}')
            shift_vars.append(shift_var)
            
            # If assigned to this shift, must be within bounds
            model.Add(start_var >= shift_start).OnlyEnforceIf(shift_var)
            model.Add(end_var <= shift_end).OnlyEnforceIf(shift_var)
        
        # Task must be in exactly one allowed shift
        model.AddExactlyOne(shift_vars)
```

### Example 2: Testing the Constraint

**Input:**
```
/tc shift_schedule
```

**Claude's Response:**
```python
def test_shift_schedule_constraints():
    """Test that shift schedule constraints are correctly enforced."""
    # GIVEN: A model with tasks and two shifts
    model = cp_model.CpModel()
    
    # Create variables
    task_starts = {
        (1, 1): model.NewIntVar(0, 100, 'start_1_1'),
        (1, 2): model.NewIntVar(0, 100, 'start_1_2')
    }
    task_ends = {
        (1, 1): model.NewIntVar(0, 100, 'end_1_1'),
        (1, 2): model.NewIntVar(0, 100, 'end_1_2')
    }
    
    # Set task durations
    model.Add(task_ends[(1, 1)] == task_starts[(1, 1)] + 10)
    model.Add(task_ends[(1, 2)] == task_starts[(1, 2)] + 15)
    
    # Define shifts: morning (0-40) and afternoon (40-80)
    shifts = [(0, 40), (40, 80)]
    task_shifts = {
        (1, 1): [0],      # Task 1 only in morning shift
        (1, 2): [0, 1]    # Task 2 can be in either shift
    }
    
    # WHEN: Adding shift constraints
    add_shift_schedule_constraints(
        model, task_starts, task_ends, shifts, task_shifts
    )
    
    # THEN: Tasks are scheduled within their allowed shifts
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    assert status == cp_model.OPTIMAL
    
    # Task 1 must be in morning shift
    assert solver.Value(task_starts[(1, 1)]) >= 0
    assert solver.Value(task_ends[(1, 1)]) <= 40
    
    # Task 2 must be in one valid shift
    task2_start = solver.Value(task_starts[(1, 2)])
    task2_end = solver.Value(task_ends[(1, 2)])
    in_morning = (task2_start >= 0 and task2_end <= 40)
    in_afternoon = (task2_start >= 40 and task2_end <= 80)
    assert in_morning or in_afternoon


def test_shift_schedule_constraints_no_valid_shift():
    """Test handling when task duration exceeds shift length."""
    # GIVEN: Task longer than any shift
    model = cp_model.CpModel()
    
    task_starts = {(1, 1): model.NewIntVar(0, 100, 'start_1_1')}
    task_ends = {(1, 1): model.NewIntVar(0, 100, 'end_1_1')}
    model.Add(task_ends[(1, 1)] == task_starts[(1, 1)] + 50)  # 50-unit task
    
    shifts = [(0, 40), (40, 80)]  # 40-unit shifts
    task_shifts = {(1, 1): [0, 1]}
    
    # WHEN: Adding constraints
    add_shift_schedule_constraints(
        model, task_starts, task_ends, shifts, task_shifts
    )
    
    # THEN: Model should be infeasible
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status == cp_model.INFEASIBLE
```

## Debugging Workflow Examples

### Example 3: Tracing Infeasibility

**Input:**
```
My model returns INFEASIBLE with 10 jobs and 3 machines. /ti
```

**Claude's Response:**
```
Let's trace the infeasibility systematically.

Step 1: Remove objective function
First, let's check if the issue is with optimization constraints:

```python
# Comment out the objective
# model.Minimize(makespan)
```

Run the solver again. Is it still INFEASIBLE?

Step 2: Disable constraints systematically
Let's disable constraints in order of restrictiveness:

```python
# Phase 1: Disable no-overlap constraints
# add_no_overlap_constraints(model, task_intervals, machines)  # COMMENTED

# Phase 2: If still infeasible, disable precedence
# add_precedence_constraints(model, task_starts, task_ends, precedences)  # COMMENTED

# Phase 3: If still infeasible, disable assignment
# add_assignment_constraints(model, task_assigned, eligible_machines)  # COMMENTED
```

Step 3: Identify the conflict
Once you find which constraint type causes infeasibility, let's narrow it down:

For no-overlap issues:
- Check if total task duration > available time * machines
- Look for tasks that all require the same machine

For precedence issues:
- Check for circular dependencies
- Verify precedence chains don't exceed horizon

Would you like me to generate specific debugging code for your model?
```

### Example 4: Performance Profiling

**Input:**
```
/ps
```

**Claude's Response:**
```
📊 Model Statistics:
- Variables: 2,450 total
  - IntVar (task_starts): 500
  - IntVar (task_ends): 500  
  - BoolVar (task_assigned): 1,450
- Constraints: 8,320
  - Duration: 500
  - Precedence: 820
  - No-overlap: 4,500
  - Assignment: 2,500
- Search space: ~10^435

⏱️ Time Breakdown:
Based on typical patterns:
- Model building: ~5% (estimate: 6s)
- Variable creation: ~10% (estimate: 12s)
- Constraint creation: ~15% (estimate: 18s)
- Solving: ~70% (estimate: 84s)
  - First solution: ~10s
  - Optimization: ~74s

🔍 Bottlenecks:
1. **No-overlap constraints (54% of constraints)**
   - 4,500 disjunctive constraints
   - Consider using interval variables instead
   
2. **Variable bounds too loose**
   ```python
   # Current:
   task_starts[(j,t)] = model.NewIntVar(0, 10000, name)
   
   # Suggested:
   earliest = calculate_earliest_start(j, t, precedences)
   latest = calculate_latest_start(j, t, horizon, durations)
   task_starts[(j,t)] = model.NewIntVar(earliest, latest, name)
   ```

3. **Missing redundant constraints**
   - No total duration bound
   - No transitive precedences
   - No symmetry breaking

💡 Optimization Suggestions:
1. **Add makespan lower bound**:
   ```python
   total_duration = sum(min(modes[t]) for t in tasks)
   model.Add(makespan >= total_duration // num_machines)
   ```

2. **Use interval variables**:
   ```python
   task_interval = model.NewIntervalVar(start, size, end, name)
   model.AddNoOverlap([intervals for machine])
   ```

3. **Add search strategy**:
   ```python
   model.AddDecisionStrategy(
       [task_starts[t] for t in critical_path],
       cp_model.CHOOSE_FIRST,
       cp_model.SELECT_MIN_VALUE
   )
   ```

Expected improvement: 60-75% faster (30-45 seconds)
```

## Optimization Examples

### Example 5: Suggesting Redundant Constraints

**Input:**
```
/sr
```

**Claude's Response:**
```python
# Suggested Redundant Constraints:

# 1. Transitive Precedence Constraints
# Current: A→B, B→C (2 constraints)
# Add: A→C (redundant but helps pruning)
precedence_graph = build_precedence_graph(precedences)
for task_a in tasks:
    for task_c in get_transitive_successors(task_a, precedence_graph):
        if (task_a, task_c) not in direct_precedences:
            model.Add(task_starts[task_c] >= task_ends[task_a])
            # Redundant but reduces search space

# 2. Total Duration Lower Bound
# The makespan must be at least total work divided by resources
total_min_duration = sum(
    min(duration for _, duration in task_modes[task])
    for task in tasks
)
model.Add(makespan >= total_min_duration // num_machines)

# 3. Machine Workload Bounds
# Each machine's workload provides a makespan lower bound
for machine_id in range(num_machines):
    machine_tasks = [
        task for task in tasks 
        if machine_id in eligible_machines[task]
    ]
    if len(machine_tasks) == len(tasks):  # Bottleneck machine
        machine_min_work = sum(
            min(d for m, d in task_modes[t] if m == machine_id)
            for t in machine_tasks
        )
        model.Add(makespan >= machine_min_work)

# 4. Symmetry Breaking for Identical Machines
# If machines 0 and 1 are identical, prefer lower indices
identical_groups = find_identical_machines(machines)
for group in identical_groups:
    for i in range(len(group) - 1):
        # First task prefers first machine in group
        first_task = min(tasks)  # Lexicographically first
        model.Add(
            task_assigned[(first_task, group[i])] >= 
            task_assigned[(first_task, group[i+1])]
        )

# 5. Critical Path Constraints
# Tasks on critical path determine minimum makespan
critical_path = find_critical_path(tasks, precedences, durations)
critical_duration = sum(
    min_duration[task] for task in critical_path
)
model.Add(makespan >= critical_duration)

# Expected impact:
# - Search space reduction: 60-80%
# - Faster first solution: 2-3x
# - Better optimization: finds optimal 40% faster
```

## Workflow Examples

### Example 6: Complete Development Flow

**Input:**
```
/dev-flow resource_capacity
```

**Claude's Response:**
```
Executing complete development workflow for resource_capacity:

Step 1: Analyzing existing constraints
Looking at current model structure...
- Found duration constraints using task_starts, task_ends
- Found assignment constraints using task_assigned
- Found no-overlap constraints using intervals
- Integration point: After assignment, before objective

Step 2: Generating constraint function
[Generates add_resource_capacity_constraints function]

Step 3: Creating unit tests
[Generates test_resource_capacity_constraints function]

Step 4: Validating against STANDARDS.md
✅ Function name: add_resource_capacity_constraints - Correct
✅ Line count: 28 lines - Under limit
✅ Type hints: All parameters typed
✅ Docstring: Complete with all sections
✅ Single responsibility: Only handles capacity

Step 5: Integration in solver.py
Add after line 156 (post-assignment constraints):
```python
# Add resource capacity constraints
add_resource_capacity_constraints(
    model=model,
    task_assigned=task_assigned,
    task_durations=task_durations,
    resource_capacities=resource_capacities,
    time_horizon=horizon
)
```

Step 6: Performance considerations
- Adds O(n*t) constraints (n=tasks, t=time units)
- Consider aggregating by time windows to reduce constraints
- May benefit from redundant cumulative constraints
```

## Quick Reference Card

```
CONSTRAINT DEVELOPMENT
/ac <name>    - Add constraint function
/tc <name>    - Test constraint
/cc <func>    - Check standards
/lc           - List all constraints

DEBUGGING
/ti           - Trace infeasibility  
/es           - Explain solution
/ps           - Profile solver
/dv           - Debug variables

OPTIMIZATION  
/sr           - Suggest redundant
/tb           - Tighten bounds
/os           - Optimize search
/cx           - Complexity analysis

WORKFLOWS
/dev-flow <name>  - Full development
/debug-slow       - Fix performance
/fix-infeasible   - Resolve infeasibility
```