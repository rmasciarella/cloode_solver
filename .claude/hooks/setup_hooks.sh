#!/bin/bash
# Setup Claude Code hooks for the modular solver development workflow

echo "Setting up Claude Code hooks for modular solver project..."

# Post-edit hooks - run after file modifications
echo "Adding post-edit hooks..."

# Format code after edits
claude code hooks add post-edit "poetry run black src/ tests/" \
  --description "Auto-format Python code after edits"

# Check linting after edits
claude code hooks add post-edit "poetry run ruff check src/ tests/" \
  --description "Run linting checks after edits"

# Pre-commit hooks - run before commits
echo "Adding pre-commit hooks..."

# Run all quality checks before commit
claude code hooks add pre-commit "poetry run black --check src/ tests/ && poetry run ruff check src/ tests/" \
  --description "Ensure code quality before commits"

# Run quick tests before commit
claude code hooks add pre-commit "poetry run pytest tests/unit/ -x --tb=short" \
  --description "Run unit tests before commits"

# Post-test hooks - run after test commands
echo "Adding post-test hooks..."

# Generate coverage report after tests
claude code hooks add post-test "poetry run pytest --cov=src --cov-report=term-missing" \
  --description "Show coverage report after running tests"

# File change hooks - monitor specific files
echo "Adding file change hooks..."

# Validate database schema changes
claude code hooks add file-change "scripts/setup_database_tables.py" \
  "echo 'Database schema changed - remember to run migration scripts!'" \
  --description "Remind about database migrations"

# Check constraint dependencies
claude code hooks add file-change "src/solver/constraints/*" \
  "python scripts/check_constraint_dependencies.py" \
  --description "Verify constraint dependencies remain valid"

echo "Claude Code hooks configured successfully!"
echo ""
echo "To view all hooks: claude code hooks list"
echo "To remove a hook: claude code hooks remove <hook-id>"
echo "To disable temporarily: claude code hooks disable <hook-id>"