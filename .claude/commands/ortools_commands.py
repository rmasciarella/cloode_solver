"""OR-Tools Custom Commands for Claude.

This file implements the custom commands defined in COMMANDS.md as slash commands.
Each command follows the pattern from the documentation.
"""

# Constraint Development Commands


def add_constraint(name: str) -> str:
    """Generate a new constraint function following STANDARDS.md."""
    return f"""Generate a new constraint function for '{name}' following requirements:

1. Use the constraint function template from TEMPLATES.md
2. Function name must be: add_{name}_constraints
3. Include complete docstring with:
   - Mathematical formulation
   - Business logic explanation
   - Args documentation
   - Constraints added list
   - Performance considerations
4. Function body must be 30 lines or less
5. All parameters must have type hints
6. Return type must be -> None
7. Follow variable naming conventions from STANDARDS.md

Ask for clarification if needed about:
- What variables does this constraint need?
- What is the business rule this enforces?
- Are there any special conditions or edge cases?"""


def test_constraint(name: str) -> str:
    """Generate unit test for constraint function."""
    return f"""Generate unit test for the add_{name}_constraints function:

1. Use the unit test template from TEMPLATES.md
2. Function name must be: test_{name}_constraints
3. Use GIVEN-WHEN-THEN structure
4. Include tests for:
   - Normal operation
   - Edge cases
   - Integration with other constraints
5. Verify the constraint is actually enforced
6. Check solver status is OPTIMAL or FEASIBLE
7. Assert the specific constraint behavior

Include edge case tests as separate test functions."""


def check_constraint(function_name: str) -> str:
    """Validate constraint against STANDARDS.md."""
    return f"""Review the {function_name} function against STANDARDS.md checklist:

- [ ] Function name follows pattern: add_<constraint_type>_constraints
- [ ] Function has exactly 30 lines or less (excluding docstring)
- [ ] All parameters have type hints
- [ ] Return type is -> None
- [ ] Docstring includes:
  - [ ] Mathematical formulation
  - [ ] Business logic explanation
  - [ ] List of constraints added
  - [ ] Performance considerations
- [ ] No hardcoded values (uses parameters/constants)
- [ ] Follows variable naming convention
- [ ] Has corresponding unit test

Provide specific feedback on any violations and suggest improvements."""


def list_constraints() -> str:
    """Show all constraints in current model."""
    return """Analyze solver.py or the specified file and list all constraint functions:

1. Find all functions matching add_*_constraints pattern
2. Show their line numbers
3. List their required variables
4. Show dependency order
5. Group by phase if applicable

Format as:
Phase X Constraints:
1. function_name() - Lines X-Y
   Variables: list_of_variables
   Depends on: other_constraints"""


# Debugging Commands


def trace_infeasible() -> str:
    """Systematically debug infeasible model."""
    return """Help debug an infeasible model using this systematic approach:

Step 1: Remove objective function
- Comment out model.Minimize/Maximize
- Check if model becomes feasible

Step 2: Disable constraints systematically
- Start with most restrictive (no-overlap usually)
- Then precedence constraints
- Then assignment constraints
- Finally duration constraints

Step 3: Binary search for minimal infeasible set
- Re-enable half of disabled constraints
- Narrow down to specific conflict

Step 4: Analyze the conflict
- Check data for impossible requirements
- Look for circular dependencies
- Verify time windows

Step 5: Suggest fixes
- Extend horizon
- Add alternative modes
- Relax specific constraints

Start with: "First, let's remove the objective function and see if that helps..." """


def explain_solution() -> str:
    """Convert solver output to business explanation."""
    return """Convert the solver's solution into a business-friendly explanation:

Include:
📅 Overall Timeline: Start to end time in human-readable format
🏭 Machine Utilization:
   - Percentage utilized for each machine
   - Task assignments with times
   - Idle periods

📊 Key Insights:
   - Bottlenecks identified
   - Critical path
   - Optimization opportunities

💡 Recommendations:
   - How to improve throughput
   - Resource allocation suggestions

Use clear formatting and avoid technical jargon."""


def profile_solver() -> str:
    """Analyze solver performance."""
    return """Profile the solver's performance and provide detailed analysis:

📊 Model Statistics:
- Variable counts by type
- Constraint counts by type
- Search space size estimate

⏱️ Time Breakdown:
- Model building time
- Constraint creation time
- Solving time (first solution vs optimization)

🔍 Bottlenecks:
- Which constraints take most time
- Variable bound analysis
- Search strategy effectiveness

💡 Optimization Suggestions:
1. Redundant constraints to add
2. Variable bounds to tighten
3. Search strategy improvements
4. Solver parameter tuning"""


def debug_variables() -> str:
    """Display variable state for debugging."""
    return """Display detailed variable information for debugging:

📌 Task Variables:
- Show bounds and solved values
- Highlight suspicious patterns (too wide bounds, unassigned)

📌 Assignment Variables:
- Show boolean assignment states
- Identify unassigned tasks

🔍 Analysis:
- Variables with unnecessarily wide bounds
- Potential conflicts
- Unexpected patterns

Format each variable clearly with name, type, bounds, and value."""


# Optimization Commands


def suggest_redundant() -> str:
    """Identify redundant constraints for faster solving."""
    return """Analyze the model and suggest redundant constraints for speed:

1. Transitive Relations:
   - If A→B and B→C, add A→C
   - Identify precedence chains

2. Aggregate Constraints:
   - Total duration bounds
   - Machine capacity limits
   - Makespan bounds

3. Symmetry Breaking:
   - Order identical machines
   - Break task symmetries

4. Implied Bounds:
   - Tighten based on precedences
   - Use deadline propagation

Provide code examples for each suggested constraint."""


def tighten_bounds() -> str:
    """Analyze and suggest tighter variable bounds."""
    return """Analyze all variables and suggest tighter bounds:

For each variable type:
1. Calculate theoretical minimum/maximum
2. Use precedence chains to tighten
3. Apply deadline constraints
4. Consider resource availability

Show:
- Current bounds vs suggested bounds
- Reasoning for each suggestion
- Implementation code
- Expected search space reduction
- Estimated performance impact"""


def optimize_search() -> str:
    """Suggest search strategies for problem."""
    return """Recommend search strategies based on problem characteristics:

1. Variable Selection:
   - Critical path first
   - Bottleneck resources
   - High-impact decisions

2. Value Selection:
   - Min value for starts
   - Load balancing for assignments

3. Search Phases:
   - Phase 1: Critical decisions
   - Phase 2: Secondary variables

4. Solver Parameters:
   - Worker threads
   - Time limits
   - Solution limits

Provide complete AddDecisionStrategy code."""


def analyze_complexity() -> str:
    """Provide Big O analysis of model."""
    return """Analyze the computational complexity of the model:

📊 Variable Complexity:
- Count growth with problem size
- Memory requirements

📈 Constraint Complexity:
- Time to create constraints
- Constraint checking cost

🔍 Solver Complexity:
- Search space size
- Theoretical bounds

💡 Scalability Analysis:
- Current limits
- Bottlenecks at scale
- Suggested decompositions

Include Big O notation for each component."""


# Compound Workflow Commands


def dev_flow(constraint_name: str) -> str:
    """Complete development workflow."""
    return f"""Execute complete development workflow for {constraint_name}:

1. First, analyze existing constraints to understand integration points
2. Generate the constraint function using add_constraint template
3. Create comprehensive unit tests
4. Validate against STANDARDS.md
5. Show integration points in solver.py
6. Suggest performance optimizations if needed

This is a compound workflow - execute each step in sequence."""


def debug_slow() -> str:
    """Execute performance debugging workflow."""
    return """Execute performance debugging workflow:

1. Profile the solver to identify bottlenecks
2. Analyze variable bounds for tightening opportunities
3. Suggest redundant constraints
4. Recommend search strategies
5. Provide implementation priority list

Show concrete improvements with expected impact."""


def fix_infeasible() -> str:
    """Infeasibility resolution workflow."""
    return """Execute infeasibility resolution workflow:

1. Trace infeasibility systematically
2. Identify minimal conflict set
3. Analyze data for issues
4. Explain the problem in business terms
5. Suggest multiple solution approaches

Guide through each step interactively."""


# Command registry for easy lookup
COMMANDS = {
    # Full commands
    "/add-constraint": add_constraint,
    "/test-constraint": test_constraint,
    "/check-constraint": check_constraint,
    "/list-constraints": list_constraints,
    "/trace-infeasible": trace_infeasible,
    "/explain-solution": explain_solution,
    "/profile-solver": profile_solver,
    "/debug-variables": debug_variables,
    "/suggest-redundant": suggest_redundant,
    "/tighten-bounds": tighten_bounds,
    "/optimize-search": optimize_search,
    "/analyze-complexity": analyze_complexity,
    "/dev-flow": dev_flow,
    "/debug-slow": debug_slow,
    "/fix-infeasible": fix_infeasible,
    # Aliases for faster access
    "/ac": add_constraint,
    "/tc": test_constraint,
    "/cc": check_constraint,
    "/lc": list_constraints,
    "/ti": trace_infeasible,
    "/es": explain_solution,
    "/ps": profile_solver,
    "/dv": debug_variables,
    "/sr": suggest_redundant,
    "/tb": tighten_bounds,
    "/os": optimize_search,
    "/cx": analyze_complexity,
}


def get_command_prompt(command: str, args: str = "") -> str:
    """Get the prompt for a given command."""
    cmd_func = COMMANDS.get(command)
    if cmd_func:
        # Check if command expects arguments
        import inspect

        sig = inspect.signature(cmd_func)
        if sig.parameters:
            return (
                cmd_func(args)
                if args
                else f"Error: {command} requires args: {list(sig.parameters.keys())}"
            )
        else:
            return cmd_func()
    else:
        available = "\n".join(sorted(COMMANDS.keys()))
        return f"Unknown command: {command}\n\nAvailable commands:\n{available}"
