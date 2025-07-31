# Setting Up Test Data for OR-Tools Scheduling Solver

This guide walks you through setting up test data in Supabase for the Fresh Solver project.

## Prerequisites

1. Supabase project with connection details in `.env` file:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

2. Python dependencies installed:
   ```bash
   uv pip install supabase python-dotenv ortools
   ```

## Step 1: Create Database Tables

The test tables must be created manually in Supabase:

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to **SQL Editor**
3. Open the file `migrations/000_create_test_tables.sql`
4. Copy the entire SQL content
5. Paste it into the SQL Editor
6. Click **Run** to execute the migration

This will create the following tables:
- `test_work_cells` - Manufacturing cells that contain machines
- `test_resources` - Machines that can process tasks
- `test_jobs` - Manufacturing jobs to be scheduled
- `test_tasks` - Individual tasks within jobs
- `test_task_modes` - Different ways a task can be executed (machine + duration)
- `test_task_precedences` - Dependencies between tasks

## Step 2: Populate Test Data

Once tables are created, run the population script:

```bash
uv run python scripts/populate_test_data.py
```

Or use the helper script:

```bash
uv run python create_tables_and_populate.py
```

## Test Data Overview

The test data creates a realistic small manufacturing scenario:

### Work Cells (2)
- **Cell A**: Capacity 2, contains Machine 1 & 2
- **Cell B**: Capacity 1, contains Machine 3

### Machines (3)
- **Machine 1**: In Cell A, $100/hour
- **Machine 2**: In Cell A, $120/hour
- **Machine 3**: In Cell B, $150/hour

### Jobs (2)
- **Job 1**: Linear workflow with 5 tasks (1→2→3→4→5)
  - Due in 3 days
  - Tasks can run on Machine 1 or 2
  - Task 1 is a setup task
  
- **Job 2**: Diamond workflow with 5 tasks
  - Due in 5 days
  - Task precedence: 1→(2,3)→4→5
  - Tasks 1-3 can run on Machine 2 or 3
  - Tasks 4-5 only on Machine 3
  - Task 3 is unattended

### Task Durations
- Vary from 45-135 minutes (3-9 time units)
- Each task has different durations on different machines
- Generally faster on more expensive machines

### Constraints Exercised
1. **Timing**: Task durations and job due dates
2. **Precedence**: Both linear and diamond patterns
3. **Machine Assignment**: Tasks restricted to specific machines
4. **Machine Exclusivity**: Each machine can only process one task at a time

## Verification

After populating data, verify using:

```bash
uv run python check_tables.py
```

Or load the data programmatically:

```python
from src.data.loaders.database import DatabaseLoader

loader = DatabaseLoader(use_test_tables=True)
problem = loader.load_problem()
```

## Test IDs Reference

After population, test IDs are saved to `tests/test_data/test_ids.json` for use in tests.

## Troubleshooting

1. **Tables don't exist error**: Ensure you've run the migration in Supabase SQL Editor
2. **Connection errors**: Check your `.env` file has correct Supabase credentials
3. **Module not found**: Run `uv pip install supabase python-dotenv ortools`

## Clean Up

To reset test data, run the migration again in Supabase SQL Editor - it drops existing tables first.