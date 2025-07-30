# Quick Start: Using Claude Commands with OR-Tools Solver

## Available Commands

### Essential Commands for OR-Tools Development

| Command | Purpose | Example Usage |
|---------|---------|---------------|
| `/project-structure` | View project organization | "Show me the project structure" |
| `/solver-status` | Check implementation progress | "What constraints are implemented?" |
| `/constraint-patterns` | Show constraint code patterns | "How do I add a new constraint?" |
| `/test` | Run the test suite | "Run all tests" |
| `/check-standards` | Verify code compliance | "Check if my code follows standards" |
| `/performance` | Analyze solver speed | "How fast is the solver?" |

## Usage Examples

### 1. Starting Development
```
You: Show me the project structure
Claude: [Analyzes and displays the OR-Tools solver organization]

You: What's the current implementation status?
Claude: [Shows Phase 1 progress, completed constraints, and next steps]
```

### 2. Adding New Constraints
```
You: /constraint-patterns
Claude: [Shows the standard pattern for constraint functions with examples]

You: I need to add a resource capacity constraint
Claude: [Provides template following the 30-line rule and proper structure]
```

### 3. Testing Your Changes
```
You: Run the tests
Claude: [Executes test suite and reports results]

You: /performance
Claude: [Analyzes solver performance against targets]
```

### 4. Checking Standards
```
You: Check if my new constraint follows standards
Claude: [Reviews code against STANDARDS.md requirements]
```

## Natural Language Alternatives

You don't need to use slash commands. These work too:
- "What's the folder structure?" → `/project-structure`
- "Which phase are we in?" → `/solver-status`
- "Show constraint examples" → `/constraint-patterns`
- "Test the solver" → `/test`
- "Check code quality" → `/check-standards`
- "Is it fast enough?" → `/performance`

## Tips for Effective Use

1. **Be specific about what you need**
   - ❌ "Help with constraints"
   - ✅ "Show me how to add precedence constraints"

2. **Use commands to maintain context**
   - Start with `/solver-status` to understand current state
   - Use `/constraint-patterns` before implementing new constraints
   - Run `/test` after making changes

3. **Combine commands for workflows**
   ```
   1. /solver-status (see what's done)
   2. /constraint-patterns (get templates)
   3. [implement your code]
   4. /check-standards (verify compliance)
   5. /test (ensure it works)
   6. /performance (check speed)
   ```

## Common Workflows

### Adding a New Constraint
1. Check current status: `/solver-status`
2. Get the pattern: `/constraint-patterns`
3. Implement following the template
4. Verify standards: `/check-standards`
5. Test it: `/test`

### Debugging Performance Issues
1. Run benchmarks: `/performance`
2. Review constraint efficiency
3. Add solver hints or redundant constraints
4. Re-run: `/performance`

### Understanding the Codebase
1. Start with: `/project-structure`
2. Check implementation: `/solver-status`
3. Review patterns: `/constraint-patterns`

## Project-Specific Context

This OR-Tools solver follows strict standards:
- **30-line rule**: Constraint functions must be ≤30 lines
- **One constraint per function**: Each function adds ONE type of constraint
- **Type hints required**: All parameters must have type annotations
- **Performance targets**: Must solve medium datasets in <60 seconds

Claude knows these standards and will help you follow them.

## Getting Help

If you're unsure which command to use:
- Just describe what you want to do
- Claude will suggest the appropriate command
- Or Claude will execute the right action directly

Example:
```
You: I want to see if my code is fast enough
Claude: I'll analyze the solver performance for you using the performance checking tools...
[Runs performance analysis]
```

## Remember

- Commands can be typed with `/` or described naturally
- Claude understands the OR-Tools project context
- All commands are tailored for this solver project
- Focus on Phase 1 constraints first (timing, precedence, assignment)