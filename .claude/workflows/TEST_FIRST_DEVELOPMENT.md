# Test-First Development Pattern for OR-Tools

## Overview

Test-Driven Development (TDD) adapted specifically for constraint programming with OR-Tools, ensuring correctness and performance from the start.

## TDD Cycle for OR-Tools

```
┌─────────────────────────────────────────────┐
│              TDD Cycle                      │
├────────┬────────┬────────┬────────┬────────┤
│  RED   │ GREEN  │REFACTOR│OPTIMIZE│VALIDATE│
│ Write  │ Make   │ Clean  │ Perf   │ Check  │
│ Test   │ Pass   │ Code   │ Tune   │ Solver │
└────────┴────────┴────────┴────────┴────────┘
```

## Phase 1: RED - Write Failing Test First

### Step 1: Define Expected Behavior

```python
# tests/unit/constraints/test_skills.py
def test_skill_matching_constraint():
    """Test that tasks are only assigned to machines with required skills."""
    # This test will fail - constraint doesn't exist yet
    
    # GIVEN: Model with tasks requiring specific skills
    model = cp_model.CpModel()
    
    # Task 1 requires "welding" skill
    task_skills = {(1, 1): ["welding"]}
    
    # Machine 1 has welding, Machine 2 doesn't
    machine_skills = {
        1: ["welding", "cutting"],
        2: ["painting", "assembly"]
    }
    
    # Variables
    task_assigned = {}
    for task in [(1, 1)]:
        for machine in [1, 2]:
            task_assigned[(task[0], task[1], machine)] = \
                model.NewBoolVar(f'assign_{task[0]}_{task[1]}_{machine}')
    
    # WHEN: Adding skill matching constraints (doesn't exist yet!)
    from src.solver.constraints.skills import add_skill_matching_constraints
    add_skill_matching_constraints(
        model, task_assigned, task_skills, machine_skills
    )
    
    # THEN: Task should only be assignable to Machine 1
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    assert status == cp_model.OPTIMAL
    assert solver.Value(task_assigned[(1, 1, 1)]) == 1  # Assigned to Machine 1
    assert solver.Value(task_assigned[(1, 1, 2)]) == 0  # Not to Machine 2
```

### Step 2: Run Test to Confirm Failure

```bash
$ pytest tests/unit/constraints/test_skills.py::test_skill_matching_constraint

FAILED - ImportError: cannot import name 'add_skill_matching_constraints'
```

## Phase 2: GREEN - Make Test Pass

### Step 1: Implement Minimal Solution

```python
# src/solver/constraints/skills.py
from ortools.sat.python import cp_model
from typing import Dict, List, Tuple

def add_skill_matching_constraints(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int, int], cp_model.IntVar],
    task_skills: Dict[Tuple[int, int], List[str]],
    machine_skills: Dict[int, List[str]]
) -> None:
    """Add constraints ensuring tasks assigned to capable machines.
    
    Constraints added:
        - Task can only be assigned to machine with required skills
    """
    for (job_id, task_id), required_skills in task_skills.items():
        for machine_id, available_skills in machine_skills.items():
            # Check if machine has all required skills
            has_all_skills = all(
                skill in available_skills 
                for skill in required_skills
            )
            
            if not has_all_skills:
                # Prohibit assignment
                model.Add(task_assigned[(job_id, task_id, machine_id)] == 0)
```

### Step 2: Verify Test Passes

```bash
$ pytest tests/unit/constraints/test_skills.py::test_skill_matching_constraint

PASSED
```

## Phase 3: REFACTOR - Improve Code Quality

### Step 1: Add More Tests First

```python
def test_multiple_skill_requirements():
    """Test tasks requiring multiple skills."""
    # GIVEN: Task requiring multiple skills
    model = cp_model.CpModel()
    task_skills = {(1, 1): ["welding", "precision"]}
    machine_skills = {
        1: ["welding"],  # Missing precision
        2: ["welding", "precision", "cutting"]  # Has both
    }
    
    # ... rest of test ...
    
    # THEN: Only Machine 2 should be eligible
    assert solver.Value(task_assigned[(1, 1, 1)]) == 0
    assert solver.Value(task_assigned[(1, 1, 2)]) == 1

def test_no_skill_requirements():
    """Test tasks with no skill requirements."""
    # Edge case: task with empty skill list
    
def test_no_capable_machines():
    """Test when no machine has required skills."""
    # Should make model infeasible
```

### Step 2: Refactor Implementation

```python
def add_skill_matching_constraints(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int, int], cp_model.IntVar],
    task_skills: Dict[Tuple[int, int], List[str]],
    machine_skills: Dict[int, List[str]]
) -> None:
    """Add constraints ensuring tasks assigned to capable machines.
    
    Mathematical formulation:
        For each task t with skills S_t and machine m with skills S_m:
        assigned[t,m] => S_t ⊆ S_m
    
    Business logic:
        Tasks can only be assigned to machines that have all required skills.
        
    Constraints added:
        - If machine lacks any required skill, assignment forbidden
        - Empty skill requirements mean any machine is capable
    """
    for (job_id, task_id), required_skills in task_skills.items():
        # Handle empty skill requirements
        if not required_skills:
            continue  # No constraints needed
            
        for machine_id in machine_skills:
            key = (job_id, task_id, machine_id)
            
            # Skip if variable doesn't exist (machine not eligible)
            if key not in task_assigned:
                continue
                
            # Check skill compatibility
            machine_has_skills = machine_skills.get(machine_id, [])
            can_assign = all(
                skill in machine_has_skills 
                for skill in required_skills
            )
            
            if not can_assign:
                # Prohibit this assignment
                model.Add(task_assigned[key] == 0)
```

## Phase 4: OPTIMIZE - Performance Tuning

### Step 1: Add Performance Test

```python
@pytest.mark.benchmark
def test_skill_matching_performance(benchmark):
    """Benchmark skill matching with many tasks/machines."""
    # GIVEN: Large problem
    num_tasks = 1000
    num_machines = 50
    num_skills = 20
    
    model, variables, skills = create_large_skill_problem(
        num_tasks, num_machines, num_skills
    )
    
    # WHEN: Adding constraints
    result = benchmark(
        add_skill_matching_constraints,
        model, variables, skills['tasks'], skills['machines']
    )
    
    # THEN: Should complete quickly
    assert benchmark.stats['mean'] < 0.1  # Less than 100ms
```

### Step 2: Optimize If Needed

```python
def add_skill_matching_constraints_optimized(
    model: cp_model.CpModel,
    task_assigned: Dict[Tuple[int, int, int], cp_model.IntVar],
    task_skills: Dict[Tuple[int, int], List[str]],
    machine_skills: Dict[int, List[str]]
) -> None:
    """Optimized version with preprocessing."""
    
    # Precompute skill compatibility matrix
    compatibility = {}
    for (job_id, task_id), req_skills in task_skills.items():
        if not req_skills:  # Skip empty
            continue
            
        req_set = set(req_skills)  # Convert to set for O(1) lookup
        
        for machine_id, avail_skills in machine_skills.items():
            avail_set = set(avail_skills)
            
            # Check subset relationship
            if req_set.issubset(avail_set):
                compatibility[(job_id, task_id, machine_id)] = True
            else:
                compatibility[(job_id, task_id, machine_id)] = False
    
    # Apply constraints based on compatibility
    for key, var in task_assigned.items():
        if key in compatibility and not compatibility[key]:
            model.Add(var == 0)
```

## Phase 5: VALIDATE - Solver Verification

### Step 1: Integration Test

```python
def test_skills_with_full_solver():
    """Test skill constraints in complete solver."""
    # GIVEN: Complete problem with multiple constraint types
    problem = SchedulingProblem()
    
    # Add tasks with skills
    problem.add_task(Task(id=1, name="Welding Job", skills=["welding"]))
    problem.add_task(Task(id=2, name="Paint Job", skills=["painting"]))
    
    # Add machines with skills
    problem.add_machine(Machine(id=1, name="Welder", skills=["welding"]))
    problem.add_machine(Machine(id=2, name="Painter", skills=["painting"]))
    
    # Add precedence
    problem.add_precedence(1, 2)  # Paint after welding
    
    # WHEN: Solving
    solver = FreshSolver()
    solution = solver.solve(problem)
    
    # THEN: Skills should be respected
    assert solution.task_assignments[1] == 1  # Welding on welder
    assert solution.task_assignments[2] == 2  # Painting on painter
    assert solution.task_starts[2] >= solution.task_ends[1]  # Precedence
```

## TDD Workflow Integration

### With Claude Commands

```bash
# Step 1: Write test first
/test-constraint skill_matching

# Step 2: Run test (should fail)
pytest tests/unit/constraints/test_skills.py -v

# Step 3: Implement constraint
/add-constraint skill_matching

# Step 4: Run test again (should pass)
pytest tests/unit/constraints/test_skills.py -v

# Step 5: Check implementation
/check-constraint add_skill_matching_constraints

# Step 6: Profile if needed
/profile-solver --focus skill_constraints
```

### Continuous TDD Cycle

```python
class TDDSession:
    """Track TDD cycles in development."""
    
    def __init__(self):
        self.cycles = []
        self.current_cycle = None
        
    def start_cycle(self, feature: str):
        """Begin new TDD cycle."""
        self.current_cycle = {
            'feature': feature,
            'test_written': datetime.now(),
            'test_passing': None,
            'refactored': None,
            'optimized': None
        }
        
    def mark_green(self):
        """Mark test as passing."""
        self.current_cycle['test_passing'] = datetime.now()
        
    def mark_refactored(self):
        """Mark refactoring complete."""
        self.current_cycle['refactored'] = datetime.now()
        
    def complete_cycle(self):
        """Complete current cycle."""
        self.cycles.append(self.current_cycle)
        cycle_time = (
            self.current_cycle['test_passing'] - 
            self.current_cycle['test_written']
        )
        print(f"Cycle time: {cycle_time}")
```

## TDD Best Practices for OR-Tools

### 1. Test Constraint Behavior, Not Implementation

```python
# ❌ Bad: Testing implementation details
def test_constraint_adds_specific_formula():
    # Don't test the exact formula used
    assert "model.Add(x <= y)" in constraint_code

# ✅ Good: Testing behavior
def test_constraint_enforces_ordering():
    # Test that constraint achieves its goal
    solution = solve_with_constraint()
    assert solution.respects_ordering()
```

### 2. Use Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(
    num_tasks=st.integers(min_value=1, max_value=100),
    num_machines=st.integers(min_value=1, max_value=20)
)
def test_skill_matching_properties(num_tasks, num_machines):
    """Test properties that should always hold."""
    problem = generate_random_problem(num_tasks, num_machines)
    solution = solve_with_skills(problem)
    
    # Properties that must always be true
    assert all_tasks_have_required_skills(solution)
    assert no_skill_violations(solution)
    assert solution_is_feasible_or_infeasible(solution)
```

### 3. Test Error Conditions First

```python
def test_error_conditions():
    """Test error handling before happy path."""
    # Test with None
    with pytest.raises(ValueError):
        add_skill_matching_constraints(None, {}, {}, {})
    
    # Test with invalid data
    with pytest.raises(KeyError):
        add_skill_matching_constraints(
            model, 
            task_assigned,
            {(1, 1): ["nonexistent_skill"]},
            {}
        )
```

### 4. Performance Tests from Start

```python
def test_constraint_performance_baseline():
    """Establish performance baseline early."""
    sizes = [10, 100, 1000]
    times = []
    
    for size in sizes:
        start = time.time()
        model = create_model_with_constraints(size)
        elapsed = time.time() - start
        times.append(elapsed)
        
        # Should be roughly linear
        if len(times) > 1:
            ratio = times[-1] / times[-2]
            assert ratio < 15  # Not worse than O(n log n)
```

## TDD Patterns for Phases

### Phase Development Pattern

```python
# Phase 2 TDD: Start with integration test
def test_phase_2_complete_integration():
    """Test all Phase 2 features together."""
    problem = create_phase_2_problem()
    
    # Should include all Phase 2 constraints
    assert has_resource_capacity(problem)
    assert has_skill_matching(problem)
    assert has_variable_durations(problem)
    
    solution = solve_phase_2(problem)
    assert solution.meets_all_phase_2_requirements()
```

### Incremental Feature Pattern

```python
# Feature 1: Basic skills
def test_basic_skill_matching():
    """Single skill per task."""
    pass

# Feature 2: Multiple skills
def test_multiple_skill_requirements():
    """Tasks needing multiple skills."""
    pass

# Feature 3: Skill levels
def test_skill_level_matching():
    """Skills with proficiency levels."""
    pass

# Build features incrementally, each with full TDD cycle
```

## Common TDD Pitfalls in OR-Tools

### 1. Testing Solver Internals
Don't test how OR-Tools works internally

### 2. Overly Specific Tests
Test behavior, not exact values

### 3. Ignoring Infeasibility
Always test when constraints make problem infeasible

### 4. Missing Performance Tests
OR-Tools performance crucial - test early

### 5. Not Testing Interactions
Constraints interact - test combinations