# Phase 2 Implementation Recommendations

## Executive Summary

Phase 2 focuses on implementing 12 custom commands that transform Claude from a general assistant into an OR-Tools development specialist. These commands should be implemented as Claude-aware patterns that leverage the context files created in Phase 1.

## Implementation Strategy

### 1. Command Architecture

Since Claude doesn't execute code directly, implement commands as:
1. **Structured Prompts**: Commands trigger specific Claude behaviors
2. **Response Templates**: Consistent output formats
3. **Context Integration**: Commands reference STANDARDS.md and TEMPLATES.md

### 2. Priority Order (Recommended)

#### Week 1: Core Development Commands
Start with the most frequently used commands:

1. **`/add-constraint`** (Highest Priority)
   - Most common task in OR-Tools development
   - Builds on TEMPLATES.md constraint template
   - Immediate value for daily work

2. **`/test-constraint`** (High Priority)
   - Natural follow-up to constraint creation
   - Enforces test-first development
   - Uses unit test template

3. **`/check-constraint`** (High Priority)
   - Validates against STANDARDS.md
   - Prevents technical debt
   - Quick feedback loop

#### Week 2: Debugging & Analysis Commands

4. **`/trace-infeasible`** (Critical for Production)
   - Most common OR-Tools problem
   - Systematic debugging approach
   - References CONTEXT.md gotchas

5. **`/profile-solver`** (Performance Critical)
   - Identifies bottlenecks
   - Suggests concrete improvements
   - Uses performance insights from CONTEXT.md

6. **`/explain-solution`** (User Value)
   - Translates solver output
   - Business-friendly explanations
   - Builds trust in solutions

#### Week 3: Optimization Commands

7. **`/suggest-redundant`** (Performance Impact)
   - Advanced solver optimization
   - Requires model analysis
   - High value for large problems

8. **`/tighten-bounds`** (Performance Impact)
   - Variable bound analysis
   - Significant speed improvements
   - Uses precedence analysis

9. **`/optimize-search`** (Advanced)
   - Search strategy selection
   - Problem-specific heuristics
   - References solver strategies

#### Week 4: Utility Commands

10. **`/list-constraints`** (Navigation)
    - Model overview
    - Quick reference
    - Helps with large codebases

11. **`/debug-variables`** (Debugging Aid)
    - Variable state inspection
    - Bound checking
    - Value validation

12. **`/analyze-complexity`** (Planning)
    - Big O analysis
    - Scalability predictions
    - Capacity planning

## Implementation Templates

### Command Implementation Pattern

```markdown
## Command: /add-constraint <constraint_name>

### Trigger Recognition
When user types: "/add-constraint resource_capacity"

### Claude Response Flow
1. Parse constraint name and context
2. Reference TEMPLATES.md constraint template
3. Check STANDARDS.md for rules
4. Generate code following patterns
5. Include unit test stub
6. Suggest integration points

### Output Format
```python
# Generated constraint function
def add_resource_capacity_constraints(...):
    """[Generated from template]"""
    # Implementation

# Unit test stub
def test_resource_capacity_constraints():
    """[Generated from template]"""
    # Test implementation
```

### Integration Checklist
- [ ] Add to solver.py
- [ ] Update variable dependencies
- [ ] Run unit tests
- [ ] Check performance impact
```

### Command Documentation Pattern

For each command, create documentation in `.claude/COMMANDS.md`:

```markdown
# Custom Commands Reference

## /add-constraint
**Purpose**: Generate new constraint function following standards
**Usage**: `/add-constraint <constraint_name>`
**Example**: `/add-constraint machine_maintenance`
**Output**: 
- Constraint function (max 30 lines)
- Unit test template
- Integration checklist

## /trace-infeasible
**Purpose**: Debug infeasible models systematically
**Usage**: `/trace-infeasible`
**Process**:
1. Remove objective function
2. Disable constraints incrementally
3. Identify minimal infeasible set
4. Suggest fixes
```

## Testing Strategy

### Command Validation Tests

1. **Input Parsing Tests**
   - Various command formats
   - Edge cases (empty names, special characters)
   - Multi-word constraint names

2. **Output Compliance Tests**
   - Generated code follows STANDARDS.md
   - Functions under 30 lines
   - Proper type hints and docstrings

3. **Integration Tests**
   - Generated code compiles
   - Tests are executable
   - No conflicts with existing code

### Example Test Scenarios

```python
# Test command parsing
test_cases = [
    "/add-constraint simple",
    "/add-constraint multi_word_name",
    "/add-constraint with-dashes",
    "/ADD-CONSTRAINT uppercase",
]

# Test output validation
for generated_code in outputs:
    assert count_lines(generated_code) <= 30
    assert has_type_hints(generated_code)
    assert follows_naming_convention(generated_code)
```

## Integration with Claude Workflow

### 1. Update CLAUDE.md

Add command reference section:

```markdown
## Quick Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/add-constraint` | Generate constraint function | `/add-constraint resource_limit` |
| `/trace-infeasible` | Debug infeasible model | `/trace-infeasible` |
| `/suggest-redundant` | Add helper constraints | `/suggest-redundant` |
```

### 2. Create Command Shortcuts

In `.claude/SHORTCUTS.md`:

```markdown
# Command Shortcuts

## Rapid Development Flow
```
/ac resource_capacity  # Short for /add-constraint
/tc resource_capacity  # Short for /test-constraint
/cc add_resource_capacity_constraints  # Short for /check-constraint
```

## Common Development Scenarios
```
/dev-flow constraint_name  # Runs: add → test → check
/debug-slow  # Runs: profile → tighten-bounds → suggest-redundant
/fix-infeasible  # Runs: trace → explain → suggest-fixes
```
```

### 3. Context-Aware Responses

Commands should reference current context:

```python
# Good: Context-aware
"Based on your current task_starts variables in solver.py line 45..."

# Bad: Generic
"To add a constraint, create a function..."
```

## Success Metrics

### Quantitative
- Command recognition rate: >95%
- Generated code compilation rate: 100%
- Standards compliance: 100%
- Average time saved per command: 5-10 minutes

### Qualitative
- Reduced cognitive load
- Fewer context switches
- Consistent code quality
- Faster development cycles

## Risk Mitigation

### Risk 1: Command Misinterpretation
**Mitigation**: 
- Clear command syntax
- Confirmation before generation
- Preview mode for complex commands

### Risk 2: Generated Code Quality
**Mitigation**:
- Strict template adherence
- Automated validation
- Manual review checklist

### Risk 3: Integration Conflicts
**Mitigation**:
- Check existing code first
- Suggest safe integration points
- Warn about potential conflicts

## Next Steps

1. **Week 1**: Implement first 3 commands
   - Test with real use cases
   - Gather feedback
   - Refine templates

2. **Week 2**: Add debugging commands
   - Focus on common problems
   - Create troubleshooting flows
   - Document solutions

3. **Week 3**: Advanced optimization
   - Performance-focused commands
   - Model analysis tools
   - Search strategies

4. **Week 4**: Polish and integrate
   - Command shortcuts
   - Workflow automation
   - Documentation updates

## Appendix: Command Specifications

### Detailed Specifications for Each Command

[Include detailed specs for all 12 commands with:
- Input format
- Processing logic
- Output template
- Error handling
- Integration points]