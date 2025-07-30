# /project-structure - Analyze OR-Tools Project Organization

Analyzes and displays the Fresh OR-Tools solver project structure with context about the current implementation phase and architectural decisions.

## Pattern Matching
- Direct: `/project-structure`
- Natural: "show me the project structure", "what's the folder layout?", "analyze the codebase organization"

## Implementation

1. Use LS and Glob to explore project directories
2. Identify key components and their purposes
3. Check current phase implementation status
4. Format output with visual hierarchy

## Output Template

```
## Project Overview
This is a modular constraint programming scheduling solver using Google OR-Tools CP-SAT framework.

## Core Structure:

📁 **src/** - Main source code
  📁 **solver/** - Core solver implementation
    - `core/` - Main solver orchestration (FreshSolver class)
    - `constraints/` - Modular constraint functions
      - `phase1/` - Basic scheduling constraints
      - `phase2/` - Resource capacity (upcoming)
      - `phase3/` - Advanced features (future)
    - `models/` - Data models (Job, Task, Machine)
    - `utils/` - Time calculations and utilities
  📁 **data/** - Data layer
    - `loaders/` - Database and file loaders
    - `schemas/` - Supabase schemas

📁 **tests/** - Comprehensive test suite
  - `unit/` - Unit tests for each component
  - `integration/` - Phase integration tests
  - `performance/` - Performance benchmarks

📁 **scripts/** - Utility scripts
  - `run_tests.py` - Test runner with coverage
  - `populate_test_data.py` - Load test data

📁 **config/** - Configuration files
📁 **docs/** - Documentation

## Current Phase: Phase 1
- ✅ Basic scheduling with timing constraints
- ✅ Precedence relationships
- ✅ Machine assignments
- 🔄 Performance optimization
- 📅 Next: Resource capacity (Phase 2)

## Key Files:
- `src/solver/core/solver.py` - Main solver class
- `src/solver/models/problem.py` - Data models
- `STANDARDS.md` - Coding standards (30-line rule)
- `CLAUDE.md` - AI assistance guidelines
```

## Context Integration
- Reference CLAUDE.md for project-specific guidance
- Highlight adherence to STANDARDS.md
- Show phase development progress