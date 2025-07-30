# Effective Prompts for OR-Tools Development

## Constraint Development

### Adding New Constraint
"I need to add a {constraint_type} constraint that ensures {business_rule}. 
Current variables: {variable_list}
Performance target: {solve_time}
Please follow STANDARDS.md and ensure the function is under 30 lines."

### Modifying Existing Constraint
"Update the {constraint_name} constraint to handle {new_requirement}.
Maintain backward compatibility with existing tests.
Current implementation is in {file_path} at line {line_number}."

### Constraint Validation
"Review the {constraint_name} constraint against STANDARDS.md.
Check: function length, naming convention, docstring completeness, type hints.
Suggest improvements for solver efficiency."

## Debugging & Troubleshooting

### Infeasibility Analysis
"My model is infeasible with these constraints: {constraint_list}.
Dataset size: {num_jobs} jobs, {num_tasks} tasks.
Help me trace which constraints conflict and suggest minimal changes."

### Performance Issues
"My solver takes {current_time} seconds on {dataset_size}.
Target: {target_time} seconds.
Analyze my model and suggest:
1) Redundant constraints to add
2) Tighter variable bounds
3) Better search strategies"

### Memory Problems
"Getting memory errors with {num_variables} variables.
Current variable structure: {variable_description}.
Suggest ways to reduce variable count or use interval variables."

## Model Design

### Variable Creation
"Design decision variables for {feature_description}.
Consider: bound tightness, solver efficiency, integration with existing variables.
Current variables: {existing_variables}."

### Objective Function
"Create objective function for {goal_description}.
Must balance: {competing_objectives}.
Use weighted sum or hierarchical optimization as appropriate."

### Search Strategy
"Recommend search strategy for model with:
- {num_jobs} jobs with {avg_tasks_per_job} tasks each
- {constraint_types} constraints
- Objective: {objective_type}"

## Testing

### Unit Test Generation
"Generate unit test for {constraint_function}.
Test cases should cover:
- Normal operation
- Edge cases
- Integration with other constraints
Follow the GIVEN-WHEN-THEN pattern."

### Integration Test Design
"Create integration test for Phase {phase_number} including:
- All constraints: {constraint_list}
- Performance verification
- Solution quality checks"

### Performance Benchmark
"Design performance benchmark for {feature}.
Include datasets: tiny (2 jobs), small (5 jobs), medium (20 jobs).
Measure: solve time, memory usage, solution quality."

## Code Review

### Constraint Review
"Review this constraint implementation:
```python
{code}
```
Check against STANDARDS.md and suggest improvements for:
- Code clarity
- Solver efficiency
- Test coverage"

### Model Architecture Review
"Analyze the overall model architecture in {file_path}.
Evaluate: variable organization, constraint ordering, solver configuration.
Suggest architectural improvements."

## Data Handling

### Database Integration
"Implement {operation} for Supabase integration.
Data model: {model_description}.
Include: validation, error handling, transaction management."

### Data Validation
"Add validation for {data_type} ensuring:
- Required fields present
- Time durations positive
- Foreign key relationships valid
- Business rules enforced"

## Quick Templates

### "Make it faster"
"Profile my model and identify the top 3 performance bottlenecks.
Current solve time: {time}. Target: {target_time}."

### "Why doesn't it work?"
"Debug why {specific_behavior} is happening.
Expected: {expected_behavior}.
Actual: {actual_behavior}.
Relevant code: {file}:{line_range}"

### "Follow the pattern"
"Implement {feature} following the existing pattern in {example_file}.
Maintain consistency with: naming, structure, error handling."

### "Explain this solution"
"Explain the solver's solution in business terms:
- Why tasks are scheduled when they are
- How constraints affected the schedule
- What trade-offs were made"

## Migration & Refactoring

### Phase Migration
"Prepare the codebase for Phase {next_phase} implementation.
New features: {feature_list}.
Identify: required data model changes, new variables needed, integration points."

### Refactor for Performance
"Refactor {component} for better performance.
Current issues: {performance_problems}.
Maintain: API compatibility, test coverage, STANDARDS.md compliance."

## Advanced Prompts

### Solver Configuration Optimization
"Analyze my solver configuration and suggest optimal parameters for:
- {problem_characteristics}
- Dataset scale: {scale}
- Time budget: {time_limit}"

### Constraint Relaxation
"Implement soft constraints for {constraint_type}.
Penalty structure: {penalty_description}.
Integrate with existing hard constraints."

### Multi-Objective Optimization
"Convert single objective to multi-objective for:
1. {objective_1}
2. {objective_2}
3. {objective_3}
Use: lexicographic, weighted sum, or Pareto optimization."

## Template Usage Tips

1. **Be Specific**: Replace all {placeholders} with actual values
2. **Provide Context**: Include relevant file paths and line numbers
3. **State Goals**: Always include performance targets or success criteria
4. **Reference Standards**: Mention STANDARDS.md for consistency
5. **Incremental Approach**: Break complex requests into phases