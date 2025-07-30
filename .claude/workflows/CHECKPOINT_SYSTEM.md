# Checkpoint System for Long Claude Sessions

## Purpose

Maintain context and continuity across extended Claude sessions, preventing loss of progress and enabling efficient session resumption.

## Checkpoint Architecture

```
┌─────────────────────────────────────────┐
│          Session Timeline               │
├─────┬─────┬─────┬─────┬─────┬─────────┤
│ CP1 │ Work│ CP2 │ Work│ CP3 │  Resume │
│Start│     │ Mid │     │ End │  Next   │
└─────┴─────┴─────┴─────┴─────┴─────────┘
```

## Checkpoint Types

### 1. Automatic Checkpoints

Triggered automatically at key moments:

```markdown
## 🔄 Automatic Checkpoint: Task Completion
**Time**: 2024-01-20 14:30
**Completed**: Added precedence constraints
**Files Modified**: 
- src/solver/constraints/precedence.py (created)
- tests/unit/test_precedence.py (created)
**Next Task**: Add no-overlap constraints
**Model State**: 150 variables, 230 constraints, FEASIBLE
```

### 2. Manual Checkpoints

User-triggered for important milestones:

```markdown
## 📍 Manual Checkpoint: Phase 1 Complete
**Time**: 2024-01-20 16:45
**Milestone**: All Phase 1 constraints implemented
**Summary**:
- ✅ Duration constraints
- ✅ Precedence constraints  
- ✅ Assignment constraints
- ✅ No-overlap constraints
**Performance**: Solving 50-task problem in 8.3s
**Ready for**: Phase 2 development
```

### 3. Context Checkpoints

For managing Claude's context window:

```markdown
## 🧠 Context Checkpoint: Session Midpoint
**Active Context**:
- Working on: No-overlap constraints
- Current file: src/solver/constraints/no_overlap.py:45
- Issue: Performance degradation with 100+ tasks
- Approach: Using interval variables instead of booleans
**Discard**: Earlier implementation attempts
**Retain**: Current approach and test results
```

## Checkpoint Implementation

### Session State Class

```python
# .claude/session_state.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import json

@dataclass
class Checkpoint:
    """Represents a development checkpoint."""
    timestamp: datetime
    type: str  # 'automatic', 'manual', 'context'
    name: str
    summary: str
    files_modified: List[str]
    model_state: Dict[str, any]
    context_retain: List[str]
    context_discard: List[str]
    
    def to_claude_prompt(self) -> str:
        """Convert checkpoint to Claude-readable format."""
        return f"""
## Checkpoint: {self.name}
Time: {self.timestamp}
Type: {self.type}

Summary: {self.summary}

Files Modified:
{chr(10).join(f'- {f}' for f in self.files_modified)}

Model State:
- Variables: {self.model_state.get('var_count', 'Unknown')}
- Constraints: {self.model_state.get('constraint_count', 'Unknown')}
- Status: {self.model_state.get('status', 'Unknown')}

Continue from here with context:
{chr(10).join(f'- {c}' for c in self.context_retain)}
"""

class SessionManager:
    """Manages long Claude sessions with checkpoints."""
    
    def __init__(self, session_name: str):
        self.session_name = session_name
        self.start_time = datetime.now()
        self.checkpoints: List[Checkpoint] = []
        self.current_task = None
        
    def create_checkpoint(self, name: str, type: str = 'automatic') -> Checkpoint:
        """Create a new checkpoint."""
        checkpoint = Checkpoint(
            timestamp=datetime.now(),
            type=type,
            name=name,
            summary="",
            files_modified=[],
            model_state={},
            context_retain=[],
            context_discard=[]
        )
        self.checkpoints.append(checkpoint)
        return checkpoint
        
    def get_resume_prompt(self) -> str:
        """Generate prompt for resuming session."""
        if not self.checkpoints:
            return "Starting new session - no previous checkpoints"
            
        last_cp = self.checkpoints[-1]
        return f"""
# Resuming Session: {self.session_name}

Last checkpoint: {last_cp.name}
Time since last: {datetime.now() - last_cp.timestamp}

{last_cp.to_claude_prompt()}

Previous checkpoints in session:
{chr(10).join(f'{i+1}. {cp.name} ({cp.type})' for i, cp in enumerate(self.checkpoints[:-1]))}
"""
```

### Checkpoint Usage Patterns

#### Pattern 1: Task-Based Checkpoints

```python
# At task start
session.current_task = "Implement resource capacity constraints"
cp = session.create_checkpoint(f"Starting: {session.current_task}")

# During task
cp.files_modified.append("src/solver/constraints/capacity.py")
cp.model_state['var_count'] = 250
cp.context_retain.append("Using interval variables for capacity")

# At task completion
cp.summary = "Successfully added capacity constraints with tests"
session.create_checkpoint(f"Completed: {session.current_task}")
```

#### Pattern 2: Debug Checkpoints

```python
# Before debugging
debug_cp = session.create_checkpoint("Pre-debug state", type='manual')
debug_cp.model_state['last_working'] = model.copy()

# After debugging
fix_cp = session.create_checkpoint("Post-debug fix")
fix_cp.summary = f"Fixed infeasibility: {root_cause}"
fix_cp.context_retain.append(f"Solution: {fix_description}")
```

#### Pattern 3: Context Window Management

```python
# When context getting large
if context_size > 0.7 * MAX_CONTEXT:
    ctx_cp = session.create_checkpoint("Context reduction", type='context')
    ctx_cp.context_discard = [
        "Earlier failed attempts",
        "Detailed debug logs",
        "Intermediate test results"
    ]
    ctx_cp.context_retain = [
        "Current working approach",
        "Key insights discovered",
        "Next steps planned"
    ]
```

## Claude Integration

### Starting Sessions

```markdown
## New Session Start Template

"Starting new OR-Tools development session.
Goal: {session_goal}
Planned tasks:
1. {task_1}
2. {task_2}
3. {task_3}

Creating initial checkpoint..."
```

### Mid-Session Checkpoints

```markdown
## Mid-Session Checkpoint Template

"📍 Checkpoint: {checkpoint_name}

Progress so far:
- ✅ {completed_item_1}
- ✅ {completed_item_2}
- 🔄 {in_progress_item}

Current focus: {current_work}
Next steps: {next_steps}

Continue? [Yes/Take break]"
```

### Resuming Sessions

```markdown
## Resume Session Template

"Resuming from checkpoint: {last_checkpoint}

Quick recap:
- Session goal: {original_goal}
- Completed: {completed_tasks}
- Current task: {current_task}
- Model state: {model_summary}

Ready to continue with: {next_action}"
```

## Best Practices

### 1. Checkpoint Frequency

- **Every 30 minutes** for long sessions
- **After each major task** completion
- **Before risky changes** (debugging, major refactors)
- **When switching contexts** (different problem areas)

### 2. Information to Capture

Essential checkpoint data:
```python
checkpoint_data = {
    'what': 'Task/feature being worked on',
    'why': 'Reason for this work',
    'where': 'Current file:line position',
    'state': 'Model feasibility and performance',
    'next': 'Planned next steps',
    'issues': 'Any blocking problems',
    'insights': 'Key learnings or discoveries'
}
```

### 3. Context Reduction Strategies

When context window fills:

```markdown
## Context Reduction Checkpoint

RETAIN:
- Current task and approach
- Working code snippets
- Unresolved issues
- Key insights/decisions

DISCARD:
- Completed task details
- Old error messages
- Superseded approaches
- Verbose test outputs
```

### 4. Session Handoff

For switching between sessions:

```python
def create_handoff_summary(session: SessionManager) -> str:
    """Create summary for session handoff."""
    return f"""
# Session Handoff: {session.session_name}

## Completed Tasks
{format_completed_tasks(session)}

## Current State
- Working on: {session.current_task}
- Model: {session.checkpoints[-1].model_state}
- Blockers: {get_blockers(session)}

## Critical Context
{get_critical_context(session)}

## Next Session Should
1. {next_step_1}
2. {next_step_2}
3. {next_step_3}
"""
```

## Integration with Commands

Checkpoints work with custom commands:

```bash
# Create checkpoint before major change
"Creating checkpoint before adding complex constraints..."

/add-constraint complex_resource_allocation

# If issues arise
/trace-infeasible
"Checkpoint available for rollback if needed"

# After successful implementation
"Checkpoint: Complex constraints working ✅"
```

## Checkpoint Storage

### File-Based Checkpoints

```python
# Save checkpoint to file
checkpoint_file = f".claude/checkpoints/{session_name}_{timestamp}.json"

def save_checkpoint(checkpoint: Checkpoint, filepath: str):
    """Persist checkpoint to file."""
    with open(filepath, 'w') as f:
        json.dump(checkpoint.__dict__, f, indent=2, default=str)

def load_checkpoint(filepath: str) -> Checkpoint:
    """Load checkpoint from file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return Checkpoint(**data)
```

### Session History

```python
# .claude/session_history.md
## Session History

### 2024-01-20: Phase 1 Implementation
- Duration: 4 hours
- Checkpoints: 12
- Completed: All Phase 1 constraints
- Key insights: Interval variables more efficient

### 2024-01-21: Performance Optimization  
- Duration: 2 hours
- Checkpoints: 6
- Completed: Reduced solve time by 60%
- Key insights: Redundant constraints crucial
```

## Examples

### Example 1: Long Implementation Session

```python
# Session start
session = SessionManager("phase_2_resources")

# Hour 1
cp1 = session.create_checkpoint("Analyzed requirements")
implement_basic_resources()

# Hour 2  
cp2 = session.create_checkpoint("Basic resources working")
add_resource_capacity()

# Hour 3 - Context getting full
cp3 = session.create_checkpoint("Context reduction", type='context')
cp3.context_discard = ["Early exploration code"]
cp3.context_retain = ["Working resource model"]

# Hour 4
cp4 = session.create_checkpoint("Session complete")
print(session.get_resume_prompt())
```

### Example 2: Debug Session

```python
# Complex debugging session
debug_session = SessionManager("infeasibility_debug")

# Checkpoint before investigation
pre_cp = debug_session.create_checkpoint("Pre-debug state")
pre_cp.model_state['working_model'] = model.copy()

# Investigation checkpoints
inv_cp1 = debug_session.create_checkpoint("Disabled precedence")
inv_cp2 = debug_session.create_checkpoint("Found issue: circular dep")

# Solution checkpoint
fix_cp = debug_session.create_checkpoint("Fixed circular dependency")
fix_cp.summary = "Removed A->B->C->A cycle"
```