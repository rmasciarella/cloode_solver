# Context Window Management Strategies

## Overview

Optimize Claude's context window usage to maintain effectiveness throughout long development sessions. Claude has a large but finite context window that must be managed strategically.

## Context Window Zones

```
┌─────────────────────────────────────────────┐
│           Claude Context Window              │
├──────────────┬──────────────┬──────────────┤
│   Critical   │   Working    │   Archive    │
│     25%      │     50%      │     25%      │
│  Essential   │   Active     │  Reference   │
└──────────────┴──────────────┴──────────────┘
```

## Zone Definitions

### 1. Critical Zone (25%)
**Must Retain Throughout Session**
- Current task definition
- Active code being modified
- Unresolved errors/issues
- Key project constraints (STANDARDS.md summary)
- Current checkpoint state

### 2. Working Zone (50%)
**Active Development Context**
- Recent code changes
- Test results
- Current investigation paths
- Relevant documentation sections
- Recent Claude responses

### 3. Archive Zone (25%)
**Historical Reference**
- Completed tasks
- Resolved issues
- Old test results
- Previous approaches tried
- Can be summarized or discarded

## Management Strategies

### Strategy 1: Progressive Summarization

Transform verbose content into concise summaries:

```markdown
## Before (Archive Zone - 500 tokens)
"Tried implementing capacity constraints with individual boolean variables for each time slot. Created variables capacity_used[machine][time] for times 0-1000. This resulted in 10,000 variables just for capacity tracking. The solver took 45 seconds on tiny dataset. Memory usage was 2.3GB. Abandoned this approach."

## After (Critical Zone - 50 tokens)
"❌ Capacity attempt 1: Individual booleans per timeslot = 10K vars, 45s solve time. Use intervals instead."
```

### Strategy 2: Context Markers

Use markers to indicate context importance:

```markdown
## 🔴 CRITICAL: Current Issue
Model infeasible after adding maintenance windows. Task (1,2) cannot fit.

## 🟡 WORKING: Investigation
Checking maintenance windows overlap with task duration...

## 🟢 ARCHIVE: Resolved
Fixed: Maintenance window was 1 hour, task needed 2 hours.
```

### Strategy 3: Smart Truncation

Replace file contents with summaries:

```python
# Instead of showing full file (2000 tokens):
"""
Full contents of src/solver/constraints/capacity.py
[200 lines of code]
"""

# Show summary (200 tokens):
"""
src/solver/constraints/capacity.py (200 lines)
Functions:
- add_capacity_constraints() - Main entry point
- calculate_resource_usage() - Helper for usage calc
- create_capacity_intervals() - Interval creation
Key: Uses interval variables with cumulative constraint
Status: ✅ Tested and working
"""
```

## Context Management Patterns

### Pattern 1: Task-Scoped Context

```markdown
## Task Context Template

### 🎯 Current Task: {task_name}
**Goal**: {specific_goal}
**Approach**: {chosen_approach}
**Status**: {in_progress|blocked|testing}

### 📍 Current Position
File: {filepath}:{line_number}
Function: {function_name}
Last action: {last_action}

### ⚠️ Active Issues
1. {issue_1}
2. {issue_2}

### 📝 Discard After Task
- Detailed implementation attempts
- Verbose error messages
- Intermediate test results
```

### Pattern 2: Sliding Window

Maintain a sliding window of recent context:

```python
class ContextWindow:
    """Manages Claude's context window efficiently."""
    
    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens
        self.critical = []  # 25%
        self.working = []   # 50%
        self.archive = []   # 25%
        
    def add_context(self, content: str, zone: str = 'working'):
        """Add content to appropriate zone."""
        if zone == 'critical':
            self.critical.append(content)
        elif zone == 'working':
            self.working.append(content)
            self._check_working_overflow()
        else:
            self.archive.append(content)
            
    def _check_working_overflow(self):
        """Move old working content to archive."""
        if self._count_tokens(self.working) > self.max_tokens * 0.5:
            # Move oldest 25% to archive
            move_count = len(self.working) // 4
            self.archive.extend(self.working[:move_count])
            self.working = self.working[move_count:]
            
    def get_context_prompt(self) -> str:
        """Generate optimized context for Claude."""
        return f"""
## Critical Context
{self._format_critical()}

## Working Context
{self._format_working()}

## Reference (Summarized)
{self._summarize_archive()}
"""
```

### Pattern 3: Context Compression

```python
def compress_context(content: str, importance: str) -> str:
    """Compress content based on importance level."""
    
    if importance == 'critical':
        return content  # No compression
        
    elif importance == 'working':
        # Moderate compression
        return compress_code_blocks(content)
        
    elif importance == 'archive':
        # Heavy compression
        return extract_key_points(content)

def compress_code_blocks(code: str) -> str:
    """Compress code while maintaining readability."""
    lines = code.split('\n')
    
    # Keep function signatures and key logic
    compressed = []
    for line in lines:
        if any(keyword in line for keyword in 
               ['def', 'class', 'return', 'raise', 'TODO']):
            compressed.append(line)
        elif line.strip().startswith('#') and 'important' in line.lower():
            compressed.append(line)
            
    return '\n'.join(compressed)
```

## Context Window Alerts

### Usage Monitoring

```python
def monitor_context_usage() -> dict:
    """Monitor context window usage."""
    return {
        'total_tokens': estimate_current_tokens(),
        'usage_percent': estimate_current_tokens() / MAX_TOKENS * 100,
        'critical_zone': count_critical_tokens(),
        'working_zone': count_working_tokens(),
        'archive_zone': count_archive_tokens(),
        'action_needed': usage_percent > 80
    }

# Alert when nearing limit
if monitor_context_usage()['usage_percent'] > 80:
    print("⚠️ Context window 80% full. Consider creating checkpoint and summarizing.")
```

### Context Reduction Triggers

```markdown
## Automatic Context Reduction

Triggered when:
- Context usage > 80%
- Starting new major task
- After completing phase
- Before complex debugging
- Session > 2 hours

Actions:
1. Summarize completed work
2. Archive resolved issues
3. Compress verbose outputs
4. Create checkpoint
5. Clear working zone
```

## Best Practices

### 1. Preemptive Management

Don't wait for context to fill:

```markdown
## Every 30 minutes or 5 completed tasks:

"📊 Context check:
- Usage: 65%
- Can discard: Old test outputs, resolved issues
- Must retain: Current task, active errors
- Action: Compress working zone"
```

### 2. Smart Summarization Templates

```markdown
## Code File Summary Template
File: {filepath}
Size: {lines} lines, {functions} functions
Purpose: {one_line_purpose}
Key functions: {main_functions}
Status: {working|testing|complete}
Issues: {active_issues}

## Task Completion Summary
Task: {task_name}
Result: {success|partial|blocked}
Key changes: {bullet_points}
Lessons: {key_learnings}
Time: {duration}
```

### 3. Context Handoff

For session transitions:

```markdown
## Session Handoff Context

### Minimum Viable Context
1. Current file:line position
2. Active task and approach
3. Blocking issues
4. Next planned action

### Discardable Context
- Completed task details
- Resolved error messages
- Old code versions
- Detailed test outputs
```

## Integration with Checkpoints

```python
def create_context_checkpoint(session: SessionManager) -> Checkpoint:
    """Create checkpoint optimized for context management."""
    cp = session.create_checkpoint("Context Management", type='context')
    
    # Analyze current context
    usage = monitor_context_usage()
    
    # Mark content for retention/discard
    cp.context_retain = [
        f"Current task: {session.current_task}",
        f"Active issues: {get_active_issues()}",
        f"Critical code: {get_current_function()}"
    ]
    
    cp.context_discard = [
        "Completed tasks details",
        "Old error messages", 
        "Superseded approaches",
        "Verbose test outputs"
    ]
    
    return cp
```

## Context Templates

### 1. New Task Start

```markdown
## 🆕 Starting Task: {task_name}

Discarding from context:
- Previous task implementation details
- Old test results
- Resolved issues

Retaining:
- Project standards summary
- Current model state
- Key insights from previous tasks
```

### 2. Debug Session

```markdown
## 🐛 Debug Context

Critical (retain all):
- Error message
- Failing code
- Recent changes

Working (compress):
- Investigation attempts
- Test outputs

Archive (summarize):
- Previous debug sessions
```

### 3. Long Session

```markdown
## ⏱️ Long Session Management (2+ hours)

Hour 1-2: Full context maintained
Hour 2-3: Compress working zone by 50%
Hour 3+: Retain only critical + current task

Checkpoint every hour with context summary
```

## Context Recovery

If context is lost:

```python
def recover_context(checkpoint_file: str) -> str:
    """Recover minimal context from checkpoint."""
    checkpoint = load_checkpoint(checkpoint_file)
    
    return f"""
## Context Recovery from {checkpoint.name}

Critical Information:
{checkpoint.get_critical_context()}

Current State:
- Task: {checkpoint.current_task}
- Files: {checkpoint.files_modified}
- Model: {checkpoint.model_state}

Continue from:
{checkpoint.next_action}
"""
```

## Examples

### Example 1: Task Transition

```markdown
## Before Task Transition (8000 tokens)
[Detailed implementation of precedence constraints]
[Full test results]
[Debug investigation details]

## After Task Transition (800 tokens)
✅ Precedence constraints: Implemented and tested
Key insight: Transitive constraints improved performance 40%
Next: No-overlap constraints
```

### Example 2: Debug Compression

```markdown
## Before (2000 tokens)
[Full stack trace]
[Detailed variable states]
[Multiple solution attempts]

## After (200 tokens)
🐛 Issue: Circular dependency A→B→C→A
Tried: Direct removal ❌, Weak constraints ❌
Solution: Break at B→C with delayed precedence ✅
```