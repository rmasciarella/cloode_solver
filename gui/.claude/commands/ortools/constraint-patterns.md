# /constraint-patterns - Show OR-Tools Constraint Implementation Patterns

Displays the standard patterns for implementing constraint functions in the Fresh OR-Tools solver, following STANDARDS.md requirements.

## Pattern Matching
- Direct: `/constraint-patterns`
- Natural: "show constraint examples", "how do I add constraints?", "constraint function template", "constraint patterns"

## Implementation

1. Show the standard constraint function pattern
2. Provide concrete examples from the codebase
3. Highlight key rules from STANDARDS.md
4. Include testing patterns

## Output Template

```
## OR-Tools Constraint Function Patterns

### Standard Pattern (REQUIRED)

```python
def add_<constraint_type>_constraints(
    model: cp_model.CpModel,
    variables: Dict[Any, Any],
    problem: SchedulingProblem
) -> None:
    """Add <constraint_type> constraints.
    
    Args:
        model: The CP-SAT model
        variables: Relevant decision variables
        problem: Problem data
        
    Constraints Added:
        - [List specific constraints added]
        
    Performance:
        - O(n) where n = number of constraints
    """
    # Implementation (max 30 lines)
    for item in problem.items:
        model.Add(constraint_expression)
```

### Example 1: Precedence Constraints

```python
def add_precedence_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[int, int], IntVar],
    task_ends: Dict[Tuple[int, int], IntVar],
    precedences: List[Tuple[Tuple[int, int], Tuple[int, int]]]
) -> None:
    """Add precedence constraints between tasks.
    
    Constraints Added:
        - task2.start >= task1.end for each precedence
    """
    for (job1, task1), (job2, task2) in precedences:
        model.Add(
            task_starts[(job2, task2)] >= task_ends[(job1, task1)]
        )
```

### Example 2: No-Overlap Constraints

```python
def add_no_overlap_constraints(
    model: cp_model.CpModel,
    task_intervals: Dict[Tuple[int, int, int], IntervalVar],
    machines: List[Machine]
) -> None:
    """Ensure tasks on same machine don't overlap.
    
    Constraints Added:
        - NoOverlap for all intervals on each machine
    """
    for machine in machines:
        machine_intervals = [
            interval for (j, t, m), interval in task_intervals.items()
            if m == machine.id
        ]
        if machine_intervals:
            model.AddNoOverlap(machine_intervals)
```

### Key Rules (from STANDARDS.md):

1. **One constraint type per function** ✓
2. **Function name**: `add_<type>_constraints()` ✓
3. **Maximum 30 lines** (excluding docstring) ✓
4. **Type hints required** on all parameters ✓
5. **Return type**: Always `-> None` ✓
6. **Docstring must include**:
   - Brief description
   - Args documentation
   - "Constraints Added" section
   - Performance notes (if relevant)

### Testing Pattern:

```python
def test_<constraint_type>_constraints():
    """Test that constraints are correctly enforced."""
    # GIVEN: Model with test data
    model = cp_model.CpModel()
    variables = create_test_variables(model)
    
    # WHEN: Adding constraints
    add_<constraint_type>_constraints(model, variables, test_data)
    
    # THEN: Solution satisfies constraints
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL
    assert constraint_is_satisfied(solver, variables)
```

### Common Patterns:

1. **Conditional Constraints**:
   ```python
   if optional_task:
       model.Add(constraint).OnlyEnforceIf(task_present)
   ```

2. **Redundant Constraints**:
   ```python
   # Add redundant constraint for better pruning
   if len(items) > 100:
       model.Add(aggregate_constraint)
   ```

3. **Efficient Iteration**:
   ```python
   # Pre-filter to avoid unnecessary constraints
   relevant_items = [i for i in items if i.is_relevant]
   for item in relevant_items:
       model.Add(constraint)
   ```

### Next Steps:
- Use `/add-constraint <name>` to generate a new constraint
- Use `/test-constraint <name>` to generate tests
- Use `/check-standards` to verify compliance
```

## Context Integration
- Enforce STANDARDS.md rules
- Reference existing implementations
- Guide toward best practices