# Development Workflows for OR-Tools Projects

## 0. Template Development Session Management (NEW PRIORITY)

### Template-First Development Session Pattern
For this template-optimized architecture delivering 5-8x performance improvements:

```
Session Start: "Continue template optimization for {template_id}. 
Last session performance: {baseline_time}s → {optimized_time}s. 
Current focus: {optimization_area}"

Key Context to Preserve:
- Template ID and instance count being optimized
- Baseline performance metrics from previous sessions  
- Current parameter tuning status (blessed vs experimental)
- Identified performance bottlenecks and applied solutions
- Pending optimization strategies from previous sessions
```

### Template Development Session Checkpoints
```
Every 30 Minutes or Major Milestone:

"Checkpoint - Template {template_id}:
- Baseline: {original_performance}
- Current: {current_performance} 
- Improvement: {speedup_factor}x speedup
- Techniques Applied: {optimization_techniques}
- Next Steps: {pending_optimizations}
- Parameters Status: {blessed|experimental|testing}"
```

### Template Context Preservation Structure
Store optimization history in this format for cross-session continuity:

```json
{
  "template_id": "manufacturing_job_v2",
  "optimization_sessions": [
    {
      "date": "2024-01-15",
      "focus": "symmetry_breaking", 
      "baseline_time": 12.3,
      "optimized_time": 3.2,
      "improvement_factor": "3.8x",
      "techniques_applied": ["job_lex_order", "machine_precedence"],
      "blessed_parameters": {
        "num_search_workers": 8,
        "search_branching": "FIXED_SEARCH"
      },
      "next_session_focus": "parameter_tuning_linearization"
    }
  ],
  "current_status": {
    "performance_target": "< 2.0s for 10 instances",
    "current_performance": "3.2s for 10 instances", 
    "gap_to_target": "37% slower than target",
    "priority_optimizations": ["linearization_level", "redundant_constraints"]
  }
}
```

### Session End Documentation
```
"Template {template_id} session complete:
- Started: {baseline_metrics}
- Achieved: {final_metrics}
- Total Improvement: {total_speedup_factor}x
- Techniques Applied: {all_techniques}
- Performance vs Target: {target_comparison}
- Blessed Parameters: {parameter_status}
- Next Session Priority: {next_focus_areas}
- Ready for Production: {yes|no - reason}"
```

## 1. New Constraint Implementation Workflow

### Step 1: Analysis and Planning
```
You: "I need to add {constraint_type} constraints. /add-constraint {constraint_name}"

Claude: [Generates constraint function template]

You: "Analyze existing constraints to understand integration points"

Claude: [Reviews codebase, identifies patterns and dependencies]
```

### Step 2: Test-First Development
```
You: "Create unit tests for {constraint_name} before implementation"

Claude: [Generates comprehensive test cases following GIVEN-WHEN-THEN]

You: "Run tests to confirm they fail"
```

### Step 3: Implementation
```
You: "Implement the constraint following STANDARDS.md"

Claude: [Implements constraint within 30-line limit]

You: "Validate against standards: /check-constraint {function_name}"
```

### Step 4: Integration and Testing
```
You: "Run unit tests and fix any issues"

You: "Add constraint to solver.py in correct order"

You: "Run integration tests for Phase {X}"
```

### Step 5: Performance Validation
```
You: "Profile performance impact of new constraint"

You: "If slow: /suggest-redundant"
```

## 2. Debugging Infeasible Model Workflow

### Step 1: Initial Diagnosis
```
You: "Model returns INFEASIBLE. /trace-infeasible"

Claude: [Provides systematic debugging approach]
```

### Step 2: Isolate Problem
```
You: "Disable constraints one by one starting with:"
1. Objective function
2. No-overlap constraints  
3. Precedence constraints
4. Duration constraints

You: "Found feasible at step {X}. The issue is with {constraint_type}"
```

### Step 3: Data Validation
```
You: "Check data for impossible requirements in {constraint_type}"

Claude: [Generates data validation code]

You: "Found: {specific_data_issue}"
```

### Step 4: Fix and Verify
```
You: "Fix by {solution_approach}"

You: "Re-enable all constraints and verify feasibility"

You: "Document issue in troubleshooting guide"
```

## 3. Performance Optimization Workflow

### Step 1: Baseline Measurement
```
You: "Current performance: {X} seconds on {dataset_size}"

You: "/profile-solver"

Claude: [Analyzes solver statistics and bottlenecks]
```

### Step 2: Variable Optimization
```
You: "/tighten-bounds"

Claude: [Suggests tighter variable bounds based on constraints]

You: "Implement tighter bounds"

Result: Performance improved to {Y} seconds
```

### Step 3: Add Redundancy
```
You: "/suggest-redundant"

Claude: [Identifies redundant constraints that help solver]

You: "Add redundant constraints"

Result: Performance improved to {Z} seconds
```

### Step 4: Search Strategy
```
You: "/optimize-search"

Claude: [Recommends search strategy based on problem structure]

You: "Implement search strategy"

Final result: Meets performance target
```

## 4. Code Review Workflow

### Step 1: Self-Review Checklist
```
Before requesting review:
- [ ] Run linting: `make lint`
- [ ] Run tests: `uv run python run_tests.py`
- [ ] Check performance benchmarks
- [ ] Validate against STANDARDS.md
```

### Step 2: Claude Review
```
You: "Review my implementation of {feature}:
```python
[paste code]
```
Check against STANDARDS.md"

Claude: [Provides detailed review with specific improvements]
```

### Step 3: Integration Review
```
You: "Review how {feature} integrates with existing code"

Claude: [Checks integration points, suggests improvements]
```

## 5. Phase Migration Workflow

### Step 1: Planning
```
You: "Prepare for Phase {N} implementation"

Claude: [Analyzes requirements, identifies needed changes]
```

### Step 2: Data Model Updates
```
You: "What data model changes are needed for Phase {N}?"

Claude: [Specifies new fields, relationships, validations]

You: "Update data models with backward compatibility"
```

### Step 3: Variable Structure Design
```
You: "Design variable structure for {new_feature}"

Claude: [Proposes variable design optimized for solver]
```

### Step 4: Incremental Implementation
```
You: "Phase {N}, Step 1 of {M}: {specific_component}"

[Implement incrementally with checkpoints]

You: "Checkpoint: {component} complete. Continue with {next}"
```

## 6. Test-Driven Development Workflow

### Step 1: Behavior Specification
```
You: "Define expected behavior for {feature}"

Claude: [Creates behavior specifications]
```

### Step 2: Test Creation
```
You: "Create failing tests for each behavior"

Claude: [Generates comprehensive test suite]
```

### Step 3: Minimal Implementation
```
You: "Implement minimal code to pass test 1"

[Iterate through each test]
```

### Step 4: Refactoring
```
You: "All tests pass. Refactor for clarity and performance"

Claude: [Suggests refactoring while maintaining test pass]
```

## 7. Database Integration Workflow

### Step 1: Schema Design
```
You: "Design schema for {feature} compatible with Supabase"

Claude: [Creates schema with proper relationships]
```

### Step 2: Migration Creation
```
You: "Create migration script for schema changes"

Claude: [Generates safe migration with rollback]
```

### Step 3: Data Loading Implementation
```
You: "Implement data loading with validation"

Claude: [Creates loader with comprehensive validation]
```

### Step 4: Integration Testing
```
You: "Test with real database connection"

You: "Test with invalid data for error handling"
```

## 8. Continuous Improvement Workflow

### Weekly Review
```
You: "What patterns am I repeating that could be automated?"

Claude: [Identifies repetitive tasks for configuration]

You: "Add to CLAUDE.md custom commands"
```

### Problem Documentation
```
You: "Encountered new issue: {description}"

You: "Add to troubleshooting guide with solution"
```

### Performance Tracking
```
You: "Log performance metrics for {dataset_size}"

Track trends and identify degradation early
```

## 9. Long Session Management Workflow

### Session Start
```
You: "Continue from yesterday's work on {feature}"

Claude: [Acknowledges context and current state]
```

### Regular Checkpoints
```
Every 30 minutes or major milestone:

You: "Checkpoint: Completed {X}, working on {Y}"
```

### Context Refresh
```
If conversation gets long:

You: "Let's summarize progress so far and continue"

Claude: [Provides concise summary and current focus]
```

### Session End
```
You: "End of session summary: 
- Completed: {list}
- In progress: {current_task}
- Next steps: {todo_list}"
```

## 10. Emergency Debugging Workflow

### Critical Issue Response
```
You: "URGENT: Production solver failing with {error}"

Claude: [Provides immediate triage steps]
```

### Quick Diagnosis
```
1. Check recent changes: `git log --oneline -10`
2. Verify data integrity
3. Run with minimal test case
4. Enable debug logging
```

### Temporary Fix
```
You: "Need quick fix to restore service"

Claude: [Suggests safe temporary workaround]
```

### Root Cause Analysis
```
After service restored:

You: "Perform root cause analysis"

Claude: [Systematic investigation of failure]
```

## 11. Type Safety Maintenance Workflow

### Daily Type Checking
```
You: "Run full type safety check"

Claude: "Execute: make lint (includes mypy + ruff + black)"

# Expected output:
# - ruff: All checks passed!
# - black: All files formatted correctly
# - mypy: Success: no issues found in 34 source files
```

### Adding New Constraint with Type Safety
```
You: "/add-constraint {name} with full type safety"

Claude: [Generates constraint with proper type aliases and mypy compliance]

You: "Verify type safety: mypy src/"

Claude: [Confirms zero mypy errors]
```

### Type Error Resolution Workflow
```
You: "Fix mypy error: {error_message}"

Claude: [Analyzes OR-Tools typing patterns and suggests fix]

# Common resolution steps:
1. Check if centralized type aliases are being used
2. Verify OR-Tools objects use cp_model.IntVar notation
3. Handle Optional types with proper None checks
4. Use ruff format . for line length issues
```

### Phased Type Safety Implementation
For adding type safety to existing code:

```
Step 1: "Start with easy mypy fixes - function parameters and return types"
Step 2: "Add OR-Tools specific type annotations using centralized aliases"  
Step 3: "Handle complex cases like Optional types and Union types"
Step 4: "Fix any ruff formatting issues from new type annotations"
Step 5: "Validate: ensure mypy src/ passes with zero errors"
```

### Type Safety Integration Testing
```
You: "Test that type safety doesn't break functionality"

# Verification steps:
1. Run complete test suite: uv run python run_tests.py
2. Confirm 180 tests pass, 1 skipped
3. Verify 91% coverage maintained
4. Check that solver performance is unchanged
```

## Claude Workflow Optimizations

### Incremental Development Pattern
When implementing new features:
1. Ask Claude to first analyze existing code structure: "Analyze the current constraint structure before adding X"
2. Request constraint formulation before implementation: "Formulate the mathematical constraints for X"
3. Generate tests before writing constraint code: "Create unit tests for the X constraint"
4. Use continuity phrases: "Continue from the precedence constraints we discussed..."

### Context Window Management
- **Break large tasks into phases**: "This is phase 1 of 3: Create decision variables for resource constraints"
- **Use explicit checkpoints**: "Checkpoint: All variables created successfully. Now moving to constraints."
- **Reference previous work**: "Building on the task_assigned variables from earlier..."
- **Maintain state**: "Let's continue where we left off with the machine intervals"

### Effective File References
Instead of vague references:
- ❌ "Update the constraint file"
- ✅ "In src/solver/constraints/timing.py, after line 45 in add_precedence_constraints..."

### Requesting Code Reviews
- "Validate this constraint against STANDARDS.md"
- "Check if this follows our 30-line limit and naming conventions"
- "Ensure this matches our variable naming pattern: task_*[(job_id, task_id)]"

## Best Practices for All Workflows

### 1. Always Start with Context
- Reference specific files and line numbers
- Mention current phase and objectives
- State performance requirements

### 2. Use Incremental Approach
- Break large tasks into phases
- Checkpoint after each phase
- Maintain ability to rollback

### 3. Validate Continuously
- Run tests after each change
- Check performance impact
- Verify standards compliance

### 4. Document As You Go
- Update comments for complex logic
- Add to troubleshooting guide
- Keep CLAUDE.md current

### 5. Leverage Claude's Memory
- Reference previous discussions
- Build on established patterns
- Avoid re-explaining context