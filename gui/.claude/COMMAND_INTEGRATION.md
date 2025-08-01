# OR-Tools Command System Integration Guide

## Overview

This guide explains how Claude should recognize and execute the OR-Tools custom commands. The command system transforms Claude into a specialized OR-Tools development assistant with deep knowledge of constraint programming patterns.

## Command Recognition

### How Claude Should Detect Commands

1. **Direct Commands**: When user types `/command-name [args]`
2. **Aliases**: Recognize short forms (e.g., `/ac` → `/add-constraint`)
3. **Workflow Commands**: Compound commands that execute multiple steps
4. **Context-Aware**: Commands should use current file/line information when available

### Command Processing Flow

```python
# When Claude detects a command:
1. Parse command and arguments
2. Check for aliases and expand
3. Gather context (current file, line, solver state)
4. Execute command handler
5. Return formatted response
```

## Command Implementation Details

### 1. Constraint Development Commands

#### `/add-constraint <name>` or `/ac <name>`

**Recognition Pattern**: `/add-constraint` or `/ac` followed by constraint name

**Claude's Response Process**:
1. Ask clarifying questions if needed
2. Generate constraint function using TEMPLATES.md
3. Ensure compliance with STANDARDS.md
4. Provide integration instructions

**Example Interaction**:
```
User: /add-constraint maintenance_window
Claude: [Generates complete constraint function with docstring, suggests where to integrate]
```

#### `/test-constraint <name>` or `/tc <name>`

**Recognition Pattern**: `/test-constraint` or `/tc` followed by constraint name

**Claude's Response**:
- Generate comprehensive unit tests
- Include GIVEN-WHEN-THEN structure
- Add edge cases
- Provide test execution commands

#### `/check-constraint <function_name>` or `/cc <function_name>`

**Recognition Pattern**: `/check-constraint` or `/cc` followed by function name

**Claude's Analysis**:
- Verify naming convention
- Check line count (≤30)
- Validate docstring completeness
- Ensure type hints present
- Suggest improvements

#### `/list-constraints` or `/lc`

**Recognition Pattern**: `/list-constraints` or `/lc` (no arguments)

**Claude's Response**:
- Scan solver.py or specified file
- List all constraint functions
- Show dependencies
- Display call order

### 2. Debugging Commands

#### `/trace-infeasible` or `/ti`

**Recognition Pattern**: `/trace-infeasible` or `/ti`

**Claude's Systematic Process**:
1. Remove objective function
2. Disable constraints by restrictiveness
3. Binary search for conflicts
4. Validate data
5. Suggest solutions

#### `/explain-solution` or `/es`

**Recognition Pattern**: `/explain-solution` or `/es`

**Claude's Explanation Includes**:
- Timeline overview
- Machine utilization
- Bottleneck analysis
- Optimization opportunities
- Business-friendly language

#### `/profile-solver` or `/ps`

**Recognition Pattern**: `/profile-solver` or `/ps`

**Claude's Analysis**:
- Model statistics
- Time breakdown
- Bottleneck identification
- Scaling analysis
- Optimization priorities

#### `/debug-variables` or `/dv`

**Recognition Pattern**: `/debug-variables` or `/dv`

**Claude's Output**:
- Variable bounds and values
- Assignment states
- Suspicious patterns
- Debug recommendations

### 3. Optimization Commands

#### `/suggest-redundant` or `/sr`

**Recognition Pattern**: `/suggest-redundant` or `/sr`

**Claude's Suggestions**:
- Transitive constraints
- Bound propagation
- Symmetry breaking
- Domain-specific redundancies

#### `/tighten-bounds` or `/tb`

**Recognition Pattern**: `/tighten-bounds` or `/tb`

**Claude's Analysis**:
- Current vs optimal bounds
- Calculation methods
- Implementation code
- Expected improvements

#### `/optimize-search` or `/os`

**Recognition Pattern**: `/optimize-search` or `/os`

**Claude's Recommendations**:
- Problem-specific strategies
- Variable/value selection
- Solver parameters
- Performance comparison

#### `/analyze-complexity` or `/cx`

**Recognition Pattern**: `/analyze-complexity` or `/cx`

**Claude's Analysis**:
- Variable complexity: O(n×m)
- Constraint complexity by type
- Search space size
- Scalability limits

### 4. Workflow Commands

#### `/dev-flow <constraint_name>`

**Executes**: `/add-constraint` → `/test-constraint` → `/check-constraint`

#### `/debug-slow`

**Executes**: `/profile-solver` → `/tighten-bounds` → `/suggest-redundant`

#### `/fix-infeasible`

**Executes**: `/trace-infeasible` → `/explain-solution` → suggestions

## Context Awareness

### Information Claude Should Track

```python
context = {
    "current_file": "src/solver/constraints.py",
    "current_line": 145,
    "solver_output": "Status: OPTIMAL...",
    "model_info": {
        "num_tasks": 500,
        "num_machines": 10,
        "constraints": ["duration", "precedence", "no_overlap"]
    }
}
```

### Using Context in Commands

1. **File-Aware**: Reference specific lines when suggesting edits
2. **State-Aware**: Use solver output for `/explain-solution`
3. **Model-Aware**: Tailor suggestions to problem size

## Response Formatting

### Standard Response Structure

```markdown
## 🎯 Command Result: /command-name

### 📊 Analysis/Output
[Main content]

### 💡 Recommendations
[Actionable suggestions]

### 🔗 Next Steps
[Related commands or actions]
```

### Code Generation Format

```python
## Generated Code:

```python
# Generated code here
```

### Integration Instructions:
1. Add to file: `path/to/file.py`
2. Import in: `solver.py`
3. Call after: [specific location]
```

## Error Handling

### Common Error Responses

1. **Missing Arguments**:
   ```
   ❌ Please specify constraint name: /add-constraint <name>
   ```

2. **Unknown Command**:
   ```
   Unknown command: /xyz. Type /help for available commands.
   ```

3. **Missing Context**:
   ```
   ❌ Please provide solver output or solution data to explain
   ```

## Integration with CLAUDE.md

### Command References in CLAUDE.md

The main CLAUDE.md file should reference these commands in the Custom Commands section. When users ask about available commands, Claude should:

1. List all commands with descriptions
2. Show aliases
3. Provide usage examples
4. Suggest relevant commands based on context

### Workflow Integration

Commands should integrate with the workflows defined in WORKFLOWS.md:

1. **Development Workflow**: Use `/dev-flow` for new constraints
2. **Debugging Workflow**: Use `/debug-slow` for performance
3. **Infeasibility Workflow**: Use `/fix-infeasible` for issues

## Best Practices for Claude

### 1. Proactive Command Suggestion

When users describe a problem, suggest relevant commands:
- "My solver is slow" → Suggest `/profile-solver`
- "Model is infeasible" → Suggest `/trace-infeasible`
- "Need new constraint" → Suggest `/add-constraint`

### 2. Command Chaining

After one command, suggest logical next steps:
- After `/add-constraint` → Suggest `/test-constraint`
- After `/profile-solver` → Suggest `/tighten-bounds`

### 3. Context Preservation

Maintain context between commands:
```
User: /profile-solver
Claude: [Shows bottleneck in no-overlap constraints]
User: /suggest-redundant
Claude: Based on the no-overlap bottleneck identified earlier...
```

### 4. Educational Responses

Include learning opportunities:
- Explain why a constraint is structured that way
- Show the mathematical formulation
- Reference relevant STANDARDS.md sections

## Testing Commands

### How Claude Should Test Commands

1. **Unit Tests**: Each command has tests in `test_ortools_commands.py`
2. **Integration Tests**: Test command workflows
3. **Context Tests**: Verify context handling

### Running Tests

```bash
# Run command system tests
python -m pytest tests/test_ortools_commands.py -v

# Run specific test
python -m pytest tests/test_ortools_commands.py::TestORToolsCommands::test_add_constraint_command -v
```

## Command Evolution

### Adding New Commands

1. Add to `ortools_commands.py`
2. Update COMMANDS.md
3. Add tests
4. Update this guide

### Deprecating Commands

1. Mark as deprecated in COMMANDS.md
2. Suggest replacement command
3. Maintain for backwards compatibility

## Quick Reference Card

```
CONSTRAINT DEVELOPMENT
/ac <name>          - Add new constraint
/tc <name>          - Create tests
/cc <function>      - Check standards
/lc                 - List all constraints

DEBUGGING
/ti                 - Trace infeasible
/es                 - Explain solution
/ps                 - Profile performance
/dv                 - Debug variables

OPTIMIZATION
/sr                 - Suggest redundant
/tb                 - Tighten bounds
/os                 - Optimize search
/cx                 - Analyze complexity

WORKFLOWS
/dev-flow <name>    - Full development
/debug-slow         - Performance fix
/fix-infeasible     - Resolve infeasible
```

## Conclusion

This command system transforms Claude into a specialized OR-Tools assistant. By recognizing and executing these commands, Claude provides structured, consistent, and expert guidance for constraint programming development.