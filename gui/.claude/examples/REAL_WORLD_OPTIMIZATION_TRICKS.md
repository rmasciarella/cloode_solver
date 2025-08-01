# Real-World OR-Tools Optimization Tricks

## Overview

Battle-tested optimization tricks from production systems handling millions of variables. These techniques come from real deployments in logistics, manufacturing, healthcare, and tech companies.

## The Golden Rules

1. **Good Enough Beats Perfect** - 95% optimal in 1 minute beats 100% optimal in 1 hour
2. **Decompose Ruthlessly** - No single model should take > 10 minutes
3. **Fail Fast** - Detect infeasibility early
4. **Cache Everything** - Reuse previous solutions
5. **Monitor Religiously** - You can't optimize what you don't measure

## Production-Ready Tricks

### 1. The Warm Start Cache Pattern

```python
class SolutionCache:
    """Cache and reuse solutions for similar problems."""
    
    def __init__(self, cache_size=100):
        self.cache = {}  # problem_hash -> solution
        self.cache_hits = 0
        self.cache_misses = 0
        
    def get_problem_hash(self, problem):
        """Create hash of problem structure (not data)."""
        # Hash only structural elements
        return hash((
            len(problem.tasks),
            len(problem.machines),
            tuple(sorted(problem.precedences)),
            problem.horizon // 10  # Bucket similar horizons
        ))
    
    def get_warm_start(self, problem, model, variables):
        """Apply warm start if available."""
        problem_hash = self.get_problem_hash(problem)
        
        if problem_hash in self.cache:
            self.cache_hits += 1
            solution = self.cache[problem_hash]
            
            # Apply hints with small perturbation
            for var_name, value in solution.items():
                if var_name in variables:
                    # Add some noise to avoid local optima
                    noise = random.randint(-5, 5)
                    hint_value = max(0, value + noise)
                    model.AddHint(variables[var_name], hint_value)
            
            return True
        
        self.cache_misses += 1
        return False
    
    def store_solution(self, problem, solution):
        """Store solution for future use."""
        problem_hash = self.get_problem_hash(problem)
        self.cache[problem_hash] = solution
        
        # LRU eviction
        if len(self.cache) > self.cache_size:
            oldest = min(self.cache.keys())
            del self.cache[oldest]
```

### 2. The Progressive Tightening Pattern

```python
class ProgressiveTightener:
    """Solve with relaxed constraints, then tighten."""
    
    def solve_progressively(self, problem, time_budget=300):
        # Start with relaxed problem
        relaxation_levels = [
            1.5,   # 50% relaxation
            1.2,   # 20% relaxation
            1.1,   # 10% relaxation
            1.0    # No relaxation
        ]
        
        best_solution = None
        time_per_level = time_budget / len(relaxation_levels)
        
        for level in relaxation_levels:
            # Relax constraints
            relaxed_problem = self.relax_problem(problem, level)
            
            # Build model
            model = cp_model.CpModel()
            variables = build_model(model, relaxed_problem)
            
            # Use previous solution as hint
            if best_solution:
                apply_solution_as_hints(model, variables, best_solution)
            
            # Solve with time limit
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = time_per_level
            solver.parameters.num_search_workers = 8
            
            status = solver.Solve(model)
            
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                best_solution = extract_solution(solver, variables)
                print(f"Found solution at relaxation {level}")
            else:
                print(f"No solution at relaxation {level}, keeping previous")
                break
        
        return best_solution
    
    def relax_problem(self, problem, factor):
        """Relax problem constraints by factor."""
        relaxed = copy.deepcopy(problem)
        
        # Relax time windows
        for task in relaxed.tasks:
            if hasattr(task, 'due_date'):
                task.due_date = int(task.due_date * factor)
        
        # Relax resource capacities
        for resource in relaxed.resources:
            resource.capacity = int(resource.capacity * factor)
        
        # Extend horizon
        relaxed.horizon = int(relaxed.horizon * factor)
        
        return relaxed
```

### 3. The Divide and Conquer Pattern

```python
class DivideAndConquerSolver:
    """Split large problems into overlapping subproblems."""
    
    def solve_large_problem(self, problem, chunk_size=100):
        if len(problem.tasks) <= chunk_size:
            return solve_directly(problem)
        
        # Split into time windows with overlap
        windows = self.create_time_windows(problem, chunk_size)
        solutions = []
        
        for i, window in enumerate(windows):
            print(f"Solving window {i+1}/{len(windows)}")
            
            # Create subproblem
            subproblem = self.extract_window_problem(
                problem, 
                window,
                previous_solution=solutions[-1] if solutions else None
            )
            
            # Solve subproblem
            solution = self.solve_subproblem(subproblem)
            solutions.append(solution)
            
            # Early termination if infeasible
            if not solution:
                print(f"Window {i} infeasible, stopping")
                return None
        
        # Merge solutions
        return self.merge_solutions(solutions, problem)
    
    def create_time_windows(self, problem, chunk_size):
        """Create overlapping time windows."""
        windows = []
        window_duration = problem.horizon // (chunk_size // 10)
        overlap = window_duration // 4
        
        start = 0
        while start < problem.horizon:
            end = min(start + window_duration, problem.horizon)
            windows.append((start, end))
            start += window_duration - overlap  # Overlap windows
        
        return windows
    
    def extract_window_problem(self, problem, window, previous_solution):
        """Extract subproblem for time window."""
        start_time, end_time = window
        
        # Tasks that could execute in this window
        window_tasks = [
            task for task in problem.tasks
            if task.earliest_start < end_time and 
               task.latest_end > start_time
        ]
        
        # Create subproblem
        subproblem = Problem()
        subproblem.tasks = window_tasks
        subproblem.horizon = end_time - start_time
        
        # Fix tasks from previous solution
        if previous_solution:
            for task_id, start in previous_solution.items():
                if start < start_time:  # Already scheduled
                    # Add as fixed constraint
                    subproblem.fixed_tasks[task_id] = start
        
        return subproblem
```

### 4. The Fallback Chain Pattern

```python
class FallbackChainSolver:
    """Try multiple approaches in order of speed."""
    
    def __init__(self):
        self.strategies = [
            (self.greedy_heuristic, 1),      # 1 second
            (self.local_search, 10),         # 10 seconds
            (self.cpsat_quick, 60),          # 1 minute
            (self.cpsat_full, 300),          # 5 minutes
            (self.decomposed_solve, 1800)    # 30 minutes
        ]
    
    def solve(self, problem, time_budget=600):
        """Try strategies until time budget exhausted."""
        best_solution = None
        best_quality = float('inf')
        start_time = time.time()
        
        for strategy_func, strategy_time in self.strategies:
            remaining_time = time_budget - (time.time() - start_time)
            
            if remaining_time <= 0:
                break
            
            allowed_time = min(strategy_time, remaining_time)
            
            try:
                solution = strategy_func(problem, allowed_time)
                quality = evaluate_solution(solution)
                
                if quality < best_quality:
                    best_solution = solution
                    best_quality = quality
                    print(f"{strategy_func.__name__}: quality={quality}")
                
                # Stop if good enough
                if quality < problem.target_quality:
                    break
                    
            except Exception as e:
                print(f"{strategy_func.__name__} failed: {e}")
                continue
        
        return best_solution
    
    def greedy_heuristic(self, problem, time_limit):
        """Fast greedy solution."""
        # Sort tasks by urgency
        tasks = sorted(problem.tasks, key=lambda t: t.due_date)
        schedule = {}
        
        for task in tasks:
            # Find earliest feasible slot
            earliest = find_earliest_slot(task, schedule)
            schedule[task.id] = earliest
        
        return schedule
```

### 5. The Constraint Learning Pattern

```python
class ConstraintLearner:
    """Learn effective redundant constraints from solutions."""
    
    def __init__(self):
        self.learned_patterns = []
        self.pattern_effectiveness = defaultdict(float)
    
    def analyze_good_solutions(self, solutions):
        """Extract patterns from good solutions."""
        patterns = []
        
        for solution in solutions:
            # Pattern 1: Task ordering
            for t1, s1 in solution.items():
                for t2, s2 in solution.items():
                    if s1 < s2:
                        pattern = ('order', t1, t2, s2 - s1)
                        patterns.append(pattern)
            
            # Pattern 2: Resource usage
            resource_usage = calculate_resource_usage(solution)
            for resource, usage_pattern in resource_usage.items():
                pattern = ('resource', resource, max(usage_pattern))
                patterns.append(pattern)
        
        # Keep frequent patterns
        pattern_counts = Counter(patterns)
        self.learned_patterns = [
            p for p, count in pattern_counts.items() 
            if count >= len(solutions) * 0.8  # 80% frequency
        ]
    
    def apply_learned_constraints(self, model, variables):
        """Add learned constraints to new model."""
        for pattern in self.learned_patterns:
            if pattern[0] == 'order':
                _, t1, t2, min_gap = pattern
                if t1 in variables and t2 in variables:
                    # Soft constraint with violation cost
                    violation = model.NewBoolVar(f'learned_violation_{t1}_{t2}')
                    model.Add(
                        variables[t2] >= variables[t1] + min_gap
                    ).OnlyEnforceIf(violation.Not())
                    
            elif pattern[0] == 'resource':
                _, resource, max_usage = pattern
                # Add as hint rather than hard constraint
                # ...
```

### 6. The Smart Timeout Pattern

```python
class SmartTimeoutManager:
    """Adaptive timeout based on problem characteristics."""
    
    def __init__(self):
        self.history = []  # (problem_features, solve_time, quality)
        
    def predict_solve_time(self, problem):
        """Predict time needed based on history."""
        features = self.extract_features(problem)
        
        if len(self.history) < 10:
            # Not enough data, use conservative estimate
            return 60 * (features['num_tasks'] / 100)
        
        # Find similar problems
        similar = [
            (hist_features, time, quality)
            for hist_features, time, quality in self.history
            if self.similarity(features, hist_features) > 0.8
        ]
        
        if similar:
            # Use 90th percentile of similar problems
            times = sorted([time for _, time, _ in similar])
            return times[int(len(times) * 0.9)]
        
        # Fallback to linear model
        return self.linear_prediction(features)
    
    def adaptive_solve(self, problem, max_time=3600):
        """Solve with adaptive timeouts."""
        predicted_time = self.predict_solve_time(problem)
        
        # Try with predicted time first
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = min(predicted_time, max_time)
        
        start_time = time.time()
        status = solver.Solve(build_model(problem))
        actual_time = time.time() - start_time
        
        if status == cp_model.OPTIMAL:
            # Found optimal, record and return
            self.record_result(problem, actual_time, 'optimal')
            return solver
        
        elif status == cp_model.FEASIBLE:
            # Found feasible, maybe try for better
            remaining = max_time - actual_time
            if remaining > predicted_time * 0.5:
                # Try to improve
                solver.parameters.max_time_in_seconds = remaining
                solver.Solve(model)  # Continue from current
        
        return solver
```

### 7. The Parallel Portfolio Pattern

```python
class ParallelPortfolioSolver:
    """Run multiple configurations in parallel."""
    
    def solve_with_portfolio(self, problem, num_workers=8):
        """Use different strategies on different workers."""
        
        # Define portfolio of configurations
        portfolio = [
            {'search': 'auto', 'emphasis': 'feasibility'},
            {'search': 'fixed', 'emphasis': 'optimality'},
            {'search': 'portfolio', 'emphasis': 'balance'},
            {'search': 'lns', 'emphasis': 'improvement'},
            {'use_sat': True, 'linearization': 2},
            {'symmetry_level': 2, 'probing': 2},
            {'restart_period': 100, 'random': True},
            {'presolve': 'aggressive', 'cuts': True}
        ]
        
        # Ensure we have enough configurations
        while len(portfolio) < num_workers:
            # Create variations
            base = random.choice(portfolio)
            variation = base.copy()
            variation['random_seed'] = random.randint(0, 1000)
            portfolio.append(variation)
        
        # Run in parallel using multiprocessing
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for i, config in enumerate(portfolio[:num_workers]):
                future = executor.submit(
                    self.solve_with_config,
                    problem,
                    config,
                    worker_id=i
                )
                futures.append(future)
            
            # Return first good solution
            for future in as_completed(futures):
                try:
                    solution = future.result()
                    if solution and solution['quality'] < threshold:
                        # Cancel other workers
                        for f in futures:
                            f.cancel()
                        return solution
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        # Return best solution found
        return self.best_solution
```

### 8. The Incremental Refinement Pattern

```python
class IncrementalRefiner:
    """Iteratively refine solution quality."""
    
    def refine_solution(self, problem, initial_solution, iterations=10):
        """Improve solution through local refinements."""
        
        current_solution = initial_solution
        current_quality = evaluate_solution(current_solution)
        
        for i in range(iterations):
            # Pick refinement strategy based on iteration
            if i < 3:
                # Large neighborhood changes early
                refined = self.large_neighborhood_search(
                    problem, current_solution, destroy_rate=0.3
                )
            elif i < 7:
                # Medium changes
                refined = self.variable_neighborhood_search(
                    problem, current_solution
                )
            else:
                # Fine tuning
                refined = self.small_perturbations(
                    problem, current_solution
                )
            
            refined_quality = evaluate_solution(refined)
            
            # Accept improvements
            if refined_quality < current_quality:
                current_solution = refined
                current_quality = refined_quality
                print(f"Iteration {i}: improved to {refined_quality}")
            
            # Early termination if good enough
            if current_quality < problem.target_quality:
                break
        
        return current_solution
    
    def large_neighborhood_search(self, problem, solution, destroy_rate):
        """Remove and re-solve part of solution."""
        # Randomly destroy part of solution
        destroyed_tasks = random.sample(
            list(solution.keys()),
            int(len(solution) * destroy_rate)
        )
        
        # Create partial problem
        partial_solution = {
            k: v for k, v in solution.items()
            if k not in destroyed_tasks
        }
        
        # Re-solve destroyed part
        subproblem = create_subproblem(problem, destroyed_tasks)
        new_partial = solve_with_fixed_tasks(subproblem, partial_solution)
        
        # Combine solutions
        return {**partial_solution, **new_partial}
```

## Performance Monitoring Tricks

### 1. The Solver Health Dashboard

```python
class SolverHealthMonitor:
    """Monitor solver performance in production."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alerts = []
    
    def monitor_solve(self, problem, solver, status):
        """Record solve metrics."""
        metrics = {
            'timestamp': time.time(),
            'problem_size': len(problem.tasks),
            'solve_time': solver.WallTime(),
            'objective': solver.ObjectiveValue() if status == cp_model.OPTIMAL else None,
            'num_branches': solver.NumBranches(),
            'num_conflicts': solver.NumConflicts(),
            'memory_usage': get_memory_usage(),
            'status': solver.StatusName(status)
        }
        
        # Check for anomalies
        if metrics['solve_time'] > 300:  # 5 minutes
            self.alerts.append(f"Slow solve: {metrics['solve_time']}s")
        
        if metrics['memory_usage'] > 2000:  # 2GB
            self.alerts.append(f"High memory: {metrics['memory_usage']}MB")
        
        # Store for analysis
        for key, value in metrics.items():
            self.metrics[key].append(value)
        
        return metrics
    
    def get_performance_summary(self):
        """Generate performance report."""
        return {
            'avg_solve_time': np.mean(self.metrics['solve_time']),
            'p95_solve_time': np.percentile(self.metrics['solve_time'], 95),
            'success_rate': sum(1 for s in self.metrics['status'] if s != 'INFEASIBLE') / len(self.metrics['status']),
            'alerts': self.alerts[-10:]  # Recent alerts
        }
```

### 2. The A/B Testing Framework

```python
class SolverABTest:
    """A/B test different solver configurations."""
    
    def __init__(self, config_a, config_b):
        self.config_a = config_a
        self.config_b = config_b
        self.results_a = []
        self.results_b = []
    
    def run_test(self, problems, split_ratio=0.5):
        """Run A/B test on problem set."""
        random.shuffle(problems)
        split_point = int(len(problems) * split_ratio)
        
        # Run configuration A
        for problem in problems[:split_point]:
            result = self.solve_with_config(problem, self.config_a)
            self.results_a.append(result)
        
        # Run configuration B
        for problem in problems[split_point:]:
            result = self.solve_with_config(problem, self.config_b)
            self.results_b.append(result)
        
        # Statistical analysis
        return self.analyze_results()
    
    def analyze_results(self):
        """Compare configurations statistically."""
        from scipy import stats
        
        times_a = [r['time'] for r in self.results_a]
        times_b = [r['time'] for r in self.results_b]
        
        quality_a = [r['quality'] for r in self.results_a]
        quality_b = [r['quality'] for r in self.results_b]
        
        return {
            'time_improvement': (np.mean(times_a) - np.mean(times_b)) / np.mean(times_a),
            'quality_improvement': (np.mean(quality_a) - np.mean(quality_b)) / np.mean(quality_a),
            'time_significance': stats.ttest_ind(times_a, times_b).pvalue,
            'quality_significance': stats.ttest_ind(quality_a, quality_b).pvalue,
            'recommendation': 'B' if np.mean(times_b) < np.mean(times_a) else 'A'
        }
```

## The Ultimate Production Checklist

### Before Deployment
- [ ] Test with 10x expected data size
- [ ] Set memory limits explicitly
- [ ] Add timeout for every solve call
- [ ] Implement fallback strategies
- [ ] Add solution validation
- [ ] Set up monitoring/alerting
- [ ] Test infeasible case handling
- [ ] Verify solution determinism
- [ ] Load test the system
- [ ] Document configuration choices

### In Production
- [ ] Monitor solve time percentiles
- [ ] Track solution quality metrics
- [ ] Alert on anomalies
- [ ] Keep solution cache warm
- [ ] Regular A/B tests
- [ ] Update solver version carefully
- [ ] Maintain problem/solution database
- [ ] Regular performance reviews

### Emergency Procedures
1. **Solver hanging**: Kill after 2x expected time
2. **Memory explosion**: Restart with reduced problem
3. **Infeasibility spike**: Check data quality first
4. **Quality degradation**: Increase time limits
5. **Slow performance**: Enable more workers

## Final Wisdom

> "The best optimization is the one that ships on time and keeps running at 3 AM."

Remember:
- Production is different from benchmarks
- Monitor everything, assume nothing
- Have multiple fallback strategies
- Cache aggressively but intelligently
- Decomposition is your friend
- Perfect is the enemy of good enough

These tricks have saved countless hours of compute time and prevented many production incidents. Use them wisely!