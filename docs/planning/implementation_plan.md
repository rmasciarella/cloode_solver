# Phase 1: Core Foundation & Basic Scheduling

Goal: Establish clean architecture with minimal viable scheduling

## Core structure
```python
class CPSATScheduler:
    def __init__(self):
        self.model = cp_model.CpModel()
        self.tasks = {}  # task_id -> interval_var
        self.task_starts = {}
        self.task_ends = {}

    def create_task_intervals(self, tasks):
        """Create interval variables - the foundation of scheduling"""
        for task in tasks:
            start = self.model.NewIntVar(0, horizon, f'start_{task.id}')
            duration = task.duration  # Fixed initially
            end = self.model.NewIntVar(0, horizon, f'end_{task.id}')

            # Core constraint: start + duration = end
            self.model.Add(start + duration == end)

            # Store for easy access
            interval = self.model.NewIntervalVar(start, duration, end, f'task_{task.id}')
            self.tasks[task.id] = interval
            self.task_starts[task.id] = start
            self.task_ends[task.id] = end
```

Constraints to add:
1. Basic precedence (simple AddBoolOr for dependencies)
2. Time horizon bounds
3. Simple makespan objective

# Phase 2: Resource Assignment Framework

Goal: Add resource assignment with efficient integer variables

```python
def create_resource_assignments(self, tasks, resources):
    """Use integer variables for resource assignment - OR-Tools best practice"""
    self.resource_assignments = {}

    for task in tasks:
        # Single integer variable per task (0 = unassigned, 1-N = resource index)
        assignment = self.model.NewIntVar(1, len(resources), f'assign_{task.id}')
        self.resource_assignments[task.id] = assignment

        # Optional intervals for each possible assignment
        self.optional_intervals[task.id] = {}
        for r_idx, resource in enumerate(resources, 1):
            presence = self.model.NewBoolVar(f'presence_{task.id}_{resource.id}')
            optional = self.model.NewOptionalIntervalVar(
                self.task_starts[task.id],
                task.duration,
                self.task_ends[task.id],
                presence,
                f'optional_{task.id}_{resource.id}'
            )
            self.optional_intervals[task.id][r_idx] = (optional, presence)

            # Link assignment variable to presence
            self.model.Add(assignment == r_idx).OnlyEnforceIf(presence)
```

Constraints to add:
1. Exactly one resource per task (sum of presences = 1)
2. Basic capacity constraints using cumulative
3. Cost calculation infrastructure

# Phase 3: Advanced Scheduling Features

Goal: Add batching, setup times, and work cells

```python
def add_batch_constraints(self, batch_groups):
    """Efficient batch processing with cookie-cutter patterns"""
    for group in batch_groups:
        if len(group.tasks) <= 1:
            continue

        # All tasks in batch must use same resource
        first_task = group.tasks[0]
        for task in group.tasks[1:]:
            self.model.Add(
                self.resource_assignments[first_task] ==
                self.resource_assignments[task]
            )

        # Tasks must be contiguous (no gaps)
        sorted_tasks = sorted(group.tasks, key=lambda t: t.sequence)
        for i in range(len(sorted_tasks) - 1):
            self.model.Add(
                self.task_ends[sorted_tasks[i].id] ==
                self.task_starts[sorted_tasks[i+1].id]
            )
```

Constraints to add:
1. Batch grouping and contiguity
2. Setup times between different products
3. Work cell capacity limits
4. Mode selection (alternative durations/resources)

# Phase 4: Labor & Calendar Integration

Goal: Add human resource scheduling with availability

```python
def add_labor_constraints(self, labor_resources, calendars):
    """Integrate work calendars and labor capacity"""
    # Create availability intervals for each worker
    for worker in labor_resources:
        for shift in worker.calendar.shifts:
            # Use fixed intervals for availability
            available = self.model.NewFixedInterval(
                shift.start, shift.duration, f'avail_{worker.id}_{shift.id}'
            )

            # Tasks assigned to this worker must fit within shifts
            # Uses efficient cumulative constraint
```

Constraints to add:
1. Labor assignment variables (similar to machines)
2. Calendar-based availability
3. Skill requirements
4. Multi-resource tasks (machine + labor)

# Phase 5: Advanced Objectives & Optimization

Goal: Implement sophisticated two-phase optimization

```python
def solve_two_phase(self):
    """Two-phase optimization following OR-Tools patterns"""
    # Phase 1: Minimize time objectives
    lateness_vars = []
    for job in jobs:
        lateness = self.model.NewIntVar(0, horizon, f'lateness_{job.id}')
        job_end = max(self.task_ends[t.id] for t in job.tasks)
        self.model.AddMaxEquality(lateness, [0, job_end - job.due_date])
        lateness_vars.append(lateness)

    makespan = self.model.NewIntVar(0, horizon, 'makespan')
    self.model.AddMaxEquality(makespan, list(self.task_ends.values()))

    # Phase 1 objective
    self.model.Minimize(sum(lateness_vars) + makespan)

    # Solve phase 1
    solver = cp_model.CpSolver()
    status = solver.Solve(self.model)
    phase1_obj = solver.ObjectiveValue()

    # Phase 2: Add cost minimization with phase 1 constraint
    self.model.Add(sum(lateness_vars) + makespan <= int(phase1_obj * 1.1))

    # Cost objective
    cost_terms = []
    for task_id, assignment in self.resource_assignments.items():
        for r_idx, resource in enumerate(resources, 1):
            cost_terms.append(
                self.model.NewBoolVar() * resource.cost * task.duration
            )

    self.model.Minimize(sum(cost_terms))
```

# Phase 6: Production Hardening

Goal: Add robustness and special cases

Final additions:
1. Sequence reservation (mutex constraints)
2. Ghost tasks for cross-job exclusivity
3. WIP limits and flow balancing
4. Solution hints and warm starting
5. Symmetry breaking for identical resources
6. Search strategies and time limits

# Key Implementation Principles:

1. **Start Simple**: Begin with basic interval variables and precedence
2. **Use Integer Variables**: For resource assignments (more efficient than booleans)
3. **Leverage Optional Intervals**: For resource-task combinations
4. **Cookie-Cutter Constraints**: Use proven patterns (cumulative, circuit, etc.)
5. **Avoid String Lookups**: Direct variable access via dictionaries
6. **Pure Functions**: Constraints should only create expressions, not solve
7. **Incremental Complexity**: Each phase builds on previous foundation
8. **Test Each Phase**: Ensure correctness before adding complexity

# Recommended File Structure:

```
src/solver_rewrite/
├── core/
│   ├── model.py          # CPSATScheduler class
│   ├── variables.py      # Variable creation helpers
│   └── objectives.py     # Objective function builders
├── constraints/
│   ├── temporal.py       # Time-based constraints
│   ├── resources.py      # Resource assignment
│   ├── batching.py       # Batch processing
│   └── advanced.py       # WIP, sequences, etc.
├── data/
│   ├── loader.py         # Data loading
│   └── validator.py      # Input validation
└── solver.py             # Main entry point
```

This phased approach allows you to:
- Build incrementally with working solver at each phase
- Test thoroughly between phases
- Refactor minimally as you add features
- Maintain clean separation of concerns
- Follow OR-Tools best practices throughout