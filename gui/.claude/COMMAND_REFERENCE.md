# OR-Tools Command Reference

This document explains how to use the custom OR-Tools commands with Claude.

## Setup Status

Currently, these commands are implemented as Python functions in `.claude/commands/ortools_commands.py` but are not yet registered as actual slash commands in Claude.

## How to Use Commands Now

Since slash commands need to be registered at the Claude system level, you can use these patterns:

### Method 1: Direct Request
Instead of `/ac maintenance_window`, say:
- "Add a maintenance window constraint following our templates"
- "Generate constraint for maintenance_window using STANDARDS.md"

### Method 2: Reference the Command
- "Use the /add-constraint logic for maintenance_window"
- "Apply /trace-infeasible workflow to debug my model"

### Method 3: Task Tool
The Task tool with specific agents can execute similar workflows:
- Use `implementation-specialist` for constraint development
- Use `debugging-specialist` for troubleshooting
- Use `system-architect` for design decisions

## Command Quick Reference

### Constraint Development
| Command | Alias | Purpose | Example |
|---------|-------|---------|---------|
| `/add-constraint` | `/ac` | Generate constraint function | `/ac shift_schedule` |
| `/test-constraint` | `/tc` | Generate unit tests | `/tc shift_schedule` |
| `/check-constraint` | `/cc` | Validate against standards | `/cc add_precedence_constraints` |
| `/list-constraints` | `/lc` | List all constraints | `/lc` |

### Debugging
| Command | Alias | Purpose | Example |
|---------|-------|---------|---------|
| `/trace-infeasible` | `/ti` | Debug infeasible model | `/ti` |
| `/explain-solution` | `/es` | Business explanation | `/es` |
| `/profile-solver` | `/ps` | Performance analysis | `/ps` |
| `/debug-variables` | `/dv` | Variable inspection | `/dv` |

### Optimization
| Command | Alias | Purpose | Example |
|---------|-------|---------|---------|
| `/suggest-redundant` | `/sr` | Redundant constraints | `/sr` |
| `/tighten-bounds` | `/tb` | Optimize bounds | `/tb` |
| `/optimize-search` | `/os` | Search strategies | `/os` |
| `/analyze-complexity` | `/cx` | Big O analysis | `/cx` |

### Workflows
| Command | Purpose | Example |
|---------|---------|---------|
| `/dev-flow` | Complete development cycle | `/dev-flow resource_capacity` |
| `/debug-slow` | Performance optimization | `/debug-slow` |
| `/fix-infeasible` | Infeasibility resolution | `/fix-infeasible` |

## Making Commands Work

Until these are registered as system-level slash commands, I will:

1. **Recognize the pattern** - When you type `/ac maintenance_window`
2. **Execute the logic** - Follow the command's implementation
3. **Provide expected output** - As defined in COMMANDS.md

## Examples

### Example 1: Constraint Development
```
You: /ac maintenance_window
Claude: [Generates complete constraint function following templates]

You: /tc maintenance_window  
Claude: [Generates comprehensive unit tests]

You: /cc add_maintenance_window_constraints
Claude: [Validates against STANDARDS.md checklist]
```

### Example 2: Performance Debugging
```
You: My solver takes 120 seconds. /debug-slow
Claude: [Executes full performance workflow]
1. Profiles solver
2. Analyzes bounds
3. Suggests redundant constraints
4. Recommends search strategy
```

### Example 3: Quick Aliases
```
You: /ti
Claude: [Starts infeasibility tracing workflow]

You: /ps
Claude: [Profiles solver performance]
```

## Command Implementation Details

The actual command logic is in:
```
.claude/commands/ortools_commands.py
```

Each command returns a detailed prompt that I execute to provide the expected functionality.