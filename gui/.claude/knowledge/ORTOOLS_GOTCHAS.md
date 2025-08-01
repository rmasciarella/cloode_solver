# Top 10 OR-Tools Gotchas

## Overview

Common pitfalls and surprising behaviors in Google OR-Tools CP-SAT solver that can trip up even experienced developers. Learn from these gotchas to avoid hours of debugging.

## 1. Time Horizon Integer Overflow 🚨

### The Gotcha
```python
# ❌ This can cause integer overflow!
horizon = sum(task.duration for task in tasks) * 2
model.NewIntVar(0, horizon, 'start_time')  # Fails with large datasets
```

### Why It Happens
CP-SAT uses 64-bit integers, but multiplication can overflow with large task counts or durations.

### The Fix
```python
# ✅ Calculate horizon safely
import sys

def safe_horizon(tasks, buffer_percent=20):
    total_duration = sum(task.duration for task in tasks)
    horizon = int(total_duration * (1 + buffer_percent/100))
    
    # Check for overflow
    if horizon > sys.maxsize // 2:
        raise ValueError(f"Horizon {horizon} too large")
    
    return horizon
```

## 2. Variable Naming Collisions 💥

### The Gotcha
```python
# ❌ Creates duplicate variable names!
for job in jobs:
    for task in job.tasks:
        # Same name for different tasks!
        var = model.NewIntVar(0, 100, f'start_{task.id}')
```

### Why It Happens
Task IDs might not be globally unique across jobs.

### The Fix
```python
# ✅ Use composite keys
for job in jobs:
    for task in job.tasks:
        var = model.NewIntVar(0, 100, f'start_{job.id}_{task.id}')
        
# Or use tuples as dictionary keys
task_starts = {}
for job in jobs:
    for task in job.tasks:
        task_starts[(job.id, task.id)] = model.NewIntVar(
            0, horizon, f'start_{job.id}_{task.id}'
        )
```

## 3. Optional Intervals Trap 🎭

### The Gotcha
```python
# ❌ Forgetting to handle optional intervals
interval = model.NewOptionalIntervalVar(
    start, size, end, is_present, 'optional_task'
)
# Later...
model.Add(start >= 0)  # This forces the task to be present!
```

### Why It Happens
Constraints on optional interval variables implicitly force them to be present.

### The Fix
```python
# ✅ Use OnlyEnforceIf for optional constraints
interval = model.NewOptionalIntervalVar(
    start, size, end, is_present, 'optional_task'
)

# Only apply constraint if task is present
model.Add(start >= earliest_start).OnlyEnforceIf(is_present)
model.Add(end <= latest_end).OnlyEnforceIf(is_present)
```

## 4. Boolean Logic Confusion 🤔

### The Gotcha
```python
# ❌ This doesn't work as expected!
if task_assigned[(1, 1, 1)] == 1:  # BoolVar can't be compared directly
    model.Add(some_constraint)
```

### Why It Happens
BoolVars are symbolic variables, not Python booleans.

### The Fix
```python
# ✅ Use implications or OnlyEnforceIf
# Option 1: Implication
model.Add(some_constraint).OnlyEnforceIf(task_assigned[(1, 1, 1)])

# Option 2: Create derived constraints
is_assigned = task_assigned[(1, 1, 1)]
model.Add(duration == 10).OnlyEnforceIf(is_assigned)
model.Add(duration == 0).OnlyEnforceIf(is_assigned.Not())
```

## 5. Objective Function Scaling 📊

### The Gotcha
```python
# ❌ Mixed scales cause poor optimization
model.Minimize(
    1000000 * makespan +  # Large scale
    sum(task_starts.values())  # Small scale
)
```

### Why It Happens
The solver might ignore the smaller component due to numerical precision.

### The Fix
```python
# ✅ Normalize scales
# Option 1: Scale to similar ranges
makespan_weight = 100  # Not 1000000
start_time_weight = 1

model.Minimize(
    makespan_weight * makespan + 
    start_time_weight * sum(task_starts.values())
)

# Option 2: Use hierarchical optimization
# First minimize makespan
model.Minimize(makespan)
solver.Solve(model)
makespan_value = solver.Value(makespan)

# Then minimize start times with makespan constraint
model.Add(makespan == makespan_value)
model.Minimize(sum(task_starts.values()))
```

## 6. Constraint Propagation Order 🔄

### The Gotcha
```python
# ❌ Poor constraint ordering slows solving
# Adding complex constraints first
model.AddNoOverlap(intervals)  # Complex global constraint

# Then simple bounds
for task in tasks:
    model.Add(task_starts[task] >= 0)
    model.Add(task_ends[task] <= horizon)
```

### Why It Happens
Complex constraints without bounds create huge search spaces.

### The Fix
```python
# ✅ Add constraints in order of increasing complexity
# 1. Variable bounds first
for task in tasks:
    model.Add(task_starts[task] >= task.earliest_start)
    model.Add(task_ends[task] <= task.latest_end)

# 2. Simple constraints
for task in tasks:
    model.Add(task_ends[task] == task_starts[task] + task.duration)

# 3. Complex global constraints last
model.AddNoOverlap(intervals)
```

## 7. Memory Explosion with Intermediate Variables 💾

### The Gotcha
```python
# ❌ Creating too many intermediate variables
for t1 in tasks:
    for t2 in tasks:
        if t1 != t2:
            # Creates O(n²) variables!
            before = model.NewBoolVar(f'{t1}_before_{t2}')
            model.Add(task_ends[t1] <= task_starts[t2]).OnlyEnforceIf(before)
```

### Why It Happens
Each variable consumes memory and slows the solver.

### The Fix
```python
# ✅ Use constraints directly when possible
# Only create variables when needed for the model
precedence_pairs = [(t1, t2) for t1, t2 in precedences]
for t1, t2 in precedence_pairs:
    model.Add(task_ends[t1] <= task_starts[t2])

# If you need the boolean, create only what's necessary
precedence_active = {}
for (t1, t2) in actual_precedences_only:
    var = model.NewBoolVar(f'prec_{t1}_{t2}')
    precedence_active[(t1, t2)] = var
```

## 8. Solution Callback Overhead 📞

### The Gotcha
```python
# ❌ Heavy computation in callback
def solution_callback(solver):
    # This runs for EVERY solution found!
    solution = extract_full_solution(solver)  # Expensive
    validate_solution(solution)  # More expense
    save_to_database(solution)  # I/O in callback!
```

### Why It Happens
Callbacks run synchronously and block the solver.

### The Fix
```python
# ✅ Keep callbacks lightweight
best_objective = float('inf')

def solution_callback(solver):
    global best_objective
    current = solver.ObjectiveValue()
    
    if current < best_objective:
        best_objective = current
        # Just save key info, process later
        solutions_queue.put({
            'objective': current,
            'time': solver.WallTime(),
            'task_starts': {t: solver.Value(v) for t, v in task_starts.items()}
        })
```

## 9. Symmetry Breaking Forgotten 🔀

### The Gotcha
```python
# ❌ Identical machines create symmetry
machines = [Machine(id=i, capacity=10) for i in range(5)]
# Solver explores equivalent solutions: task on M1 vs M2
```

### Why It Happens
Symmetrical solutions explosion: n! equivalent solutions for n identical resources.

### The Fix
```python
# ✅ Break symmetry with constraints
# Option 1: Prefer lower-indexed machines
for i in range(len(machines) - 1):
    load_i = sum(task_assigned[t, i] * task.duration for t in tasks)
    load_i_plus_1 = sum(task_assigned[t, i+1] * task.duration for t in tasks)
    model.Add(load_i >= load_i_plus_1)

# Option 2: Fix some assignments
if tasks and machines:
    # Assign first task to first available machine
    model.Add(task_assigned[tasks[0], machines[0]] == 1)
```

## 10. Search Strategy Neglect 🎯

### The Gotcha
```python
# ❌ Using default search for complex problems
solver = cp_model.CpSolver()
status = solver.Solve(model)  # Might take forever!
```

### Why It Happens
Default search may not exploit problem structure.

### The Fix
```python
# ✅ Define problem-specific search strategy
# For scheduling: decide start times in order
all_starts = []
for job in jobs:
    for task in job.tasks:
        all_starts.append(task_starts[(job.id, task.id)])

# Try minimum values first (pack left)
model.AddDecisionStrategy(
    all_starts,
    cp_model.CHOOSE_FIRST,
    cp_model.SELECT_MIN_VALUE
)

# Set solver parameters
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 300
solver.parameters.num_search_workers = 8  # Parallel search
solver.parameters.log_search_progress = True
```

## Bonus Gotchas

### 11. Integer Division Truncation
```python
# ❌ Loses precision
average_duration = sum(durations) / len(durations)
model.Add(some_var == average_duration)  # Truncates!

# ✅ Use multiplication to avoid division
model.Add(some_var * len(durations) == sum(durations))
```

### 12. Negative Values in Domains
```python
# ❌ Forgetting negative values exist
slack = model.NewIntVar(-horizon, horizon, 'slack')
model.Add(slack >= 0)  # Why create negative domain?

# ✅ Think about actual domain needs
slack = model.NewIntVar(0, horizon, 'slack')  # If always positive
```

## Prevention Checklist

Before running your model:

1. **Check integer overflow** - Calculate maximum values
2. **Verify variable names** - Ensure uniqueness
3. **Review optional constraints** - Use OnlyEnforceIf
4. **Validate boolean logic** - No direct comparisons
5. **Normalize objectives** - Similar scales
6. **Order constraints** - Simple to complex
7. **Count variables** - Avoid quadratic explosion
8. **Optimize callbacks** - Keep them fast
9. **Break symmetries** - Add ordering constraints
10. **Set search strategy** - Guide the solver

## Debug Commands

```bash
# When stuck, use these Claude commands:
/trace-infeasible  # Find constraint conflicts
/debug-variables   # Check variable bounds
/profile-solver    # Find performance bottlenecks
```

Remember: OR-Tools is powerful but has quirks. When something seems wrong, it usually is! Check these gotchas first before diving deep into debugging.