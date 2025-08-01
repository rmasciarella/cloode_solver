# Claude Code Development Hooks Configuration

This document describes the Claude Code native hooks configured for the modular solver project.

## Overview

Claude Code hooks are shell commands that execute automatically during your development workflow. They help maintain code quality, run tests, and automate repetitive tasks.

## Configured Hooks

### 1. Post-Edit Hooks (after file modifications)

**Auto-format code**
```bash
poetry run black src/ tests/
```
- Runs: After any file edit
- Purpose: Ensures consistent code formatting

**Lint check**
```bash
poetry run ruff check src/ tests/
```
- Runs: After any file edit
- Purpose: Catches code quality issues immediately

### 2. Pre-Commit Hooks (before git commits)

**Quality checks**
```bash
poetry run black --check src/ tests/ && poetry run ruff check src/ tests/
```
- Runs: Before commits
- Purpose: Prevents committing unformatted or poor quality code

**Quick unit tests**
```bash
poetry run pytest tests/unit/ -x --tb=short
```
- Runs: Before commits
- Purpose: Ensures basic functionality isn't broken

### 3. Post-Test Hooks

**Coverage report**
```bash
poetry run pytest --cov=src --cov-report=term-missing
```
- Runs: After test commands
- Purpose: Shows test coverage with missing lines

### 4. File-Specific Hooks

**Database schema monitor**
- File: `scripts/setup_database_tables.py`
- Command: Reminder message about migrations
- Purpose: Alerts when database schema might need migration

**Constraint dependency check**
- Files: `src/solver/constraints/*`
- Command: `python scripts/check_constraint_dependencies.py`
- Purpose: Validates constraint dependencies remain consistent

## Hook Management Commands

```bash
# List all active hooks
claude code hooks list

# Disable a hook temporarily
claude code hooks disable <hook-id>

# Enable a disabled hook
claude code hooks enable <hook-id>

# Remove a hook permanently
claude code hooks remove <hook-id>

# Add a new hook
claude code hooks add <event> "<command>" --description "Purpose"
```

## Custom Hook Ideas

Based on your workflow, consider adding:

1. **Performance monitoring**
   ```bash
   claude code hooks add post-edit "src/solver/core.py" \
     "echo 'Core solver modified - remember to run performance benchmarks'"
   ```

2. **Documentation updates**
   ```bash
   claude code hooks add post-edit "src/solver/constraints/*" \
     "echo 'Constraint modified - update docs/constraints.md if needed'"
   ```

3. **Security checks**
   ```bash
   claude code hooks add pre-commit \
     "grep -r 'SUPABASE_\|SECRET\|KEY' src/ --exclude-dir=__pycache__ || true"
   ```

## Best Practices

1. **Keep hooks fast** - Slow hooks interrupt your workflow
2. **Make hooks informative** - Use clear messages for reminders
3. **Use fail-fast options** - Add `-x` to pytest for quick feedback
4. **Avoid blocking hooks** - Use warnings instead of failures where appropriate
5. **Review hooks regularly** - Remove ones that no longer add value

## Troubleshooting

If hooks are causing issues:

1. **Temporarily disable all hooks**
   ```bash
   claude code hooks disable-all
   ```

2. **Check hook output**
   ```bash
   claude code hooks logs
   ```

3. **Modify hook configuration**
   - Edit `.claude/hooks/config.json` directly if needed

## Integration with CI/CD

These local hooks complement but don't replace CI/CD checks. Ensure your CI/CD pipeline includes:
- Full test suite (not just unit tests)
- Security scanning
- Performance benchmarks
- Documentation generation