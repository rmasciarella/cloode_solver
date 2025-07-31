# Constraint Performance Considerations

## No-Overlap vs Cumulative Constraints

### Overview

When modeling machine scheduling, we have two main approaches for handling task conflicts:
1. **No-Overlap Constraint** (`AddNoOverlap`)
2. **Cumulative Constraint** (`AddCumulative`)

### Performance Comparison

#### No-Overlap Constraint
- **Best for**: Machines with capacity = 1
- **Performance**: More efficient for single-capacity resources
- **Reason**: Specialized algorithm for disjunctive scheduling
- **Complexity**: O(n log n) for propagation

```python
# Efficient for unit capacity
model.AddNoOverlap(intervals)
```

#### Cumulative Constraint
- **Required for**: Machines with capacity > 1
- **Performance**: More expensive but necessary for parallel tasks
- **Reason**: Handles resource consumption tracking
- **Complexity**: O(n²) for propagation in worst case

```python
# Necessary for multi-capacity resources
model.AddCumulative(intervals, demands, capacity)
```

### Our Implementation Strategy

The Fresh Solver uses a hybrid approach:

1. **All machines** get no-overlap constraints by default
   - This efficiently handles capacity=1 machines
   - Creates optional intervals for task-machine assignments

2. **High-capacity machines** (capacity > 1) additionally get cumulative constraints
   - Only applied when truly needed
   - Allows parallel task execution
   - More expensive but necessary for correctness

### Example Performance Impact

For a problem with:
- 100 tasks
- 10 machines (8 with capacity=1, 2 with capacity=3)

**Pure Cumulative Approach**: 10 cumulative constraints
**Our Hybrid Approach**: 10 no-overlap + 2 cumulative constraints

Result: ~60% fewer expensive cumulative constraints!

### Best Practices

1. **Always use no-overlap** for single-capacity resources
2. **Only use cumulative** when parallel execution is possible
3. **Consider decomposition** for very high capacity machines
4. **Monitor solve times** when adding high-capacity machines

### Code Example

```python
# Efficient constraint selection
if machine.capacity == 1:
    # Use faster no-overlap
    model.AddNoOverlap(machine_intervals)
else:
    # Use cumulative only when needed
    model.AddCumulative(intervals, demands, machine.capacity)
```

### Solver Tips

- The CP-SAT solver has specialized propagators for no-overlap
- Cumulative constraints involve more complex reasoning
- When possible, model single-capacity resources explicitly
- Consider breaking high-capacity machines into virtual single-capacity units if solve time is critical