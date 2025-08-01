# Performance Optimization Playbook for OR-Tools

## Overview

A comprehensive guide to optimizing OR-Tools CP-SAT solver performance, from quick wins to advanced techniques. Target: achieve 10x-100x speedups through systematic optimization.

## Performance Optimization Hierarchy

```
┌─────────────────────────────────────────────┐
│         Optimization Impact Levels          │
├──────────┬───────────┬──────────┬──────────┤
│Quick Wins│  Model    │  Search  │ Advanced │
│  (10x)   │ Structure │ Strategy │  (100x)  │
│          │   (50x)   │  (20x)   │          │
└──────────┴───────────┴──────────┴──────────┘
```

## Quick Wins (5 minutes, 10x speedup)

### 1. Enable Parallel Search

```python
# ❌ Default: Single thread
solver = cp_model.CpSolver()
status = solver.Solve(model)

# ✅ Use all CPU cores
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8  # Or os.cpu_count()
solver.parameters.log_search_progress = True
status = solver.Solve(model)
```

### 2. Set Time Limits

```python
# ❌ May run forever
solver.Solve(model)

# ✅ Get good solution quickly
solver.parameters.max_time_in_seconds = 300  # 5 minutes
# First solution within 1% of optimal often found quickly
```

### 3. Tighten Variable Bounds

```python
# ❌ Loose bounds = huge search space
start = model.NewIntVar(0, 1000000, 'start')

# ✅ Tight bounds from problem analysis
earliest = task.earliest_possible_start()
latest = task.latest_possible_start()
start = model.NewIntVar(earliest, latest, 'start')
```

### 4. Use Solution Hints

```python
# ✅ Warm start from previous solution
if previous_solution:
    for task_id, start_time in previous_solution.items():
        model.AddHint(task_starts[task_id], start_time)
```

### 5. Presolve Optimization

```python
# ✅ Let CP-SAT presolve work harder
solver.parameters.cp_model_presolve = True
solver.parameters.presolve_bounded_deductions = 8  # More deductions
```

## Model Structure Optimization (1 hour, 50x speedup)

### 1. Symmetry Breaking

```python
class SymmetryBreaker:
    """Break symmetries to reduce search space."""
    
    @staticmethod
    def break_machine_symmetry(model, machines, task_assigned):
        """If machines are identical, prefer lower indices."""
        identical_groups = group_identical_machines(machines)
        
        for group in identical_groups:
            # Force lexicographic ordering
            for i in range(len(group) - 1):
                load_i = model.NewIntVar(0, horizon, f'load_{group[i]}')
                load_j = model.NewIntVar(0, horizon, f'load_{group[i+1]}')
                
                # Calculate loads
                for task in tasks:
                    model.Add(load_i == sum(
                        task_assigned[task, group[i]] * task.duration
                        for task in tasks
                    ))
                
                # Prefer lower index for lower load
                model.Add(load_i >= load_j)
    
    @staticmethod
    def break_task_symmetry(model, tasks, task_starts):
        """If tasks are identical, order them."""
        identical_tasks = group_identical_tasks(tasks)
        
        for group in identical_tasks:
            # Order by start time
            for i in range(len(group) - 1):
                model.Add(
                    task_starts[group[i]] <= task_starts[group[i+1]]
                )
```

### 2. Redundant Constraints

```python
class RedundantConstraintAdder:
    """Add constraints that are logically redundant but help propagation."""
    
    @staticmethod
    def add_cumulative_bounds(model, tasks, horizon):
        """Add cumulative resource bounds."""
        # If all tasks must fit in horizon
        total_work = sum(task.duration for task in tasks)
        min_machines_needed = (total_work + horizon - 1) // horizon
        
        # Add as constraint
        machines_used = model.NewIntVar(min_machines_needed, len(machines), 'machines_used')
        # This helps solver reason about resource usage
    
    @staticmethod
    def add_precedence_transitivity(model, precedences, task_starts):
        """Add transitive precedence constraints."""
        # Build precedence graph
        graph = build_precedence_graph(precedences)
        
        # Add transitive edges
        for task in tasks:
            descendants = find_all_descendants(graph, task)
            for desc in descendants:
                if (task, desc) not in direct_precedences:
                    # Add redundant constraint
                    model.Add(task_starts[desc] >= task_starts[task] + task.duration)
```

### 3. Variable Elimination

```python
def eliminate_unnecessary_variables(model, problem):
    """Remove variables that can be computed from others."""
    
    # ❌ Before: Separate end variables
    task_starts = {}
    task_ends = {}
    for task in tasks:
        task_starts[task] = model.NewIntVar(0, horizon, f'start_{task}')
        task_ends[task] = model.NewIntVar(0, horizon, f'end_{task}')
        model.Add(task_ends[task] == task_starts[task] + task.duration)
    
    # ✅ After: Compute ends from starts
    task_starts = {}
    for task in tasks:
        task_starts[task] = model.NewIntVar(0, horizon, f'start_{task}')
    
    # Use expressions instead of variables
    def get_task_end(task):
        return task_starts[task] + task.duration
```

### 4. Circuit/Path Constraints

```python
def use_circuit_constraint(model, locations):
    """Use specialized circuit constraint for routing."""
    # ❌ Before: Many individual constraints
    for i in locations:
        for j in locations:
            if i != j:
                # Complex constraints for routing
                pass
    
    # ✅ After: Single circuit constraint
    arcs = []
    for i in locations:
        for j in locations:
            if i != j:
                arc = model.NewBoolVar(f'arc_{i}_{j}')
                arcs.append((i, j, arc))
    
    model.AddCircuit(arcs)  # Efficient specialized constraint
```

## Search Strategy Optimization (2 hours, 20x speedup)

### 1. Variable and Value Selection

```python
def optimize_search_strategy(model, problem):
    """Define problem-specific search strategy."""
    
    # Strategy 1: Schedule critical tasks first
    critical_tasks = find_critical_path_tasks(problem)
    critical_vars = [task_starts[t] for t in critical_tasks]
    other_vars = [task_starts[t] for t in tasks if t not in critical_tasks]
    
    # Decide critical tasks first
    model.AddDecisionStrategy(
        critical_vars,
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MIN_VALUE  # Pack left
    )
    
    # Then other tasks
    model.AddDecisionStrategy(
        other_vars,
        cp_model.CHOOSE_LOWEST_MIN,  # Most constrained first
        cp_model.SELECT_MIN_VALUE
    )
```

### 2. Search Phases

```python
class PhasedSearch:
    """Multi-phase search strategy."""
    
    @staticmethod
    def apply_phased_search(model, variables):
        # Phase 1: Decide machine assignments
        assignment_vars = [v for k, v in variables.items() if 'assign' in k]
        model.AddDecisionStrategy(
            assignment_vars,
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MAX_VALUE  # Prefer assignments
        )
        
        # Phase 2: Decide timing
        timing_vars = [v for k, v in variables.items() if 'start' in k]
        model.AddDecisionStrategy(
            timing_vars,
            cp_model.CHOOSE_MIN_DOMAIN_SIZE,  # Most constrained
            cp_model.SELECT_MIN_VALUE
        )
```

### 3. Randomization and Restarts

```python
# ✅ Use random restarts for diversity
solver.parameters.random_seed = 42
solver.parameters.randomize_search = True
solver.parameters.search_branching = cp_model.FIXED_SEARCH

# Or use multiple workers with different seeds
solver.parameters.num_search_workers = 8
solver.parameters.diversify_search = True
```

### 4. Solution Improvement

```python
def focus_on_improvement(solver, model):
    """Configure solver to improve solutions quickly."""
    # Focus on finding better solutions
    solver.parameters.optimize_with_core = True
    solver.parameters.optimize_with_max_hs = True
    
    # Stop when close to optimal
    solver.parameters.relative_gap_limit = 0.01  # Within 1%
```

## Advanced Techniques (1 day, 100x speedup)

### 1. Problem Decomposition

```python
class ProblemDecomposer:
    """Decompose large problems into subproblems."""
    
    def decompose_by_time(self, problem, window_size=100):
        """Solve in time windows."""
        subproblems = []
        current_time = 0
        
        while current_time < problem.horizon:
            # Tasks that could start in this window
            window_tasks = [
                t for t in problem.tasks
                if t.earliest_start < current_time + window_size
                and t.latest_start >= current_time
            ]
            
            subproblem = self.create_subproblem(
                window_tasks,
                current_time,
                current_time + window_size
            )
            subproblems.append(subproblem)
            
            current_time += window_size // 2  # Overlap windows
        
        return subproblems
    
    def solve_decomposed(self, subproblems):
        """Solve subproblems and merge solutions."""
        partial_solutions = []
        
        for i, subproblem in enumerate(subproblems):
            # Use previous solution as hint
            if i > 0:
                self.add_boundary_constraints(
                    subproblem,
                    partial_solutions[-1]
                )
            
            solution = solve_subproblem(subproblem)
            partial_solutions.append(solution)
        
        return merge_solutions(partial_solutions)
```

### 2. Model Reformulation

```python
class ModelReformulator:
    """Reformulate model for better performance."""
    
    @staticmethod
    def use_interval_variables(model, problem):
        """Replace start/end/duration with intervals."""
        # ❌ Before: Separate variables
        starts = {}
        ends = {}
        durations = {}
        
        # ✅ After: Interval variables
        intervals = {}
        for task in problem.tasks:
            if task.is_optional:
                presence = model.NewBoolVar(f'presence_{task.id}')
                intervals[task.id] = model.NewOptionalIntervalVar(
                    starts[task.id],
                    task.duration,
                    ends[task.id],
                    presence,
                    f'interval_{task.id}'
                )
            else:
                intervals[task.id] = model.NewIntervalVar(
                    starts[task.id],
                    task.duration,
                    ends[task.id],
                    f'interval_{task.id}'
                )
        
        # Use NoOverlap instead of complex constraints
        model.AddNoOverlap(intervals.values())
```

### 3. Lazy Constraint Generation

```python
class LazyConstraintGenerator:
    """Generate constraints only when needed."""
    
    def __init__(self, model):
        self.model = model
        self.generated_constraints = set()
    
    def solve_with_lazy_constraints(self):
        """Iteratively add violated constraints."""
        while True:
            solver = cp_model.CpSolver()
            status = solver.Solve(self.model)
            
            if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                return None
            
            # Check for violations
            violations = self.find_violations(solver)
            
            if not violations:
                return self.extract_solution(solver)
            
            # Add violated constraints
            for violation in violations:
                if violation not in self.generated_constraints:
                    self.add_constraint(violation)
                    self.generated_constraints.add(violation)
```

### 4. Custom Search

```python
class CustomSearch:
    """Implement custom search procedures."""
    
    def __init__(self, model):
        self.model = model
    
    def large_neighborhood_search(self, initial_solution, iterations=100):
        """LNS: destroy and repair solutions."""
        current_solution = initial_solution
        best_solution = initial_solution
        best_cost = self.evaluate(initial_solution)
        
        for i in range(iterations):
            # Destroy: remove part of solution
            partial = self.destroy(current_solution, destroy_rate=0.3)
            
            # Repair: fix the partial solution
            new_solution = self.repair(partial)
            new_cost = self.evaluate(new_solution)
            
            # Accept or reject
            if new_cost < best_cost:
                best_solution = new_solution
                best_cost = new_cost
                current_solution = new_solution
            elif self.accept_worse(new_cost, best_cost, i):
                current_solution = new_solution
        
        return best_solution
```

## Performance Monitoring

### Profiling Tools

```python
class PerformanceProfiler:
    """Profile solver performance."""
    
    def __init__(self):
        self.metrics = {}
    
    def profile_solve(self, model, solver):
        """Detailed performance profiling."""
        import time
        
        # Model statistics
        self.metrics['variables'] = model.NumVariables()
        self.metrics['constraints'] = model.NumConstraints()
        self.metrics['boolean_variables'] = model.NumBooleanVariables()
        
        # Solve with callbacks
        start_time = time.time()
        first_solution_time = None
        solution_count = 0
        
        def callback(solver):
            nonlocal first_solution_time, solution_count
            if first_solution_time is None:
                first_solution_time = time.time() - start_time
            solution_count += 1
        
        solver.solve_with_solution_callback(model, callback)
        
        # Collect metrics
        self.metrics['total_time'] = time.time() - start_time
        self.metrics['first_solution_time'] = first_solution_time
        self.metrics['solution_count'] = solution_count
        self.metrics['branches'] = solver.NumBranches()
        self.metrics['conflicts'] = solver.NumConflicts()
        
        return self.metrics
    
    def suggest_improvements(self):
        """Suggest optimizations based on metrics."""
        suggestions = []
        
        if self.metrics['first_solution_time'] > 10:
            suggestions.append("Add solution hints or warm start")
        
        if self.metrics['conflicts'] > 1000000:
            suggestions.append("Add redundant constraints or symmetry breaking")
        
        if self.metrics['variables'] > 100000:
            suggestions.append("Consider problem decomposition")
        
        return suggestions
```

## Performance Checklist

### Before Solving
- [ ] Variable bounds as tight as possible
- [ ] Symmetries identified and broken
- [ ] Search strategy defined
- [ ] Parallel search enabled
- [ ] Time limit set

### Model Design
- [ ] Use interval variables where applicable
- [ ] Add redundant constraints
- [ ] Eliminate unnecessary variables
- [ ] Group constraints efficiently
- [ ] Consider decomposition for large problems

### During Development
- [ ] Profile each constraint type
- [ ] Measure first solution time
- [ ] Track solution quality over time
- [ ] Monitor memory usage
- [ ] Test with different random seeds

### Optimization Priorities
1. **Correctness first** - Ensure model is correct
2. **Quick feasible** - Get first solution fast
3. **Good enough** - 95% optimal often sufficient
4. **Scale later** - Optimize when needed

## Common Performance Pitfalls

1. **Creating too many variables** - Use expressions
2. **Loose bounds** - Always tighten
3. **Missing symmetry breaking** - Add ordering
4. **Default search** - Always customize
5. **Single thread** - Use all cores
6. **No time limit** - Always set one
7. **Perfectionism** - Good enough is often best

## Real-World Example

```python
# Optimizing a 5000-task scheduling problem
# Before: 6 hours, 8GB RAM
# After: 3 minutes, 500MB RAM

def optimize_large_schedule():
    # 1. Decompose by time windows
    daily_problems = decompose_by_day(problem)
    
    # 2. Solve with overlap
    solutions = []
    for day_problem in daily_problems:
        # 3. Use previous solution as hint
        if solutions:
            add_boundary_hints(day_problem, solutions[-1])
        
        # 4. Aggressive search
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 16
        solver.parameters.max_time_in_seconds = 30
        solver.parameters.random_seed = 42
        
        # 5. Stop at good enough
        solver.parameters.relative_gap_limit = 0.02  # 2% gap
        
        solution = solver.Solve(day_problem)
        solutions.append(solution)
    
    # 6. Merge and polish
    final = merge_solutions(solutions)
    return polish_solution(final, time_limit=60)
```

Remember: Premature optimization is evil, but OR-Tools performance matters at scale!