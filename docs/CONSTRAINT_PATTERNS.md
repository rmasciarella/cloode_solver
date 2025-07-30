# OR-Tools CP-SAT Cookie Cutter Constraint Patterns

## Overview

This document provides proven constraint patterns for common scheduling scenarios. Each pattern has been tested for computational efficiency and solver performance.

## Basic Patterns

### 1. Machine Capacity (Cumulative Resource)
```python
def add_machine_capacity_constraints(
    model: cp_model.CpModel,
    machine_intervals: Dict[str, List[IntervalVar]],
    machine_demands: Dict[Tuple[str, str, str], IntVar],
    machines: List[Machine]
) -> None:
    """Add cumulative constraints for machine capacity.
    
    Constraints Added:
        - Sum of demands at any time <= machine capacity
        - Uses AddCumulative for efficient propagation
    """
    for machine in machines:
        if machine.capacity > 1:
            intervals = machine_intervals[machine.resource_id]
            demands = [machine_demands.get((j, t, machine.resource_id), 1) 
                      for (j, t, m) in machine_demands 
                      if m == machine.resource_id]
            
            if intervals and demands:
                model.AddCumulative(intervals, demands, machine.capacity)
```

### 2. Setup Times Between Tasks
```python
def add_setup_time_constraints(
    model: cp_model.CpModel,
    task_starts: Dict,
    task_ends: Dict,
    task_assigned: Dict,
    setup_times: Dict[Tuple[str, str], int]
) -> None:
    """Add sequence-dependent setup times.
    
    Constraints Added:
        - If task1 then task2 on same machine: start2 >= end1 + setup_time
        - Uses circuit constraint for TSP-like problems
    """
    # For each machine, track task sequences
    for machine_id in machines:
        machine_tasks = [(j, t) for (j, t, m) in task_assigned if m == machine_id]
        
        for i, task1 in enumerate(machine_tasks):
            for task2 in machine_tasks[i+1:]:
                # Both tasks on this machine?
                both_assigned = model.NewBoolVar(f'both_{task1}_{task2}_{machine_id}')
                model.Add(task_assigned[(*task1, machine_id)] == 1).OnlyEnforceIf(both_assigned)
                model.Add(task_assigned[(*task2, machine_id)] == 1).OnlyEnforceIf(both_assigned)
                
                # Setup time constraint
                setup = setup_times.get((task1[1], task2[1]), 0)
                model.Add(
                    task_starts[task2] >= task_ends[task1] + setup
                ).OnlyEnforceIf(both_assigned)
```

### 3. Time Windows (Availability)
```python
def add_time_window_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict,
    task_assigned: Dict,
    availability_windows: Dict[str, List[Tuple[int, int]]]
) -> None:
    """Constrain tasks to run within availability windows.
    
    Constraints Added:
        - Tasks must execute entirely within an availability window
        - Uses forbidden intervals for efficiency
    """
    for (job_id, task_id), interval in task_intervals.items():
        task = problem.get_task(task_id)
        
        for mode in task.modes:
            machine_id = mode.machine_resource_id
            is_assigned = task_assigned[(job_id, task_id, machine_id)]
            
            if machine_id in availability_windows:
                windows = availability_windows[machine_id]
                
                # Task must be in at least one window
                in_window_vars = []
                for start_win, end_win in windows:
                    in_window = model.NewBoolVar(f'in_window_{task_id}_{start_win}')
                    model.Add(interval.StartExpr() >= start_win).OnlyEnforceIf(in_window)
                    model.Add(interval.EndExpr() <= end_win).OnlyEnforceIf(in_window)
                    in_window_vars.append(in_window)
                
                # At least one window if assigned
                model.Add(sum(in_window_vars) >= 1).OnlyEnforceIf(is_assigned)
```

### 4. Resource Pools (Shared Tools)
```python
def add_resource_pool_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict,
    resource_requirements: Dict[str, Dict[str, int]],
    resource_capacity: Dict[str, int]
) -> None:
    """Add constraints for shared resource pools.
    
    Constraints Added:
        - Resource usage at any time <= available capacity
        - Handles multiple resource types
    """
    for resource_type, capacity in resource_capacity.items():
        # Collect all intervals needing this resource
        intervals = []
        demands = []
        
        for (job_id, task_id), interval in task_intervals.items():
            task_key = task_id
            if task_key in resource_requirements:
                if resource_type in resource_requirements[task_key]:
                    intervals.append(interval)
                    demands.append(resource_requirements[task_key][resource_type])
        
        if intervals:
            model.AddCumulative(intervals, demands, capacity)
```

### 5. Precedence with Min/Max Delays
```python
def add_precedence_delay_constraints(
    model: cp_model.CpModel,
    task_starts: Dict,
    task_ends: Dict,
    precedences_with_delays: List[Tuple[Tuple[str, str], Tuple[str, str], int, int]]
) -> None:
    """Add precedence with minimum and maximum delays.
    
    Constraints Added:
        - min_delay <= start_successor - end_predecessor <= max_delay
        - Useful for cooling times, transport, etc.
    """
    for (job1, task1), (job2, task2), min_delay, max_delay in precedences_with_delays:
        # Minimum delay
        model.Add(
            task_starts[(job2, task2)] >= task_ends[(job1, task1)] + min_delay
        )
        
        # Maximum delay (if not infinite)
        if max_delay < float('inf'):
            model.Add(
                task_starts[(job2, task2)] <= task_ends[(job1, task1)] + max_delay
            )
```

### 6. Alternative Resources (OR constraints)
```python
def add_alternative_resource_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict,
    resource_groups: Dict[str, List[str]],
    task_resource_group: Dict[str, str]
) -> None:
    """Task can use any resource from a group.
    
    Constraints Added:
        - Task must use exactly one resource from its group
        - No overlap on each individual resource
    """
    # Create optional intervals for each task-resource combination
    optional_intervals = {}  # (task, resource) -> optional interval
    
    for (job_id, task_id), base_interval in task_intervals.items():
        if task_id in task_resource_group:
            group = task_resource_group[task_id]
            resources = resource_groups[group]
            
            presence_vars = []
            for resource_id in resources:
                presence = model.NewBoolVar(f'uses_{task_id}_{resource_id}')
                presence_vars.append(presence)
                
                optional = model.NewOptionalIntervalVar(
                    base_interval.StartExpr(),
                    base_interval.SizeExpr(),
                    base_interval.EndExpr(),
                    presence,
                    f'opt_{task_id}_{resource_id}'
                )
                optional_intervals[(task_id, resource_id)] = optional
            
            # Exactly one resource
            model.AddExactlyOne(presence_vars)
```

### 7. Batch Processing
```python
def add_batch_constraints(
    model: cp_model.CpModel,
    task_starts: Dict,
    task_ends: Dict,
    batch_compatible: Dict[str, List[str]],
    batch_size: int
) -> None:
    """Group compatible tasks into batches.
    
    Constraints Added:
        - Compatible tasks in same batch start together
        - Batch size limits
    """
    # Create batch assignment variables
    batch_vars = {}  # (task, batch_id) -> bool
    
    for task_id, compatible_tasks in batch_compatible.items():
        for batch_id in range(len(compatible_tasks) // batch_size + 1):
            batch_vars[(task_id, batch_id)] = model.NewBoolVar(
                f'batch_{task_id}_{batch_id}'
            )
    
    # Tasks in same batch start together
    for batch_id in range(max_batches):
        batch_tasks = [t for t in tasks if (t, batch_id) in batch_vars]
        
        if len(batch_tasks) >= 2:
            # Same start time for all in batch
            for i in range(1, len(batch_tasks)):
                model.Add(
                    task_starts[batch_tasks[i]] == task_starts[batch_tasks[0]]
                ).OnlyEnforceIf(batch_vars[(batch_tasks[i], batch_id)])
```

### 8. Skills and Qualifications
```python
def add_skill_constraints(
    model: cp_model.CpModel,
    task_worker_assigned: Dict[Tuple[str, str, str], BoolVar],
    worker_skills: Dict[str, Set[str]],
    task_required_skills: Dict[str, Set[str]]
) -> None:
    """Ensure workers have required skills for tasks.
    
    Constraints Added:
        - Worker assigned only if has all required skills
        - Skill-based capacity limits
    """
    for (job_id, task_id), required_skills in task_required_skills.items():
        eligible_workers = []
        
        for worker_id, skills in worker_skills.items():
            if required_skills.issubset(skills):
                eligible_workers.append(worker_id)
        
        # At least one eligible worker
        assignment_vars = [
            task_worker_assigned[(job_id, task_id, w)]
            for w in eligible_workers
            if (job_id, task_id, w) in task_worker_assigned
        ]
        
        if assignment_vars:
            model.Add(sum(assignment_vars) >= 1)
```

## Advanced Patterns

### 9. Learning Curves
```python
def add_learning_curve_constraints(
    model: cp_model.CpModel,
    task_durations: Dict,
    task_sequence: Dict[str, IntVar],
    learning_factor: float = 0.9
) -> None:
    """Model duration reduction from experience.
    
    Constraints Added:
        - Duration decreases with repetition
        - Maintains minimum duration threshold
    """
    # Track task repetition count
    for task_type in task_types:
        tasks_of_type = [t for t in tasks if t.type == task_type]
        
        for i, task in enumerate(tasks_of_type):
            if i > 0:
                # Duration reduces by learning factor
                base_duration = task.base_duration
                min_duration = int(base_duration * 0.5)  # 50% minimum
                
                learned_duration = model.NewIntVar(
                    min_duration, base_duration, f'learned_{task.id}'
                )
                
                # Approximation: duration = base * (learning_factor ^ position)
                model.Add(learned_duration <= int(base_duration * (learning_factor ** i)))
                model.Add(task_durations[task.id] == learned_duration)
```

### 10. Energy/Cost Optimization
```python
def add_energy_cost_constraints(
    model: cp_model.CpModel,
    task_starts: Dict,
    task_ends: Dict,
    energy_prices: List[Tuple[int, int, float]],  # (start, end, price)
    task_energy: Dict[str, int]
) -> None:
    """Optimize for time-of-use energy costs.
    
    Constraints Added:
        - Track energy usage by time period
        - Create cost variables for optimization
    """
    total_cost = 0
    
    for (start_period, end_period, price) in energy_prices:
        period_energy = 0
        
        for (job_id, task_id), energy in task_energy.items():
            # Is task active during this period?
            active = model.NewBoolVar(f'active_{task_id}_{start_period}')
            
            model.Add(task_starts[(job_id, task_id)] < end_period).OnlyEnforceIf(active)
            model.Add(task_ends[(job_id, task_id)] > start_period).OnlyEnforceIf(active)
            
            period_energy += active * energy
        
        total_cost += period_energy * int(price * 100)  # Convert to cents
    
    return total_cost  # Can be minimized
```

## Performance Tips

### 1. Variable Bounds
Always set the tightest possible bounds:
```python
# Bad: loose bounds
start = model.NewIntVar(0, 1000000, 'start')

# Good: tight bounds based on problem
earliest = max(release_time, sum(predecessor_durations))
latest = due_date - sum(successor_durations)
start = model.NewIntVar(earliest, latest, 'start')
```

### 2. Symmetry Breaking
Add constraints to eliminate symmetric solutions:
```python
# For identical machines, order task assignments
if machine1.capacity == machine2.capacity:
    model.Add(
        sum(task_assigned[(j, t, machine1)] for j, t in tasks) >=
        sum(task_assigned[(j, t, machine2)] for j, t in tasks)
    )
```

### 3. Search Hints
Provide good starting solutions:
```python
# Based on heuristic or previous solution
for (job_id, task_id), start_value in heuristic_solution.items():
    model.AddHint(task_starts[(job_id, task_id)], start_value)
```

### 4. Redundant Constraints
Add logically redundant but computationally helpful constraints:
```python
# If A->B and B->C, add A->C for better propagation
if 'A' in pred['B'] and 'B' in pred['C']:
    model.Add(task_starts['C'] >= task_ends['A'])
```

### 5. Model Statistics
Always check model complexity:
```python
print(f"Variables: {model.NumVariables()}")
print(f"Constraints: {model.NumConstraints()}")
print(f"Boolean variables: {model.NumBooleans()}")

# If > 100k variables, consider decomposition
```

## Testing Patterns

### Unit Test Template
```python
def test_capacity_constraint():
    """Test machine capacity is respected."""
    # GIVEN: 2 tasks, machine with capacity 1
    model = cp_model.CpModel()
    intervals = [
        model.NewIntervalVar(0, 5, 10, 'task1'),
        model.NewIntervalVar(0, 5, 10, 'task2')
    ]
    
    # WHEN: Adding capacity constraint
    model.AddNoOverlap(intervals)  # Capacity 1
    
    # THEN: Tasks don't overlap
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    assert status == cp_model.OPTIMAL
    assert (solver.Value(intervals[0].EndExpr()) <= 
            solver.Value(intervals[1].StartExpr()) or
            solver.Value(intervals[1].EndExpr()) <= 
            solver.Value(intervals[0].StartExpr()))
```

## Common Mistakes to Avoid

1. **Creating too many variables**: Use optional intervals instead of separate presence variables
2. **Weak propagation**: Always prefer native CP-SAT constraints over manual implications
3. **Missing bounds**: Every integer variable should have reasonable bounds
4. **Ignoring solver warnings**: Pay attention to model validation messages
5. **Over-constraining**: Test with small instances to ensure feasibility

Remember: Start simple, validate each constraint, then add complexity incrementally!