# Schema Alignment Plan: Frontend ↔ Backend Solver Integration

## Executive Summary

**Current State**: Backend has sophisticated OR-Tools solver with 5-8x performance gains, but frontend schema only supports ~60% of solver capabilities due to missing critical tables and architectural inconsistencies.

**Goal**: Complete frontend schema alignment to unlock full solver potential for enterprise-grade scheduling.

## Critical Missing Tables (Priority 1 - Breaks Core Functionality)

### 1. `optimized_task_modes` - CRITICAL
```typescript
export interface OptimizedTaskModes {
  id: string
  optimized_task_id: string
  machine_id: string
  processing_time: number
  setup_time: number
  cost_per_hour: number
  energy_consumption?: number
  preferred: boolean
  created_at: string
  updated_at: string
}
```
**Impact**: Without this, machine assignment constraints cannot function. Solver cannot select optimal machines per task.

### 2. `solved_schedules` - Solution Storage
```typescript
export interface SolvedSchedules {
  id: string
  pattern_id: string
  solver_version: string
  objective_value: number
  makespan: number
  total_cost: number
  total_lateness: number
  machine_utilization: number
  solve_time_seconds: number
  status: 'optimal' | 'feasible' | 'infeasible' | 'timeout'
  solver_log?: string
  created_at: string
}
```
**Impact**: No way to store or retrieve solver solutions. Performance tracking impossible.

### 3. `scheduled_tasks` - Task Assignments
```typescript
export interface ScheduledTasks {
  id: string
  solved_schedule_id: string
  job_instance_id: string
  optimized_task_id: string
  assigned_machine_id: string
  assigned_operator_id?: string
  start_time: number
  end_time: number
  processing_time: number
  setup_time: number
  actual_cost: number
  sequence_position?: number
  created_at: string
}
```
**Impact**: Individual task assignments cannot be stored or displayed.

### 4. `sequence_reservations` - Resource Management
```typescript
export interface SequenceReservations {
  id: string
  machine_id: string
  start_time: number
  end_time: number
  reserved_by: 'opto' | 'bat' | 'maintenance'
  job_instance_id?: string
  description?: string
  created_at: string
}
```
**Impact**: Opto/BAT exclusive access management broken.

## Architectural Inconsistencies (Priority 2 - Causes Confusion)

### 1. Terminology Standardization
- **Current**: `template_tasks` in frontend, `optimized_tasks` in solver
- **Solution**: Migrate frontend to use `optimized_tasks` consistently
- **Migration Strategy**: Create compatibility views, update services gradually

### 2. Reference Alignment
- **Current**: Frontend `job_instances.template_id`, Solver expects `pattern_id`
- **Solution**: Update frontend schema to use `pattern_id`
- **Impact**: Breaks existing job instance queries

### 3. Duplicate Setup Tables
- **Current**: Both `template_task_setup_times` AND `optimized_task_setup_times`
- **Solution**: Deprecate template version, use optimized only
- **Cleanup**: Remove duplicate data, update references

## Missing Performance Infrastructure (Priority 3 - Limits Monitoring)

### 1. Template Performance Views
```sql
CREATE VIEW template_performance_metrics AS
SELECT 
  op.id as pattern_id,
  op.name as pattern_name,
  COUNT(DISTINCT ji.id) as total_instances,
  AVG(ss.solve_time_seconds) as avg_solve_time,
  AVG(ss.makespan) as avg_makespan,
  AVG(ss.machine_utilization) as avg_utilization
FROM optimized_patterns op
LEFT JOIN job_instances ji ON ji.pattern_id = op.id
LEFT JOIN solved_schedules ss ON ss.pattern_id = op.id
GROUP BY op.id, op.name;
```

### 2. Solver Benchmarking Tables
```typescript
export interface SolverBenchmarks {
  id: string
  pattern_id: string
  instance_count: number
  legacy_solve_time: number
  optimized_solve_time: number
  performance_ratio: number
  memory_usage_mb: number
  constraint_count: number
  variable_count: number
  created_at: string
}
```

## Implementation Roadmap

### Phase 1: Critical Tables (Week 1-2)
1. **Add missing core tables to `database.types.ts`**
   - optimized_task_modes
   - solved_schedules  
   - scheduled_tasks
   - sequence_reservations

2. **Create corresponding Supabase services**
   - CRUD operations for each table
   - Type-safe queries with proper relations
   - Error handling and validation

3. **Update solver service integration**
   - Solution storage workflows
   - Task assignment retrieval
   - Machine mode selection

### Phase 2: Architectural Cleanup (Week 3-4)
1. **Standardize terminology**
   - Create migration scripts for template → optimized
   - Update all frontend references
   - Maintain compatibility views temporarily

2. **Fix reference mismatches**
   - Update job_instances schema
   - Fix template_id → pattern_id references
   - Update all service queries

3. **Remove duplicates**
   - Consolidate setup time tables
   - Clean up redundant data
   - Update dependent queries

### Phase 3: Performance Infrastructure (Week 5-6)
1. **Add performance tracking**
   - Solver benchmark tables
   - Performance metric views
   - Historical trend analysis

2. **Enhanced monitoring**
   - Real-time solver status
   - Performance comparison dashboards
   - Optimization recommendations

## Migration Scripts Required

### 1. Schema Migration
```sql
-- Add missing tables
-- Update references  
-- Create compatibility views
-- Add indexes for performance
```

### 2. Data Migration
```sql
-- Migrate template_tasks to optimized_tasks
-- Update job_instances references
-- Consolidate setup time data
-- Preserve historical data
```

### 3. Service Updates
```typescript
// Update all frontend services
// Add new CRUD operations
// Fix type definitions
// Update error handling
```

## Testing Strategy

### 1. Schema Validation
- Verify all solver queries work with new schema
- Test constraint generation with missing tables added
- Validate solution storage/retrieval workflows

### 2. Performance Testing  
- Measure query performance with new indexes
- Test solver integration end-to-end
- Validate 5-8x performance gains maintained

### 3. Compatibility Testing
- Ensure existing frontend functionality preserved
- Test migration scripts on sample data
- Validate RLS policies work with new tables

## Success Metrics

### Technical Metrics
- [ ] 100% solver table coverage in frontend schema
- [ ] All constraint generation tests pass
- [ ] Solution storage/retrieval functional
- [ ] Migration scripts execute without data loss
- [ ] Performance benchmarks maintained

### Business Metrics  
- [ ] Full solver capabilities accessible from frontend
- [ ] Machine assignment optimization functional
- [ ] Multi-objective optimization results displayed
- [ ] Historical performance tracking available
- [ ] Enterprise scalability demonstrated

## Risk Mitigation

### 1. Breaking Changes
- **Risk**: Schema changes break existing functionality
- **Mitigation**: Phased rollout with compatibility views
- **Rollback**: Maintain old schema versions during transition

### 2. Data Loss
- **Risk**: Migration scripts lose critical data
- **Mitigation**: Full backups before any changes
- **Testing**: Validate migrations on copies first

### 3. Performance Regression
- **Risk**: New schema impacts query performance
- **Mitigation**: Comprehensive indexing strategy
- **Monitoring**: Performance benchmarks before/after

## Dependencies

### External Dependencies
- Supabase schema migration tools
- OR-Tools solver backend (no changes needed)
- Database backup/restore capabilities

### Internal Dependencies  
- Frontend service layer updates
- Type definition regeneration
- Component updates for new data structures

## Timeline

**Total Duration**: 6 weeks

**Week 1-2**: Critical table implementation
**Week 3-4**: Architectural cleanup and migrations  
**Week 5-6**: Performance infrastructure and testing

**Milestone Reviews**: Weekly progress reviews with solver team
**Go/No-Go Decision**: After Phase 1 completion

## Conclusion

This schema alignment will unlock the full potential of your sophisticated OR-Tools solver, enabling:

1. **Complete Functionality**: All solver capabilities accessible from frontend
2. **Enterprise Scale**: Template-based optimization with proven 5-8x gains
3. **Production Ready**: Comprehensive solution storage and performance tracking
4. **Maintainable**: Clean architecture without legacy/modern confusion

The investment in schema alignment will transform the frontend from supporting ~60% to 100% of the solver's world-class capabilities.
