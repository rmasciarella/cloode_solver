# Claude Custom Commands for OR-Tools Development

## Command Implementation Guide

This file defines how Claude should respond to custom commands. Each command triggers specific behaviors and outputs.

---

## Constraint Development Commands

### `/add-constraint <name>`
**Purpose**: Generate a new constraint function following STANDARDS.md

**When triggered**: User types `/add-constraint` followed by constraint name

**Claude's Response**:
1. Ask for clarification if needed:
   - "What variables does this constraint need?"
   - "What is the business rule this enforces?"
2. Generate using TEMPLATES.md constraint template
3. Ensure function is under 30 lines
4. Include comprehensive docstring
5. Add type hints for all parameters

**Example Output**:
```python
def add_maintenance_window_constraints(
    model: cp_model.CpModel,
    task_starts: Dict[Tuple[int, int], IntVar],
    task_ends: Dict[Tuple[int, int], IntVar],
    maintenance_windows: List[Tuple[int, int]]
) -> None:
    """Add maintenance window constraints to prevent task scheduling.
    
    Mathematical formulation:
        For each task t and maintenance window w:
        task_end[t] <= window_start[w] OR task_start[t] >= window_end[w]
    
    Business logic:
        Tasks cannot be scheduled during maintenance windows.
        
    Constraints added:
        - Disjunctive constraints for task-window non-overlap
        
    Performance: O(n*m) where n=tasks, m=windows
    """
    for (job_id, task_id), start_var in task_starts.items():
        end_var = task_ends[(job_id, task_id)]
        
        for window_start, window_end in maintenance_windows:
            # Task must be before or after maintenance
            b = model.NewBoolVar(f'before_maint_{job_id}_{task_id}_{window_start}')
            model.Add(end_var <= window_start).OnlyEnforceIf(b)
            model.Add(start_var >= window_end).OnlyEnforceIf(b.Not())
```

### `/test-constraint <name>`
**Purpose**: Generate unit test for constraint function

**Claude's Response**:
1. Use TEMPLATES.md unit test template
2. Include GIVEN-WHEN-THEN structure
3. Test normal operation
4. Test edge cases
5. Test integration with other constraints

**Example Output**:
```python
def test_maintenance_window_constraints():
    """Test that maintenance windows are respected."""
    # GIVEN: Model with task and maintenance window
    model = cp_model.CpModel()
    task_starts = {(1, 1): model.NewIntVar(0, 100, 'start_1_1')}
    task_ends = {(1, 1): model.NewIntVar(0, 100, 'end_1_1')}
    model.Add(task_ends[(1, 1)] == task_starts[(1, 1)] + 10)
    
    maintenance_windows = [(30, 50)]  # Maintenance from 30 to 50
    
    # WHEN: Adding maintenance constraints
    add_maintenance_window_constraints(
        model, task_starts, task_ends, maintenance_windows
    )
    
    # THEN: Task scheduled outside maintenance window
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    assert status == cp_model.OPTIMAL
    task_end = solver.Value(task_ends[(1, 1)])
    task_start = solver.Value(task_starts[(1, 1)])
    
    # Task should not overlap with maintenance
    assert task_end <= 30 or task_start >= 50
```

### `/check-constraint <function_name>`
**Purpose**: Validate constraint against STANDARDS.md

**Claude's Response - Checklist**:
- [ ] Function name follows pattern: `add_<constraint_type>_constraints`
- [ ] Function has exactly 30 lines or less (excluding docstring)
- [ ] All parameters have type hints
- [ ] Return type is `-> None`
- [ ] Docstring includes:
  - [ ] Mathematical formulation
  - [ ] Business logic explanation
  - [ ] List of constraints added
  - [ ] Performance considerations
- [ ] No hardcoded values (uses parameters/constants)
- [ ] Follows variable naming convention
- [ ] Has corresponding unit test

**Output Format**:
```
Checking: add_maintenance_window_constraints

✅ Naming convention: Correct
✅ Line count: 22 lines (under 30)
✅ Type hints: All parameters typed
✅ Docstring: Complete with all sections
⚠️  Performance: Consider adding redundant constraints for large window counts
✅ Standards compliance: PASSED

Suggestions:
- Consider interval variables for maintenance windows
- Add redundant constraint: total_maintenance_time <= horizon
```

### `/list-constraints`
**Purpose**: Show all constraints in current model

**Claude's Response**:
1. Scan solver.py or specified file
2. List all `add_*_constraints` functions
3. Show calling order
4. Indicate dependencies

**Output Format**:
```
Constraints in solver.py:

Phase 1 Constraints:
1. add_duration_constraints() - Lines 45-67
   Variables: task_starts, task_ends
   
2. add_precedence_constraints() - Lines 70-85  
   Variables: task_starts, task_ends
   Depends on: duration constraints
   
3. add_no_overlap_constraints() - Lines 88-120
   Variables: task_intervals, task_assigned
   Depends on: duration, assignment constraints

4. add_assignment_constraints() - Lines 123-145
   Variables: task_assigned, task_modes
   
Total: 4 constraint functions
Dependencies: precedence → duration, no_overlap → assignment
```

### Type Safety Commands

### `/type-check <file>` or `/tc-file <file>`
**Purpose**: Check specific file for type safety compliance

**When triggered**: User wants to verify mypy compliance for specific file

**Claude's Response**:
1. Run mypy on specific file: `mypy {file_path}`
2. Identify any OR-Tools typing issues
3. Suggest fixes using centralized type aliases from TEMPLATES.md
4. Verify integration with existing typed code

**Example Output**:
```
Type Checking: src/solver/constraints/phase1/precedence.py

✅ mypy: Success: no issues found in 1 source file
✅ Uses centralized type aliases: TaskStartDict, TaskEndDict
✅ OR-Tools types: All cp_model.IntVar properly annotated
✅ Return type: -> None (correct for constraint function)

Standards compliance: PASSED
```

### `/fix-type-error <error_message>`
**Purpose**: Resolve specific mypy error with OR-Tools context

**When triggered**: User provides mypy error message to fix

**Claude's Response**:
1. Analyze error in context of OR-Tools patterns
2. Check if centralized type aliases should be used
3. Provide specific fix with explanation
4. Suggest verification steps

**Example Output**:
```
Analyzing mypy error: "Item 'None' of 'Optional[cp_model.CpSolver]' has no attribute 'Value'"

Issue: Accessing solver result without status check
OR-Tools Pattern: Always verify solver status before accessing values

Fix:
```python
# Before (causes error)
value = solver.Value(my_var)

# After (type-safe)
if solver.StatusName() in ['OPTIMAL', 'FEASIBLE']:
    value = solver.Value(my_var)  # Safe access
else:
    logger.warning(f"Solver failed: {solver.StatusName()}")
```

Next steps:
1. Apply fix to {file_path}
2. Run mypy to verify: mypy src/
3. Test functionality: uv run python run_tests.py
```

### `/validate-types`
**Purpose**: Run complete type safety validation on entire codebase

**Claude's Response**:
1. Execute `make lint` (includes mypy + ruff + black)
2. Report on type safety compliance across all files
3. Identify any files needing type annotations
4. Suggest improvements for better type safety

**Example Output**:
```
Complete Type Safety Validation:

✅ mypy src/: Success: no issues found in 34 source files
✅ ruff check .: All checks passed!
✅ black --check .: All files formatted correctly

Type Safety Status: 100% COMPLIANT

Files by type coverage:
- Fully typed: 34/34 files (100%)
- Using centralized aliases: 28/34 files (82%)
- OR-Tools typed: 15/15 constraint files (100%)

Recommendations:
- Consider adding type aliases to remaining 6 utility files
- All constraint functions properly typed ✅
```

---

## Debugging Commands

### `/trace-infeasible`
**Purpose**: Systematically debug infeasible model

**Claude's Response Process**:
```python
# Step 1: Remove objective
"First, let's remove the objective function to see if it's a feasibility issue."

# Step 2: Disable constraints systematically
"Now disable constraints in this order:
1. No-overlap constraints (most restrictive)
2. Precedence constraints  
3. Assignment constraints
4. Duration constraints (least restrictive)"

# Step 3: Binary search
"Model became feasible after removing no-overlap. 
Let's binary search to find minimal infeasible set..."

# Step 4: Identify conflict
"Found conflict: Task (1,3) and (2,1) both require Machine 2 
at time slots 10-15. Their time windows don't allow other scheduling."

# Step 5: Suggest fixes
"Solutions:
1. Extend horizon to allow sequential scheduling
2. Add alternative machine modes for these tasks
3. Relax precedence between conflicting tasks"
```

### `/explain-solution`
**Purpose**: Convert solver output to business explanation

**Input Required**: Solution data or solver output

**Claude's Response Template**:
```
Schedule Explanation:

📅 Overall Timeline: 0 to 85 time units (21.25 hours)

🏭 Machine Utilization:
- Machine 1: 68% utilized (58/85 time units)
  • Job 1 Task 2: Time 0-15
  • Job 2 Task 1: Time 15-30
  • [Idle]: Time 30-45
  • Job 3 Task 1: Time 45-60
  
- Machine 2: 45% utilized (38/85 time units)
  • Job 1 Task 1: Time 0-20
  • Job 2 Task 3: Time 35-50
  • [Idle]: Time 50-85

📊 Key Insights:
- Bottleneck: Machine 1 is critical path
- Idle time: Machine 2 has 55% idle capacity
- Precedence impact: Job 2 Task 3 waits 15 units for Task 2

💡 Optimization Opportunities:
- Consider parallel tasks on Machine 2
- Machine 1 needs capacity expansion for growth
```

### `/profile-solver`
**Purpose**: Analyze solver performance

**Claude's Response Includes**:
1. Variable count analysis
2. Constraint complexity
3. Search space size
4. Bottleneck identification

**Output Format**:
```
Solver Performance Profile:

📊 Model Statistics:
- Variables: 2,450 (1,200 IntVar, 1,250 BoolVar)
- Constraints: 8,320
- Search space: ~10^120

⏱️ Time Breakdown:
- Model building: 0.3s (12%)
- Constraint creation: 0.8s (32%)
- Solving: 1.4s (56%)
  - First solution: 0.2s
  - Optimization: 1.2s

🔍 Bottlenecks:
1. No-overlap constraints: 45% of solve time
   - 1,250 disjunctive constraints
   - Consider interval variables
   
2. Variable bounds: Too loose
   - task_starts: [0, 10000] → could be [0, 850]
   - Tighter bounds from precedence analysis

💡 Optimization Suggestions:
1. Add redundant constraint: sum(durations) <= makespan
2. Use search strategy: assign critical path first
3. Set solution limit for large problems
```

### `/debug-variables`
**Purpose**: Display variable state for debugging

**Claude's Response Format**:
```
Variable Debug Information:

📌 Task Start Variables:
task_starts[(1,1)]: 
  - Bounds: [0, 50]
  - Solved value: 15
  - Name: "start_1_1"
  
task_starts[(1,2)]:
  - Bounds: [20, 80] 
  - Solved value: 45
  - Name: "start_1_2"
  - Note: Lower bound from precedence

📌 Assignment Variables:
task_assigned[(1,1,machine_1)]:
  - Type: BoolVar
  - Value: True
  
task_assigned[(1,1,machine_2)]:
  - Type: BoolVar
  - Value: False

🔍 Suspicious Patterns:
- Wide bounds on task_starts[(2,3)]: [0, 1000]
- Unassigned task: (3,2) has no True assignment
- Overlapping intervals: Check (1,3) and (2,1)
```

---

## Optimization Commands

### `/suggest-redundant`
**Purpose**: Identify redundant constraints for faster solving

**Claude's Analysis Process**:
1. Analyze constraint structure
2. Identify transitive relationships
3. Find implied bounds
4. Suggest symmetry breaking

**Output Format**:
```python
# Suggested Redundant Constraints:

# 1. Transitive precedence
# If A→B and B→C, add A→C
if task_1_precedes_task_2 and task_2_precedes_task_3:
    model.Add(task_starts[(1,3)] >= task_ends[(1,1)])

# 2. Total duration constraint
total_duration = sum(task_durations.values())
model.Add(makespan >= total_duration)

# 3. Machine capacity
for machine_id in machines:
    machine_tasks_duration = sum(
        duration for (j,t,m), var in task_assigned.items()
        if m == machine_id and solver.Value(var)
    )
    model.Add(machine_tasks_duration <= makespan)

# 4. Symmetry breaking
# If machines are identical, assign lower job IDs first
if machines_are_identical:
    model.Add(task_assigned[(1,1,1)] >= task_assigned[(1,1,2)])
```

### `/tighten-bounds`
**Purpose**: Analyze and suggest tighter variable bounds

**Claude's Analysis Output**:
```python
# Current vs Suggested Bounds:

# Task Start Variables:
task_starts[(1,1)]:
  Current: [0, 1000]
  Suggested: [0, 50]  # Cannot start later due to precedence chain
  
task_starts[(2,3)]:
  Current: [0, 1000]  
  Suggested: [35, 120]  # Min from precedence, max from deadline

# Implementation:
task_starts[(1,1)] = model.NewIntVar(0, 50, 'start_1_1')
task_starts[(2,3)] = model.NewIntVar(35, 120, 'start_2_3')

# Makespan Variable:
Current: [0, 10000]
Suggested: [total_min_duration, critical_path_length * 1.2]

# Expected Impact:
- Search space reduction: 85%
- Estimated speedup: 3-5x
```

### `/optimize-search`
**Purpose**: Suggest search strategies for problem

**Claude's Strategy Recommendation**:
```python
# Recommended Search Strategy:

# 1. Critical Path First
critical_tasks = identify_critical_path(precedence_graph)
critical_vars = [task_starts[t] for t in critical_tasks]

model.AddDecisionStrategy(
    critical_vars,
    cp_model.CHOOSE_FIRST,
    cp_model.SELECT_MIN_VALUE
)

# 2. Bottleneck Resources
bottleneck_assignments = [
    var for (j,t,m), var in task_assigned.items()
    if m in bottleneck_machines
]

model.AddDecisionStrategy(
    bottleneck_assignments,
    cp_model.CHOOSE_LOWEST_MIN,
    cp_model.SELECT_MAX_VALUE
)

# 3. Solver Parameters
solver.parameters.search_branching = cp_model.FIXED_SEARCH
solver.parameters.num_search_workers = 8
solver.parameters.log_search_progress = True

# For large problems:
solver.parameters.max_time_in_seconds = 300
solver.parameters.solution_limit = 100
```

### `/analyze-complexity`
**Purpose**: Provide Big O analysis of model

**Claude's Analysis Output**:
```
Model Complexity Analysis:

📊 Variable Complexity:
- Task variables: O(n) where n = number of tasks
- Assignment variables: O(n × m) where m = machines
- Total variables: O(n × m)

📈 Constraint Complexity:
- Duration constraints: O(n)
- Precedence constraints: O(p) where p = precedence pairs
- No-overlap constraints: O(n² × m) worst case
- Assignment constraints: O(n × m)
- Total constraints: O(n² × m)

🔍 Solver Complexity:
- Search space: O(m^n) - exponential
- First solution: O(n × m) with good heuristics
- Optimal solution: NP-hard

💡 Scalability Analysis:
Current model scales well up to:
- 100 tasks: < 1 second
- 1,000 tasks: < 30 seconds  
- 10,000 tasks: Consider decomposition

Bottleneck at scale: No-overlap constraints
Solution: Use interval variables and global constraints
```

---

## Template Development Commands ⚡

### `/template-benchmark <template_id> [--instances <count>] [--params-file <path>]`
**Purpose**: Comprehensive performance analysis of template across multiple scales

**When triggered**: User wants to analyze template performance at different scales

**Claude's Response**:
1. Execute enhanced `validate_template_performance.py` with JSON output
2. Format results in performance table showing:
   - Instance count vs solve time
   - Template vs legacy comparison
   - Complexity analysis (theoretical improvement)
   - Memory efficiency metrics

**Example Output**:
```
Template Performance Analysis: manufacturing_job_v2

| Instances | Template Time | Legacy Time | Speedup | Complexity Reduction |
|-----------|---------------|-------------|---------|---------------------|
| 3         | 0.8s         | 2.1s        | 2.6x    | 15x                 |
| 5         | 1.2s         | 8.4s        | 7.0x    | 125x                |
| 10        | 2.1s         | 45.2s       | 21.5x   | 1000x               |

Template Efficiency: ✅ 5-8x improvement validated
Scalability: ✅ Sub-linear scaling confirmed
Memory: ✅ O(template × instances) complexity achieved
```

### `/template-optimize-params <template_id>`
**Purpose**: Interactive parameter tuning workflow for template

**When triggered**: User wants to optimize CP-SAT parameters for specific template

**Claude's Response Process**:
1. Run baseline benchmark with default parameters
2. Test key parameter variations:
   - `num_search_workers`: 1, 4, 8, max_cores
   - `linearization_level`: 0, 1, 2
   - `search_branching`: AUTOMATIC, FIXED_SEARCH
3. Apply statistical analysis to find robust parameter set
4. Generate optimized parameters JSON file
5. Suggest `/template-promote-params` to persist

**Example Output**:
```
Parameter Optimization for template: manufacturing_job_v2

Testing parameter combinations...
✅ Baseline (default): 3.2s
⚡ num_search_workers=8: 1.8s (1.8x speedup)
⚡ linearization_level=1: 1.9s (1.7x speedup)
⚡ search_branching=FIXED: 1.6s (2.0x speedup)

Optimal combination: 1.1s (2.9x speedup)
- num_search_workers: 8
- linearization_level: 1
- search_branching: FIXED_SEARCH
- max_time_in_seconds: 60

Generated: manufacturing_job_v2_params.json
Next: /template-promote-params manufacturing_job_v2 manufacturing_job_v2_params.json
```

### `/template-promote-params <template_id> <params_file.json>`
**Purpose**: Store blessed parameters for production use

**When triggered**: User wants to make optimized parameters permanent

**Claude's Response**:
1. Validate parameter file format
2. Update job_templates table with solver_parameters JSON
3. Verify integration with FreshSolver parameter loading
4. Confirm production system will use blessed parameters

**Example Output**:
```
Promoting parameters for template: manufacturing_job_v2

✅ Parameter file validated: manufacturing_job_v2_params.json
✅ Database updated: job_templates.solver_parameters
✅ FreshSolver integration verified
✅ Production deployment ready

Parameters now active:
- All new instances will use optimized parameters
- 2.9x performance improvement expected
- Rollback available via: /template-revert-params manufacturing_job_v2
```

### `/template-add-symmetry <strategy>`
**Purpose**: Generate symmetry breaking constraints for common patterns

**When triggered**: User wants to add symmetry breaking to reduce equivalent solutions

**Strategies Available**:
- `job_lex_order`: Lexicographical ordering for identical jobs
- `machine_precedence`: Resource assignment ordering
- `task_start_order`: Time-based symmetry breaking

**Example Output**:
```python
# Symmetry breaking for identical jobs (strategy: job_lex_order)
def add_job_lexicographical_symmetry_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    problem: SchedulingProblem
) -> None:
    """Add lexicographical ordering constraints for identical job instances."""
    if not problem.is_template_based:
        return
        
    instances = sorted(problem.job_instances, key=lambda x: x.instance_id)
    
    for i in range(len(instances) - 1):
        curr_instance = instances[i]
        next_instance = instances[i + 1]
        
        # First task of current instance must start no later than first task of next
        first_task = problem.job_template.template_tasks[0]
        curr_key = (curr_instance.instance_id, first_task.template_task_id)
        next_key = (next_instance.instance_id, first_task.template_task_id)
        
        if curr_key in task_starts and next_key in task_starts:
            model.Add(task_starts[curr_key] <= task_starts[next_key])
```

### `/template-regression-test`
**Purpose**: Run comprehensive regression testing across all templates

**When triggered**: User wants to validate all templates after system changes

**Claude's Response**:
1. Identify all templates with blessed parameters
2. Execute standardized test suite for each template
3. Flag performance regressions > 20%
4. Report parameter drift or constraint conflicts
5. Generate regression report with recommendations

**Example Output**:
```
Template Regression Test Results:

📊 Templates Tested: 3/3
⏱️  Total Test Time: 45.2s

✅ manufacturing_job_v2: PASSED
   - Performance: 1.1s (expected: 1.1s ±0.2s)
   - Parameters: Optimal
   - Constraints: All satisfied

⚠️  logistics_route_v1: DEGRADED
   - Performance: 8.4s (expected: 5.2s ±1.0s)
   - Regression: 61% slower than baseline
   - Recommendation: Re-optimize parameters

❌ packaging_sequence_v3: FAILED
   - Error: Infeasible model
   - Issue: New constraints conflict with template structure
   - Action: Review recent constraint changes

Summary:
- 1/3 templates performing optimally
- 1/3 templates need parameter re-optimization
- 1/3 templates need constraint review
```

---

## Command Shortcuts (Aliases)

For faster development, these shortcuts are available:

```bash
# Legacy OR-Tools Commands  
/ac  →  /add-constraint
/tc  →  /test-constraint  
/cc  →  /check-constraint
/lc  →  /list-constraints
/tc-file →  /type-check (file-specific type checking)
/fix-type →  /fix-type-error
/vt  →  /validate-types
/ti  →  /trace-infeasible
/es  →  /explain-solution
/ps  →  /profile-solver
/dv  →  /debug-variables
/sr  →  /suggest-redundant
/tb  →  /tighten-bounds
/os  →  /optimize-search
/cx  →  /analyze-complexity

# Template Commands ⚡
/tb-tpl  →  /template-benchmark
/opt-tpl →  /template-optimize-params
/prm-tpl →  /template-promote-params
/sym-tpl →  /template-add-symmetry
/reg-tpl →  /template-regression-test
```

## Workflow Commands (Compound)

### `/dev-flow <constraint_name>`
Executes: `/add-constraint` → `/test-constraint` → `/check-constraint`

### `/debug-slow`
Executes: `/profile-solver` → `/tighten-bounds` → `/suggest-redundant`

### `/fix-infeasible`
Executes: `/trace-infeasible` → `/explain-solution` → suggestions

---

## Usage Notes

1. **Context Awareness**: Commands should reference current file and line numbers
2. **Incremental Output**: Show progress during long operations
3. **Error Handling**: Gracefully handle missing information
4. **Confirmations**: Ask before generating large code blocks
5. **Integration**: Always suggest where to integrate generated code