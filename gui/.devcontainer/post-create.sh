#!/bin/bash
set -e

echo "🚀 Setting up Modular Solver Dev Container..."

# Debug: Show current directory and contents
echo "📍 Current directory: $(pwd)"
echo "📁 Directory contents:"
ls -la

# Ensure we're in the project directory
cd /workspace || { echo "❌ Failed to cd to /workspace"; exit 1; }

echo "📍 Now in: $(pwd)"
echo "📁 Workspace contents:"
ls -la

# Check for pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "❌ ERROR: pyproject.toml not found in /workspace"
    echo "📁 Looking for pyproject.toml in parent directories..."
    find / -name "pyproject.toml" -type f 2>/dev/null | head -10
    exit 1
fi

# Copy .env file if it exists in the workspace
if [ -f ".env" ]; then
    echo "📋 Found .env file in workspace"
else
    echo "⚠️  No .env file found - you may need to create one"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."

# Check if we have a poetry.lock file but no [tool.poetry] section
if [ -f "poetry.lock" ] && ! grep -q "\[tool.poetry\]" pyproject.toml; then
    echo "⚠️  Found poetry.lock but pyproject.toml uses standard format"
    echo "🔧 Installing with pip instead..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        python -m venv .venv
    fi
    
    # Activate virtual environment and install
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e ".[dev]"
else
    # Use poetry if available
    poetry install
fi

# Configure git (if needed)
if [ -n "$GIT_USER_NAME" ]; then
    git config --global user.name "$GIT_USER_NAME"
fi
if [ -n "$GIT_USER_EMAIL" ]; then
    git config --global user.email "$GIT_USER_EMAIL"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p data/output
mkdir -p data/temp

# Set up pre-commit hooks (if pre-commit is installed)
if command -v pre-commit &> /dev/null; then
    echo "🔧 Setting up pre-commit hooks..."
    poetry run pre-commit install
fi

# Run initial tests to verify setup
echo "🧪 Running initial tests..."
poetry run pytest tests/unit/ -v --tb=short || echo "⚠️  Some tests failed - check your environment setup"

# Display Claude Code authentication reminder
echo ""
echo "✅ Dev Container setup complete!"
echo ""
echo "🔑 To use Claude Code, run: claude login"
echo "   Then follow the authentication flow in your browser."
echo ""
echo "📚 Quick commands:"
echo "   - Run solver: poetry run python -m solver.core"
echo "   - Run tests: poetry run pytest"
echo "   - Format code: poetry run black src/ tests/"
echo "   - Lint code: poetry run ruff check src/ tests/"
echo ""