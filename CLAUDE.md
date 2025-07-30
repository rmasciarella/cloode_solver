# CLAUDE.md
@.claude/STANDARDS.md
@.claude/COMMANDS.md  
@.claude/CONTEXT.md
@.claude/TEMPLATES.md
@.claude/WORKFLOWS.md
@.claude/PROMPTS.md
@.claude/DEVELOPMENT.md
@.claude/TROUBLESHOOTING.md

This file provides concise guidance to Claude Code when working with this OR-Tools constraint programming solver optimized for template-based scheduling.

## Essential Commands

**CRITICAL**: Use UV prefix for all Python commands: `uv run python script.py`

```bash
# Core Development Workflow
make lint                    # Complete quality check: ruff + black + mypy (REQUIRED)
uv run python run_tests.py   # Run all tests with coverage
uv run python solver.py      # Run solver with test data

# Template Development (5-8x Performance Gains)
uv run python scripts/validate_template_performance.py  # Benchmark templates
/template-benchmark <template_id>                       # Claude command for analysis
```

## Project Architecture ⚡

**Template-First Constraint Programming Solver** using Google OR-Tools CP-SAT for parallel identical job scheduling with 5-8x performance improvements over legacy approaches.

- **Primary**: Template-based optimization (current focus)
- **Legacy**: Traditional job-shop scheduling (backward compatibility)
- **Framework**: OR-Tools CP-SAT with 100% type safety (mypy)

## Template Development Workflow (NEW STANDARD)

All development follows template-first methodology for optimal performance:

1. **Create Template**: Use `TemplateDatabaseLoader` with existing database structure
2. **Benchmark**: Validate with `scripts/validate_template_performance.py`
3. **Optimize**: Tune CP-SAT parameters using `/template-optimize-params`
4. **Deploy**: Store blessed parameters with `/template-promote-params`

### Template Optimization Priority
1. **Symmetry Breaking** (highest impact): Manual lexicographical ordering
2. **Parameter Tuning** (medium impact): `num_search_workers`, `search_branching`
3. **Solution Hinting** (specialized): Template re-solving scenarios

### Performance Targets
- Simple Templates (5-10 tasks): < 1s for 10+ instances
- Medium Templates (20-50 tasks): < 10s for 5+ instances
- Complex Templates (100+ tasks): < 60s for 3+ instances

## Cross-Session Context Preservation

**Template Development Sessions** - Always preserve optimization history:

```
"Continue template optimization for {template_id}.
Last session: {baseline_time}s → {current_time}s ({speedup}x improvement)
Techniques applied: {optimization_list}
Current focus: {next_optimization_area}"

Checkpoint every 30 minutes:
"Template {template_id} checkpoint:
- Performance: {baseline} → {current} ({improvement}x)
- Status: {blessed|experimental|testing}
- Next: {pending_optimizations}"
```

## Quick Command Reference

See `.claude/COMMANDS.md` for complete list. Essential shortcuts:
```bash
# Constraint Development
/ac <name>     # Add constraint following STANDARDS.md
/tc <name>     # Generate unit tests
/cc <function> # Check against standards

# Template Optimization ⚡
/template-benchmark <template_id>    # Performance analysis
/template-optimize-params <template_id>  # Parameter tuning
/template-promote-params <template_id> <params.json>  # Deploy to production

# Debugging
/ti            # Trace infeasible model
/ps            # Profile solver performance
/debug-slow    # Complete performance workflow
```

## Type Safety (100% Compliance)

All code must pass `mypy src/` with 0 errors. Use centralized type aliases from `.claude/TEMPLATES.md`.

```python
# Standard imports for constraint functions
from ortools.sat.python import cp_model
from .types import TaskStartDict, TaskEndDict, TaskKey  # Centralized aliases
```

## Key Standards

**All functions must follow STANDARDS.md:**
- Constraint functions: max 30 lines, single responsibility  
- Variable naming: `task_starts[(job_id, task_id)]`
- Type safety: 100% mypy compliance required
- Time units: 15-minute intervals throughout
- Testing: GIVEN-WHEN-THEN pattern

## Architecture Files Reference

- **Development Details**: `.claude/DEVELOPMENT.md` - Core components, design patterns, testing
- **Troubleshooting**: `.claude/TROUBLESHOOTING.md` - Debug workflows, common issues
- **Complete Workflows**: `.claude/WORKFLOWS.md` - Step-by-step development processes
- **Standards**: `.claude/STANDARDS.md` - Coding standards, type safety, performance
- **Commands**: `.claude/COMMANDS.md` - Complete OR-Tools command system
- **Templates**: `.claude/TEMPLATES.md` - Code generation templates with type aliases
- **Context**: `.claude/CONTEXT.md` - Domain knowledge, edge cases, performance insights
- **Prompts**: `.claude/PROMPTS.md` - Effective prompt patterns

## Dependencies

Install: `uv add ortools ortools-stubs supabase python-dotenv pytest pytest-cov ruff black mypy`

**Note**: `ortools-stubs` essential for 100% type safety with OR-Tools CP-SAT framework.
