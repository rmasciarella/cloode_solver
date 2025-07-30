# Infeasibility Debugging Guide for OR-Tools

## Overview

A systematic approach to debugging infeasible OR-Tools CP-SAT models. When the solver returns INFEASIBLE, this guide helps you find and fix the root cause efficiently.

## Quick Diagnosis Flowchart

```
Is Model INFEASIBLE?
├── YES → Check Obvious Issues First
│   ├── Empty domains? → Fix bounds
│   ├── Contradictory constraints? → Review logic
│   └── Impossible requirements? → Relax constraints
└── NO → Check Near-Infeasibility
    ├── Solver timeout? → Increase time limit
    ├── Poor solution quality? → Review objectives
    └── Numerical issues? → Scale values
```

## Step-by-Step Debugging Process

### Step 1: Verify Basic Sanity

```python
def sanity_check_model(model, problem):
    """Basic sanity checks before deep debugging."""
    issues = []
    
    # Check 1: Task durations positive
    for task in problem.tasks:
        if task.duration <= 0:
            issues.append(f"Task {task.id} has non-positive duration: {task.duration}")
    
    # Check 2: Time windows valid
    for task in problem.tasks:
        if hasattr(task, 'earliest_start') and hasattr(task, 'latest_end'):
            if task.earliest_start >= task.latest_end:
                issues.append(f"Task {task.id} has invalid time window")
            if task.latest_end - task.earliest_start < task.duration:
                issues.append(f"Task {task.id} duration exceeds time window")
    
    # Check 3: Precedences don't create cycles
    if has_circular_dependencies(problem.precedences):
        issues.append("Circular dependencies detected in precedences")
    
    return issues
```

### Step 2: Binary Search for Infeasibility

```python
def find_infeasibility_boundary(problem):
    """Binary search to find when problem becomes infeasible."""
    original_horizon = problem.horizon
    
    # Start with very relaxed problem
    low = original_horizon * 2
    high = original_horizon // 2
    
    while low > high + 1:
        mid = (low + high) // 2
        problem.horizon = mid
        
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        status = solver.Solve(build_model(problem))
        
        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            low = mid  # Can tighten more
        else:
            high = mid  # Too tight
    
    print(f"Problem becomes infeasible when horizon < {high}")
    problem.horizon = original_horizon
    return high
```

### Step 3: Isolate Constraint Groups

```python
class ConstraintGroupDebugger:
    """Debug by selectively enabling constraint groups."""
    
    def __init__(self, problem):
        self.problem = problem
        self.constraint_groups = {
            'duration': self.add_duration_constraints,
            'precedence': self.add_precedence_constraints,
            'assignment': self.add_assignment_constraints,
            'no_overlap': self.add_no_overlap_constraints,
            'capacity': self.add_capacity_constraints,
            'time_windows': self.add_time_window_constraints
        }
    
    def debug_by_group(self):
        """Find which constraint group causes infeasibility."""
        results = {}
        
        # Test each group individually
        for name, add_func in self.constraint_groups.items():
            model = cp_model.CpModel()
            variables = self.create_variables(model)
            
            # Add only this constraint group
            add_func(model, variables)
            
            solver = cp_model.CpSolver()
            status = solver.Solve(model)
            results[name] = status == cp_model.FEASIBLE
            
            print(f"{name}: {'✓ FEASIBLE' if results[name] else '✗ INFEASIBLE'}")
        
        # Test combinations
        self.test_combinations(results)
        
        return results
    
    def test_combinations(self, individual_results):
        """Test constraint combinations to find conflicts."""
        feasible_groups = [g for g, f in individual_results.items() if f]
        
        # Test pairs
        for i, group1 in enumerate(feasible_groups):
            for group2 in feasible_groups[i+1:]:
                model = cp_model.CpModel()
                variables = self.create_variables(model)
                
                self.constraint_groups[group1](model, variables)
                self.constraint_groups[group2](model, variables)
                
                solver = cp_model.CpSolver()
                status = solver.Solve(model)
                
                if status != cp_model.FEASIBLE:
                    print(f"CONFLICT: {group1} + {group2} = INFEASIBLE")
```

### Step 4: Minimal Infeasible Subset (MIS)

```python
def find_minimal_infeasible_subset(model, constraints):
    """Find minimal set of constraints causing infeasibility."""
    # Start with all constraints
    active_constraints = list(constraints)
    
    # Try removing each constraint
    for i in range(len(active_constraints)):
        test_constraints = active_constraints[:i] + active_constraints[i+1:]
        
        test_model = cp_model.CpModel()
        # Rebuild model with subset
        apply_constraints(test_model, test_constraints)
        
        solver = cp_model.CpSolver()
        status = solver.Solve(test_model)
        
        if status == cp_model.INFEASIBLE:
            # Still infeasible without constraint i
            active_constraints = test_constraints
    
    return active_constraints
```

### Step 5: Assumption-Based Debugging

```python
class AssumptionDebugger:
    """Debug using solver assumptions."""
    
    def __init__(self, model):
        self.model = model
        self.assumptions = []
    
    def add_assumption(self, literal, name):
        """Add named assumption for debugging."""
        self.assumptions.append({
            'literal': literal,
            'name': name,
            'required': True
        })
    
    def debug_with_assumptions(self):
        """Find which assumptions cause infeasibility."""
        solver = cp_model.CpSolver()
        
        # Try with all assumptions
        assumption_literals = [a['literal'] for a in self.assumptions]
        status = solver.SolveWithAssumptions(self.model, assumption_literals)
        
        if status == cp_model.FEASIBLE:
            print("Model is feasible with all assumptions")
            return
        
        # Binary search on assumptions
        self.find_conflicting_assumptions(solver)
    
    def find_conflicting_assumptions(self, solver):
        """Find minimal conflicting assumption set."""
        for i, assumption in enumerate(self.assumptions):
            # Try without this assumption
            test_assumptions = [
                a['literal'] for j, a in enumerate(self.assumptions) 
                if j != i
            ]
            
            status = solver.SolveWithAssumptions(self.model, test_assumptions)
            
            if status == cp_model.FEASIBLE:
                print(f"Removing assumption '{assumption['name']}' makes model feasible")
```

## Common Infeasibility Patterns

### Pattern 1: Over-Constrained Time Windows

```python
# Problem: Multiple tight time windows
task1: must finish by time 100
task2: must start after task1, duration 60
task3: must start after task2, must finish by time 150

# Debug approach:
def debug_time_windows(tasks, precedences):
    # Calculate critical path
    critical_path_length = calculate_critical_path(tasks, precedences)
    
    # Check against time windows
    for task in tasks:
        if hasattr(task, 'latest_end'):
            slack = task.latest_end - critical_path_to_task(task)
            if slack < 0:
                print(f"Task {task.id} impossible: needs {-slack} more time")
```

### Pattern 2: Resource Capacity Conflicts

```python
# Problem: Peak resource demand exceeds capacity
def debug_resource_capacity(tasks, resources):
    # Find resource bottlenecks
    for resource in resources:
        # Calculate minimum time needed
        total_demand = sum(
            task.duration * task.resource_need[resource.id]
            for task in tasks
            if resource.id in task.resource_need
        )
        
        available_time = resource.capacity * resource.availability_hours
        
        if total_demand > available_time:
            shortfall = total_demand - available_time
            print(f"Resource {resource.id} short by {shortfall} units")
```

### Pattern 3: Precedence Impossibilities

```python
# Problem: Precedence chain too long for horizon
def debug_precedence_chain(problem):
    # Find longest chain
    longest_chain = find_longest_precedence_chain(problem)
    chain_duration = sum(problem.get_task(t).duration for t in longest_chain)
    
    if chain_duration > problem.horizon:
        print(f"Precedence chain {longest_chain} needs {chain_duration}")
        print(f"But horizon is only {problem.horizon}")
        
        # Suggest solutions
        print("\nSolutions:")
        print(f"1. Increase horizon to at least {chain_duration}")
        print("2. Reduce task durations in critical path")
        print("3. Parallelize some sequential tasks")
```

## Infeasibility Debugging Toolkit

### Tool 1: Constraint Relaxation

```python
class ConstraintRelaxer:
    """Systematically relax constraints to find feasibility."""
    
    def __init__(self, model, problem):
        self.model = model
        self.problem = problem
        self.relaxations = []
    
    def relax_time_windows(self, percentage=20):
        """Relax time windows by percentage."""
        for task in self.problem.tasks:
            if hasattr(task, 'earliest_start'):
                task.earliest_start = int(task.earliest_start * (1 - percentage/100))
            if hasattr(task, 'latest_end'):
                task.latest_end = int(task.latest_end * (1 + percentage/100))
        
        self.relaxations.append(f"Time windows relaxed by {percentage}%")
    
    def relax_capacity(self, extra_capacity=1):
        """Add extra capacity to resources."""
        for resource in self.problem.resources:
            resource.capacity += extra_capacity
        
        self.relaxations.append(f"Added {extra_capacity} capacity to all resources")
    
    def find_minimal_relaxation(self):
        """Find minimum relaxation needed for feasibility."""
        original_problem = copy.deepcopy(self.problem)
        
        relaxation_levels = [10, 20, 30, 40, 50]
        
        for level in relaxation_levels:
            self.problem = copy.deepcopy(original_problem)
            self.relax_time_windows(level)
            
            if self.is_feasible():
                print(f"Feasible with {level}% time window relaxation")
                return level
        
        return None
```

### Tool 2: Visual Debugging

```python
def visualize_infeasibility(problem, constraint_type):
    """Create visual representation of conflicts."""
    
    if constraint_type == 'precedence':
        # Generate precedence graph
        import networkx as nx
        import matplotlib.pyplot as plt
        
        G = nx.DiGraph()
        for task in problem.tasks:
            G.add_node(task.id, duration=task.duration)
        
        for pred, succ in problem.precedences:
            G.add_edge(pred, succ)
        
        # Find and highlight critical path
        critical_path = nx.dag_longest_path(G, weight='duration')
        
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue')
        nx.draw_networkx_nodes(G, pos, nodelist=critical_path, node_color='red')
        
        plt.title("Precedence Graph (Critical Path in Red)")
        plt.show()
    
    elif constraint_type == 'resource':
        # Generate resource usage timeline
        visualize_resource_demand(problem)
```

### Tool 3: Solution Hints

```python
def provide_solution_hint(model, variables, partial_solution):
    """Provide partial solution to guide solver."""
    for var_name, value in partial_solution.items():
        if var_name in variables:
            model.AddHint(variables[var_name], value)
    
    # Test if hint helps
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model)
    
    return status == cp_model.FEASIBLE
```

## Debugging Commands Reference

```bash
# Use these Claude commands for debugging:

/trace-infeasible
# Analyzes model and identifies constraint conflicts

/debug-variables
# Shows variable domains and detects empty domains

/check-constraint precedence
# Validates specific constraint type

/suggest-relaxation
# Recommends constraint relaxations

/profile-solver --focus constraints
# Identifies which constraints take most time
```

## Best Practices

1. **Start Simple**: Begin with a tiny problem that's known to be feasible
2. **Add Incrementally**: Add constraints one at a time
3. **Log Everything**: Print constraint counts and variable domains
4. **Test Bounds**: Verify every variable has valid domain
5. **Visualize**: Draw precedence graphs and resource timelines
6. **Binary Search**: Use binary search to find feasibility boundaries
7. **Save States**: Keep working versions to compare against

## Common Fixes

### Quick Fixes
1. **Increase horizon**: `problem.horizon *= 1.5`
2. **Relax time windows**: `task.latest_end += buffer`
3. **Add resources**: `resource.capacity += 1`
4. **Remove constraints**: Start with optional ones
5. **Reduce precision**: Round to larger time units

### Structural Fixes
1. **Reformulate model**: Sometimes a different approach works better
2. **Decompose problem**: Solve in stages
3. **Use soft constraints**: Convert hard constraints to penalties
4. **Preprocess data**: Clean before modeling
5. **Add valid inequalities**: Help solver prune infeasible space

Remember: Infeasibility is often a data problem, not a modeling problem. Always validate your input data first!