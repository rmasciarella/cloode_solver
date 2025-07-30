# CLAUDE.md
@.claude/STANDARDS.md
@.claude/COMMANDS.md
@.claude/CONTEXT.md
@.claude/TEMPLATES.md
@.claude/WORKFLOWS.md
@.claude/PROMPTS.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**IMPORTANT**: This project uses UV for Python package management. All Python commands must be prefixed with `uv run` (e.g., `uv run python script.py`, `uv run python -m pytest`).

### Running Tests
```bash
# Run all tests with coverage
uv run python run_tests.py

# Run specific test file
uv run python -m pytest tests/unit/test_constraints.py -v

# Run single test
uv run python -m pytest tests/unit/test_solver.py::test_solver_init -v
```

### Running the Solver
```bash
# Run with test data from database
uv run python solver.py

# Load test data into database
uv run python populate_test_data.py
```

### Development Commands
```bash
# Code Quality Tools (Complete Type Safety Pipeline)
make lint                      # Complete quality check: ruff + black + mypy (REQUIRED before commits)
ruff check .                   # Run linting only
ruff check . --fix             # Auto-fix linting issues
black .                        # Format all Python files
black --check .                # Check formatting without changes
mypy src/                      # Type check the source code (must pass with 0 errors)

# Individual tools for debugging
ruff format .                  # Format files and handle type annotation line lengths
```

## Architecture

This is a constraint programming scheduling solver using Google OR-Tools CP-SAT framework. The project follows a phased development approach:

- **Phase 1** (current): Basic job-shop scheduling with timing, precedence, and machine assignment
- **Future phases**: Resource capacity, skills matching, shift constraints, etc.

### Core Components

1. **Data Models** (`data_models.py`): Dataclasses for Job, Task, Machine, SchedulingProblem
   - All time durations are stored as 15-minute intervals
   - Validation happens in `__post_init__` methods

2. **Constraint Functions** (`constraints.py`): Modular functions that each add one type of constraint
   - Follow strict naming: `add_<constraint_type>_constraints()`
   - Maximum 30 lines per function
   - Must document constraints added in docstring

3. **Solver** (`solver.py`): Main FreshSolver class orchestrates the solving process
   - Creates decision variables (task_starts, task_ends, task_assigned, etc.)
   - Applies constraints in dependency order
   - Uses search strategies for performance

4. **Database Integration** (`db_loader.py`): Supabase client for loading/saving data
   - Uses environment variables for connection
   - Test data setup via SQL scripts

5. **Type Safety** (`typing` integration): Comprehensive mypy coverage
   - 100% type safety maintained (0 mypy errors across 34 source files)
   - Centralized type aliases for OR-Tools structures
   - ortools-stubs for proper CP-SAT typing

### Key Design Patterns

1. **Variable Naming Convention**:
   ```python
   task_starts[(job_id, task_id)]  # When task starts
   task_ends[(job_id, task_id)]    # When task ends
   task_assigned[(job_id, task_id, machine_id)]  # Boolean assignment
   ```

2. **Time Handling**: All durations converted to 15-minute intervals
   - Horizon includes 20% buffer
   - Use `solver_utils.py` for time calculations

3. **Performance Requirements**:
   - Tiny dataset (2 jobs, 10 tasks): < 1 second
   - Small dataset (5 jobs, 50 tasks): < 10 seconds
   - Medium dataset (20 jobs, 500 tasks): < 60 seconds

### Testing Strategy

- Unit tests for each constraint function
- Integration tests for complete phases
- Performance benchmarks with different dataset sizes
- Test fixtures in `tests/conftest.py`

## Important Standards

Refer to `STANDARDS.md` for comprehensive coding standards including:
- Constraint function rules (one constraint type per function, max 30 lines)
- Variable naming conventions
- **Type safety requirements (all functions must be fully typed)**
- Testing patterns
- Error handling approaches
- Performance optimization techniques

## Dependencies

- Python 3.x
- ortools (Google OR-Tools)
- ortools-stubs (type annotations for mypy)
- supabase (for database)
- python-dotenv (environment variables)
- pytest (testing)

Install with: `uv add ortools ortools-stubs supabase python-dotenv pytest pytest-cov ruff black mypy`

**Note**: ortools-stubs provides proper type hints for OR-Tools CP-SAT framework, essential for achieving 100% type safety.

## Custom Commands for OR-Tools Development

Claude is configured with specialized commands that transform it into an OR-Tools development expert. These commands provide structured, consistent guidance following best practices.

### Command System Overview
- **Implementation**: `.claude/commands/ortools_commands.py`
- **Documentation**: `.claude/COMMANDS.md`, `.claude/COMMAND_REFERENCE.md`
- **Examples**: `.claude/COMMAND_EXAMPLES.md`

### Constraint Development Commands
- `/add-constraint <name>` or `/ac <name>` - Generate constraint function following STANDARDS.md
- `/test-constraint <name>` or `/tc <name>` - Create comprehensive unit tests
- `/check-constraint <function>` or `/cc <function>` - Validate against standards
- `/list-constraints` or `/lc` - Show all constraints in model

### Solver Debugging Commands
- `/trace-infeasible` or `/ti` - Systematic infeasibility analysis
- `/explain-solution` or `/es` - Business-friendly solution explanation
- `/profile-solver` or `/ps` - Performance bottleneck analysis
- `/debug-variables` or `/dv` - Variable state inspection

### Performance Optimization Commands
- `/suggest-redundant` or `/sr` - Identify helpful redundant constraints
- `/tighten-bounds` or `/tb` - Optimize variable bounds
- `/optimize-search` or `/os` - Search strategy recommendations
- `/analyze-complexity` or `/cx` - Big O complexity analysis

### Workflow Commands (Compound)
- `/dev-flow <name>` - Complete development cycle (add → test → check)
- `/debug-slow` - Performance optimization (profile → bounds → redundant)
- `/fix-infeasible` - Infeasibility resolution (trace → explain)

### Command Usage Examples
```bash
# Quick constraint development
/ac maintenance_window
/tc maintenance_window
/cc add_maintenance_window_constraints

# Performance debugging
/ps                    # Profile to find bottlenecks
/tb                    # Get bound tightening suggestions
/sr                    # Add redundant constraints

# Using aliases for speed
/ac shift_schedule     # Same as /add-constraint
/ti                    # Same as /trace-infeasible
```

### How Commands Work
1. Claude recognizes command patterns (e.g., `/command-name args`)
2. Executes appropriate analysis or code generation
3. Returns formatted, actionable output
4. Suggests logical next commands
5. Maintains context between related commands

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

## Troubleshooting Guide

### Model Infeasibility
**Symptom**: Solver returns INFEASIBLE status
**Solution**: Ask Claude: "Help me trace infeasibility by systematically disabling constraints. Start with the most restrictive ones like narrow time windows or tight precedences."

### Slow Solver Performance
**Symptom**: Solver takes > 60 seconds on medium datasets
**Solutions**:
1. "Profile my model with solver.SolveWithSolutionCallback and identify bottlenecks"
2. "Analyze my variable bounds - are any unnecessarily large?"
3. "Suggest redundant constraints that could help prune the search space"

### Memory Issues
**Symptom**: Out of memory errors with large datasets
**Solution**: "Analyze my variable creation patterns and suggest ways to reduce variable count. Consider interval variables vs boolean arrays."

### Constraint Conflicts
**Symptom**: Valid business rules create unsolvable model
**Solution**: "Help me identify conflicting constraints by creating a minimal reproduction case"

### No Solution Found (Timeout)
**Symptom**: Solver times out without finding solution
**Solutions**:
1. "Suggest a search strategy based on my problem structure"
2. "Help me add solver hints for likely good solutions"
3. "Identify if I should increase time limit or refactor model"

### Unit Test Failures
**Symptom**: Constraint tests fail after changes
**Solution**: "Debug why this constraint test fails. Check if the test assumptions still match the implementation."

### Integration Issues
**Symptom**: Individual constraints work but fail when combined
**Solution**: "Create an integration test that reproduces this issue with minimal constraints"