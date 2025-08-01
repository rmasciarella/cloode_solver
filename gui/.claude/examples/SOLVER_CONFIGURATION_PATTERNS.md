# Solver Configuration Patterns for OR-Tools

## Overview

Configuration patterns for the CP-SAT solver organized by problem type and optimization goals. Each pattern includes parameter settings, rationale, and performance expectations.

## Configuration by Problem Type

### 1. Job Shop Scheduling

```python
def configure_for_job_shop(solver: cp_model.CpSolver, problem_size: str = 'medium'):
    """Configure solver for job shop scheduling problems."""
    
    if problem_size == 'small':  # < 50 tasks
        solver.parameters.num_search_workers = 4
        solver.parameters.max_time_in_seconds = 60
        solver.parameters.relative_gap_limit = 0.0  # Find optimal
        
    elif problem_size == 'medium':  # 50-500 tasks
        solver.parameters.num_search_workers = 8
        solver.parameters.max_time_in_seconds = 300
        solver.parameters.relative_gap_limit = 0.01  # Within 1%
        solver.parameters.linearization_level = 2
        
    elif problem_size == 'large':  # > 500 tasks
        solver.parameters.num_search_workers = 16
        solver.parameters.max_time_in_seconds = 3600
        solver.parameters.relative_gap_limit = 0.05  # Within 5%
        solver.parameters.use_lns_only = True  # Large Neighborhood Search
        
    # Common settings
    solver.parameters.log_search_progress = True
    solver.parameters.optimize_with_core = True
    solver.parameters.cp_model_presolve = True
```

### 2. Resource Allocation

```python
def configure_for_resource_allocation(solver: cp_model.CpSolver, 
                                     num_resources: int,
                                     num_tasks: int):
    """Configure for resource allocation/assignment problems."""
    
    # Focus on finding feasible solutions quickly
    solver.parameters.num_search_workers = min(8, num_resources)
    solver.parameters.search_branching = cp_model.FIXED_SEARCH
    
    if num_tasks > 1000:
        # For large problems, use decomposition-friendly settings
        solver.parameters.subsolvers = [
            'default_lp',     # Good for resource constraints
            'core',           # Optimization
            'quick_restart',  # Diversity
            'reduced_costs'   # Pruning
        ]
    
    # Symmetry is common in resource problems
    solver.parameters.symmetry_level = 2  # Aggressive symmetry breaking
    solver.parameters.instantiate_all_variables = False
```

### 3. Routing/TSP Problems

```python
def configure_for_routing(solver: cp_model.CpSolver, 
                         num_locations: int,
                         time_limit: int = 300):
    """Configure for routing and traveling salesman problems."""
    
    solver.parameters.max_time_in_seconds = time_limit
    
    # Routing benefits from specific search strategies
    solver.parameters.use_lns_only = num_locations > 100
    solver.parameters.lns_focus_on_decision_variables = True
    
    # Good for circuit constraints
    solver.parameters.use_sat_inprocessing = True
    solver.parameters.num_search_workers = 8
    
    # First solution strategies matter for routing
    solver.parameters.stop_after_first_solution = False
    solver.parameters.random_seed = 42  # Reproducibility
```

### 4. Bin Packing

```python
def configure_for_bin_packing(solver: cp_model.CpSolver,
                             num_items: int,
                             optimize_bins: bool = True):
    """Configure for bin packing problems."""
    
    if optimize_bins:
        # Minimize number of bins
        solver.parameters.use_objectives_in_sat = True
        solver.parameters.core_minimization_level = 2
        
    # Bin packing has natural bounds
    solver.parameters.use_pseudo_costs = True
    solver.parameters.exploit_best_bound = True
    
    # Symmetry between identical bins
    solver.parameters.symmetry_level = 2
    solver.parameters.presolve_use_bva = True
```

## Configuration by Optimization Goal

### 1. Find Feasible Solution Quickly

```python
def configure_for_quick_feasibility(solver: cp_model.CpSolver):
    """Get any feasible solution as fast as possible."""
    
    solver.parameters.num_search_workers = 16  # Maximum parallelism
    solver.parameters.stop_after_first_solution = True
    solver.parameters.random_seed = 0  # Try different seeds if stuck
    
    # Disable optimization
    solver.parameters.optimize_with_core = False
    solver.parameters.optimize_with_max_hs = False
    
    # Fast presolve
    solver.parameters.presolve_bounded_deductions = 1
    solver.parameters.cp_model_presolve = True
```

### 2. Find Near-Optimal Solution

```python
def configure_for_quality_solution(solver: cp_model.CpSolver,
                                  time_budget: int = 600):
    """Balance solution quality with solve time."""
    
    solver.parameters.max_time_in_seconds = time_budget
    solver.parameters.relative_gap_limit = 0.02  # Within 2%
    
    # Enable all optimization techniques
    solver.parameters.optimize_with_core = True
    solver.parameters.optimize_with_max_hs = True
    solver.parameters.use_objectives_in_sat = True
    
    # Good general settings
    solver.parameters.num_search_workers = 8
    solver.parameters.linearization_level = 2
    solver.parameters.cp_model_probing_level = 2
```

### 3. Prove Optimality

```python
def configure_for_optimality_proof(solver: cp_model.CpSolver):
    """Prove optimal solution (may take long time)."""
    
    solver.parameters.relative_gap_limit = 0.0
    solver.parameters.absolute_gap_limit = 0.0
    
    # Thorough search
    solver.parameters.num_search_workers = 16
    solver.parameters.interleave_search = True
    
    # Strong presolve
    solver.parameters.presolve_bounded_deductions = 8
    solver.parameters.cp_model_presolve = True
    solver.parameters.cp_model_probing_level = 2
    
    # No time limit
    solver.parameters.max_time_in_seconds = 0
```

### 4. Interactive/Incremental Solving

```python
def configure_for_interactive_solving(solver: cp_model.CpSolver):
    """Configure for interactive use with quick updates."""
    
    # Quick iterations
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 4
    
    # Warm start friendly
    solver.parameters.keep_all_feasible_solutions_in_presolve = True
    solver.parameters.enumerate_all_solutions = False
    
    # Less aggressive presolve for model changes
    solver.parameters.presolve_bounded_deductions = 1
```

## Advanced Configuration Patterns

### 1. Memory-Constrained Environments

```python
def configure_for_memory_limits(solver: cp_model.CpSolver,
                               memory_limit_mb: int = 2000):
    """Configure for limited memory environments."""
    
    # Limit solver memory
    solver.parameters.max_memory_in_mb = memory_limit_mb
    
    # Reduce parallel workers (each uses memory)
    solver.parameters.num_search_workers = min(4, os.cpu_count() // 2)
    
    # Disable memory-intensive features
    solver.parameters.use_lns_only = False  # LNS can use lots of memory
    solver.parameters.enumerate_all_solutions = False
    
    # Conservative presolve
    solver.parameters.presolve_bounded_deductions = 1
```

### 2. Distributed Solving

```python
def configure_for_distributed_solving(solver: cp_model.CpSolver,
                                     worker_id: int,
                                     num_workers: int):
    """Configure for distributed/parallel solving."""
    
    # Different random seeds per worker
    solver.parameters.random_seed = worker_id
    
    # Diversify search strategies
    strategies = [
        cp_model.AUTOMATIC_SEARCH,
        cp_model.FIXED_SEARCH,
        cp_model.PORTFOLIO_SEARCH,
        cp_model.LP_SEARCH
    ]
    solver.parameters.search_branching = strategies[worker_id % len(strategies)]
    
    # Share bounds but not solutions
    solver.parameters.share_objective_bounds = True
    solver.parameters.share_level_zero_bounds = True
```

### 3. Anytime Optimization

```python
class AnytimeOptimizer:
    """Progressive optimization with improving solutions over time."""
    
    def __init__(self, model: cp_model.CpModel):
        self.model = model
        self.solver = cp_model.CpSolver()
        self.configure_anytime()
    
    def configure_anytime(self):
        """Configure for anytime behavior."""
        # Report all improving solutions
        self.solver.parameters.enumerate_all_solutions = False
        self.solver.parameters.log_search_progress = True
        
        # Focus on improvement
        self.solver.parameters.optimize_with_core = True
        self.solver.parameters.optimize_with_max_hs = True
        
        # Diverse search
        self.solver.parameters.num_search_workers = 8
        self.solver.parameters.interleave_search = True
    
    def solve_with_callback(self, callback):
        """Solve with user callback for each improvement."""
        solution_printer = cp_model.ObjectiveSolutionPrinter()
        self.solver.Solve(self.model, solution_printer)
```

### 4. Robustness and Determinism

```python
def configure_for_deterministic_solving(solver: cp_model.CpSolver):
    """Ensure reproducible results across runs."""
    
    # Fixed random seed
    solver.parameters.random_seed = 12345
    
    # Single thread for determinism
    solver.parameters.num_search_workers = 1
    
    # Disable randomized components
    solver.parameters.randomize_search = False
    solver.parameters.use_lns_only = False  # LNS has randomness
    
    # Fixed search
    solver.parameters.search_branching = cp_model.FIXED_SEARCH
```

## Problem-Specific Tuning Guide

### Decision Flowchart

```
Start
├── Is problem LARGE (>1000 variables)?
│   ├── YES → Use LNS, limit presolve
│   └── NO → Continue
├── Is FEASIBILITY more important than OPTIMALITY?
│   ├── YES → stop_after_first_solution, parallel search
│   └── NO → Continue
├── Are there SYMMETRIES?
│   ├── YES → symmetry_level = 2
│   └── NO → Continue
├── Is there a TIME LIMIT?
│   ├── YES → relative_gap_limit > 0
│   └── NO → Continue
└── Enable standard optimizations
```

### Performance Tuning Checklist

1. **Start with defaults** - Often good enough
2. **Profile first** - Measure before optimizing
3. **Set time limits** - Avoid infinite runs
4. **Use multiple workers** - Free parallelism
5. **Enable logging** - Understand behavior
6. **Try different seeds** - Some problems are lucky
7. **Adjust gap limits** - Good enough is often best

## Configuration Templates

### Template 1: Production Scheduler

```python
class ProductionSchedulerConfig:
    """Configuration for production scheduling systems."""
    
    @staticmethod
    def configure(solver: cp_model.CpSolver, 
                  problem_size: str,
                  time_limit: int = 300):
        
        # Base configuration
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.log_search_progress = True
        solver.parameters.num_search_workers = 8
        
        # Size-specific adjustments
        configs = {
            'small': {
                'relative_gap_limit': 0.0,
                'linearization_level': 2,
                'cp_model_probing_level': 2
            },
            'medium': {
                'relative_gap_limit': 0.02,
                'linearization_level': 1,
                'cp_model_probing_level': 1
            },
            'large': {
                'relative_gap_limit': 0.05,
                'use_lns_only': True,
                'linearization_level': 0
            }
        }
        
        for param, value in configs.get(problem_size, {}).items():
            setattr(solver.parameters, param, value)
```

### Template 2: Real-Time Optimizer

```python
class RealTimeOptimizerConfig:
    """Configuration for real-time optimization."""
    
    @staticmethod
    def configure(solver: cp_model.CpSolver,
                  response_time_ms: int = 1000):
        
        # Convert to seconds with safety margin
        time_limit = response_time_ms * 0.8 / 1000.0
        
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 4  # Less overhead
        solver.parameters.stop_after_first_solution = response_time_ms < 100
        
        # Fast heuristics
        solver.parameters.use_lns_only = True
        solver.parameters.lns_focus_on_decision_variables = True
        
        # Minimal presolve
        solver.parameters.presolve_bounded_deductions = 0
        solver.parameters.cp_model_presolve = False
```

## Best Practices

1. **Start Simple**: Use defaults, then tune based on evidence
2. **Measure Impact**: Change one parameter at a time
3. **Know Your Problem**: Different problems need different configs
4. **Set Limits**: Always set time/memory limits in production
5. **Log Progress**: Enable logging to understand behavior
6. **Test Robustness**: Try different random seeds
7. **Document Choices**: Explain why each parameter was set

## Common Mistakes

1. **Over-tuning**: Too many parameters changed at once
2. **No time limit**: Solver runs forever
3. **Ignoring logs**: Missing important feedback
4. **Wrong objective**: Optimizing wrong metric
5. **Fixed config**: Not adapting to problem size
6. **Single thread**: Not using available parallelism
7. **No monitoring**: Not tracking solver behavior

Remember: Good configuration can make 10x-100x performance difference!