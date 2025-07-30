# Solution Storage Templates

## Overview

Comprehensive templates for storing OR-Tools solver solutions in Supabase, including efficient storage patterns, versioning, and retrieval strategies.

## Solution Data Architecture

```
┌─────────────────────────────────────────────┐
│         Solution Storage Layers             │
├──────────┬───────────┬──────────┬──────────┤
│ Metadata │   Core    │ Details  │ History  │
│  Layer   │ Solution  │  Layer   │  Layer   │
└──────────┴───────────┴──────────┴──────────┘
```

## Database Schema

### Core Tables

```sql
-- Solutions table (metadata layer)
CREATE TABLE solutions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    problem_id INTEGER REFERENCES problems(id) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL CHECK (status IN ('OPTIMAL', 'FEASIBLE', 'INFEASIBLE', 'ERROR')),
    objective_value DECIMAL(10,2),
    solve_time_seconds DECIMAL(10,3) NOT NULL,
    solver_parameters JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance metrics
    variables_count INTEGER,
    constraints_count INTEGER,
    iterations INTEGER,
    first_solution_time DECIMAL(10,3),
    
    -- Composite unique constraint for versioning
    UNIQUE(problem_id, version)
);

-- Task assignments (core solution data)
CREATE TABLE task_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    solution_id UUID REFERENCES solutions(id) ON DELETE CASCADE,
    task_id INTEGER NOT NULL,
    machine_id INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    
    -- Denormalized for query performance
    job_id INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    
    -- Indexes for common queries
    INDEX idx_solution_tasks (solution_id, task_id),
    INDEX idx_timeline (solution_id, start_time, end_time),
    INDEX idx_machine_schedule (solution_id, machine_id, start_time)
);

-- Resource utilization (if using resources)
CREATE TABLE resource_utilization (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    solution_id UUID REFERENCES solutions(id) ON DELETE CASCADE,
    resource_id INTEGER NOT NULL,
    time_point INTEGER NOT NULL,
    usage_amount INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    
    INDEX idx_resource_timeline (solution_id, resource_id, time_point)
);

-- Solution history tracking
CREATE TABLE solution_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    solution_id UUID REFERENCES solutions(id),
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    performed_by UUID REFERENCES auth.users(id)
);
```

### Materialized Views for Performance

```sql
-- Machine utilization view
CREATE MATERIALIZED VIEW machine_utilization AS
SELECT 
    s.id as solution_id,
    ta.machine_id,
    COUNT(*) as task_count,
    SUM(ta.duration) as total_duration,
    MIN(ta.start_time) as first_task_start,
    MAX(ta.end_time) as last_task_end,
    (MAX(ta.end_time) - MIN(ta.start_time)) as span,
    ROUND(SUM(ta.duration)::DECIMAL / NULLIF((MAX(ta.end_time) - MIN(ta.start_time)), 0) * 100, 2) as utilization_percent
FROM solutions s
JOIN task_assignments ta ON ta.solution_id = s.id
WHERE s.is_active = true
GROUP BY s.id, ta.machine_id;

-- Create index
CREATE INDEX idx_machine_util_solution ON machine_utilization(solution_id);

-- Refresh strategy
REFRESH MATERIALIZED VIEW CONCURRENTLY machine_utilization;
```

## Solution Storage Patterns

### Pattern 1: Basic Solution Storage

```python
# src/solver/storage/solution_storage.py
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from dataclasses import asdict

class SolutionStorage:
    """Store and retrieve solver solutions."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def store_solution(
        self,
        solution: Solution,
        problem_id: int,
        solver_params: Optional[Dict] = None
    ) -> str:
        """Store solution with all details."""
        try:
            # Start transaction
            solution_id = self._create_solution_record(
                solution, problem_id, solver_params
            )
            
            # Store assignments
            self._store_task_assignments(solution_id, solution)
            
            # Store resource utilization if applicable
            if hasattr(solution, 'resource_utilization'):
                self._store_resource_utilization(
                    solution_id, solution.resource_utilization
                )
            
            # Update problem status
            self._update_problem_status(problem_id, solution_id)
            
            return solution_id
            
        except Exception as e:
            logger.error(f"Failed to store solution: {e}")
            raise
    
    def _create_solution_record(
        self, 
        solution: Solution,
        problem_id: int,
        solver_params: Optional[Dict]
    ) -> str:
        """Create main solution record."""
        # Get next version number
        version = self._get_next_version(problem_id)
        
        solution_data = {
            'problem_id': problem_id,
            'version': version,
            'status': solution.status,
            'objective_value': solution.objective_value,
            'solve_time_seconds': solution.solve_time,
            'solver_parameters': solver_params or {},
            'variables_count': solution.variables_count,
            'constraints_count': solution.constraints_count,
            'iterations': solution.iterations,
            'first_solution_time': solution.first_solution_time
        }
        
        response = self.client.table('solutions')\
            .insert(solution_data)\
            .execute()
            
        return response.data[0]['id']
    
    def _store_task_assignments(
        self, 
        solution_id: str,
        solution: Solution
    ) -> None:
        """Store task assignments efficiently."""
        assignments = []
        
        for task_id, machine_id in solution.task_assignments.items():
            assignments.append({
                'solution_id': solution_id,
                'task_id': task_id,
                'machine_id': machine_id,
                'start_time': solution.task_starts[task_id],
                'end_time': solution.task_ends[task_id],
                'job_id': solution.task_to_job[task_id],
                'duration': solution.task_ends[task_id] - solution.task_starts[task_id]
            })
        
        # Batch insert for performance
        if assignments:
            self.client.table('task_assignments')\
                .insert(assignments)\
                .execute()
```

### Pattern 2: Large Solution Handling

```python
class LargeSolutionStorage(SolutionStorage):
    """Handle storage of large solutions efficiently."""
    
    BATCH_SIZE = 1000  # Insert in batches
    
    def store_large_solution(
        self,
        solution: Solution,
        problem_id: int
    ) -> str:
        """Store large solution with batching and compression."""
        solution_id = self._create_solution_record(solution, problem_id)
        
        # Process assignments in batches
        assignments = self._prepare_assignments(solution_id, solution)
        
        for i in range(0, len(assignments), self.BATCH_SIZE):
            batch = assignments[i:i + self.BATCH_SIZE]
            self._store_assignment_batch(batch)
            
            # Log progress
            progress = min(100, (i + self.BATCH_SIZE) / len(assignments) * 100)
            logger.info(f"Stored {progress:.1f}% of assignments")
        
        # Store compressed full solution for backup
        self._store_compressed_backup(solution_id, solution)
        
        return solution_id
    
    def _store_compressed_backup(
        self,
        solution_id: str,
        solution: Solution
    ) -> None:
        """Store compressed solution for disaster recovery."""
        import gzip
        import json
        
        # Convert solution to JSON
        solution_dict = {
            'task_assignments': dict(solution.task_assignments),
            'task_starts': dict(solution.task_starts),
            'task_ends': dict(solution.task_ends),
            'status': solution.status,
            'objective_value': solution.objective_value
        }
        
        # Compress
        json_str = json.dumps(solution_dict)
        compressed = gzip.compress(json_str.encode('utf-8'))
        
        # Store in blob storage
        blob_path = f"solutions/{solution_id}/backup.gz"
        self.client.storage.from_('solution-backups')\
            .upload(blob_path, compressed)
```

### Pattern 3: Solution Versioning

```python
class VersionedSolutionStorage(SolutionStorage):
    """Handle solution versioning and history."""
    
    def store_with_history(
        self,
        solution: Solution,
        problem_id: int,
        changes_description: str = None
    ) -> str:
        """Store solution with version history."""
        # Check if updating existing solution
        current_active = self._get_active_solution(problem_id)
        
        if current_active:
            # Deactivate current
            self._deactivate_solution(current_active['id'])
            
            # Log changes
            self._log_solution_change(
                current_active['id'],
                solution,
                changes_description
            )
        
        # Store new version
        solution_id = self.store_solution(solution, problem_id)
        
        return solution_id
    
    def _get_next_version(self, problem_id: int) -> int:
        """Get next version number for problem."""
        response = self.client.table('solutions')\
            .select('version')\
            .eq('problem_id', problem_id)\
            .order('version', desc=True)\
            .limit(1)\
            .execute()
            
        if response.data:
            return response.data[0]['version'] + 1
        return 1
    
    def _log_solution_change(
        self,
        old_solution_id: str,
        new_solution: Solution,
        description: str
    ) -> None:
        """Log changes between solutions."""
        old_solution = self.retrieve_solution(old_solution_id)
        
        changes = self._calculate_changes(old_solution, new_solution)
        
        history_entry = {
            'solution_id': old_solution_id,
            'action': 'replaced',
            'changes': {
                'description': description,
                'objective_change': new_solution.objective_value - old_solution.objective_value,
                'task_changes': changes['task_changes'],
                'timing_changes': changes['timing_changes']
            }
        }
        
        self.client.table('solution_history')\
            .insert(history_entry)\
            .execute()
```

## Solution Retrieval Patterns

### Pattern 1: Efficient Retrieval

```python
class SolutionRetrieval:
    """Retrieve solutions efficiently."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self._cache = {}  # Simple cache
    
    def get_active_solution(self, problem_id: int) -> Optional[Solution]:
        """Get current active solution for problem."""
        # Check cache first
        cache_key = f"active_{problem_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Fetch from database
        response = self.client.table('solutions')\
            .select('*, task_assignments(*)')\
            .eq('problem_id', problem_id)\
            .eq('is_active', True)\
            .single()\
            .execute()
            
        if not response.data:
            return None
            
        solution = self._reconstruct_solution(response.data)
        
        # Cache for future use
        self._cache[cache_key] = solution
        
        return solution
    
    def get_solution_timeline(
        self,
        solution_id: str,
        machine_id: Optional[int] = None
    ) -> List[Dict]:
        """Get timeline view of solution."""
        query = self.client.table('task_assignments')\
            .select('task_id, machine_id, start_time, end_time, job_id')\
            .eq('solution_id', solution_id)\
            .order('start_time')
        
        if machine_id:
            query = query.eq('machine_id', machine_id)
            
        response = query.execute()
        
        return self._format_timeline(response.data)
    
    def _format_timeline(self, assignments: List[Dict]) -> List[Dict]:
        """Format assignments for timeline visualization."""
        timeline = []
        
        for assignment in assignments:
            timeline.append({
                'id': f"task_{assignment['task_id']}",
                'group': f"machine_{assignment['machine_id']}",
                'title': f"Job {assignment['job_id']} - Task {assignment['task_id']}",
                'start_time': assignment['start_time'],
                'end_time': assignment['end_time'],
                'className': f"job-{assignment['job_id']}"
            })
            
        return timeline
```

### Pattern 2: Comparative Retrieval

```python
class SolutionComparison:
    """Compare multiple solutions."""
    
    def compare_solutions(
        self,
        solution_ids: List[str]
    ) -> Dict:
        """Compare multiple solutions."""
        solutions = []
        
        for sol_id in solution_ids:
            response = self.client.table('solutions')\
                .select('*, machine_utilization!inner(*)')\
                .eq('id', sol_id)\
                .single()\
                .execute()
                
            solutions.append(response.data)
        
        return {
            'solutions': solutions,
            'comparison': {
                'objective_values': [s['objective_value'] for s in solutions],
                'solve_times': [s['solve_time_seconds'] for s in solutions],
                'utilization': self._compare_utilization(solutions),
                'makespan': self._compare_makespan(solutions)
            }
        }
    
    def get_solution_history(
        self,
        problem_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get solution history for problem."""
        response = self.client.table('solutions')\
            .select('id, version, status, objective_value, created_at')\
            .eq('problem_id', problem_id)\
            .order('version', desc=True)\
            .limit(limit)\
            .execute()
            
        return response.data
```

## Query Optimization

### Indexed Queries

```python
class OptimizedQueries:
    """Optimized query patterns."""
    
    def get_machine_schedule(
        self,
        solution_id: str,
        machine_id: int
    ) -> List[Dict]:
        """Get schedule for specific machine - uses index."""
        # Uses idx_machine_schedule index
        response = self.client.table('task_assignments')\
            .select('*')\
            .eq('solution_id', solution_id)\
            .eq('machine_id', machine_id)\
            .order('start_time')\
            .execute()
            
        return response.data
    
    def get_concurrent_tasks(
        self,
        solution_id: str,
        time_point: int
    ) -> List[Dict]:
        """Get tasks active at specific time - uses timeline index."""
        # Uses idx_timeline index
        response = self.client.table('task_assignments')\
            .select('*')\
            .eq('solution_id', solution_id)\
            .lte('start_time', time_point)\
            .gte('end_time', time_point)\
            .execute()
            
        return response.data
```

### Aggregation Queries

```sql
-- Create function for solution statistics
CREATE OR REPLACE FUNCTION get_solution_stats(p_solution_id UUID)
RETURNS TABLE (
    total_tasks INTEGER,
    total_machines INTEGER,
    makespan INTEGER,
    avg_utilization DECIMAL,
    total_idle_time INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT ta.task_id)::INTEGER as total_tasks,
        COUNT(DISTINCT ta.machine_id)::INTEGER as total_machines,
        MAX(ta.end_time)::INTEGER as makespan,
        AVG(mu.utilization_percent) as avg_utilization,
        SUM(mu.span - mu.total_duration)::INTEGER as total_idle_time
    FROM task_assignments ta
    LEFT JOIN machine_utilization mu ON mu.solution_id = ta.solution_id 
        AND mu.machine_id = ta.machine_id
    WHERE ta.solution_id = p_solution_id;
END;
$$ LANGUAGE plpgsql;

-- Usage from Python
stats = client.rpc('get_solution_stats', {'p_solution_id': solution_id}).execute()
```

## Solution Export Templates

### JSON Export

```python
def export_solution_json(solution_id: str) -> Dict:
    """Export solution as JSON."""
    response = client.table('solutions')\
        .select('''
            *,
            task_assignments (
                task_id,
                machine_id,
                start_time,
                end_time,
                job_id
            )
        ''')\
        .eq('id', solution_id)\
        .single()\
        .execute()
        
    return {
        'metadata': {
            'solution_id': response.data['id'],
            'problem_id': response.data['problem_id'],
            'status': response.data['status'],
            'objective': response.data['objective_value'],
            'created_at': response.data['created_at']
        },
        'schedule': response.data['task_assignments']
    }
```

### CSV Export

```python
def export_solution_csv(solution_id: str) -> str:
    """Export solution as CSV."""
    import csv
    import io
    
    assignments = get_task_assignments(solution_id)
    
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=['task_id', 'job_id', 'machine_id', 'start_time', 'end_time']
    )
    
    writer.writeheader()
    writer.writerows(assignments)
    
    return output.getvalue()
```

## Best Practices

### 1. Use Transactions

```python
async def store_solution_transactional(solution: Solution) -> str:
    """Store solution in transaction."""
    async with client.transaction():
        solution_id = await create_solution_record(solution)
        await store_assignments(solution_id, solution)
        await update_problem_status(solution.problem_id)
    return solution_id
```

### 2. Implement Archival

```python
def archive_old_solutions(days_old: int = 90):
    """Archive old solutions to cold storage."""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Move to archive table
    client.rpc('archive_old_solutions', {
        'cutoff_date': cutoff_date.isoformat()
    }).execute()
```

### 3. Monitor Performance

```python
def get_storage_metrics() -> Dict:
    """Get solution storage metrics."""
    return {
        'total_solutions': count_solutions(),
        'active_solutions': count_active_solutions(),
        'avg_solution_size': get_avg_solution_size(),
        'storage_used_mb': get_storage_usage(),
        'query_performance': get_query_stats()
    }
```

### 4. Handle Edge Cases

```python
def store_infeasible_solution(
    problem_id: int,
    infeasibility_reason: str
) -> str:
    """Store infeasible solution for analysis."""
    solution_data = {
        'problem_id': problem_id,
        'status': 'INFEASIBLE',
        'solver_parameters': {
            'infeasibility_reason': infeasibility_reason,
            'conflict_constraints': identify_conflicts()
        }
    }
    
    response = client.table('solutions').insert(solution_data).execute()
    return response.data[0]['id']
```

## Security Considerations

### Row Level Security

```sql
-- Only allow users to see their own solutions
ALTER TABLE solutions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own solutions"
ON solutions FOR SELECT
USING (auth.uid() = created_by);

CREATE POLICY "Users can create own solutions"
ON solutions FOR INSERT
WITH CHECK (auth.uid() = created_by);
```

### Data Validation

```python
def validate_solution_before_store(solution: Solution) -> bool:
    """Validate solution data before storage."""
    # Check all tasks are assigned
    if len(solution.task_assignments) != len(solution.all_tasks):
        raise ValueError("Not all tasks assigned")
    
    # Check times are consistent
    for task_id in solution.task_starts:
        if solution.task_ends[task_id] <= solution.task_starts[task_id]:
            raise ValueError(f"Invalid time range for task {task_id}")
    
    return True
```

This comprehensive solution storage system ensures efficient and reliable persistence of OR-Tools solutions!