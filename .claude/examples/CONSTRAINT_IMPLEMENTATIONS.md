# Example Constraint Implementations for OR-Tools

## Overview

Production-ready implementations of common constraints for OR-Tools CP-SAT solver. Each example includes mathematical formulation, implementation, tests, and usage patterns.

## Table of Contents

1. [Basic Scheduling Constraints](#basic-scheduling)
2. [Resource Constraints](#resource-constraints)
3. [Precedence Constraints](#precedence-constraints)
4. [Time Window Constraints](#time-window-constraints)
5. [Skill Matching Constraints](#skill-matching)
6. [Setup Time Constraints](#setup-time)
7. [Shift Constraints](#shift-constraints)
8. [Load Balancing Constraints](#load-balancing)
9. [Maintenance Window Constraints](#maintenance-windows)
10. [Complex Multi-Constraint Examples](#complex-examples)

## Basic Scheduling Constraints {#basic-scheduling}

### 1. Duration Constraints

```python
def add_duration_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    tasks: List[Task]
) -> None:
    """Ensure task end = start + duration.
    
    Mathematical formulation:
        ∀ task i: end_i = start_i + duration_i
    
    Args:
        model: CP-SAT model
        task_starts: Decision variables for task start times
        task_ends: Decision variables for task end times
        tasks: List of tasks with durations
        
    Constraints added:
        - end[i] == start[i] + duration[i] for each task
    """
    for task in tasks:
        model.Add(
            task_ends[task.id] == task_starts[task.id] + task.duration
        )

# Test
def test_duration_constraints():
    model = cp_model.CpModel()
    
    # Create variables
    task_starts = {1: model.NewIntVar(0, 100, 'start_1')}
    task_ends = {1: model.NewIntVar(0, 100, 'end_1')}
    tasks = [Task(id=1, duration=10)]
    
    # Add constraints
    add_duration_constraints(model, task_starts, task_ends, tasks)
    
    # Solve and verify
    solver = cp_model.CpSolver()
    solver.Solve(model)
    
    assert solver.Value(task_ends[1]) == solver.Value(task_starts[1]) + 10
```

### 2. No-Overlap Constraints

```python
def add_no_overlap_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict[Tuple[int, int], cp_model.IntervalVar],
    machines: List[int]
) -> None:
    """Ensure tasks don't overlap on the same machine.
    
    Mathematical formulation:
        ∀ machine m, tasks i,j on m where i≠j:
        end_i ≤ start_j ∨ end_j ≤ start_i
    
    Implementation uses efficient AddNoOverlap global constraint.
    """
    # Group intervals by machine
    machine_intervals = defaultdict(list)
    
    for (task_id, machine_id), interval in task_intervals.items():
        machine_intervals[machine_id].append(interval)
    
    # Add no-overlap for each machine
    for machine_id, intervals in machine_intervals.items():
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

# Alternative implementation with optional tasks
def add_no_overlap_with_optional_tasks(
    model: cp_model.CpModel,
    tasks: List[Task],
    machines: List[Machine]
) -> Dict:
    """No-overlap with optional task assignment."""
    intervals = {}
    
    for machine in machines:
        machine_intervals = []
        
        for task in tasks:
            # Create optional interval
            start = model.NewIntVar(0, horizon, f'start_{task.id}_{machine.id}')
            end = model.NewIntVar(0, horizon, f'end_{task.id}_{machine.id}')
            presence = model.NewBoolVar(f'presence_{task.id}_{machine.id}')
            
            interval = model.NewOptionalIntervalVar(
                start, task.duration, end, presence,
                f'interval_{task.id}_{machine.id}'
            )
            
            intervals[(task.id, machine.id)] = {
                'interval': interval,
                'start': start,
                'end': end,
                'presence': presence
            }
            
            machine_intervals.append(interval)
        
        # No overlap on each machine
        model.AddNoOverlap(machine_intervals)
    
    # Each task on exactly one machine
    for task in tasks:
        presences = [
            intervals[(task.id, m.id)]['presence']
            for m in machines
        ]
        model.AddExactlyOne(presences)
    
    return intervals
```

## Resource Constraints {#resource-constraints}

### 3. Cumulative Resource Constraints

```python
def add_cumulative_resource_constraints(
    model: cp_model.CpModel,
    task_intervals: List[cp_model.IntervalVar],
    resource_demands: List[int],
    resource_capacity: int,
    resource_name: str = "resource"
) -> None:
    """Ensure cumulative resource usage doesn't exceed capacity.
    
    Mathematical formulation:
        ∀ time t: Σ(demand_i | task i active at t) ≤ capacity
    
    Uses efficient AddCumulative global constraint.
    """
    if not task_intervals:
        return
    
    model.AddCumulative(
        intervals=task_intervals,
        demands=resource_demands,
        capacity=resource_capacity
    )

# Example: Machine power consumption limit
def add_power_consumption_constraints(
    model: cp_model.CpModel,
    tasks: List[Task],
    max_power: int
) -> None:
    """Limit total power consumption at any time."""
    intervals = []
    demands = []
    
    for task in tasks:
        # Create interval for task
        interval = model.NewIntervalVar(
            task.start_var,
            task.duration,
            task.end_var,
            f'power_interval_{task.id}'
        )
        intervals.append(interval)
        demands.append(task.power_consumption)
    
    # Add cumulative constraint
    model.AddCumulative(intervals, demands, max_power)

# Advanced: Time-varying capacity
def add_time_varying_capacity_constraints(
    model: cp_model.CpModel,
    tasks: List[Task],
    capacity_profile: List[Tuple[int, int, int]]  # (start, end, capacity)
) -> None:
    """Handle resources with time-varying capacity."""
    for start_time, end_time, capacity in capacity_profile:
        # Tasks overlapping this time window
        window_intervals = []
        window_demands = []
        
        for task in tasks:
            # Create conditional interval for this window
            overlaps = model.NewBoolVar(f'overlaps_{task.id}_{start_time}')
            
            # Task overlaps if it starts before window ends
            # and ends after window starts
            model.Add(task.start_var < end_time).OnlyEnforceIf(overlaps)
            model.Add(task.end_var > start_time).OnlyEnforceIf(overlaps)
            
            # Optional interval for overlap
            overlap_start = model.NewIntVar(start_time, end_time, f'o_start_{task.id}')
            overlap_end = model.NewIntVar(start_time, end_time, f'o_end_{task.id}')
            
            model.AddMaxEquality(overlap_start, [task.start_var, start_time])
            model.AddMinEquality(overlap_end, [task.end_var, end_time])
            
            overlap_interval = model.NewOptionalIntervalVar(
                overlap_start,
                overlap_end - overlap_start,
                overlap_end,
                overlaps,
                f'overlap_{task.id}_{start_time}'
            )
            
            window_intervals.append(overlap_interval)
            window_demands.append(task.resource_demand)
        
        # Cumulative constraint for this window
        model.AddCumulative(window_intervals, window_demands, capacity)
```

## Precedence Constraints {#precedence-constraints}

### 4. Basic and Advanced Precedence

```python
def add_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    precedences: List[Tuple[int, int]]
) -> None:
    """Add basic precedence constraints.
    
    Mathematical formulation:
        ∀ (i,j) ∈ precedences: end_i ≤ start_j
    """
    for pred_id, succ_id in precedences:
        model.Add(task_ends[pred_id] <= task_starts[succ_id])

# Advanced: Precedence with delays
def add_precedence_with_delays(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    precedences_with_delays: List[Tuple[int, int, int]]  # (pred, succ, min_delay)
) -> None:
    """Precedence with minimum delay between tasks."""
    for pred_id, succ_id, min_delay in precedences_with_delays:
        model.Add(task_starts[succ_id] >= task_ends[pred_id] + min_delay)

# Advanced: Conditional precedence
def add_conditional_precedence(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    condition: cp_model.BoolVar,
    pred_id: int,
    succ_id: int
) -> None:
    """Precedence that only applies if condition is true."""
    # If condition is true, enforce precedence
    model.Add(
        task_starts[succ_id] >= task_ends[pred_id]
    ).OnlyEnforceIf(condition)
    
    # If condition is false, tasks can be in any order
    # (no constraint needed)

# Example: Precedence chains with critical path
def add_precedence_chains_with_critical_path(
    model: cp_model.CpModel,
    chains: List[List[int]],
    task_starts: Dict[int, cp_model.IntVar],
    task_durations: Dict[int, int]
) -> cp_model.IntVar:
    """Add precedence chains and return makespan variable."""
    makespan = model.NewIntVar(0, horizon, 'makespan')
    
    for chain in chains:
        # Add precedences within chain
        for i in range(len(chain) - 1):
            pred = chain[i]
            succ = chain[i + 1]
            
            model.Add(
                task_starts[succ] >= task_starts[pred] + task_durations[pred]
            )
        
        # Chain completion time
        last_task = chain[-1]
        chain_end = task_starts[last_task] + task_durations[last_task]
        
        # Update makespan
        model.Add(makespan >= chain_end)
    
    return makespan
```

## Time Window Constraints {#time-window-constraints}

### 5. Task Time Windows

```python
def add_time_window_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    time_windows: Dict[int, Tuple[int, int]]
) -> None:
    """Ensure tasks execute within their time windows.
    
    Mathematical formulation:
        ∀ task i with window [early_i, late_i]:
        early_i ≤ start_i ∧ end_i ≤ late_i
    """
    for task_id, (earliest_start, latest_end) in time_windows.items():
        model.Add(task_starts[task_id] >= earliest_start)
        model.Add(task_ends[task_id] <= latest_end)

# Advanced: Soft time windows with penalties
def add_soft_time_windows(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    preferred_windows: Dict[int, Tuple[int, int]],
    penalty_per_unit: int = 1
) -> cp_model.IntVar:
    """Soft time windows with penalties for violations."""
    total_penalty = []
    
    for task_id, (pref_start, pref_end) in preferred_windows.items():
        # Early start penalty
        early_penalty = model.NewIntVar(0, horizon * penalty_per_unit, f'early_pen_{task_id}')
        model.AddMaxEquality(
            early_penalty,
            [0, (pref_start - task_starts[task_id]) * penalty_per_unit]
        )
        
        # Late end penalty  
        late_penalty = model.NewIntVar(0, horizon * penalty_per_unit, f'late_pen_{task_id}')
        model.AddMaxEquality(
            late_penalty,
            [0, (task_ends[task_id] - pref_end) * penalty_per_unit]
        )
        
        total_penalty.extend([early_penalty, late_penalty])
    
    # Return total penalty to minimize
    penalty_var = model.NewIntVar(0, horizon * penalty_per_unit * len(preferred_windows) * 2, 'total_penalty')
    model.Add(penalty_var == sum(total_penalty))
    
    return penalty_var

# Example: Business hours constraints
def add_business_hours_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[int, cp_model.IntVar],
    task_ends: Dict[int, cp_model.IntVar],
    business_hours: List[Tuple[int, int]],  # List of (start, end) for each day
    tasks_requiring_business_hours: List[int]
) -> None:
    """Ensure certain tasks only execute during business hours."""
    for task_id in tasks_requiring_business_hours:
        # Task must be within at least one business hour window
        within_hours = []
        
        for day_start, day_end in business_hours:
            in_this_window = model.NewBoolVar(f'in_window_{task_id}_{day_start}')
            
            # Task completely within this window
            model.Add(task_starts[task_id] >= day_start).OnlyEnforceIf(in_this_window)
            model.Add(task_ends[task_id] <= day_end).OnlyEnforceIf(in_this_window)
            
            within_hours.append(in_this_window)
        
        # Must be in at least one window
        model.AddBoolOr(within_hours)
```

## Skill Matching Constraints {#skill-matching}

### 6. Skill-Based Assignment

```python
def add_skill_matching_constraints(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int], cp_model.BoolVar],
    task_skills: Dict[int, Set[str]],
    machine_skills: Dict[int, Set[str]]
) -> None:
    """Ensure tasks are only assigned to machines with required skills.
    
    Mathematical formulation:
        ∀ task i, machine j:
        assigned[i,j] = 1 → skills[i] ⊆ skills[j]
    """
    for (task_id, machine_id), assign_var in task_assigned.items():
        required_skills = task_skills.get(task_id, set())
        available_skills = machine_skills.get(machine_id, set())
        
        # If machine lacks any required skill, cannot assign
        if not required_skills.issubset(available_skills):
            model.Add(assign_var == 0)

# Advanced: Skill levels
def add_skill_level_constraints(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int], cp_model.BoolVar],
    task_skill_requirements: Dict[int, Dict[str, int]],  # skill -> min level
    worker_skill_levels: Dict[int, Dict[str, int]]  # skill -> level
) -> None:
    """Match tasks to workers based on skill levels."""
    for (task_id, worker_id), assign_var in task_assigned.items():
        requirements = task_skill_requirements.get(task_id, {})
        worker_skills = worker_skill_levels.get(worker_id, {})
        
        # Check each required skill
        can_assign = True
        for skill, min_level in requirements.items():
            worker_level = worker_skills.get(skill, 0)
            if worker_level < min_level:
                can_assign = False
                break
        
        if not can_assign:
            model.Add(assign_var == 0)

# Example: Multi-skill with preferences
def add_skill_preference_objective(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int], cp_model.BoolVar],
    skill_preferences: Dict[Tuple[int, int], int]  # (task, worker) -> preference score
) -> cp_model.IntVar:
    """Maximize skill preference scores."""
    preference_terms = []
    
    for (task_id, worker_id), assign_var in task_assigned.items():
        preference = skill_preferences.get((task_id, worker_id), 0)
        if preference > 0:
            # Add preference * assignment to objective
            preference_terms.append(preference * assign_var)
    
    total_preference = model.NewIntVar(0, 1000000, 'total_preference')
    model.Add(total_preference == sum(preference_terms))
    
    return total_preference
```

## Setup Time Constraints {#setup-time}

### 7. Sequence-Dependent Setup Times

```python
def add_setup_time_constraints(
    model: cp_model.CpModel,
    tasks: List[Task],
    machines: List[Machine],
    setup_times: Dict[Tuple[int, int], int]  # (task_type_i, task_type_j) -> time
) -> None:
    """Add sequence-dependent setup times between tasks.
    
    Complex constraint using circuit variables and intervals.
    """
    for machine in machines:
        machine_tasks = [t for t in tasks if t.machine_id == machine.id]
        
        if len(machine_tasks) <= 1:
            continue
        
        # Create circuit for task sequencing
        arcs = []
        
        # Start node (0) to tasks
        for i, task in enumerate(machine_tasks, 1):
            arc = model.NewBoolVar(f'start_to_{task.id}')
            arcs.append((0, i, arc))
        
        # Task to task arcs
        for i, task1 in enumerate(machine_tasks, 1):
            for j, task2 in enumerate(machine_tasks, 1):
                if i != j:
                    arc = model.NewBoolVar(f'arc_{task1.id}_to_{task2.id}')
                    arcs.append((i, j, arc))
                    
                    # If arc is selected, add setup time
                    setup = setup_times.get(
                        (task1.task_type, task2.task_type), 0
                    )
                    model.Add(
                        task2.start_var >= task1.end_var + setup
                    ).OnlyEnforceIf(arc)
        
        # Tasks to end node
        for i, task in enumerate(machine_tasks, 1):
            arc = model.NewBoolVar(f'{task.id}_to_end')
            arcs.append((i, len(machine_tasks) + 1, arc))
        
        # Add circuit constraint
        model.AddCircuit(arcs)

# Simplified: Setup times with direct precedence
def add_simple_setup_times(
    model: cp_model.CpModel,
    task_sequences: List[Tuple[int, int]],  # Known sequences
    task_ends: Dict[int, cp_model.IntVar],
    task_starts: Dict[int, cp_model.IntVar],
    setup_matrix: Dict[Tuple[str, str], int]
) -> None:
    """Add setup times for known task sequences."""
    for pred_id, succ_id in task_sequences:
        pred_type = get_task_type(pred_id)
        succ_type = get_task_type(succ_id)
        
        setup_time = setup_matrix.get((pred_type, succ_type), 0)
        
        # Successor must start after predecessor ends + setup
        model.Add(
            task_starts[succ_id] >= task_ends[pred_id] + setup_time
        )
```

## Shift Constraints {#shift-constraints}

### 8. Worker Shift Patterns

```python
def add_shift_constraints(
    model: cp_model.CpModel,
    worker_tasks: Dict[int, List[cp_model.IntervalVar]],
    shifts: Dict[int, List[Tuple[int, int]]],  # worker -> [(start, end), ...]
) -> None:
    """Ensure workers only work during their shifts.
    
    Uses forbidden assignments approach.
    """
    for worker_id, task_intervals in worker_tasks.items():
        worker_shifts = shifts.get(worker_id, [])
        
        if not worker_shifts:
            continue
        
        for interval in task_intervals:
            # Task must be within at least one shift
            within_shift = []
            
            for shift_start, shift_end in worker_shifts:
                in_shift = model.NewBoolVar(
                    f'task_{interval.Name()}_in_shift_{shift_start}'
                )
                
                # Get start and end expressions for interval
                start_expr = interval.StartExpr()
                end_expr = interval.EndExpr()
                
                # Task within shift
                model.Add(start_expr >= shift_start).OnlyEnforceIf(in_shift)
                model.Add(end_expr <= shift_end).OnlyEnforceIf(in_shift)
                
                within_shift.append(in_shift)
            
            # Must be in some shift
            model.AddBoolOr(within_shift).OnlyEnforceIf(interval.PresenceBoolVar())

# Advanced: Shift patterns with overtime
def add_shift_with_overtime(
    model: cp_model.CpModel,
    worker_id: int,
    regular_hours: int,
    max_overtime: int,
    tasks: List[Task],
    hourly_rate: int,
    overtime_multiplier: float = 1.5
) -> cp_model.IntVar:
    """Track regular and overtime hours with costs."""
    # Calculate total work hours
    total_hours = model.NewIntVar(0, regular_hours + max_overtime, f'total_hours_{worker_id}')
    
    task_durations = [
        task.duration * task_assigned[(task.id, worker_id)]
        for task in tasks
        if (task.id, worker_id) in task_assigned
    ]
    
    model.Add(total_hours == sum(task_durations))
    
    # Split into regular and overtime
    regular_worked = model.NewIntVar(0, regular_hours, f'regular_{worker_id}')
    overtime_worked = model.NewIntVar(0, max_overtime, f'overtime_{worker_id}')
    
    model.AddMinEquality(regular_worked, [total_hours, regular_hours])
    model.Add(overtime_worked == total_hours - regular_worked)
    
    # Calculate cost
    regular_cost = regular_worked * hourly_rate
    overtime_cost = overtime_worked * int(hourly_rate * overtime_multiplier)
    
    total_cost = model.NewIntVar(0, 1000000, f'labor_cost_{worker_id}')
    model.Add(total_cost == regular_cost + overtime_cost)
    
    return total_cost
```

## Load Balancing Constraints {#load-balancing}

### 9. Resource Load Balancing

```python
def add_load_balancing_constraints(
    model: cp_model.CpModel,
    machine_loads: Dict[int, cp_model.IntVar],
    balance_factor: float = 0.2
) -> None:
    """Balance load across machines within tolerance.
    
    Mathematical formulation:
        ∀ machines i,j: |load_i - load_j| ≤ balance_factor * average_load
    """
    if len(machine_loads) < 2:
        return
    
    # Calculate average load
    total_load = sum(machine_loads.values())
    num_machines = len(machine_loads)
    avg_load = total_load // num_machines
    
    # Maximum allowed deviation
    max_deviation = int(avg_load * balance_factor)
    
    # Pairwise balance constraints
    machine_ids = list(machine_loads.keys())
    for i in range(len(machine_ids)):
        for j in range(i + 1, len(machine_ids)):
            m1, m2 = machine_ids[i], machine_ids[j]
            
            # |load_m1 - load_m2| <= max_deviation
            diff = model.NewIntVar(-max_deviation, max_deviation, f'diff_{m1}_{m2}')
            model.Add(diff == machine_loads[m1] - machine_loads[m2])

# Advanced: Multi-objective balancing
def add_multi_criteria_balancing(
    model: cp_model.CpModel,
    resources: Dict[str, Dict[int, cp_model.IntVar]]  # resource_type -> machine -> load
) -> Dict[str, cp_model.IntVar]:
    """Balance multiple resource types simultaneously."""
    balance_objectives = {}
    
    for resource_type, machine_loads in resources.items():
        if len(machine_loads) < 2:
            continue
        
        # Calculate load variance for this resource
        loads = list(machine_loads.values())
        mean_load = sum(loads) // len(loads)
        
        # Minimize maximum deviation from mean
        max_deviation = model.NewIntVar(0, horizon, f'max_dev_{resource_type}')
        
        for machine_id, load in machine_loads.items():
            deviation = model.NewIntVar(0, horizon, f'dev_{resource_type}_{machine_id}')
            
            # deviation = |load - mean|
            diff = model.NewIntVar(-horizon, horizon, f'diff_{resource_type}_{machine_id}')
            model.Add(diff == load - mean_load)
            model.AddAbsEquality(deviation, diff)
            
            # Track maximum
            model.Add(max_deviation >= deviation)
        
        balance_objectives[resource_type] = max_deviation
    
    return balance_objectives

# Example: Fair workload distribution
def add_fairness_constraints(
    model: cp_model.CpModel,
    worker_assignments: Dict[Tuple[int, int], cp_model.BoolVar],
    task_values: Dict[int, int],  # task -> value/difficulty
    num_workers: int
) -> cp_model.IntVar:
    """Ensure fair distribution of valuable/difficult tasks."""
    worker_values = {}
    
    for worker_id in range(num_workers):
        # Sum of task values for this worker
        worker_total = []
        
        for (task_id, w_id), assign_var in worker_assignments.items():
            if w_id == worker_id:
                value = task_values.get(task_id, 1)
                worker_total.append(value * assign_var)
        
        worker_value = model.NewIntVar(0, 100000, f'worker_value_{worker_id}')
        model.Add(worker_value == sum(worker_total))
        worker_values[worker_id] = worker_value
    
    # Minimize difference between max and min
    min_value = model.NewIntVar(0, 100000, 'min_worker_value')
    max_value = model.NewIntVar(0, 100000, 'max_worker_value')
    
    model.AddMinEquality(min_value, list(worker_values.values()))
    model.AddMaxEquality(max_value, list(worker_values.values()))
    
    fairness_gap = model.NewIntVar(0, 100000, 'fairness_gap')
    model.Add(fairness_gap == max_value - min_value)
    
    return fairness_gap
```

## Maintenance Window Constraints {#maintenance-windows}

### 10. Equipment Maintenance Windows

```python
def add_maintenance_window_constraints(
    model: cp_model.CpModel,
    machine_tasks: Dict[int, List[cp_model.IntervalVar]],
    maintenance_windows: Dict[int, List[Tuple[int, int]]]  # machine -> [(start, end), ...]
) -> None:
    """Ensure no tasks scheduled during maintenance windows.
    
    Uses forbidden intervals approach.
    """
    for machine_id, task_intervals in machine_tasks.items():
        windows = maintenance_windows.get(machine_id, [])
        
        for maint_start, maint_end in windows:
            # Create maintenance interval
            maint_interval = model.NewFixedSizeIntervalVar(
                maint_start,
                maint_end - maint_start,
                f'maintenance_{machine_id}_{maint_start}'
            )
            
            # No task can overlap with maintenance
            all_intervals = task_intervals + [maint_interval]
            model.AddNoOverlap(all_intervals)

# Advanced: Flexible maintenance scheduling
def add_flexible_maintenance(
    model: cp_model.CpModel,
    machine_id: int,
    maintenance_duration: int,
    earliest_start: int,
    latest_start: int,
    task_intervals: List[cp_model.IntervalVar]
) -> cp_model.IntervalVar:
    """Schedule maintenance flexibly within time window."""
    # Maintenance start time is a decision variable
    maint_start = model.NewIntVar(
        earliest_start,
        latest_start,
        f'maint_start_{machine_id}'
    )
    
    # Create maintenance interval
    maint_interval = model.NewIntervalVar(
        maint_start,
        maintenance_duration,
        maint_start + maintenance_duration,
        f'maintenance_{machine_id}'
    )
    
    # No overlap with tasks
    model.AddNoOverlap(task_intervals + [maint_interval])
    
    return maint_interval

# Example: Preventive maintenance with wear tracking
def add_wear_based_maintenance(
    model: cp_model.CpModel,
    machine_tasks: Dict[int, List[Task]],
    wear_rates: Dict[str, int],  # task_type -> wear units
    maintenance_threshold: int,
    maintenance_duration: int
) -> Dict[int, List[cp_model.IntervalVar]]:
    """Schedule maintenance based on cumulative wear."""
    maintenance_intervals = {}
    
    for machine_id, tasks in machine_tasks.items():
        # Track cumulative wear
        cumulative_wear = 0
        maintenance_points = []
        
        # Sort tasks by start time (approximate)
        tasks.sort(key=lambda t: t.earliest_start)
        
        for i, task in enumerate(tasks):
            wear = wear_rates.get(task.task_type, 1)
            cumulative_wear += wear
            
            if cumulative_wear >= maintenance_threshold:
                # Need maintenance after this task
                maintenance_points.append(i)
                cumulative_wear = 0
        
        # Create maintenance intervals
        machine_maintenance = []
        for point in maintenance_points:
            if point < len(tasks) - 1:
                # Maintenance between tasks[point] and tasks[point+1]
                maint_start = model.NewIntVar(
                    tasks[point].end_var,
                    tasks[point + 1].start_var - maintenance_duration,
                    f'maint_start_{machine_id}_{point}'
                )
                
                maint_interval = model.NewIntervalVar(
                    maint_start,
                    maintenance_duration,
                    maint_start + maintenance_duration,
                    f'maintenance_{machine_id}_{point}'
                )
                
                machine_maintenance.append(maint_interval)
        
        maintenance_intervals[machine_id] = machine_maintenance
    
    return maintenance_intervals
```

## Complex Multi-Constraint Examples {#complex-examples}

### 11. Integrated Job Shop with Multiple Constraints

```python
class JobShopScheduler:
    """Complete job shop scheduler with multiple constraint types."""
    
    def __init__(self, horizon: int):
        self.model = cp_model.CpModel()
        self.horizon = horizon
        self.variables = {}
    
    def build_model(self, problem: JobShopProblem) -> None:
        """Build complete model with all constraints."""
        # Create variables
        self.create_variables(problem)
        
        # Add constraints in order of importance
        self.add_duration_constraints(problem)
        self.add_precedence_constraints(problem)
        self.add_no_overlap_constraints(problem)
        self.add_resource_constraints(problem)
        self.add_time_window_constraints(problem)
        self.add_skill_constraints(problem)
        self.add_setup_time_constraints(problem)
        self.add_maintenance_constraints(problem)
        
        # Add objective
        self.add_objective(problem)
    
    def create_variables(self, problem: JobShopProblem) -> None:
        """Create all decision variables."""
        # Task timing variables
        for job in problem.jobs:
            for task in job.tasks:
                # Start time
                earliest = task.earliest_start if hasattr(task, 'earliest_start') else 0
                latest = task.latest_start if hasattr(task, 'latest_start') else self.horizon
                
                start = self.model.NewIntVar(earliest, latest, f'start_{job.id}_{task.id}')
                self.variables[('start', job.id, task.id)] = start
                
                # End time (computed from start + duration)
                end = self.model.NewIntVar(
                    earliest + task.duration,
                    min(latest + task.duration, self.horizon),
                    f'end_{job.id}_{task.id}'
                )
                self.variables[('end', job.id, task.id)] = end
                
                # Machine assignment (if not pre-assigned)
                if not task.assigned_machine:
                    for machine in problem.machines:
                        if self.can_assign(task, machine):
                            assign = self.model.NewBoolVar(
                                f'assign_{job.id}_{task.id}_{machine.id}'
                            )
                            self.variables[('assign', job.id, task.id, machine.id)] = assign
    
    def add_duration_constraints(self, problem: JobShopProblem) -> None:
        """Add task duration constraints."""
        for job in problem.jobs:
            for task in job.tasks:
                start = self.variables[('start', job.id, task.id)]
                end = self.variables[('end', job.id, task.id)]
                
                self.model.Add(end == start + task.duration)
    
    def add_no_overlap_constraints(self, problem: JobShopProblem) -> None:
        """Add no-overlap on machines using intervals."""
        # Group intervals by machine
        machine_intervals = defaultdict(list)
        
        for job in problem.jobs:
            for task in job.tasks:
                start = self.variables[('start', job.id, task.id)]
                end = self.variables[('end', job.id, task.id)]
                
                if task.assigned_machine:
                    # Fixed assignment
                    interval = self.model.NewIntervalVar(
                        start, task.duration, end,
                        f'interval_{job.id}_{task.id}'
                    )
                    machine_intervals[task.assigned_machine].append(interval)
                else:
                    # Flexible assignment
                    for machine in problem.machines:
                        key = ('assign', job.id, task.id, machine.id)
                        if key in self.variables:
                            presence = self.variables[key]
                            interval = self.model.NewOptionalIntervalVar(
                                start, task.duration, end, presence,
                                f'interval_{job.id}_{task.id}_{machine.id}'
                            )
                            machine_intervals[machine.id].append(interval)
        
        # Add no-overlap for each machine
        for machine_id, intervals in machine_intervals.items():
            if len(intervals) > 1:
                self.model.AddNoOverlap(intervals)
    
    def solve(self, time_limit: int = 300) -> Optional[Solution]:
        """Solve the model."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.log_search_progress = True
        
        # Add search strategy
        self.add_search_strategy()
        
        status = solver.Solve(self.model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self.extract_solution(solver)
        
        return None

# Example usage
def solve_complex_job_shop():
    problem = JobShopProblem()
    # ... load problem data ...
    
    scheduler = JobShopScheduler(horizon=1000)
    scheduler.build_model(problem)
    
    solution = scheduler.solve(time_limit=60)
    if solution:
        print(f"Makespan: {solution.makespan}")
        visualize_solution(solution)
    else:
        print("No solution found")
```

## Best Practices

1. **Start Simple**: Implement basic constraints first, then add complexity
2. **Use Global Constraints**: Prefer AddNoOverlap, AddCumulative over manual implementation
3. **Tight Bounds**: Always use the tightest possible variable bounds
4. **Test Incrementally**: Test each constraint type in isolation first
5. **Profile Performance**: Measure which constraints take most time
6. **Document Formulations**: Include mathematical formulation in docstrings

## Testing Template

```python
def test_constraint_implementation():
    """Template for testing constraint implementations."""
    # 1. Create minimal model
    model = cp_model.CpModel()
    
    # 2. Add variables
    variables = create_test_variables(model)
    
    # 3. Add constraint to test
    add_constraint_under_test(model, variables)
    
    # 4. Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    # 5. Verify constraint is satisfied
    assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    verify_constraint_satisfied(solver, variables)
    
    # 6. Test edge cases
    test_edge_cases(model, variables)
```

This comprehensive set of constraint implementations provides a solid foundation for building complex OR-Tools scheduling models!