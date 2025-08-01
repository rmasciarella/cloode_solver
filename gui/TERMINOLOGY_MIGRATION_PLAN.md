# Terminology Migration Plan: Legacy/Template → Unique/Optimized

## Overview
Systematic rename from "legacy/template" terminology to "unique/optimized" to better reflect the actual approaches rather than suggesting one is outdated.

## Terminology Mapping

### Core Terms
```
legacy       → unique
template     → optimized
Legacy       → Unique  
Template     → Optimized
LEGACY       → UNIQUE
TEMPLATE     → OPTIMIZED
```

### Specific Patterns

#### Class Names
```python
TemplatePrecedence          → OptimizedPrecedence
TemplateTask                → OptimizedTask  
JobTemplate                 → JobOptimized
TemplateDatabaseLoader      → OptimizedDatabaseLoader
TemplateValidator           → OptimizedValidator
TemplateOptimizer           → OptimizedPatternOptimizer
TemplateGenerator           → OptimizedPatternGenerator
```

#### Variable Names
```python
template_task_starts        → optimized_task_starts
template_task_ends          → optimized_task_ends
template_task_assigned      → optimized_task_assigned
template_precedences        → optimized_precedences  
template_task_lookup        → optimized_task_lookup
job_template               → job_optimized_pattern
template_id                → optimized_pattern_id
template_task_id           → optimized_task_id
is_template_based          → is_optimized_mode
```

#### Type Aliases (TEMPLATES.md)
```python
TemplateKey                → OptimizedPatternKey
TemplateTaskKey            → OptimizedTaskKey
InstanceTaskKey            → OptimizedInstanceTaskKey
TemplateAssignmentKey      → OptimizedAssignmentKey
TemplateTaskStartDict      → OptimizedTaskStartDict
TemplateTaskEndDict        → OptimizedTaskEndDict
TemplateTaskDurationDict   → OptimizedTaskDurationDict
TemplateTaskIntervalDict   → OptimizedTaskIntervalDict
TemplateTaskAssignmentDict → OptimizedTaskAssignmentDict
TemplatePrecedenceList     → OptimizedPrecedenceList
TemplateSetupTimeDict      → OptimizedSetupTimeDict
```

#### Command Names
```bash
/template-benchmark         → /optimized-benchmark
/template-optimize-params   → /optimized-optimize-params
/template-promote-params    → /optimized-promote-params
/template-add-symmetry      → /optimized-add-symmetry
/template-regression-test   → /optimized-regression-test
/tb-tpl                    → /tb-opt
/opt-tpl                   → /opt-opt
/prm-tpl                   → /prm-opt
/sym-tpl                   → /sym-opt
/reg-tpl                   → /reg-opt
```

#### File Names
```
template_database.py           → optimized_database.py
template_validator.py          → optimized_validator.py
template_optimizer.py          → optimized_optimizer.py
template_generator.py          → optimized_generator.py
template_constraints.py        → optimized_constraints.py
template_problem_factory.py    → optimized_problem_factory.py
template_scheduling_example.py → optimized_scheduling_example.py
complete_template_workflow.py  → complete_optimized_workflow.py
```

#### Database Schema
```sql
job_templates               → job_optimized_patterns
template_tasks             → optimized_pattern_tasks
template_precedences       → optimized_pattern_precedences
template_id                → optimized_pattern_id
template_task_id           → optimized_task_id
```

#### Documentation Files
```
TEMPLATE_INTEGRATION_COMPLETE.md    → OPTIMIZED_INTEGRATION_COMPLETE.md
template_database_architecture.md   → optimized_database_architecture.md
template_hierarchical_results.md    → optimized_hierarchical_results.md
```

## Migration Order

### Phase 1: Core Data Models
1. `src/solver/models/problem.py` - Update class definitions and properties
2. Type aliases in `.claude/TEMPLATES.md` - Update centralized type definitions
3. Core solver logic in `src/solver/core/solver.py`

### Phase 2: Constraint Files
4. `src/solver/constraints/phase1/template_constraints.py` → `optimized_constraints.py`
5. All constraint files referencing template variables
6. Database loader files

### Phase 3: Template-Specific Modules
7. `src/solver/templates/` directory → `src/solver/optimized/`
8. All files in templates directory
9. Test fixtures and examples

### Phase 4: Documentation and Commands
10. `.claude/` documentation files - Update all references
11. `CLAUDE.md` - Update command names and terminology
12. Command implementations and shortcuts

### Phase 5: Database and Infrastructure
13. Migration scripts for database schema
14. Production scripts and configurations
15. Benchmark and performance files

### Phase 6: Tests and Validation
16. All test files with template references
17. Integration tests and benchmarks
18. Final validation and cleanup

## Files to Update (61 total)

### High Priority (Core)
- `/Users/quanta/projects/fresh_solver/src/solver/models/problem.py`
- `/Users/quanta/projects/fresh_solver/src/solver/core/solver.py`
- `/Users/quanta/projects/fresh_solver/src/data/loaders/template_database.py`
- `/Users/quanta/projects/fresh_solver/.claude/TEMPLATES.md`
- `/Users/quanta/projects/fresh_solver/CLAUDE.md`

### Medium Priority (Constraints & Logic)
- `/Users/quanta/projects/fresh_solver/src/solver/constraints/phase1/template_constraints.py`
- `/Users/quanta/projects/fresh_solver/src/solver/templates/` (entire directory)
- `/Users/quanta/projects/fresh_solver/tests/fixtures/template_problem_factory.py`

### Lower Priority (Documentation & Scripts)
- All `.md` documentation files
- Migration scripts
- Example and script files

## Validation Steps

1. **Syntax Check**: Ensure all Python files compile without syntax errors
2. **Type Safety**: Run `make lint` to verify mypy compliance maintained
3. **Test Suite**: Run full test suite to ensure functionality preserved
4. **Performance**: Validate that optimized mode still delivers 5-8x performance
5. **Database**: Test database integration with new schema names
6. **Commands**: Verify all renamed commands work correctly

## Rollback Plan

Keep original terminology mapping document. If issues arise:
1. Revert specific files using git
2. Update mappings based on discovered issues
3. Re-run migration for problematic areas
4. Full rollback possible via git reset if needed

## Success Criteria

- [x] All 61 files updated with new terminology
- [ ] 0 mypy errors maintained
- [ ] All tests pass (currently 180 tests, 1 skipped, 91% coverage)
- [ ] Performance benchmarks maintain 5-8x improvement
- [ ] Documentation is consistent and accurate
- [ ] Commands work with new names and maintain backward compatibility where needed