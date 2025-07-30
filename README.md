# Fresh OR-Tools Solver

A constraint programming scheduling solver using Google OR-Tools CP-SAT framework, designed with a phased development approach.

## Project Structure

```
fresh_solver/
├── src/                    # Main source code
│   ├── solver/            # Core solver package
│   │   ├── core/          # Solver implementation
│   │   ├── constraints/   # Modular constraint functions
│   │   ├── models/        # Data models
│   │   ├── strategies/    # Search strategies
│   │   └── utils/         # Utility functions
│   └── data/              # Data layer
│       ├── loaders/       # Data loading implementations
│       ├── repositories/  # Data access patterns
│       └── schemas/       # Database schemas
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── config/                # Configuration files
└── main.py               # Main entry point
```

## Quick Start

1. Install dependencies:
```bash
pip install ortools supabase python-dotenv pytest pytest-cov
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Load test data:
```bash
python scripts/populate_test_data.py
```

4. Run the solver:
```bash
python -m src.solver --test --time-limit 30
```

## Development Phases

- **Phase 1** (current): Basic job-shop scheduling with timing, precedence, and machine assignment
- **Phase 2**: Resource capacity constraints and skills matching
- **Phase 3**: Shift constraints and advanced scheduling features

## Testing

Run all tests:
```bash
python scripts/run_tests.py
```

Run specific tests:
```bash
python -m pytest tests/unit/test_solver.py -v
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **Solver Core**: Main solver orchestration and model building
- **Constraints**: Modular constraint functions (max 30 lines each)
- **Data Models**: Type-safe dataclasses with validation
- **Data Layer**: Abstract loaders for different data sources
- **Utils**: Time calculations and solution extraction

See `STANDARDS.md` for detailed coding standards and `CLAUDE.md` for AI assistance guidelines.