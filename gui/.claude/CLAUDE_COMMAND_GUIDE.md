# Claude Command Integration Guide for OR-Tools Solver

This guide explains how Claude should recognize and respond to custom commands in the Fresh OR-Tools Solver project.

## Command System Architecture

### Python Implementation
The OR-Tools commands are implemented in `.claude/commands/ortools_commands.py` with:
- Full command implementations for 12+ specialized commands
- Alias support for quick access
- Workflow commands for common tasks
- Context-aware responses

### Command Documentation
Command specifications are in `.claude/commands/ortools/`:
- `index.md` - Complete command reference
- Individual `.md` files for each major command
- Pattern matching and output templates

## Command Recognition Patterns

### 1. Direct Command Invocation
When users type commands starting with `/`, Claude should:
1. Recognize the command format: `/command-name [arguments]`
2. Parse any arguments or options
3. Execute the appropriate action
4. Provide command-specific responses

### 2. Natural Language Recognition
Claude should also recognize when users are asking for command-like actions in natural language:
- "Can you check the project structure?" → `/project-structure`
- "What's the current solver status?" → `/solver-status`
- "Run the tests" → `/test`
- "Show me the constraint patterns" → `/constraint-patterns`

## Command Response Templates

### `/project-structure` - Analyze Project Organization
**Recognition patterns:**
- `/project-structure`
- "show me the project structure"
- "analyze the codebase organization"
- "what's the folder structure?"

**Response template:**
```
I'll analyze the OR-Tools solver project structure for you.

## Project Overview
This is a modular constraint programming scheduling solver using Google OR-Tools CP-SAT framework.

## Core Structure:
[Use LS and Glob to explore, then format as:]

📁 **src/** - Main source code
  📁 **solver/** - Core solver implementation
    - `core/` - Main solver orchestration
    - `constraints/` - Modular constraint functions (Phase 1-3)
    - `models/` - Data models (Job, Task, Machine)
    - `utils/` - Time calculations and utilities
  📁 **data/** - Data layer
    - `loaders/` - Database and file loaders
    - `schemas/` - Supabase schemas

📁 **tests/** - Comprehensive test suite
  - `unit/` - Unit tests for each component
  - `integration/` - Phase integration tests
  - `performance/` - Performance benchmarks

## Current Phase: Phase 1
- ✅ Basic scheduling with timing constraints
- ✅ Precedence relationships
- ✅ Machine assignments
- 🔄 Next: Resource capacity (Phase 2)
```

### `/solver-status` - Check Solver Implementation Status
**Recognition patterns:**
- `/solver-status`
- "what's the implementation status?"
- "which constraints are done?"
- "show solver progress"

**Response template:**
```
I'll check the current solver implementation status.

## OR-Tools Solver Status

### Phase 1 Implementation (Current)
[Read relevant files then report:]

✅ **Completed Components:**
- Core solver class (`FreshSolver`)
- Basic constraint functions:
  - `add_timing_constraints()` - Task duration enforcement
  - `add_precedence_constraints()` - Task ordering
  - `add_assignment_constraints()` - Machine allocation
- Data models with validation
- Supabase integration

🔄 **In Progress:**
- Performance optimization
- Search strategies
- Solution quality metrics

### Variable Status:
- `task_starts[(job_id, task_id)]` - ✅ Implemented
- `task_ends[(job_id, task_id)]` - ✅ Implemented
- `task_assigned[(job_id, task_id, machine_id)]` - ✅ Implemented

### Test Coverage:
[Run pytest with coverage if needed]
- Unit tests: [X]% coverage
- Integration tests: Phase 1 complete
- Performance benchmarks: Meeting targets
```

### `/constraint-patterns` - Show Constraint Implementation Patterns
**Recognition patterns:**
- `/constraint-patterns`
- "show me constraint examples"
- "how do I add constraints?"
- "constraint function patterns"

**Response template:**
```
Here are the standard constraint patterns for the OR-Tools solver:

## Constraint Function Pattern

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
    """
    # Implementation (max 30 lines)
```

## Example Implementation:

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

## Key Rules:
1. One constraint type per function
2. Maximum 30 lines of code
3. Clear variable naming
4. Document constraints in docstring
5. Type hints required
```

### `/test` - Run Tests
**Recognition patterns:**
- `/test`
- "run the tests"
- "test the solver"
- "check if tests pass"

**Response template:**
```
I'll run the tests for the OR-Tools solver.

[Execute: python scripts/run_tests.py or python -m pytest]

## Test Results

### Unit Tests:
✅ test_constraints.py - All constraint functions tested
✅ test_data_models.py - Data validation working
✅ test_solver.py - Core solver functionality verified

### Integration Tests:
✅ Phase 1 Integration - Complete scheduling working
  - Small dataset (5 jobs): Solved in X.Xs
  - Medium dataset (20 jobs): Solved in X.Xs

### Performance Benchmarks:
✅ Tiny dataset: X.Xs (target: <1s)
✅ Small dataset: X.Xs (target: <10s)
✅ Medium dataset: X.Xs (target: <60s)

### Coverage Report:
- Overall: X%
- Constraints: X%
- Core solver: X%
```

### `/check-standards` - Verify Code Standards Compliance
**Recognition patterns:**
- `/check-standards`
- "check if code follows standards"
- "verify coding standards"
- "standards compliance"

**Response template:**
```
I'll check the code against OR-Tools development standards.

## Standards Compliance Check

### Variable Naming ✅/❌
[Check files for compliance]
- Decision variables use descriptive dictionaries ✅
- Constants use UPPER_CASE ✅
- Helper structures use lowercase_with_underscores ✅

### Constraint Functions ✅/❌
- Each function handles one constraint type ✅
- Functions start with `add_` prefix ✅
- All have complete type hints ✅
- Docstrings list constraints added ✅
- No function exceeds 30 lines ✅

### Testing Standards ✅/❌
- Unit tests for each constraint ✅
- Integration tests per phase ✅
- Performance benchmarks included ✅

### Issues Found:
[List any standards violations]

### Recommendations:
[Suggest fixes for any issues]
```

### `/performance` - Analyze Solver Performance
**Recognition patterns:**
- `/performance`
- "check solver performance"
- "how fast is the solver?"
- "performance analysis"

**Response template:**
```
I'll analyze the OR-Tools solver performance.

[Run performance tests if needed]

## Performance Analysis

### Current Performance Metrics:
| Dataset Size | Target | Actual | Status |
|-------------|--------|--------|--------|
| Tiny (2 jobs, 10 tasks) | <1s | X.Xs | ✅ |
| Small (5 jobs, 50 tasks) | <10s | X.Xs | ✅ |
| Medium (20 jobs, 500 tasks) | <60s | X.Xs | ✅ |

### Optimization Strategies Applied:
✅ Tight variable bounds based on horizon
✅ Efficient constraint formulation
✅ Search strategies defined
❌ Redundant constraints (TODO)

### Bottleneck Analysis:
[Identify slow parts]

### Recommendations:
1. Add redundant constraints for better pruning
2. Implement symmetry breaking
3. Use parallel search if available
```

## Error Handling

### Command Not Found
When a command isn't recognized:
```
I don't recognize the command `/<command>`. 

Available OR-Tools solver commands:
- `/project-structure` - Analyze project organization
- `/solver-status` - Check implementation progress
- `/constraint-patterns` - Show constraint examples
- `/test` - Run test suite
- `/check-standards` - Verify code standards
- `/performance` - Analyze solver performance

Would you like help with one of these commands?
```

### Ambiguous Natural Language
When natural language could map to multiple commands:
```
I can help you with that in a few ways:

1. `/solver-status` - Check which solver components are implemented
2. `/test` - Run the test suite to verify functionality
3. `/performance` - Analyze solver performance metrics

Which would you like me to do?
```

## Integration with Context Files

### Reading Project Instructions
Always check `CLAUDE.md` and `.claude/STANDARDS.md` for project-specific guidance:

```python
# When implementing constraints, follow standards:
- Max 30 lines per function
- One constraint type per function
- Complete docstrings required
```

### Using Templates
Reference `.claude/TEMPLATES.md` for code generation patterns specific to OR-Tools.

### Following Workflows
Check `.claude/WORKFLOWS.md` for phase implementation procedures.

## Quick Command Reference Card

```
OR-Tools Solver Commands:
├── /project-structure    - View project organization
├── /solver-status       - Implementation progress
├── /constraint-patterns - Constraint examples
├── /test               - Run test suite
├── /check-standards    - Verify code compliance
└── /performance        - Performance analysis

Natural language alternatives work too:
- "Show me the project structure"
- "What's implemented so far?"
- "Run the tests"
```

## Best Practices for Claude

1. **Always acknowledge the command** - Let users know you understood their request
2. **Execute relevant tools** - Use Read, Bash, Glob as needed to gather information
3. **Format responses clearly** - Use the templates but adapt to actual findings
4. **Provide actionable insights** - Don't just report status, suggest next steps
5. **Reference project standards** - Link to STANDARDS.md when relevant
6. **Stay project-focused** - Keep responses specific to OR-Tools solver context

## Example Conversation Flow

User: "Check how the solver is doing"

Claude: "I'll check the current solver implementation status for you.

[Executes /solver-status logic]

The OR-Tools solver is currently in Phase 1 with basic scheduling features complete. All core constraints (timing, precedence, and assignment) are implemented and tested. The solver meets performance targets for small to medium datasets.

Would you like me to:
1. Show you specific constraint implementations?
2. Run the test suite?
3. Check what's planned for Phase 2?"

This creates natural, helpful interactions while leveraging the custom command system.

## Available OR-Tools Commands

### Core Commands
- `/project-structure` - Analyze project organization
- `/solver-status` - Check implementation progress  
- `/constraint-patterns` - Show constraint templates
- `/test` - Run test suite
- `/check-standards` - Verify code compliance
- `/performance` - Analyze solver performance

### Development Commands
- `/add-constraint <name>` - Generate new constraint function
- `/test-constraint <name>` - Generate constraint tests
- `/debug-variables` - Display variable states
- `/trace-infeasible` - Debug infeasible models
- `/explain-solution` - Convert output to business terms

### Optimization Commands
- `/suggest-redundant` - Identify performance constraints
- `/tighten-bounds` - Optimize variable bounds
- `/optimize-search` - Improve search strategies
- `/analyze-complexity` - Big O analysis

### Quick Aliases
- `/ac` → `/add-constraint`
- `/tc` → `/test-constraint`
- `/ps` → `/project-structure`
- `/ss` → `/solver-status`

### Workflow Commands
- `/dev-flow` - Complete development workflow
- `/debug-slow` - Performance debugging workflow
- `/fix-infeasible` - Infeasibility resolution workflow

For detailed command documentation, see `.claude/commands/ortools/index.md`