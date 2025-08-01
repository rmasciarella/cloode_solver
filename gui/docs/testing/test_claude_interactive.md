# Interactive Claude Configuration Test Guide

This guide provides specific test scenarios to validate your Claude configuration capabilities.

## 🧪 Test 1: Constraint Development Commands

### Test 1.1: Add New Constraint
```
Prompt: /add-constraint maintenance_window
```
**Expected**: Should generate a complete constraint function with:
- Proper function signature
- Type hints on all parameters
- Mathematical formulation in docstring
- Business logic explanation
- Under 30 lines of code

### Test 1.2: Generate Tests
```
Prompt: /tc maintenance_window
```
**Expected**: Unit test with GIVEN-WHEN-THEN structure

### Test 1.3: Validate Standards
```
Prompt: /cc add_precedence_constraints
```
**Expected**: Checklist with ✅/❌ for each standard

## 🔍 Test 2: Debugging Workflows

### Test 2.1: Infeasible Model
```
Prompt: My solver returns INFEASIBLE with 5 jobs, 50 tasks, and 3 machines. /trace-infeasible
```
**Expected**: Step-by-step debugging process starting with objective removal

### Test 2.2: Performance Issue
```
Prompt: Solver takes 120 seconds on medium dataset (target: 60s). /profile-solver
```
**Expected**: Detailed performance analysis with bottleneck identification

## ⚡ Test 3: Complex Scenarios

### Test 3.1: Full Development Flow
```
Prompt: I need to add skill matching constraints. Use /dev-flow skill_match
```
**Expected**: Should execute add → test → check workflow

### Test 3.2: Code Generation from Template
```
Prompt: Generate a Worker data model with skills and availability using TEMPLATES.md
```
**Expected**: Complete dataclass with validation in __post_init__

## 🏗️ Test 4: Real Integration

### Test 4.1: Update Existing Code
```
Prompt: In src/solver/constraints.py, after line 45, add a resource capacity constraint that ensures no machine exceeds its daily capacity limit
```
**Expected**: Should read file, understand context, and add appropriate constraint

### Test 4.2: Fix Performance
```
Prompt: Profile my solver and suggest the top 3 optimizations. Current time: 85s, target: 30s
```
**Expected**: Should use /ps, /tb, and /sr commands in sequence

## 📋 Test 5: Edge Cases

### Test 5.1: Invalid Command
```
Prompt: /invalid-command test
```
**Expected**: Should handle gracefully, suggest valid commands

### Test 5.2: Conflicting Standards
```
Prompt: Review this 50-line constraint function against STANDARDS.md
```
**Expected**: Should flag the 30-line limit violation

## 🎯 Test 6: Context Awareness

### Test 6.1: Phase-Specific Request
```
Prompt: We're in Phase 1. What constraints should I implement next?
```
**Expected**: Should reference CONTEXT.md and current implementation status

### Test 6.2: Performance Targets
```
Prompt: Will this model meet our performance targets for medium datasets?
```
**Expected**: Should reference the 60-second target for 500 tasks

## 📊 Scoring Your Configuration

Rate each test:
- ✅ **Excellent**: Follows templates/standards exactly, provides actionable output
- ⚠️ **Good**: Correct approach but missing some details
- ❌ **Needs Work**: Incorrect or incomplete response

### Target Scores:
- Command Recognition: 6/6 commands work correctly
- Template Adherence: Generated code matches templates
- Context Integration: Uses project-specific knowledge
- Workflow Execution: Chains commands appropriately
- Error Handling: Gracefully handles edge cases

## 💡 Advanced Tests

### Test A: Multi-Phase Analysis
```
Prompt: Analyze what changes are needed to migrate from Phase 1 to Phase 2, focusing on resource capacity constraints
```

### Test B: Custom Workflow
```
Prompt: Create a custom workflow for daily solver performance monitoring
```

### Test C: Documentation Integration
```
Prompt: My constraint violates STANDARDS.md section 4. Show me the specific standard and how to fix it
```

## 🔄 Continuous Testing

After each major change to your Claude configuration:
1. Run through Tests 1-3 (basic functionality)
2. Try one complex integration test
3. Document any new patterns that work well
4. Update PROMPTS.md with successful prompt patterns