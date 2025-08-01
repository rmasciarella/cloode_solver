# Memory Management Best Practices for OR-Tools

## Overview

Efficient memory management is crucial for solving large-scale optimization problems with OR-Tools. This guide covers strategies to minimize memory usage, prevent memory leaks, and handle memory-constrained environments.

## Memory Usage Breakdown

```
┌─────────────────────────────────────────────┐
│         OR-Tools Memory Components          │
├──────────┬───────────┬──────────┬──────────┤
│Variables │Constraints│  Search  │ Solution │
│  (40%)   │   (30%)   │  State   │ Storage  │
│          │           │  (20%)   │  (10%)   │
└──────────┴───────────┴──────────┴──────────┘
```

## Memory-Efficient Model Building

### 1. Minimize Variable Creation

```python
# ❌ BAD: Creating unnecessary variables
class InefficientModel:
    def build(self, tasks, machines):
        # Creates n² boolean variables even if most are impossible
        self.assignments = {}
        for task in tasks:
            for machine in machines:
                self.assignments[(task.id, machine.id)] = model.NewBoolVar(
                    f'assign_{task.id}_{machine.id}'
                )

# ✅ GOOD: Create only necessary variables
class EfficientModel:
    def build(self, tasks, machines):
        # Only create variables for valid assignments
        self.assignments = {}
        for task in tasks:
            valid_machines = self.get_valid_machines(task)
            for machine in valid_machines:
                self.assignments[(task.id, machine.id)] = model.NewBoolVar(
                    f'assign_{task.id}_{machine.id}'
                )
    
    def get_valid_machines(self, task):
        """Return only machines that can handle this task."""
        return [m for m in machines if task.skills <= m.skills]
```

### 2. Use Integer Variables Efficiently

```python
# ❌ BAD: Wide domains consume memory
start_time = model.NewIntVar(0, 1000000, 'start')  # 1M values!

# ✅ GOOD: Tight bounds reduce memory
earliest = max(0, task.release_time)
latest = min(horizon - task.duration, task.deadline - task.duration)
start_time = model.NewIntVar(earliest, latest, 'start')

# ✅ BETTER: Reuse variables when possible
class VariablePool:
    """Reuse variables with identical domains."""
    def __init__(self, model):
        self.model = model
        self.pool = {}
    
    def get_bool_var(self, name):
        key = 'bool'
        if key not in self.pool:
            self.pool[key] = []
        
        if self.pool[key]:
            return self.pool[key].pop()
        
        return self.model.NewBoolVar(name)
    
    def return_var(self, var):
        """Return variable to pool for reuse."""
        # Only for temporary variables
        self.pool['bool'].append(var)
```

### 3. Avoid Intermediate Variables

```python
# ❌ BAD: Intermediate variables for expressions
class InefficientObjective:
    def add_makespan_objective(self, model, task_ends):
        # Creates new variable for each max operation
        makespan = model.NewIntVar(0, horizon, 'makespan')
        for task_end in task_ends.values():
            is_max = model.NewBoolVar(f'is_max_{task_end}')
            model.Add(makespan >= task_end).OnlyEnforceIf(is_max)
        
        model.Minimize(makespan)

# ✅ GOOD: Use built-in max operation
class EfficientObjective:
    def add_makespan_objective(self, model, task_ends):
        # No intermediate variables needed
        model.Minimize(max(task_ends.values()))
```

## Memory-Efficient Constraint Patterns

### 1. Circuit and Path Constraints

```python
# ❌ BAD: Explicit next/prev variables for routing
class InefficientRouting:
    def build_routing(self, model, locations):
        n = len(locations)
        # O(n²) variables for next pointers
        self.next_location = {}
        for i in range(n):
            for j in range(n):
                if i != j:
                    self.next_location[(i, j)] = model.NewBoolVar(f'next_{i}_{j}')
        
        # Many constraints to ensure valid path
        # ...

# ✅ GOOD: Use AddCircuit constraint
class EfficientRouting:
    def build_routing(self, model, locations):
        # Only create arcs that make sense
        arcs = []
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations):
                if i != j and self.is_feasible_arc(loc1, loc2):
                    lit = model.NewBoolVar(f'arc_{i}_{j}')
                    arcs.append((i, j, lit))
        
        # Single efficient constraint
        model.AddCircuit(arcs)
```

### 2. Cumulative Constraints

```python
# ❌ BAD: Manual resource tracking over time
class InefficientResource:
    def track_resource_usage(self, model, tasks, capacity, horizon):
        # Variable for each time point!
        usage = {}
        for t in range(horizon):
            usage[t] = model.NewIntVar(0, capacity, f'usage_{t}')
            
            # Sum all tasks active at time t
            active_tasks = []
            for task in tasks:
                is_active = model.NewBoolVar(f'active_{task.id}_{t}')
                model.Add(task.start <= t).OnlyEnforceIf(is_active)
                model.Add(task.end > t).OnlyEnforceIf(is_active)
                active_tasks.append(is_active * task.resource_need)
            
            model.Add(usage[t] == sum(active_tasks))
            model.Add(usage[t] <= capacity)

# ✅ GOOD: Use AddCumulative constraint  
class EfficientResource:
    def track_resource_usage(self, model, tasks, capacity):
        intervals = []
        demands = []
        
        for task in tasks:
            interval = model.NewIntervalVar(
                task.start, task.duration, task.end, f'task_{task.id}'
            )
            intervals.append(interval)
            demands.append(task.resource_need)
        
        # Single constraint handles everything
        model.AddCumulative(intervals, demands, capacity)
```

## Lazy Model Building

### 1. On-Demand Variable Creation

```python
class LazyModelBuilder:
    """Create model components only when needed."""
    
    def __init__(self, model):
        self.model = model
        self._task_starts = {}
        self._task_ends = {}
        self._intervals = {}
    
    @property
    def task_starts(self):
        """Create start variables on first access."""
        if not self._task_starts:
            self._create_timing_variables()
        return self._task_starts
    
    def _create_timing_variables(self):
        """Create all timing variables at once."""
        for task in self.problem.tasks:
            start = self.model.NewIntVar(
                task.earliest_start,
                task.latest_start,
                f'start_{task.id}'
            )
            self._task_starts[task.id] = start
```

### 2. Constraint Batching

```python
class ConstraintBatcher:
    """Batch constraints to reduce memory fragmentation."""
    
    def __init__(self, model, batch_size=1000):
        self.model = model
        self.batch_size = batch_size
        self.pending_constraints = []
    
    def add_constraint(self, constraint_expr):
        """Queue constraint for batch addition."""
        self.pending_constraints.append(constraint_expr)
        
        if len(self.pending_constraints) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Add all pending constraints."""
        for constraint in self.pending_constraints:
            self.model.Add(constraint)
        self.pending_constraints = []
```

## Memory Monitoring and Profiling

### 1. Memory Usage Tracking

```python
import psutil
import gc
import os

class MemoryMonitor:
    """Monitor memory usage during model building and solving."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.checkpoints = []
    
    def checkpoint(self, label):
        """Record memory usage at checkpoint."""
        gc.collect()  # Force garbage collection
        mem_info = self.process.memory_info()
        
        self.checkpoints.append({
            'label': label,
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        })
        
        print(f"{label}: {mem_info.rss / 1024 / 1024:.1f} MB")
    
    def report(self):
        """Generate memory usage report."""
        print("\nMemory Usage Report:")
        print("-" * 50)
        
        for i, checkpoint in enumerate(self.checkpoints):
            print(f"{checkpoint['label']:30} {checkpoint['rss_mb']:8.1f} MB")
            
            if i > 0:
                delta = checkpoint['rss_mb'] - self.checkpoints[i-1]['rss_mb']
                print(f"  Delta: {delta:+.1f} MB")

# Usage
monitor = MemoryMonitor()
monitor.checkpoint("Start")

model = cp_model.CpModel()
monitor.checkpoint("Model created")

# Build model...
add_variables(model)
monitor.checkpoint("Variables added")

add_constraints(model)
monitor.checkpoint("Constraints added")

solver = cp_model.CpSolver()
monitor.checkpoint("Solver created")

status = solver.Solve(model)
monitor.checkpoint("Solve complete")

monitor.report()
```

### 2. Memory Leak Detection

```python
class MemoryLeakDetector:
    """Detect memory leaks in iterative solving."""
    
    def __init__(self, threshold_mb=100):
        self.threshold_mb = threshold_mb
        self.initial_memory = None
    
    def check_for_leak(self, iteration):
        """Check if memory is growing suspiciously."""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        if self.initial_memory is None:
            self.initial_memory = current_memory
            return False
        
        growth = current_memory - self.initial_memory
        
        if growth > self.threshold_mb:
            print(f"WARNING: Memory grew by {growth:.1f} MB after {iteration} iterations")
            return True
        
        return False

# Usage in iterative solving
detector = MemoryLeakDetector()

for i in range(100):
    model = cp_model.CpModel()
    # ... build and solve model ...
    
    if detector.check_for_leak(i):
        # Take corrective action
        gc.collect()
        # Maybe reduce problem size
```

## Large Problem Strategies

### 1. Streaming Model Building

```python
class StreamingModelBuilder:
    """Build model in chunks to handle huge problems."""
    
    def build_large_model(self, task_file, chunk_size=10000):
        model = cp_model.CpModel()
        task_starts = {}
        
        # Process tasks in chunks
        with open(task_file, 'r') as f:
            chunk = []
            for line in f:
                task = parse_task(line)
                chunk.append(task)
                
                if len(chunk) >= chunk_size:
                    self.process_chunk(model, chunk, task_starts)
                    chunk = []
            
            # Process remaining
            if chunk:
                self.process_chunk(model, chunk, task_starts)
        
        return model, task_starts
    
    def process_chunk(self, model, tasks, task_starts):
        """Process a chunk of tasks."""
        for task in tasks:
            # Create variables for this chunk
            start = model.NewIntVar(0, horizon, f'start_{task.id}')
            task_starts[task.id] = start
        
        # Add constraints for this chunk
        # ...
        
        # Clear chunk from memory
        tasks.clear()
```

### 2. Model Decomposition

```python
class DecomposedSolver:
    """Solve large problems by decomposition."""
    
    def solve_by_decomposition(self, problem, max_size=1000):
        """Decompose if problem too large."""
        if len(problem.tasks) <= max_size:
            return self.solve_directly(problem)
        
        # Decompose into subproblems
        subproblems = self.decompose(problem, max_size)
        solutions = []
        
        for i, subproblem in enumerate(subproblems):
            print(f"Solving subproblem {i+1}/{len(subproblems)}")
            
            # Solve with memory limit
            solution = self.solve_with_memory_limit(
                subproblem,
                memory_limit_mb=2000
            )
            solutions.append(solution)
            
            # Free memory
            del subproblem
            gc.collect()
        
        # Merge solutions
        return self.merge_solutions(solutions, problem)
    
    def solve_with_memory_limit(self, problem, memory_limit_mb):
        """Solve with memory constraint."""
        model = cp_model.CpModel()
        
        # Monitor memory during build
        monitor = MemoryMonitor()
        
        # Build model with checks
        variables = self.create_variables(model, problem)
        if monitor.get_current_memory() > memory_limit_mb * 0.5:
            print("Warning: Model building using significant memory")
        
        self.add_constraints(model, variables, problem)
        if monitor.get_current_memory() > memory_limit_mb * 0.8:
            print("Warning: Approaching memory limit")
            # Consider simplifying model
        
        # Solve with limits
        solver = cp_model.CpSolver()
        solver.parameters.max_memory_in_mb = memory_limit_mb
        
        return solver.Solve(model)
```

## Memory-Efficient Data Structures

### 1. Sparse Representations

```python
from collections import defaultdict

class SparseTaskAssignment:
    """Memory-efficient sparse assignment tracking."""
    
    def __init__(self):
        # Only store actual assignments, not all possibilities
        self.assignments = defaultdict(list)  # machine -> [tasks]
        self.task_to_machine = {}  # task -> machine
    
    def assign(self, task_id, machine_id):
        """Assign task to machine."""
        self.assignments[machine_id].append(task_id)
        self.task_to_machine[task_id] = machine_id
    
    def get_machine_load(self, machine_id):
        """Get tasks assigned to machine."""
        return self.assignments.get(machine_id, [])
    
    def memory_usage(self):
        """Estimate memory usage in bytes."""
        # Much less than n*m matrix
        return (
            len(self.assignments) * 64 +  # dict overhead
            len(self.task_to_machine) * 32  # mapping overhead
        )
```

### 2. Bit Packing

```python
class BitPackedSchedule:
    """Pack boolean scheduling decisions into bits."""
    
    def __init__(self, num_tasks, num_time_slots):
        # Instead of num_tasks * num_time_slots booleans
        # Use bit array
        self.rows = num_tasks
        self.cols = num_time_slots
        self.bits_per_row = (num_time_slots + 63) // 64
        self.data = [0] * (num_tasks * self.bits_per_row)
    
    def set_active(self, task, time):
        """Mark task active at time."""
        row = task * self.bits_per_row
        bit_index = time
        word_index = row + bit_index // 64
        bit_offset = bit_index % 64
        
        self.data[word_index] |= (1 << bit_offset)
    
    def is_active(self, task, time):
        """Check if task active at time."""
        row = task * self.bits_per_row
        bit_index = time
        word_index = row + bit_index // 64
        bit_offset = bit_index % 64
        
        return bool(self.data[word_index] & (1 << bit_offset))
    
    def memory_usage_bytes(self):
        """Memory usage in bytes."""
        return len(self.data) * 8  # 8 bytes per int64
```

## Best Practices Summary

### DO's ✅

1. **Set tight variable bounds** - Reduces domain storage
2. **Use built-in global constraints** - More memory efficient
3. **Create variables lazily** - Only when needed
4. **Monitor memory usage** - Catch issues early
5. **Use sparse representations** - For large, sparse problems
6. **Decompose large problems** - Solve in pieces
7. **Garbage collect explicitly** - After solving iterations
8. **Reuse solver instances** - When solving similar problems

### DON'Ts ❌

1. **Don't create unnecessary variables** - Every variable costs memory
2. **Don't use wide domains** - Tighten bounds always
3. **Don't store full matrices** - Use sparse structures
4. **Don't ignore memory growth** - Monitor and react
5. **Don't keep old models** - Delete after solving
6. **Don't use redundant intermediates** - Use expressions
7. **Don't load everything at once** - Stream when possible
8. **Don't forget to flush** - Clear caches and pools

## Memory Debugging Checklist

When facing memory issues:

- [ ] Check number of variables created
- [ ] Verify variable domain sizes
- [ ] Count constraints added
- [ ] Monitor memory growth over time
- [ ] Look for memory leaks in loops
- [ ] Consider problem decomposition
- [ ] Try sparse representations
- [ ] Enable garbage collection
- [ ] Profile memory hotspots
- [ ] Reduce parallelism if needed

Remember: OR-Tools is memory efficient by design, but large problems require careful memory management!