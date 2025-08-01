# File Reference Conventions

## Purpose

Establish consistent patterns for referencing files and code locations in Claude conversations, enabling precise navigation and reducing ambiguity.

## Reference Format Hierarchy

### 1. Full Reference (Most Precise)
```
{filepath}:{line_number}:{function_name}
```
Example: `src/solver/constraints/precedence.py:45:add_precedence_constraints`

### 2. Line Reference (Navigation-Ready)
```
{filepath}:{line_number}
```
Example: `src/solver/core/solver.py:127`

### 3. Function Reference (Context-Aware)
```
{filepath}::{function_name}
```
Example: `tests/unit/test_precedence.py::test_circular_dependency`

### 4. File Reference (General Location)
```
{filepath}
```
Example: `src/solver/models/problem.py`

## Reference Patterns

### Pattern 1: Code Modifications

```markdown
## ❌ Bad: Vague Reference
"Update the constraint function to add validation"

## ✅ Good: Precise Reference
"In src/solver/constraints/capacity.py:23:add_capacity_constraints, add validation after line 25"
```

### Pattern 2: Error Locations

```markdown
## ❌ Bad: Unclear Error Location
"The test is failing"

## ✅ Good: Exact Error Location
"Test failing at tests/unit/test_solver.py:89 in test_infeasible_model()
Error: AssertionError on line 92"
```

### Pattern 3: Cross-References

```markdown
## ❌ Bad: Ambiguous Reference
"Similar to the other function"

## ✅ Good: Clear Cross-Reference
"Similar pattern to src/solver/constraints/timing.py:34:add_duration_constraints"
```

## Navigation Helpers

### IDE-Friendly Format

Claude should format references to be clickable in most IDEs:

```python
# PyCharm/VSCode format
"src/solver/core/solver.py:45"  # Ctrl+Click navigates directly

# With column (for precise position)
"src/solver/core/solver.py:45:12"  # Line 45, Column 12

# Test reference (pytest format)
"tests/unit/test_solver.py::TestSolver::test_basic_solve"
```

### Relative vs Absolute Paths

```python
# Always use paths relative to project root
✅ "src/solver/constraints/precedence.py"
❌ "/Users/username/projects/fresh_solver/src/solver/constraints/precedence.py"
❌ "../constraints/precedence.py"
❌ "./precedence.py"
```

## Context-Aware References

### Current File Context

When already discussing a file:

```markdown
## First Reference (Full)
"In src/solver/constraints/capacity.py:45, the add_capacity_constraints function..."

## Subsequent References (Shortened)
"At line 52, add the validation check..."
"The helper function at line 78..."
"Update calculate_usage() at line 90..."
```

### Multi-File Context

When working across files:

```markdown
## Clear Multi-File References
"Move the validation from src/solver/core/solver.py:234 
to src/solver/utils/validators.py:15:validate_model"

"The pattern in src/solver/constraints/timing.py:45 
should match src/solver/constraints/precedence.py:67"
```

## Reference Templates

### 1. Bug Report Reference

```markdown
## 🐛 Bug Location
File: src/solver/constraints/assignment.py:89
Function: add_assignment_constraints()
Issue: Line 92 - KeyError when task has no valid modes
Related: src/solver/models/problem.py:156:validate_task_modes
```

### 2. Implementation Reference

```markdown
## 🔧 Implementation Point
Add to: src/solver/core/solver.py:145
After: self._add_precedence_constraints()
Before: self._add_objective()
New function: self._add_capacity_constraints()
```

### 3. Test Reference

```markdown
## 🧪 Test Location
Test file: tests/unit/constraints/test_capacity.py
Test class: TestCapacityConstraints
Test method: test_resource_overflow:45
Assertion: line 52 - check capacity not exceeded
```

## Special Cases

### 1. New File Creation

```markdown
## 📄 New File
Create: src/solver/constraints/maintenance.py
Template: Follow pattern from src/solver/constraints/precedence.py
Location: In constraints/ directory beside other constraint modules
```

### 2. File Moves/Renames

```markdown
## 📁 File Refactoring
From: src/solver/utils/helpers.py
To: src/solver/utils/time_utils.py
Update imports in:
- src/solver/core/solver.py:15
- src/solver/models/problem.py:8
- tests/unit/test_helpers.py:3
```

### 3. Deleted Code Reference

```markdown
## 🗑️ Deletion Reference
Remove: src/solver/deprecated/old_solver.py:45-89
Contains: Deprecated solve_with_timeout() function
Replaced by: src/solver/core/solver.py:234:solve()
```

## Integration with Commands

### Command Output References

```bash
/list-constraints

# Output with proper references:
1. add_duration_constraints() - src/solver/constraints/timing.py:23
2. add_precedence_constraints() - src/solver/constraints/precedence.py:45  
3. add_assignment_constraints() - src/solver/constraints/assignment.py:67
```

### Error Trace References

```bash
/trace-infeasible

# Output with navigation:
Constraint conflict detected:
1. Precedence constraint at src/solver/constraints/precedence.py:52
2. Conflicts with deadline at src/solver/models/problem.py:89
3. Check task definition at src/data/loaders/database.py:145
```

## Best Practices

### 1. Consistency

Always use the same format within a conversation:

```python
# Pick one and stick with it:
style_1 = "src/solver/core.py:45"  # Short
style_2 = "src/solver/core.py:45:solve"  # With function
style_3 = "src/solver/core.py:45 in solve()"  # Descriptive
```

### 2. Precision Levels

Match precision to need:

```python
# General discussion
"The solver in src/solver/core/solver.py handles..."

# Specific change
"At src/solver/core/solver.py:127, change the timeout to..."

# Exact position
"Insert at src/solver/core/solver.py:127:15 (after 'model =')"
```

### 3. Batch References

For multiple related changes:

```markdown
## Changes Required

1. **Variable Creation**
   - src/solver/core/solver.py:89 - Add capacity variables
   
2. **Constraint Addition**  
   - src/solver/core/solver.py:145 - Call add_capacity_constraints
   - src/solver/constraints/capacity.py:23 - Implement function
   
3. **Test Updates**
   - tests/unit/test_solver.py:234 - Add capacity test
   - tests/integration/test_phase2.py:45 - Update integration
```

## Reference Validation

### Pre-Reference Checks

Before providing a reference:

```python
def validate_reference(filepath: str, line: int = None) -> bool:
    """Validate reference before using."""
    # Check file exists
    if not os.path.exists(filepath):
        return False
        
    # Check line number if provided
    if line:
        with open(filepath) as f:
            total_lines = len(f.readlines())
            if line > total_lines:
                return False
                
    return True
```

### Reference Shortcuts

Common shorthand expansions:

```python
shortcuts = {
    "solver": "src/solver/core/solver.py",
    "constraints/": "src/solver/constraints/",
    "tests/": "tests/unit/",
    "integration/": "tests/integration/",
}

# Usage: "solver:45" → "src/solver/core/solver.py:45"
```

## Examples

### Example 1: Feature Implementation

```markdown
## Implementing Resource Capacity

1. Define data model
   - src/solver/models/problem.py:89 - Add ResourceCapacity class
   
2. Create variables
   - src/solver/core/solver.py:67:_create_variables - Add capacity vars
   
3. Implement constraints
   - Create: src/solver/constraints/capacity.py
   - Template from: src/solver/constraints/precedence.py
   
4. Add to solver
   - src/solver/core/solver.py:145 - Call new constraint function
   
5. Test
   - Create: tests/unit/constraints/test_capacity.py
   - Update: tests/integration/test_phase2.py:89
```

### Example 2: Bug Fix

```markdown
## Fixing Circular Dependency Bug

Bug: Circular dependency not detected
Location: src/solver/constraints/precedence.py:67:_check_cycles

Fix at: src/solver/constraints/precedence.py:72
Add: Cycle detection using DFS

Test: tests/unit/test_precedence.py:145:test_circular_detection
```

### Example 3: Refactoring

```markdown
## Refactoring Time Utilities

Current: src/solver/utils/helpers.py:234-289 - Mixed utilities

Refactor to:
- src/solver/utils/time_utils.py - Time-specific functions
- src/solver/utils/validators.py:45 - Validation functions

Update imports:
- src/solver/core/solver.py:15
- src/solver/models/problem.py:8-9
- All test files matching tests/**/test_*.py
```