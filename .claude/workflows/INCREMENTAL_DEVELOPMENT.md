# Incremental Development Pattern for OR-Tools

## Overview

This pattern enables systematic development of complex OR-Tools models by breaking work into manageable increments with continuous validation.

## Core Principles

1. **Start Simple**: Begin with minimal working model
2. **Add Incrementally**: One constraint type at a time
3. **Validate Continuously**: Test after each addition
4. **Maintain Working State**: Never break existing functionality

## Implementation Workflow

### Phase-Based Incremental Development

```
┌─────────────────┐
│ Minimal Model   │ → Test → Commit
└────────┬────────┘
         │
┌────────▼────────┐
│ Add Constraint  │ → Test → Commit
└────────┬────────┘
         │
┌────────▼────────┐
│ Add Objective   │ → Test → Commit
└────────┬────────┘
         │
┌────────▼────────┐
│ Optimize        │ → Test → Commit
└─────────────────┘
```

### Step 1: Minimal Viable Model

```python
# Start with simplest possible model
def create_minimal_model(problem):
    """Create model with only essential constraints."""
    model = cp_model.CpModel()
    
    # Only create variables
    variables = create_basic_variables(model, problem)
    
    # Add only duration constraints (simplest)
    add_duration_constraints(model, variables)
    
    # Simple objective (optional)
    model.Minimize(variables['makespan'])
    
    return model, variables
```

**Validation**: Model should solve with this minimal setup

### Step 2: Incremental Constraint Addition

```python
# Add constraints one type at a time
increment_sequence = [
    ('duration', add_duration_constraints),
    ('precedence', add_precedence_constraints),
    ('assignment', add_assignment_constraints),
    ('no_overlap', add_no_overlap_constraints),
]

for constraint_name, constraint_func in increment_sequence:
    print(f"Adding {constraint_name} constraints...")
    
    # Add constraint
    constraint_func(model, variables, problem)
    
    # Validate immediately
    status = test_solve(model)
    if status != cp_model.OPTIMAL:
        print(f"Model became infeasible after {constraint_name}")
        # Debug before continuing
        debug_infeasibility(model, constraint_name)
```

### Step 3: Feature-by-Feature Development

```python
# Example: Adding maintenance windows incrementally
def add_maintenance_incrementally():
    # Step 1: Simple fixed windows
    add_fixed_maintenance_windows(model, fixed_windows)
    validate_and_commit("Added fixed maintenance windows")
    
    # Step 2: Flexible windows
    add_flexible_maintenance_windows(model, flex_windows)
    validate_and_commit("Added flexible maintenance windows")
    
    # Step 3: Maintenance precedence
    add_maintenance_precedence(model, maint_precedence)
    validate_and_commit("Added maintenance precedence")
```

## Checkpoint System

### Creating Checkpoints

```python
class ModelCheckpoint:
    """Save model state at key development points."""
    
    def __init__(self, name: str):
        self.name = name
        self.timestamp = datetime.now()
        self.model_state = {}
        
    def save(self, model, variables, constraints_added):
        """Save current model state."""
        self.model_state = {
            'variable_count': len(variables),
            'constraint_count': model.NumConstraints(),
            'constraints_added': constraints_added,
            'is_feasible': self._test_feasibility(model),
        }
        
    def validate(self, current_model):
        """Ensure model hasn't regressed."""
        current_count = current_model.NumConstraints()
        saved_count = self.model_state['constraint_count']
        
        if current_count < saved_count:
            raise ValueError("Model has fewer constraints than checkpoint!")
```

### Using Checkpoints in Development

```python
# Development with checkpoints
checkpoints = []

# Checkpoint 1: After basic setup
model, vars = create_basic_model()
cp1 = ModelCheckpoint("basic_model")
cp1.save(model, vars, ['duration'])
checkpoints.append(cp1)

# Checkpoint 2: After precedence
add_precedence_constraints(model, vars)
cp2 = ModelCheckpoint("with_precedence")
cp2.save(model, vars, ['duration', 'precedence'])
checkpoints.append(cp2)

# Can rollback if needed
if model_broken:
    model, vars = restore_from_checkpoint(checkpoints[-2])
```

## Context Management for Long Sessions

### Session State Tracking

```python
class DevelopmentSession:
    """Track state across long Claude sessions."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.completed_tasks = []
        self.current_task = None
        self.checkpoints = []
        
    def start_task(self, task_name: str):
        """Mark task start."""
        self.current_task = {
            'name': task_name,
            'start': datetime.now(),
            'files_modified': []
        }
        
    def complete_task(self, summary: str):
        """Mark task completion."""
        self.current_task['end'] = datetime.now()
        self.current_task['summary'] = summary
        self.completed_tasks.append(self.current_task)
        self.current_task = None
        
    def get_session_summary(self):
        """Generate summary for Claude context."""
        return {
            'duration': datetime.now() - self.start_time,
            'tasks_completed': len(self.completed_tasks),
            'last_checkpoint': self.checkpoints[-1] if self.checkpoints else None,
            'current_focus': self.current_task['name'] if self.current_task else None
        }
```

### Claude Context Prompts

```markdown
# Resuming Development Session

"Continue from checkpoint: {checkpoint_name}
Completed so far: {completed_tasks}
Current task: {current_task}
Next planned: {next_tasks}"

# Mid-Session Context Refresh

"Current model state:
- Variables: {var_count} created
- Constraints: {constraint_types_added}
- Performance: {last_solve_time}
- Issues found: {issues_list}"
```

## Validation Gates

### After Each Increment

```python
def validate_increment(model, increment_name: str) -> bool:
    """Validation gate after each development increment."""
    
    checks = {
        'compiles': check_model_compiles(model),
        'feasible': check_model_feasible(model),
        'performance': check_performance_acceptable(model),
        'tests_pass': run_increment_tests(increment_name),
        'standards': check_standards_compliance(increment_name)
    }
    
    failed = [k for k, v in checks.items() if not v]
    
    if failed:
        print(f"Increment '{increment_name}' failed: {failed}")
        return False
        
    print(f"✓ Increment '{increment_name}' validated")
    return True
```

## Best Practices

### 1. Increment Size
- **Good**: Add one constraint type (5-30 lines)
- **Bad**: Add entire phase at once (100+ lines)

### 2. Testing Between Increments
- Always run solver after adding constraints
- Check solution quality doesn't degrade
- Verify performance stays acceptable

### 3. Documentation During Development
```python
# Document each increment
"""
Increment 3: Added resource capacity constraints
- What: Limits on machine capacity per time window
- Why: Prevents overloading machines
- Impact: +15% solve time, better resource utilization
- Tests: test_resource_capacity_*
"""
```

### 4. Rollback Strategy
```python
# Before risky changes
git commit -m "Checkpoint before adding complex constraints"
backup_model = copy.deepcopy(model)

# After testing
if not validate_increment(model, "complex_constraints"):
    model = backup_model  # Rollback
    # Try different approach
```

## Common Incremental Patterns

### Pattern 1: Constraint Complexity Ramp
```
1. Hard constraints only
2. Add soft constraints
3. Add constraint priorities
4. Fine-tune penalties
```

### Pattern 2: Data Scale Ramp
```
1. 2 jobs, 10 tasks (tiny)
2. 5 jobs, 50 tasks (small)
3. 20 jobs, 500 tasks (medium)
4. 50 jobs, 5000 tasks (large)
```

### Pattern 3: Feature Ramp
```
1. Basic scheduling
2. Add resource constraints
3. Add skill matching
4. Add shift patterns
```

## Integration with Custom Commands

Use commands to support incremental development:

```bash
# After each increment
/check-constraint {new_constraint_function}
/test-constraint {new_constraint_function}
/profile-solver  # Ensure performance acceptable

# If issues arise
/trace-infeasible
/debug-variables
/suggest-redundant
```

## Session Management Example

```python
# Start of session
session = DevelopmentSession()
session.start_task("Add maintenance constraints")

# During development
/add-constraint maintenance_window
# ... implement ...
/test-constraint maintenance_window

# End of task
session.complete_task("Added maintenance windows with tests")

# Context for Claude
print(session.get_session_summary())
```