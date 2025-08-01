# OR-Tools Solver Commands

Commands specifically designed for the Fresh OR-Tools CP-SAT solver project.

## Project Understanding Commands

### `/project-structure`
Analyzes and displays the project organization with OR-Tools context.
- Shows folder structure with explanations
- Highlights current phase implementation
- Identifies key solver components

### `/solver-status`
Provides detailed implementation status by phase.
- Shows completed constraints and variables
- Lists work in progress
- Tracks test coverage and performance
- Identifies next steps

### `/constraint-patterns`
Displays standard patterns for constraint implementation.
- Shows required function structure
- Provides working examples
- Enforces STANDARDS.md rules
- Includes testing patterns

## Development Commands

### `/add-constraint <name>`
Generates a new constraint function following standards.
- Creates properly formatted function
- Includes comprehensive docstring
- Ensures ≤30 line implementation
- Suggests integration steps

### `/test-constraint <name>`
Generates unit tests for constraint functions.
- Creates test following patterns
- Includes edge cases
- Uses proper assertions
- Follows test naming conventions

### `/check-standards`
Verifies code compliance with STANDARDS.md.
- Checks constraint function rules
- Validates naming conventions
- Ensures proper documentation
- Reports violations

## Performance & Debugging Commands

### `/performance`
Analyzes solver performance metrics.
- Shows current benchmarks
- Identifies bottlenecks
- Suggests optimizations
- Tracks against targets

### `/debug-variables`
Displays current variable state for debugging.
- Shows variable bounds and values
- Identifies constraint relationships
- Highlights suspicious patterns
- Suggests debug techniques

### `/trace-infeasible`
Guides systematic debugging of infeasible models.
- Step-by-step isolation process
- Common causes and fixes
- Data validation checks
- Solution strategies

## Advanced Analysis Commands

### `/explain-solution`
Converts solver output to business explanation.
- Translates schedule to readable format
- Shows machine utilization
- Identifies bottlenecks
- Provides optimization suggestions

### `/suggest-redundant`
Identifies redundant constraints for performance.
- Transitive precedence constraints
- Makespan bounds
- Machine load balancing
- Expected performance gains

### `/analyze-complexity`
Provides Big O analysis of the model.
- Variable complexity
- Constraint complexity
- Solver complexity
- Scalability limits

## Command Aliases

Quick shortcuts for common commands:
- `/ps` → `/project-structure`
- `/ss` → `/solver-status`
- `/cp` → `/constraint-patterns`
- `/ac` → `/add-constraint`
- `/tc` → `/test-constraint`
- `/cs` → `/check-standards`

## Workflow Commands

Compound commands for common workflows:
- `/dev-flow` → Add constraint → Test → Check standards
- `/debug-slow` → Profile → Tighten bounds → Suggest redundant
- `/fix-infeasible` → Trace infeasible → Explain solution

## Usage Tips

1. Start with `/solver-status` to understand current state
2. Use `/constraint-patterns` before implementing
3. Always `/check-standards` after coding
4. Run `/performance` to verify speed targets
5. Use `/debug-variables` when stuck

## Integration with Project

All commands are aware of:
- STANDARDS.md requirements (30-line rule, etc.)
- Current phase implementation status
- OR-Tools CP-SAT specific patterns
- Project performance targets
- Test coverage requirements