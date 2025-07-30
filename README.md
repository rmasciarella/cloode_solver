# Fresh OR-Tools Solver

A **template-first** constraint programming scheduling solver using Google OR-Tools CP-SAT framework, optimized for parallel identical job scheduling with **5-8x performance improvements** over traditional approaches.

## 🚀 Template-Based Architecture

This solver is designed exclusively for **parallel identical jobs** using a template-first methodology:

- **Template Reuse**: N jobs share 1 template structure for massive efficiency gains
- **Memory Optimization**: O(template_tasks × instances) vs O(total_tasks³) complexity
- **Performance**: 5-8x faster solving with identical job patterns
- **Scalability**: Sub-linear scaling with job instance count

## Project Structure

```
fresh_solver/
├── src/                    # Main source code
│   ├── solver/            # Core solver package
│   │   ├── core/          # Solver implementation
│   │   ├── constraints/   # Modular constraint functions
│   │   │   └── phase1/    # Template-optimized constraints
│   │   ├── models/        # Data models & template generator
│   │   ├── strategies/    # Search strategies
│   │   └── utils/         # Utility functions
│   └── data/              # Data layer
│       ├── loaders/       # Template & legacy data loaders
│       └── schemas/       # Database schemas
├── tests/                 # Comprehensive test suite
│   ├── unit/              # Unit tests (180 tests, 91% coverage)
│   ├── integration/       # Template integration tests
│   └── performance/       # Performance regression tests
├── scripts/               # Template optimization scripts
├── examples/              # Template workflow examples
├── migrations/            # Database migrations
├── .claude/               # Modular Claude configuration
│   ├── STANDARDS.md       # Coding standards & type safety
│   ├── COMMANDS.md        # Custom OR-Tools commands
│   ├── TEMPLATES.md       # Code generation templates
│   ├── WORKFLOWS.md       # Development workflows
│   ├── DEVELOPMENT.md     # Architecture & patterns
│   └── TROUBLESHOOTING.md # Debug workflows
└── CLAUDE.md              # Main Claude configuration (126 lines)
```

## Quick Start

**Important**: This project uses UV for Python package management. All commands must be prefixed with `uv run`.

1. Install UV and dependencies:
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Load template test data:
```bash
uv run python scripts/populate_template_test_data.py
```

4. Run template solver:
```bash
uv run python test_template_solver.py
```

## Template Performance Targets

Performance benchmarks for template-based scheduling:

- **Simple Templates** (5-10 tasks): < 1s for 10+ instances
- **Medium Templates** (20-50 tasks): < 10s for 5+ instances  
- **Complex Templates** (100+ tasks): < 60s for 3+ instances

## Development Commands

**Complete Type Safety Pipeline**:
```bash
make lint                      # Complete quality check: ruff + black + mypy (REQUIRED)
uv run ruff check . --fix      # Auto-fix linting issues
uv run ruff format .           # Format files (handles 88-char line length)
uv run mypy src/               # Type check (must pass with 0 errors)
```

**Testing**:
```bash
uv run python run_tests.py              # Run all tests with coverage
uv run python -m pytest tests/unit/ -v  # Run unit tests
uv run python -m pytest tests/integration/test_template_integration.py -v
```

**Template Development**:
```bash
uv run python examples/template_scheduling_example.py     # Template example
uv run python scripts/validate_template_performance.py    # Performance validation
```

## Architecture Highlights

### Template-First Design
- **JobTemplate**: Reusable job structure with template tasks and precedences
- **JobInstance**: Lightweight instance referencing template with due dates
- **Template Constraints**: Optimized constraint functions for identical jobs
- **Legacy Compatibility**: Backward compatibility with traditional job-shop scheduling

### Type Safety (100% mypy compliance)
- **34 source files** with complete type annotations
- **Centralized type aliases** for OR-Tools structures
- **ortools-stubs** integration for proper CP-SAT typing
- **88-character line length** compliance with automatic formatting

### Modular Claude Configuration
- **CLAUDE.md** (126 lines): Clean navigation hub
- **Subordinate files**: Detailed information in organized structure
- **Custom commands**: Template-specific OR-Tools development commands
- **Cross-session context**: Template optimization tracking

## Development Phases

Current implementation focuses on template-based optimization:

- **Phase 1** (Complete): Template-based job-shop scheduling with 5-8x performance improvements
- **Phase 2** (Planned): Template resource capacity and skills matching
- **Phase 3** (Future): Template shift constraints and advanced features

## AI Development Assistant

This project includes a comprehensive Claude Code configuration for OR-Tools development:

- **CLAUDE.md**: Main configuration file with template-first workflow
- **Custom Commands**: `/template-benchmark`, `/add-constraint`, `/debug-slow`
- **Type Safety Integration**: Complete mypy compliance workflows
- **Template Optimization**: Cross-session performance tracking

See `CLAUDE.md` for the complete AI assistant setup and `.claude/` directory for detailed configuration modules.

## Performance & Type Safety

- **Template Efficiency**: 5-8x performance improvements validated
- **Type Safety**: 100% mypy compliance across 34 source files
- **Test Coverage**: 180 tests with 91% coverage
- **Line Length**: 88-character limit with automatic formatting
- **Package Management**: UV for consistent Python environment