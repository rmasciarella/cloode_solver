# Transaction Boundaries for OR-Tools + Supabase

## Overview

Defining clear transaction boundaries for OR-Tools solver operations with Supabase, ensuring data consistency and atomicity.

## Transaction Architecture

```
┌─────────────────────────────────────────────┐
│         Transaction Boundaries              │
├──────────┬───────────┬──────────┬──────────┤
│ Problem  │  Solver   │ Solution │  Update  │
│  Load    │ Execution │  Store   │ Status   │
└──────────┴───────────┴──────────┴──────────┘
```

## Core Transaction Patterns

### Pattern 1: Problem Loading Transaction

```python
# src/solver/transactions/problem_loader.py
from contextlib import asynccontextmanager
from typing import Optional, Dict
import asyncio

class ProblemLoadTransaction:
    """Transactional problem loading from Supabase."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.transaction_id = None
        self.rollback_actions = []
    
    @asynccontextmanager
    async def atomic_load(self, problem_id: int):
        """Load problem data atomically."""
        try:
            # Begin transaction
            self.transaction_id = await self._begin_transaction()
            
            # Lock problem record
            await self._lock_problem(problem_id)
            
            # Load all related data
            problem_data = await self._load_problem_data(problem_id)
            
            # Validate consistency
            if not await self._validate_consistency(problem_data):
                raise InconsistentDataError("Problem data is inconsistent")
            
            # Mark as being processed
            await self._mark_processing(problem_id)
            
            yield problem_data
            
            # Commit on success
            await self._commit_transaction()
            
        except Exception as e:
            # Rollback on failure
            await self._rollback_transaction()
            raise TransactionError(f"Problem load failed: {e}") from e
        finally:
            # Release locks
            await self._release_locks()
    
    async def _lock_problem(self, problem_id: int) -> None:
        """Acquire advisory lock on problem."""
        # PostgreSQL advisory lock
        await self.client.rpc(
            'pg_advisory_xact_lock',
            {'key': f'problem_{problem_id}'}
        ).execute()
        
        self.rollback_actions.append(
            lambda: self._unlock_problem(problem_id)
        )
    
    async def _load_problem_data(self, problem_id: int) -> Dict:
        """Load all problem data in single transaction."""
        # Use single RPC call for consistency
        result = await self.client.rpc(
            'load_complete_problem',
            {'p_problem_id': problem_id}
        ).execute()
        
        return result.data
```

### Pattern 2: Solution Storage Transaction

```python
class SolutionStoreTransaction:
    """Transactional solution storage."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.stored_entities = []
    
    async def store_solution_atomic(
        self,
        solution: Solution,
        problem_id: int
    ) -> str:
        """Store solution atomically with all components."""
        transaction_started = False
        
        try:
            # Start database transaction
            await self.client.rpc('begin_transaction').execute()
            transaction_started = True
            
            # Phase 1: Create solution record
            solution_id = await self._create_solution_record(
                solution, problem_id
            )
            self.stored_entities.append(('solutions', solution_id))
            
            # Phase 2: Store assignments in batches
            await self._store_assignments_transactional(
                solution_id, solution
            )
            
            # Phase 3: Update problem status
            await self._update_problem_status(
                problem_id, solution_id
            )
            
            # Phase 4: Store metrics
            await self._store_solution_metrics(
                solution_id, solution
            )
            
            # Validate before commit
            if not await self._validate_solution_integrity(solution_id):
                raise IntegrityError("Solution validation failed")
            
            # Commit transaction
            await self.client.rpc('commit_transaction').execute()
            
            return solution_id
            
        except Exception as e:
            # Rollback on any error
            if transaction_started:
                await self.client.rpc('rollback_transaction').execute()
            
            # Clean up any partial data
            await self._cleanup_partial_data()
            
            raise TransactionError(f"Solution storage failed: {e}") from e
    
    async def _store_assignments_transactional(
        self,
        solution_id: str,
        solution: Solution
    ) -> None:
        """Store assignments with chunking for large solutions."""
        assignments = self._prepare_assignments(solution_id, solution)
        
        # Process in chunks to avoid timeout
        chunk_size = 1000
        for i in range(0, len(assignments), chunk_size):
            chunk = assignments[i:i + chunk_size]
            
            result = await self.client.table('task_assignments')\
                .insert(chunk)\
                .execute()
            
            # Track for potential rollback
            self.stored_entities.extend([
                ('task_assignments', r['id']) for r in result.data
            ])
            
            # Check transaction is still valid
            if not await self._is_transaction_valid():
                raise TransactionError("Transaction expired during storage")
```

### Pattern 3: Solver Execution Boundary

```python
class SolverExecutionBoundary:
    """Define transaction boundary for solver execution."""
    
    def __init__(self, solver: FreshSolver, db_client):
        self.solver = solver
        self.db_client = db_client
        self.checkpoints = []
    
    async def execute_with_checkpoints(
        self,
        problem: SchedulingProblem,
        problem_id: int
    ) -> Solution:
        """Execute solver with periodic checkpoints."""
        # Set up checkpoint callback
        checkpoint_interval = 60  # seconds
        last_checkpoint = time.time()
        
        def solution_callback(solver_instance):
            nonlocal last_checkpoint
            
            if time.time() - last_checkpoint > checkpoint_interval:
                # Save intermediate solution
                asyncio.create_task(
                    self._save_checkpoint(
                        solver_instance,
                        problem_id
                    )
                )
                last_checkpoint = time.time()
        
        try:
            # Mark problem as being solved
            await self._update_status(problem_id, 'SOLVING')
            
            # Execute solver
            solution = await self._run_solver_async(
                problem,
                callback=solution_callback
            )
            
            # Store final solution transactionally
            async with SolutionStoreTransaction(self.db_client) as trans:
                solution_id = await trans.store_solution_atomic(
                    solution, problem_id
                )
            
            # Update status to complete
            await self._update_status(problem_id, 'SOLVED', solution_id)
            
            return solution
            
        except Exception as e:
            # Update status to failed
            await self._update_status(
                problem_id, 
                'FAILED',
                error=str(e)
            )
            raise
        finally:
            # Clean up checkpoints
            await self._cleanup_checkpoints(problem_id)
    
    async def _save_checkpoint(
        self,
        solver_instance,
        problem_id: int
    ) -> None:
        """Save solver checkpoint for recovery."""
        checkpoint_data = {
            'problem_id': problem_id,
            'timestamp': datetime.now(),
            'best_objective': solver_instance.ObjectiveValue(),
            'solver_state': self._serialize_solver_state(solver_instance),
            'is_intermediate': True
        }
        
        # Save without blocking solver
        await self.db_client.table('solver_checkpoints')\
            .insert(checkpoint_data)\
            .execute()
```

## Advanced Transaction Patterns

### Pattern 4: Distributed Transaction Coordination

```python
class DistributedTransactionCoordinator:
    """Coordinate transactions across multiple services."""
    
    def __init__(self, db_client, cache_client, queue_client):
        self.db = db_client
        self.cache = cache_client
        self.queue = queue_client
        self.transaction_log = []
    
    async def execute_distributed_operation(
        self,
        operation: str,
        data: Dict
    ) -> Dict:
        """Execute operation across multiple systems."""
        transaction_id = str(uuid.uuid4())
        
        try:
            # Phase 1: Prepare
            prepare_results = await self._prepare_phase(
                transaction_id, operation, data
            )
            
            if not all(r['prepared'] for r in prepare_results):
                raise TransactionError("Prepare phase failed")
            
            # Phase 2: Commit
            commit_results = await self._commit_phase(
                transaction_id, prepare_results
            )
            
            return {
                'transaction_id': transaction_id,
                'status': 'committed',
                'results': commit_results
            }
            
        except Exception as e:
            # Rollback all participants
            await self._rollback_phase(transaction_id)
            raise
    
    async def _prepare_phase(
        self,
        transaction_id: str,
        operation: str,
        data: Dict
    ) -> List[Dict]:
        """Two-phase commit: prepare phase."""
        participants = []
        
        # Prepare database
        db_prepared = await self._prepare_database(
            transaction_id, operation, data
        )
        participants.append({
            'service': 'database',
            'prepared': db_prepared,
            'rollback': self._rollback_database
        })
        
        # Prepare cache
        cache_prepared = await self._prepare_cache(
            transaction_id, operation, data
        )
        participants.append({
            'service': 'cache',
            'prepared': cache_prepared,
            'rollback': self._rollback_cache
        })
        
        return participants
```

### Pattern 5: Compensating Transactions

```python
class CompensatingTransactionManager:
    """Manage compensating transactions for eventual consistency."""
    
    def __init__(self, db_client):
        self.db = db_client
        self.compensations = []
    
    async def execute_with_compensation(
        self,
        operations: List[Dict]
    ) -> None:
        """Execute operations with compensation tracking."""
        completed = []
        
        try:
            for op in operations:
                # Execute operation
                result = await self._execute_operation(op)
                completed.append(result)
                
                # Register compensation
                compensation = self._create_compensation(op, result)
                self.compensations.append(compensation)
                
        except Exception as e:
            # Execute compensations in reverse order
            await self._run_compensations(completed)
            raise
    
    def _create_compensation(
        self,
        operation: Dict,
        result: Dict
    ) -> Dict:
        """Create compensation for operation."""
        compensations = {
            'INSERT': lambda r: self._delete_compensation(r),
            'UPDATE': lambda r: self._revert_compensation(r),
            'DELETE': lambda r: self._restore_compensation(r)
        }
        
        op_type = operation['type']
        if op_type in compensations:
            return {
                'operation': operation,
                'result': result,
                'compensate': compensations[op_type]
            }
        
        raise ValueError(f"Unknown operation type: {op_type}")
    
    async def _run_compensations(
        self,
        completed_operations: List[Dict]
    ) -> None:
        """Run compensations in reverse order."""
        for comp in reversed(self.compensations):
            try:
                await comp['compensate'](comp['result'])
            except Exception as e:
                logger.error(f"Compensation failed: {e}")
                # Continue with other compensations
```

## Transaction Boundary Guidelines

### 1. Problem Loading Boundaries

```python
# Clear boundary: Load all or nothing
async def load_problem_for_solving(problem_id: int) -> SchedulingProblem:
    async with ProblemLoadTransaction(db) as loader:
        # Everything inside is atomic
        data = await loader.atomic_load(problem_id)
        
        # Validate completeness
        validator = ProblemValidator()
        if not validator.is_complete(data):
            raise IncompleteDataError()
        
        # Convert to domain model
        return SchedulingProblem.from_dict(data)
```

### 2. Solver Execution Boundaries

```python
# Boundary includes status updates
async def solve_with_status_tracking(problem: SchedulingProblem) -> Solution:
    problem_id = problem.id
    
    try:
        # Update status atomically
        await db.table('problems')\
            .update({'status': 'SOLVING', 'started_at': datetime.now()})\
            .eq('id', problem_id)\
            .execute()
        
        # Solve (long-running, outside transaction)
        solution = solver.solve(problem)
        
        # Store solution atomically
        async with SolutionStoreTransaction(db) as store:
            solution_id = await store.store_solution_atomic(
                solution, problem_id
            )
        
        # Final status update
        await db.table('problems')\
            .update({
                'status': 'SOLVED',
                'solution_id': solution_id,
                'completed_at': datetime.now()
            })\
            .eq('id', problem_id)\
            .execute()
            
        return solution
        
    except Exception as e:
        # Ensure status is updated even on failure
        await db.table('problems')\
            .update({
                'status': 'FAILED',
                'error': str(e),
                'failed_at': datetime.now()
            })\
            .eq('id', problem_id)\
            .execute()
        raise
```

### 3. Multi-Step Operation Boundaries

```python
class MultiStepOperationBoundary:
    """Define boundaries for multi-step operations."""
    
    async def process_problem_batch(
        self,
        problem_ids: List[int]
    ) -> Dict:
        """Process multiple problems with clear boundaries."""
        results = {
            'successful': [],
            'failed': [],
            'partial': []
        }
        
        for problem_id in problem_ids:
            try:
                # Each problem is independent transaction
                async with self._problem_boundary(problem_id) as problem:
                    solution = await self._solve_problem(problem)
                    
                    # Store solution in same boundary
                    solution_id = await self._store_solution(
                        solution, problem_id
                    )
                    
                    results['successful'].append({
                        'problem_id': problem_id,
                        'solution_id': solution_id
                    })
                    
            except PartialSuccessError as e:
                # Some parts succeeded
                results['partial'].append({
                    'problem_id': problem_id,
                    'completed': e.completed_steps,
                    'failed_at': e.failed_step
                })
                
            except Exception as e:
                # Complete failure
                results['failed'].append({
                    'problem_id': problem_id,
                    'error': str(e)
                })
                
        return results
```

## Consistency Patterns

### Pattern 1: Read-After-Write Consistency

```python
class ConsistentReader:
    """Ensure read-after-write consistency."""
    
    def __init__(self, db_client, cache_client):
        self.db = db_client
        self.cache = cache_client
        self.write_timestamps = {}
    
    async def write_with_consistency(
        self,
        table: str,
        data: Dict
    ) -> str:
        """Write data with consistency tracking."""
        # Write to database
        result = await self.db.table(table).insert(data).execute()
        record_id = result.data[0]['id']
        
        # Track write time
        self.write_timestamps[record_id] = time.time()
        
        # Invalidate cache
        await self.cache.delete(f"{table}:{record_id}")
        
        return record_id
    
    async def read_consistent(
        self,
        table: str,
        record_id: str
    ) -> Dict:
        """Read with consistency guarantee."""
        # Check if recent write
        write_time = self.write_timestamps.get(record_id, 0)
        if time.time() - write_time < 5:  # Within 5 seconds
            # Force read from primary
            return await self._read_from_primary(table, record_id)
        
        # Try cache first
        cached = await self.cache.get(f"{table}:{record_id}")
        if cached:
            return cached
            
        # Read from database
        data = await self._read_from_primary(table, record_id)
        
        # Update cache
        await self.cache.set(f"{table}:{record_id}", data, ttl=300)
        
        return data
```

### Pattern 2: Eventual Consistency Handling

```python
class EventualConsistencyManager:
    """Handle eventual consistency in distributed system."""
    
    async def write_with_propagation(
        self,
        primary_write: Dict,
        secondary_writes: List[Dict]
    ) -> str:
        """Write to primary and propagate to secondaries."""
        # Write to primary (synchronous)
        primary_id = await self._write_primary(primary_write)
        
        # Queue secondary writes (asynchronous)
        for secondary in secondary_writes:
            await self._queue_secondary_write(
                primary_id,
                secondary
            )
        
        # Return immediately
        return primary_id
    
    async def read_with_consistency_check(
        self,
        record_id: str,
        consistency_level: str = 'eventual'
    ) -> Dict:
        """Read with specified consistency level."""
        if consistency_level == 'strong':
            # Read from primary only
            return await self._read_primary(record_id)
            
        elif consistency_level == 'bounded':
            # Read from replica if fresh enough
            replica_data = await self._read_replica(record_id)
            if self._is_fresh_enough(replica_data, max_age=60):
                return replica_data
            return await self._read_primary(record_id)
            
        else:  # eventual
            # Read from nearest available
            return await self._read_any(record_id)
```

## Best Practices

### 1. Keep Transactions Short

```python
# ❌ Bad: Long transaction
async def bad_pattern():
    async with db.transaction():
        problem = await load_problem()  # Fast
        solution = solver.solve(problem)  # Could take hours!
        await store_solution(solution)  # Fast

# ✅ Good: Short transactions
async def good_pattern():
    # Transaction 1: Load
    async with db.transaction():
        problem = await load_problem()
    
    # No transaction: Solve
    solution = solver.solve(problem)
    
    # Transaction 2: Store
    async with db.transaction():
        await store_solution(solution)
```

### 2. Handle Partial Failures

```python
class PartialFailureHandler:
    """Handle partial failures gracefully."""
    
    async def store_solution_with_recovery(
        self,
        solution: Solution
    ) -> str:
        """Store solution with partial failure handling."""
        stored_parts = {
            'metadata': False,
            'assignments': False,
            'metrics': False
        }
        
        try:
            # Store metadata
            solution_id = await self._store_metadata(solution)
            stored_parts['metadata'] = True
            
            # Store assignments
            await self._store_assignments(solution_id, solution)
            stored_parts['assignments'] = True
            
            # Store metrics
            await self._store_metrics(solution_id, solution)
            stored_parts['metrics'] = True
            
            return solution_id
            
        except Exception as e:
            # Determine what succeeded
            if stored_parts['metadata']:
                # Can recover - mark as partial
                await self._mark_partial_solution(
                    solution_id,
                    stored_parts
                )
                raise PartialSuccessError(
                    f"Partial storage: {stored_parts}",
                    solution_id=solution_id,
                    completed=stored_parts
                )
            else:
                # Complete failure
                raise
```

### 3. Idempotent Operations

```python
def make_idempotent(operation_id: str):
    """Decorator for idempotent operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check if already executed
            existing = await db.table('operations')\
                .select('result')\
                .eq('operation_id', operation_id)\
                .single()\
                .execute()
                
            if existing.data:
                return existing.data['result']
            
            # Execute operation
            result = await func(*args, **kwargs)
            
            # Store result
            await db.table('operations')\
                .insert({
                    'operation_id': operation_id,
                    'result': result,
                    'timestamp': datetime.now()
                })\
                .execute()
                
            return result
        return wrapper
    return decorator

# Usage
@make_idempotent(operation_id='solve_problem_123')
async def solve_problem_once(problem_id: int):
    # This will only execute once
    return await solver.solve(problem_id)
```

### 4. Transaction Monitoring

```python
class TransactionMonitor:
    """Monitor transaction health."""
    
    def __init__(self):
        self.active_transactions = {}
        self.metrics = defaultdict(list)
    
    @contextmanager
    def monitor_transaction(self, name: str):
        """Monitor transaction execution."""
        tx_id = str(uuid.uuid4())
        start_time = time.time()
        
        self.active_transactions[tx_id] = {
            'name': name,
            'start': start_time,
            'status': 'active'
        }
        
        try:
            yield tx_id
            
            # Success
            duration = time.time() - start_time
            self.metrics[name].append({
                'duration': duration,
                'status': 'success'
            })
            
        except Exception as e:
            # Failure
            duration = time.time() - start_time
            self.metrics[name].append({
                'duration': duration,
                'status': 'failed',
                'error': str(e)
            })
            raise
            
        finally:
            del self.active_transactions[tx_id]
    
    def get_transaction_stats(self) -> Dict:
        """Get transaction statistics."""
        stats = {}
        
        for name, metrics in self.metrics.items():
            successful = [m for m in metrics if m['status'] == 'success']
            failed = [m for m in metrics if m['status'] == 'failed']
            
            stats[name] = {
                'total': len(metrics),
                'successful': len(successful),
                'failed': len(failed),
                'avg_duration': sum(m['duration'] for m in successful) / len(successful) if successful else 0,
                'success_rate': len(successful) / len(metrics) if metrics else 0
            }
            
        return stats
```

This comprehensive transaction boundary system ensures data consistency and reliability throughout the OR-Tools solving process!