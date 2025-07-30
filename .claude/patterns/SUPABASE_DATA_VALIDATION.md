# Supabase Data Validation Patterns

## Overview

Comprehensive patterns for validating data loaded from Supabase before processing with OR-Tools solver, ensuring data integrity and graceful error handling.

## Validation Pipeline

```
┌─────────────────────────────────────────────┐
│          Data Validation Flow               │
├──────────┬───────────┬──────────┬──────────┤
│   Load   │ Validate  │Transform │  Verify  │
│   Data   │  Schema   │  & Clean │ Business │
└──────────┴───────────┴──────────┴──────────┘
```

## Layer 1: Schema Validation

### Database Constraints

```sql
-- Enforce constraints at database level
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    earliest_start INTEGER CHECK (earliest_start >= 0),
    latest_end INTEGER CHECK (latest_end > earliest_start),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Partial index for active tasks
CREATE INDEX idx_active_tasks ON tasks(job_id) 
WHERE status = 'active';

-- Constraint to ensure task modes exist
ALTER TABLE task_modes 
ADD CONSTRAINT fk_task_exists 
FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE;
```

### Python Schema Validation

```python
# src/solver/data/validators.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict] = None

class SupabaseDataValidator:
    """Validates data loaded from Supabase."""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_problem_data(self, data: Dict) -> ValidationResult:
        """Validate complete problem data from Supabase."""
        self.validation_errors = []
        self.validation_warnings = []
        
        # Schema validation
        if not self._validate_schema(data):
            return ValidationResult(
                is_valid=False,
                errors=self.validation_errors,
                warnings=self.validation_warnings
            )
        
        # Data integrity validation
        cleaned_data = self._validate_and_clean(data)
        
        # Business rule validation
        if not self._validate_business_rules(cleaned_data):
            return ValidationResult(
                is_valid=False,
                errors=self.validation_errors,
                warnings=self.validation_warnings,
                cleaned_data=cleaned_data
            )
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=self.validation_warnings,
            cleaned_data=cleaned_data
        )
    
    def _validate_schema(self, data: Dict) -> bool:
        """Validate data structure matches expected schema."""
        required_keys = ['jobs', 'tasks', 'machines', 'precedences']
        
        for key in required_keys:
            if key not in data:
                self.validation_errors.append(f"Missing required key: {key}")
                return False
        
        # Validate each section
        if not isinstance(data['jobs'], list):
            self.validation_errors.append("'jobs' must be a list")
            return False
            
        if not isinstance(data['tasks'], list):
            self.validation_errors.append("'tasks' must be a list")
            return False
            
        return True
```

## Layer 2: Data Integrity Validation

### Task Validation

```python
def _validate_tasks(self, tasks: List[Dict]) -> List[Dict]:
    """Validate and clean task data."""
    validated_tasks = []
    task_ids = set()
    
    for task in tasks:
        # Check required fields
        if 'id' not in task:
            self.validation_errors.append(f"Task missing 'id' field: {task}")
            continue
            
        if 'duration_minutes' not in task:
            self.validation_errors.append(f"Task {task['id']} missing duration")
            continue
        
        # Check for duplicates
        if task['id'] in task_ids:
            self.validation_errors.append(f"Duplicate task ID: {task['id']}")
            continue
        task_ids.add(task['id'])
        
        # Validate duration
        duration = task.get('duration_minutes', 0)
        if duration <= 0:
            self.validation_errors.append(
                f"Task {task['id']} has invalid duration: {duration}"
            )
            continue
        
        # Validate time windows if present
        if 'earliest_start' in task and 'latest_end' in task:
            if task['earliest_start'] >= task['latest_end']:
                self.validation_errors.append(
                    f"Task {task['id']} has invalid time window"
                )
                continue
        
        # Clean and normalize
        cleaned_task = self._clean_task_data(task)
        validated_tasks.append(cleaned_task)
    
    return validated_tasks

def _clean_task_data(self, task: Dict) -> Dict:
    """Clean and normalize task data."""
    # Convert to 15-minute intervals
    duration_minutes = task['duration_minutes']
    duration_intervals = (duration_minutes + 14) // 15  # Round up
    
    cleaned = {
        'id': int(task['id']),
        'job_id': int(task['job_id']),
        'duration': duration_intervals,
        'duration_minutes': duration_minutes,
        'name': str(task.get('name', f"Task_{task['id']}")),
    }
    
    # Optional fields
    if 'earliest_start' in task:
        cleaned['earliest_start'] = int(task['earliest_start'])
    if 'latest_end' in task:
        cleaned['latest_end'] = int(task['latest_end'])
    if 'machine_id' in task:
        cleaned['machine_id'] = int(task['machine_id'])
        
    return cleaned
```

### Precedence Validation

```python
def _validate_precedences(self, precedences: List[Dict], task_ids: set) -> List[Dict]:
    """Validate precedence relationships."""
    validated_precedences = []
    precedence_pairs = set()
    
    for prec in precedences:
        # Validate structure
        if 'predecessor_id' not in prec or 'successor_id' not in prec:
            self.validation_errors.append(f"Invalid precedence: {prec}")
            continue
        
        pred_id = prec['predecessor_id']
        succ_id = prec['successor_id']
        
        # Check tasks exist
        if pred_id not in task_ids:
            self.validation_errors.append(
                f"Precedence references non-existent task: {pred_id}"
            )
            continue
        if succ_id not in task_ids:
            self.validation_errors.append(
                f"Precedence references non-existent task: {succ_id}"
            )
            continue
        
        # Check for self-loops
        if pred_id == succ_id:
            self.validation_errors.append(
                f"Self-loop precedence detected: {pred_id}"
            )
            continue
        
        # Check for duplicates
        pair = (pred_id, succ_id)
        if pair in precedence_pairs:
            self.validation_warnings.append(
                f"Duplicate precedence: {pred_id} -> {succ_id}"
            )
            continue
        precedence_pairs.add(pair)
        
        validated_precedences.append({
            'predecessor_id': int(pred_id),
            'successor_id': int(succ_id)
        })
    
    # Check for cycles
    if self._has_cycles(validated_precedences):
        self.validation_errors.append("Circular dependencies detected")
        
    return validated_precedences

def _has_cycles(self, precedences: List[Dict]) -> bool:
    """Check for circular dependencies using DFS."""
    from collections import defaultdict
    
    # Build adjacency list
    graph = defaultdict(list)
    for prec in precedences:
        graph[prec['predecessor_id']].append(prec['successor_id'])
    
    # DFS cycle detection
    visited = set()
    rec_stack = set()
    
    def has_cycle_util(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                if has_cycle_util(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    # Check all nodes
    for node in graph:
        if node not in visited:
            if has_cycle_util(node):
                return True
    
    return False
```

## Layer 3: Business Rule Validation

### Constraint Compatibility

```python
def _validate_business_rules(self, data: Dict) -> bool:
    """Validate business rules and constraint compatibility."""
    
    # Rule 1: Tasks assigned to machines must have required skills
    if 'task_skills' in data and 'machine_skills' in data:
        if not self._validate_skill_compatibility(data):
            return False
    
    # Rule 2: Resource capacity must not be exceeded
    if 'resources' in data:
        if not self._validate_resource_capacity(data):
            return False
    
    # Rule 3: Shift constraints must be feasible
    if 'shifts' in data:
        if not self._validate_shift_feasibility(data):
            return False
    
    # Rule 4: Time windows must allow feasible schedule
    if not self._validate_time_window_feasibility(data):
        return False
    
    return True

def _validate_skill_compatibility(self, data: Dict) -> bool:
    """Validate tasks can be assigned to machines with skills."""
    task_skills = {t['task_id']: t['skills'] for t in data['task_skills']}
    machine_skills = {m['machine_id']: m['skills'] for m in data['machine_skills']}
    
    for task in data['tasks']:
        if task['id'] in task_skills:
            required_skills = set(task_skills[task['id']])
            
            # Check if at least one machine can handle this task
            can_assign = False
            for machine_id, skills in machine_skills.items():
                if required_skills.issubset(set(skills)):
                    can_assign = True
                    break
            
            if not can_assign:
                self.validation_errors.append(
                    f"Task {task['id']} requires skills {required_skills} "
                    f"but no machine has all required skills"
                )
                return False
    
    return True
```

## Layer 4: Data Loading with Validation

### Safe Data Loader

```python
# src/solver/data/safe_loader.py
from supabase import create_client
from typing import Optional
import os

class SafeSupabaseLoader:
    """Load data from Supabase with validation."""
    
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment")
            
        self.client = create_client(url, key)
        self.validator = SupabaseDataValidator()
    
    def load_problem(self, problem_id: int) -> Optional[SchedulingProblem]:
        """Load and validate problem from database."""
        try:
            # Load data with error handling
            data = self._fetch_problem_data(problem_id)
            
            # Validate
            validation_result = self.validator.validate_problem_data(data)
            
            if not validation_result.is_valid:
                logger.error(f"Validation failed: {validation_result.errors}")
                raise ValueError(f"Invalid problem data: {validation_result.errors}")
            
            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(warning)
            
            # Convert to domain model
            return self._convert_to_problem(validation_result.cleaned_data)
            
        except Exception as e:
            logger.error(f"Failed to load problem {problem_id}: {e}")
            raise
    
    def _fetch_problem_data(self, problem_id: int) -> Dict:
        """Fetch problem data with transactions."""
        data = {}
        
        # Use RLS policies for access control
        # Fetch in single transaction for consistency
        
        # Jobs
        jobs_response = self.client.table('jobs')\
            .select('*')\
            .eq('problem_id', problem_id)\
            .execute()
        data['jobs'] = jobs_response.data
        
        # Tasks with related data
        tasks_response = self.client.table('tasks')\
            .select('*, task_modes(*), task_skills(*)')\
            .eq('problem_id', problem_id)\
            .execute()
        data['tasks'] = tasks_response.data
        
        # Machines
        machines_response = self.client.table('machines')\
            .select('*, machine_skills(*)')\
            .eq('problem_id', problem_id)\
            .execute()
        data['machines'] = machines_response.data
        
        # Precedences
        precedences_response = self.client.table('precedences')\
            .select('*')\
            .eq('problem_id', problem_id)\
            .execute()
        data['precedences'] = precedences_response.data
        
        return data
```

## Error Recovery Patterns

### Graceful Degradation

```python
class ValidationErrorHandler:
    """Handle validation errors gracefully."""
    
    def handle_validation_failure(
        self, 
        validation_result: ValidationResult,
        problem_id: int
    ) -> Optional[SchedulingProblem]:
        """Attempt to recover from validation failures."""
        
        if not validation_result.cleaned_data:
            return None
        
        # Try to create partial problem
        if self._can_create_partial(validation_result):
            logger.warning(
                f"Creating partial problem for {problem_id} "
                f"with {len(validation_result.errors)} errors"
            )
            return self._create_partial_problem(validation_result.cleaned_data)
        
        # Log detailed errors for debugging
        self._log_validation_errors(problem_id, validation_result)
        
        return None
    
    def _can_create_partial(self, result: ValidationResult) -> bool:
        """Check if partial problem is viable."""
        # Must have at least jobs and tasks
        if not result.cleaned_data:
            return False
            
        return ('jobs' in result.cleaned_data and 
                'tasks' in result.cleaned_data and
                len(result.cleaned_data['tasks']) > 0)
    
    def _create_partial_problem(self, data: Dict) -> SchedulingProblem:
        """Create problem with available valid data."""
        problem = SchedulingProblem()
        
        # Add valid components
        for job in data.get('jobs', []):
            problem.add_job(Job(**job))
            
        for task in data.get('tasks', []):
            problem.add_task(Task(**task))
        
        # Skip invalid precedences
        valid_task_ids = {t['id'] for t in data.get('tasks', [])}
        for prec in data.get('precedences', []):
            if (prec['predecessor_id'] in valid_task_ids and
                prec['successor_id'] in valid_task_ids):
                problem.add_precedence(
                    prec['predecessor_id'],
                    prec['successor_id']
                )
        
        return problem
```

## Transaction Patterns

### Atomic Operations

```python
class SupabaseTransactionManager:
    """Manage database transactions for consistency."""
    
    async def save_solution_atomic(
        self, 
        solution: Solution,
        problem_id: int
    ) -> bool:
        """Save solution atomically."""
        try:
            # Begin transaction (using Supabase RPC)
            async with self.client.transaction():
                # Create solution record
                solution_data = {
                    'problem_id': problem_id,
                    'status': solution.status,
                    'objective_value': solution.objective_value,
                    'solve_time': solution.solve_time,
                    'created_at': datetime.now()
                }
                
                solution_response = await self.client.table('solutions')\
                    .insert(solution_data)\
                    .execute()
                
                solution_id = solution_response.data[0]['id']
                
                # Save task assignments
                assignments = []
                for task_id, machine_id in solution.task_assignments.items():
                    assignments.append({
                        'solution_id': solution_id,
                        'task_id': task_id,
                        'machine_id': machine_id,
                        'start_time': solution.task_starts[task_id],
                        'end_time': solution.task_ends[task_id]
                    })
                
                if assignments:
                    await self.client.table('task_assignments')\
                        .insert(assignments)\
                        .execute()
                
                # Update problem status
                await self.client.table('problems')\
                    .update({'last_solved': datetime.now()})\
                    .eq('id', problem_id)\
                    .execute()
                
            return True
            
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False
```

## Real-time Validation

### Live Data Validation

```python
class RealtimeValidator:
    """Validate data changes in real-time."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.active_validations = {}
    
    def subscribe_to_changes(self, problem_id: int):
        """Subscribe to real-time changes with validation."""
        
        def on_task_change(payload):
            """Validate task changes."""
            change_type = payload['eventType']
            new_data = payload['new']
            old_data = payload.get('old', {})
            
            if change_type == 'UPDATE':
                # Validate duration changes
                if new_data.get('duration_minutes', 0) <= 0:
                    self._reject_change(
                        'tasks', 
                        new_data['id'],
                        "Duration must be positive"
                    )
                    
            elif change_type == 'INSERT':
                # Validate new task
                validator = SupabaseDataValidator()
                if not validator._validate_tasks([new_data]):
                    self._reject_change(
                        'tasks',
                        new_data['id'], 
                        "Invalid task data"
                    )
        
        # Subscribe to tables
        self.client.table('tasks')\
            .on('*', on_task_change)\
            .eq('problem_id', problem_id)\
            .subscribe()
```

## Validation Best Practices

### 1. Layer Your Validation

```python
# Database level - basic constraints
# Application level - business rules
# API level - input sanitization
# UI level - user feedback
```

### 2. Fail Fast but Recover Gracefully

```python
try:
    # Validate early
    if not validate_input(data):
        raise ValidationError("Invalid input")
    
    # Process with confidence
    result = process_valid_data(data)
    
except ValidationError as e:
    # Attempt recovery
    if can_recover(e):
        result = process_with_defaults(data)
    else:
        # Fail with clear error
        raise
```

### 3. Log Everything

```python
logger.info(f"Loading problem {problem_id}")
logger.debug(f"Fetched {len(tasks)} tasks")
logger.warning(f"Validation warnings: {warnings}")
logger.error(f"Validation failed: {errors}")
```

### 4. Test Validation Thoroughly

```python
def test_validation_edge_cases():
    """Test all validation edge cases."""
    validator = SupabaseDataValidator()
    
    # Empty data
    assert not validator.validate_problem_data({}).is_valid
    
    # Missing required fields
    assert not validator.validate_problem_data({'jobs': []}).is_valid
    
    # Invalid values
    data = {
        'jobs': [{'id': 1}],
        'tasks': [{'id': 1, 'duration_minutes': -10}]
    }
    assert not validator.validate_problem_data(data).is_valid
```

## Integration with OR-Tools

### Pre-Solver Validation

```python
def validate_before_solve(problem: SchedulingProblem) -> ValidationResult:
    """Final validation before passing to solver."""
    errors = []
    
    # Check problem is solvable
    if not problem.tasks:
        errors.append("No tasks to schedule")
    
    # Check all tasks have durations
    for task in problem.tasks:
        if task.duration <= 0:
            errors.append(f"Task {task.id} has invalid duration")
    
    # Check precedences are valid
    task_ids = {t.id for t in problem.tasks}
    for pred, succ in problem.precedences:
        if pred not in task_ids or succ not in task_ids:
            errors.append(f"Invalid precedence: {pred} -> {succ}")
    
    # Check for circular dependencies
    if has_circular_dependencies(problem.precedences):
        errors.append("Circular dependencies detected")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=[],
        cleaned_data=None
    )
```

This comprehensive validation system ensures data integrity from database to solver!