-- Simplified Template Schema for OR-Tools CP-SAT Solver
-- Focused on core template functionality with minimal complexity

-- =============================================================================
-- 1. CORE TEMPLATE DEFINITIONS (ESSENTIAL)
-- =============================================================================

-- Job Templates (Core template repository)
CREATE TABLE job_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    CONSTRAINT name_not_empty CHECK(LENGTH(name) > 0)
);

-- Template Tasks
CREATE TABLE template_tasks (
    template_task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER NOT NULL, -- For ordering and symmetry breaking
    
    CONSTRAINT position_positive CHECK(position >= 0)
);

CREATE UNIQUE INDEX idx_template_tasks_position_unique 
ON template_tasks(template_id, position);

-- Template Task Modes (Machine-Duration combinations)
CREATE TABLE template_task_modes (
    template_task_mode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    machine_id TEXT NOT NULL,
    duration_quarters INTEGER NOT NULL, -- Duration in 15-minute intervals
    
    CONSTRAINT duration_positive CHECK(duration_quarters > 0)
);

-- Template Precedences
CREATE TABLE template_precedences (
    template_precedence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    predecessor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    successor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    
    CONSTRAINT no_self_precedence CHECK(
        predecessor_template_task_id != successor_template_task_id
    )
);

-- =============================================================================
-- 2. JOB INSTANCES (LIGHTWEIGHT)
-- =============================================================================

-- Job Instances
CREATE TABLE job_instances (
    instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    instance_name TEXT NOT NULL,
    due_date TIMESTAMPTZ NOT NULL, -- Essential for minimize lateness objective
    
    CONSTRAINT instance_name_not_empty CHECK(LENGTH(instance_name) > 0)
);

-- Instance Task Assignments (Solved schedules)
CREATE TABLE instance_task_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id) ON DELETE CASCADE,
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    selected_mode_id UUID NOT NULL REFERENCES template_task_modes(template_task_mode_id),
    
    -- Solved schedule data
    start_time_quarters INTEGER,
    end_time_quarters INTEGER,
    assigned_machine_id TEXT,
    
    CONSTRAINT times_valid CHECK(
        (start_time_quarters IS NULL AND end_time_quarters IS NULL) OR
        (start_time_quarters IS NOT NULL AND end_time_quarters IS NOT NULL AND 
         start_time_quarters >= 0 AND end_time_quarters > start_time_quarters)
    ),
    
    UNIQUE(instance_id, template_task_id)
);

-- =============================================================================
-- 3. BASIC PERFORMANCE TRACKING (OPTIONAL)
-- =============================================================================

-- Simple solver performance log
CREATE TABLE solve_performance_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    instance_count INTEGER NOT NULL,
    solve_time_ms INTEGER NOT NULL,
    solver_status TEXT NOT NULL,
    
    solved_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT instance_count_positive CHECK(instance_count > 0),
    CONSTRAINT solve_time_positive CHECK(solve_time_ms >= 0)
);

-- =============================================================================
-- 4. ESSENTIAL INDEXES
-- =============================================================================

-- Template loading optimization
CREATE INDEX idx_template_tasks_loading 
ON template_tasks(template_id, position);

CREATE INDEX idx_template_modes_loading 
ON template_task_modes(template_task_id);

CREATE INDEX idx_template_precedences_loading 
ON template_precedences(template_id);

-- Instance queries
CREATE INDEX idx_job_instances_template_status 
ON job_instances(template_id, status);

-- =============================================================================
-- 5. SIMPLE TEMPLATE LOADING FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION load_template_data(p_template_id UUID)
RETURNS TABLE (
    -- Template info
    template_name TEXT,
    task_count INTEGER,
    
    -- Tasks
    task_id UUID,
    task_name TEXT,
    task_position INTEGER,
    
    -- Modes
    mode_id UUID,
    machine_id TEXT,
    duration_quarters INTEGER,
    
    -- Precedences
    predecessor_id UUID,
    successor_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jt.name,
        jt.task_count,
        
        tt.template_task_id,
        tt.name,
        tt.position,
        
        ttm.template_task_mode_id,
        ttm.machine_id,
        ttm.duration_quarters,
        
        tp.predecessor_template_task_id,
        tp.successor_template_task_id
        
    FROM job_templates jt
    JOIN template_tasks tt ON jt.template_id = tt.template_id
    LEFT JOIN template_task_modes ttm ON tt.template_task_id = ttm.template_task_id
    LEFT JOIN template_precedences tp ON jt.template_id = tp.template_id
    WHERE jt.template_id = p_template_id
    ORDER BY tt.position, ttm.machine_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE job_templates IS 'Core template definitions for template-based solver';
COMMENT ON TABLE template_tasks IS 'Template task structure enabling constraint reuse';
COMMENT ON TABLE template_task_modes IS 'Machine-duration combinations for each template task';
COMMENT ON TABLE template_precedences IS 'Template precedence relationships';
COMMENT ON TABLE job_instances IS 'Job instances referencing templates';
COMMENT ON TABLE instance_task_assignments IS 'Solved schedules for job instances';
COMMENT ON TABLE solve_performance_log IS 'Simple performance tracking';