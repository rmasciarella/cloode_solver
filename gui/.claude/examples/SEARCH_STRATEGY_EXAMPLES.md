# Search Strategy Examples for OR-Tools

## Overview

Search strategies guide how CP-SAT explores the solution space. The right strategy can improve solve time by orders of magnitude. This guide provides practical examples for different problem types.

## Core Concepts

### Variable Selection (CHOOSE_*)
- **CHOOSE_FIRST**: Follow variable order
- **CHOOSE_LOWEST_MIN**: Most constrained first
- **CHOOSE_HIGHEST_MAX**: Least constrained first
- **CHOOSE_MIN_DOMAIN_SIZE**: Smallest domain first
- **CHOOSE_MAX_DOMAIN_SIZE**: Largest domain first

### Value Selection (SELECT_*)
- **SELECT_MIN_VALUE**: Try smallest value first
- **SELECT_MAX_VALUE**: Try largest value first
- **SELECT_LOWER_HALF**: Split domain, try lower half
- **SELECT_UPPER_HALF**: Split domain, try upper half

## Strategy Examples by Problem Type

### 1. Job Shop Scheduling Strategy

```python
def job_shop_search_strategy(model: cp_model.CpModel, problem):
    """Effective search strategy for job shop scheduling."""
    
    # Phase 1: Decide critical path first
    critical_tasks = identify_critical_path(problem)
    critical_starts = [
        task_starts[(job_id, task_id)]
        for job_id, task_id in critical_tasks
    ]
    
    model.AddDecisionStrategy(
        critical_starts,
        cp_model.CHOOSE_FIRST,  # Follow critical path order
        cp_model.SELECT_MIN_VALUE  # Pack left
    )
    
    # Phase 2: Decide remaining tasks by resource contention
    remaining_tasks = [
        (job_id, task_id) 
        for job_id, task_id in all_tasks 
        if (job_id, task_id) not in critical_tasks
    ]
    
    # Sort by resource scarcity
    remaining_by_contention = sorted(
        remaining_tasks,
        key=lambda t: calculate_resource_contention(t),
        reverse=True
    )
    
    contention_starts = [
        task_starts[task] for task in remaining_by_contention
    ]
    
    model.AddDecisionStrategy(
        contention_starts,
        cp_model.CHOOSE_FIRST,  # Follow contention order
        cp_model.SELECT_MIN_VALUE
    )
    
    # Phase 3: Machine assignments (if not implied by intervals)
    if machine_assignments:
        # Prefer least loaded machines
        model.AddDecisionStrategy(
            machine_assignments,
            cp_model.CHOOSE_MIN_DOMAIN_SIZE,
            cp_model.SELECT_MIN_VALUE  # Lower indexed machines
        )
```

### 2. Bin Packing Strategy

```python
def bin_packing_search_strategy(model: cp_model.CpModel, items, bins):
    """Search strategy for bin packing problems."""
    
    # Sort items by size (largest first - First Fit Decreasing)
    sorted_items = sorted(items, key=lambda x: x.size, reverse=True)
    
    # Phase 1: Pack large items first
    large_items = [i for i in sorted_items if i.size > bin_capacity * 0.5]
    large_assignments = []
    
    for item in large_items:
        item_bins = [
            item_in_bin[(item.id, bin.id)]
            for bin in bins
        ]
        large_assignments.extend(item_bins)
    
    model.AddDecisionStrategy(
        large_assignments,
        cp_model.CHOOSE_FIRST,  # Try items in size order
        cp_model.SELECT_MAX_VALUE  # Prefer assignment (1 over 0)
    )
    
    # Phase 2: Fill remaining space
    medium_items = [
        i for i in sorted_items 
        if bin_capacity * 0.25 < i.size <= bin_capacity * 0.5
    ]
    
    for item in medium_items:
        # For each item, try bins with best fit
        item_bins = sort_bins_by_remaining_space(item, bins)
        assignments = [item_in_bin[(item.id, b)] for b in item_bins]
        
        model.AddDecisionStrategy(
            assignments,
            cp_model.CHOOSE_FIRST,  # Try best fit order
            cp_model.SELECT_MAX_VALUE
        )
```

### 3. Vehicle Routing Strategy

```python
def vehicle_routing_search_strategy(model: cp_model.CpModel, 
                                   locations, 
                                   vehicles,
                                   distance_matrix):
    """Search strategy for vehicle routing problems."""
    
    # Phase 1: Assign customers to vehicles based on clustering
    clusters = geographical_clustering(locations, len(vehicles))
    
    for vehicle_id, cluster in enumerate(clusters):
        cluster_assignments = [
            visit_by_vehicle[(loc.id, vehicle_id)]
            for loc in cluster
        ]
        
        model.AddDecisionStrategy(
            cluster_assignments,
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MAX_VALUE  # Assign to cluster vehicle
        )
    
    # Phase 2: Sequence visits within each vehicle
    for vehicle_id in range(len(vehicles)):
        # Order variables for this vehicle's route
        visit_orders = [
            visit_order[(loc.id, vehicle_id)]
            for loc in locations
        ]
        
        # Use nearest neighbor heuristic
        model.AddDecisionStrategy(
            visit_orders,
            cp_model.CHOOSE_LOWEST_MIN,  # Most constrained position
            cp_model.SELECT_MIN_VALUE  # Earlier in route
        )
    
    # Phase 3: Fine-tune with 2-opt style improvements
    # This happens during search via LNS
```

### 4. Resource Allocation Strategy

```python
def resource_allocation_strategy(model: cp_model.CpModel,
                                tasks,
                                resources,
                                skills_matrix):
    """Strategy for allocating resources with skills to tasks."""
    
    # Phase 1: Critical tasks with few qualified resources
    task_flexibility = {}
    for task in tasks:
        qualified = [
            r for r in resources 
            if all(skills_matrix[r.id][s] for s in task.required_skills)
        ]
        task_flexibility[task.id] = len(qualified)
    
    # Sort by flexibility (least flexible first)
    inflexible_tasks = sorted(
        tasks,
        key=lambda t: task_flexibility[t.id]
    )
    
    # Decide inflexible task assignments first
    for task in inflexible_tasks[:len(tasks)//3]:  # Top third
        task_assignments = [
            assigned[(task.id, resource.id)]
            for resource in resources
            if is_qualified(resource, task)
        ]
        
        model.AddDecisionStrategy(
            task_assignments,
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MAX_VALUE  # Prefer assignment
        )
    
    # Phase 2: Load balancing for remaining tasks
    remaining_assignments = []
    for task in inflexible_tasks[len(tasks)//3:]:
        for resource in resources:
            if is_qualified(resource, task):
                remaining_assignments.append(assigned[(task.id, resource.id)])
    
    model.AddDecisionStrategy(
        remaining_assignments,
        cp_model.CHOOSE_MIN_DOMAIN_SIZE,  # Most constrained
        cp_model.SELECT_MIN_VALUE  # Prefer least loaded
    )
```

## Advanced Search Strategies

### 1. Multi-Phase Search

```python
class MultiPhaseSearch:
    """Complex search with multiple phases."""
    
    def __init__(self, model: cp_model.CpModel):
        self.model = model
        self.phases = []
    
    def add_phase(self, variables, var_strategy, val_strategy, name=""):
        """Add a search phase."""
        self.phases.append({
            'variables': variables,
            'var_strategy': var_strategy,
            'val_strategy': val_strategy,
            'name': name
        })
    
    def apply(self):
        """Apply all phases in order."""
        for phase in self.phases:
            self.model.AddDecisionStrategy(
                phase['variables'],
                phase['var_strategy'],
                phase['val_strategy']
            )
            print(f"Added phase: {phase['name']}")

# Example usage
search = MultiPhaseSearch(model)

# Phase 1: Structural decisions
search.add_phase(
    variables=machine_assignments,
    var_strategy=cp_model.CHOOSE_MIN_DOMAIN_SIZE,
    val_strategy=cp_model.SELECT_MIN_VALUE,
    name="Machine assignments"
)

# Phase 2: Temporal decisions
search.add_phase(
    variables=start_times,
    var_strategy=cp_model.CHOOSE_LOWEST_MIN,
    val_strategy=cp_model.SELECT_MIN_VALUE,
    name="Task scheduling"
)

search.apply()
```

### 2. Dynamic Strategy Selection

```python
def dynamic_search_strategy(model: cp_model.CpModel, problem):
    """Choose strategy based on problem characteristics."""
    
    problem_features = analyze_problem(problem)
    
    # Decision tree for strategy selection
    if problem_features['density'] > 0.8:
        # Dense problem: focus on constraint propagation
        var_strategy = cp_model.CHOOSE_MIN_DOMAIN_SIZE
        val_strategy = cp_model.SELECT_LOWER_HALF
        
    elif problem_features['symmetry'] > 0.5:
        # Symmetric problem: break symmetries
        var_strategy = cp_model.CHOOSE_FIRST
        val_strategy = cp_model.SELECT_MIN_VALUE
        
    elif problem_features['precedence_chains'] > 10:
        # Long chains: follow dependencies
        var_strategy = cp_model.CHOOSE_LOWEST_MIN
        val_strategy = cp_model.SELECT_MIN_VALUE
        
    else:
        # Default balanced strategy
        var_strategy = cp_model.CHOOSE_MIN_DOMAIN_SIZE
        val_strategy = cp_model.SELECT_MIN_VALUE
    
    # Apply selected strategy
    all_vars = collect_all_decision_variables(model)
    model.AddDecisionStrategy(all_vars, var_strategy, val_strategy)
```

### 3. Randomized Restart Strategy

```python
def randomized_restart_strategy(model: cp_model.CpModel, 
                               solver: cp_model.CpSolver,
                               time_limit: int):
    """Use random restarts with different strategies."""
    
    strategies = [
        (cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE),
        (cp_model.CHOOSE_MIN_DOMAIN_SIZE, cp_model.SELECT_MIN_VALUE),
        (cp_model.CHOOSE_LOWEST_MIN, cp_model.SELECT_MAX_VALUE),
        (cp_model.CHOOSE_HIGHEST_MAX, cp_model.SELECT_MIN_VALUE),
    ]
    
    best_solution = None
    best_objective = float('inf')
    
    time_per_restart = time_limit // len(strategies)
    
    for i, (var_strat, val_strat) in enumerate(strategies):
        # Clear previous strategy
        restart_model = model.Copy()
        
        # Apply new strategy
        variables = get_all_variables(restart_model)
        restart_model.AddDecisionStrategy(
            variables, var_strat, val_strat
        )
        
        # Solve with time limit
        solver.parameters.max_time_in_seconds = time_per_restart
        solver.parameters.random_seed = i * 42
        
        status = solver.Solve(restart_model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            if solver.ObjectiveValue() < best_objective:
                best_solution = extract_solution(solver)
                best_objective = solver.ObjectiveValue()
    
    return best_solution
```

### 4. Learning-Based Strategy

```python
class LearningSearchStrategy:
    """Adapt search strategy based on problem solving history."""
    
    def __init__(self):
        self.problem_features = {}
        self.strategy_performance = defaultdict(list)
    
    def extract_features(self, problem):
        """Extract relevant problem features."""
        return {
            'num_variables': len(problem.variables),
            'num_constraints': len(problem.constraints),
            'density': calculate_constraint_density(problem),
            'domain_sizes': average_domain_size(problem),
            'objective_type': problem.objective_type
        }
    
    def select_strategy(self, problem):
        """Select best strategy based on history."""
        features = self.extract_features(problem)
        
        # Find similar problems
        similar_problems = self.find_similar_problems(features)
        
        if not similar_problems:
            # Default strategy for new problem type
            return cp_model.CHOOSE_MIN_DOMAIN_SIZE, cp_model.SELECT_MIN_VALUE
        
        # Choose best performing strategy
        best_strategy = self.get_best_strategy(similar_problems)
        return best_strategy
    
    def update_performance(self, problem, strategy, solve_time, quality):
        """Update strategy performance database."""
        features = self.extract_features(problem)
        self.strategy_performance[strategy].append({
            'features': features,
            'solve_time': solve_time,
            'solution_quality': quality
        })
```

## Specialized Search Patterns

### 1. Symmetry-Breaking Search

```python
def symmetry_breaking_search(model: cp_model.CpModel, 
                            symmetric_vars_groups):
    """Search that explicitly breaks symmetries."""
    
    for group in symmetric_vars_groups:
        # Force lexicographic ordering
        for i in range(len(group) - 1):
            model.Add(group[i] <= group[i + 1])
        
        # Decide first variable in group first
        model.AddDecisionStrategy(
            [group[0]],
            cp_model.CHOOSE_FIRST,
            cp_model.SELECT_MIN_VALUE
        )
```

### 2. Constraint-Guided Search

```python
def constraint_guided_search(model: cp_model.CpModel,
                           soft_constraints,
                           hard_constraints):
    """Guide search by constraint violations."""
    
    # Create violation indicators
    violations = []
    for i, constraint in enumerate(soft_constraints):
        violation = model.NewBoolVar(f'violation_{i}')
        constraint.OnlyEnforceIf(violation.Not())
        violations.append(violation)
    
    # Minimize violations first
    model.AddDecisionStrategy(
        violations,
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MIN_VALUE  # Prefer no violation
    )
    
    # Then handle main problem variables
    # ...
```

### 3. Domain-Splitting Search

```python
def domain_splitting_search(model: cp_model.CpModel, variables):
    """Use domain splitting for continuous-like problems."""
    
    # For variables with large domains
    large_domain_vars = [
        v for v in variables 
        if v.Proto().domain.size() > 1000
    ]
    
    model.AddDecisionStrategy(
        large_domain_vars,
        cp_model.CHOOSE_HIGHEST_MAX,  # Largest domain
        cp_model.SELECT_LOWER_HALF  # Binary search
    )
```

## Performance Tips

### 1. Variable Ordering Impact

```python
# Bad: Random order
vars_random = list(variables)
random.shuffle(vars_random)
model.AddDecisionStrategy(vars_random, ...)  # Poor performance

# Good: Problem-specific order
vars_ordered = order_by_criticality(variables)
model.AddDecisionStrategy(vars_ordered, ...)  # Much better
```

### 2. Strategy Combination

```python
# Combine multiple strategies effectively
def combined_strategy(model, problem):
    # 1. Bottleneck resources first
    bottleneck_vars = identify_bottlenecks(problem)
    model.AddDecisionStrategy(
        bottleneck_vars,
        cp_model.CHOOSE_MIN_DOMAIN_SIZE,
        cp_model.SELECT_MIN_VALUE
    )
    
    # 2. Then temporal variables
    temporal_vars = get_temporal_variables(problem)
    model.AddDecisionStrategy(
        temporal_vars,
        cp_model.CHOOSE_LOWEST_MIN,
        cp_model.SELECT_MIN_VALUE
    )
    
    # 3. Finally, remaining decisions
    # Let solver handle rest with default strategy
```

### 3. Search Strategy Debugging

```python
def debug_search_strategy(model: cp_model.CpModel):
    """Add search logging for debugging."""
    
    class SearchLogger(cp_model.CpSolverSolutionCallback):
        def __init__(self, variables):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.variables = variables
            self.solution_count = 0
            
        def on_solution_callback(self):
            self.solution_count += 1
            print(f"\nSolution {self.solution_count}:")
            for var in self.variables[:10]:  # First 10 vars
                print(f"  {var}: {self.Value(var)}")
    
    # Use with solver
    logger = SearchLogger(important_variables)
    solver.parameters.enumerate_all_solutions = False
    solver.Solve(model, logger)
```

## Best Practices

1. **Start with domain knowledge** - Use problem structure
2. **Order matters** - Most constrained variables first
3. **Phase your search** - Structural then temporal
4. **Break symmetries** - Explicitly order symmetric vars
5. **Monitor and adapt** - Log search progress
6. **Combine strategies** - Multi-phase often wins
7. **Test variations** - Try different random seeds

## Common Pitfalls

1. **Wrong variable order** - Critical vars last
2. **Ignoring problem structure** - Generic strategy
3. **Over-constraining search** - Too rigid
4. **No restart diversity** - Single strategy
5. **Bad value selection** - Against problem grain
6. **Missing phases** - Single phase for complex problem
7. **No symmetry breaking** - Exploring equivalent solutions

Remember: A good search strategy can be the difference between finding a solution in seconds vs. hours!