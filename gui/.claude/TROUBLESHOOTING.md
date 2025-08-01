# TROUBLESHOOTING.md - Debug Workflows & Solutions

## Model Infeasibility

### Symptom
Solver returns INFEASIBLE status

### Systematic Debugging Approach
1. **Remove objective function first** - isolate feasibility from optimization
2. **Disable constraints systematically**:
   - No-overlap constraints (most restrictive)  
   - Precedence constraints
   - Assignment constraints
   - Duration constraints (least restrictive)
3. **Binary search** - find minimal infeasible constraint set
4. **Data validation** - check for impossible business requirements

### Claude Command Workflow
```bash
/trace-infeasible                    # Systematic constraint disabling
/explain-solution                    # Understand constraint interactions
# Fix data or relax constraints, then re-enable systematically
```

### Common Root Causes
- Tight time windows with precedence conflicts
- Single machine required by overlapping tasks
- Circular precedence dependencies in data
- Zero or negative durations in task modes

## Slow Solver Performance

### Symptom  
Solver takes > 60 seconds on medium datasets (20 jobs, 500 tasks)

### Performance Optimization Workflow
```bash
/profile-solver                      # Identify bottlenecks  
/tighten-bounds                      # Optimize variable bounds
/suggest-redundant                   # Add helpful redundant constraints
/optimize-search                     # Configure search strategy
```

### Optimization Priority Order
1. **Variable bounds** - calculate tight bounds from precedences and deadlines
2. **Redundant constraints** - add transitive precedence, total duration bounds
3. **Search strategy** - order variables by criticality (critical path first)
4. **Solver parameters** - tune `num_search_workers`, `linearization_level`

### Optimized Mode Performance Issues
For optimized mode models underperforming:
```bash
/optimized-benchmark <pattern_id>    # Compare against targets
/optimized-optimize-params <pattern_id>  # Systematic parameter tuning
# Check symmetry breaking implementation
# Verify optimized pattern structure exploitation
```

## Memory Issues

### Symptom
Out of memory errors with large datasets

### Solutions
1. **Variable count reduction**:
   - Use IntervalVar instead of BoolVar arrays where possible
   - Eliminate unnecessary intermediate variables
   - Consider constraint programming vs integer programming formulation

2. **Optimized mode approach** for identical jobs:
   - Share optimized pattern structure across job instances
   - O(pattern_size × instances) vs O(total_tasks²) memory complexity

3. **Batch processing** for very large problems:
   - Decompose by time horizons or machine groups
   - Solve sub-problems and coordinate solutions

### Claude Analysis
Ask: "Analyze my variable creation patterns and suggest ways to reduce variable count. Consider interval variables vs boolean arrays."

## Constraint Conflicts  

### Symptom
Valid business rules create unsolvable model

### Resolution Process
1. **Create minimal reproduction case**:
   - Isolate conflicting constraints with small dataset
   - Identify specific constraint pairs causing issues
   
2. **Business rule validation**:
   - Verify constraints match actual business requirements
   - Check if rules are overly restrictive for edge cases
   
3. **Soft constraint implementation**:
   - Convert hard constraints to soft with penalties
   - Use hierarchical optimization for competing objectives

### Claude Command
Ask: "Help me identify conflicting constraints by creating a minimal reproduction case with 2 jobs and 5 tasks."

## No Solution Found (Timeout)

### Symptom
Solver times out without finding feasible solution

### Solutions
1. **Search strategy optimization**:
   ```python
   # Order variables by problem structure importance
   model.AddDecisionStrategy(critical_path_variables, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)
   ```

2. **Solution hints** for warm starts:
   ```python
   # Provide likely good starting solution
   for key, value in heuristic_solution.items():
       model.AddHint(variables[key], value)
   ```

3. **Time limit management**:
   - Increase solver time limit for complex problems
   - Use solution limit for good-enough solutions: `solver.parameters.solution_limit = 100`

### Optimized Mode Timeouts
Optimized mode should solve faster than unique mode. If timeout occurs:
- Verify symmetry breaking constraints are active
- Check parameter tuning status (blessed vs default)
- Validate optimized pattern structure exploitation

## Unit Test Failures

### Symptom
Constraint tests fail after implementation changes

### Debugging Process
1. **Isolate failing test**:
   ```bash
   uv run python -m pytest tests/unit/test_constraints.py::test_precedence_constraints -v
   ```

2. **Check test assumptions**:
   - Verify input data still matches test expectations
   - Confirm constraint formulation hasn't changed
   - Validate variable creation matches test setup

3. **Debug constraint logic**:
   ```python
   # Add logging to constraint function
   logger.debug(f"Adding precedence: {pred_task} -> {succ_task}")
   ```

### Claude Analysis
Ask: "Debug why this constraint test fails. Check if the test assumptions still match the implementation."

## Integration Issues

### Symptom
Individual constraints work but fail when combined

### Resolution
1. **Create minimal integration test**:
   ```python
   def test_minimal_integration():
       # Use smallest possible dataset
       # Enable constraints one by one
       # Find constraint interaction causing failure
   ```

2. **Variable dependency analysis**:
   - Map which constraints share variables
   - Identify potential constraint ordering issues
   - Check for variable bound conflicts

3. **Constraint interaction debugging**:
   ```python
   # Test constraint pairs systematically
   add_duration_constraints(model, variables)
   assert solve_succeeds(model)
   
   add_precedence_constraints(model, variables) 
   assert solve_succeeds(model)  # Fails here = precedence-duration conflict
   ```

## Type Safety Issues

### Symptom
mypy errors preventing code execution

### Resolution Process
1. **Run complete type check**:
   ```bash
   make lint  # Includes mypy + ruff + black
   ```

2. **Common OR-Tools typing fixes**:
   ```python
   # Correct: Use proper cp_model types
   var: cp_model.IntVar = model.NewIntVar(0, 100, "var_name")
   
   # Incorrect: Missing type annotation
   var = model.NewIntVar(0, 100, "var_name")
   ```

3. **Handle Optional types safely**:
   ```python
   # Check solver status before accessing values
   if solver.StatusName() in ['OPTIMAL', 'FEASIBLE']:
       value = solver.Value(my_var)  # Safe access
   ```

4. **Line length issues** from type annotations:
   ```bash
   uv run ruff format .  # Auto-fixes line length violations
   ```

### Claude Commands
```bash
/fix-type-error <error_message>      # Resolve specific mypy error
/validate-types                      # Complete codebase type check
```

## Performance Regression Detection

### Symptom
Previously fast optimized patterns now solve slowly

### Diagnosis Process
1. **Regression testing**:
   ```bash
   /optimized-regression-test           # Test all optimized patterns
   ```

2. **Parameter drift detection**:
   - Check if blessed parameters are still active
   - Verify solver version compatibility
   - Validate constraint structure hasn't changed

3. **Performance baseline validation**:
   - Compare current performance to historical benchmarks
   - Identify performance degradation > 20%
   - Root cause analysis for specific performance drops

### Recovery Actions
1. **Parameter re-optimization**:
   ```bash
   /optimized-optimize-params <pattern_id>  # Re-tune parameters
   /optimized-promote-params <pattern_id> <new_params.json>
   ```

2. **Constraint validation**:
   - Verify symmetry breaking constraints still active
   - Check for new constraints impacting performance
   - Validate optimized pattern structure exploitation

3. **Infrastructure changes**:
   - Check solver version changes
   - Verify system resources (CPU, memory)
   - Validate database query performance