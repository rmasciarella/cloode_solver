-- Template-based database schema for Fresh OR-Tools Solver
-- Week 3 Implementation: Optimized for template-based scheduling
-- 
-- This schema separates job templates from job instances to achieve
-- O(template_size × instances) performance instead of O(n³)

-- ============================================================================
-- TEMPLATE DEFINITION TABLES
-- ============================================================================

-- Job Templates: Define reusable job structures
CREATE TABLE job_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Template metadata for optimization
    task_count INTEGER NOT NULL DEFAULT 0,
    total_min_duration_minutes INTEGER NOT NULL DEFAULT 0,
    critical_path_length_minutes INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    
    CONSTRAINT job_templates_name_unique UNIQUE(name),
    CONSTRAINT job_templates_task_count_positive CHECK(task_count >= 0),
    CONSTRAINT job_templates_durations_positive CHECK(
        total_min_duration_minutes >= 0 AND 
        critical_path_length_minutes >= 0
    )
);

-- Template Tasks: Tasks within a template (reusable across instances)
CREATE TABLE template_tasks (
    template_task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    department_id TEXT,
    is_unattended BOOLEAN DEFAULT FALSE,
    is_setup BOOLEAN DEFAULT FALSE,
    
    -- Position for ordering (helps with precedence generation)
    position INTEGER NOT NULL,
    
    -- Cached durations for performance
    min_duration_minutes INTEGER,
    max_duration_minutes INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT template_tasks_position_positive CHECK(position >= 0),
    CONSTRAINT template_tasks_durations_valid CHECK(
        min_duration_minutes IS NULL OR min_duration_minutes > 0
    ),
    CONSTRAINT template_tasks_min_max_duration CHECK(
        min_duration_minutes IS NULL OR 
        max_duration_minutes IS NULL OR 
        min_duration_minutes <= max_duration_minutes
    )
);

-- Template Task Modes: Execution modes for template tasks
CREATE TABLE template_task_modes (
    template_task_mode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    machine_resource_id UUID NOT NULL REFERENCES test_resources(resource_id),
    duration_minutes INTEGER NOT NULL,
    
    -- Mode identifier for consistent mode selection across instances
    mode_name TEXT NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT template_task_modes_duration_positive CHECK(duration_minutes > 0),
    CONSTRAINT template_task_modes_unique UNIQUE(template_task_id, mode_name)
);

-- Template Precedences: Precedence relationships within templates
CREATE TABLE template_precedences (
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    predecessor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    successor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    
    -- Optional lag time between predecessor and successor
    lag_minutes INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (predecessor_template_task_id, successor_template_task_id),
    
    CONSTRAINT template_precedences_no_self_loop CHECK(
        predecessor_template_task_id != successor_template_task_id
    ),
    CONSTRAINT template_precedences_lag_non_negative CHECK(lag_minutes >= 0)
);

-- ============================================================================
-- JOB INSTANCE TABLES
-- ============================================================================

-- Job Instances: Lightweight references to templates
CREATE TABLE job_instances (
    instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    
    -- Scheduling metadata
    priority INTEGER DEFAULT 100,
    customer_id TEXT,
    order_number TEXT,
    
    -- Status tracking
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT job_instances_priority_positive CHECK(priority > 0)
);

-- Instance Task Assignments: Links instances to specific task modes
-- This table is populated during solving to record mode selections
CREATE TABLE instance_task_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id) ON DELETE CASCADE,
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    selected_mode_id UUID NOT NULL REFERENCES template_task_modes(template_task_mode_id),
    
    -- Solved schedule information
    start_time_minutes INTEGER,
    end_time_minutes INTEGER,
    assigned_machine_id UUID REFERENCES test_resources(resource_id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT instance_assignments_times_valid CHECK(
        (start_time_minutes IS NULL AND end_time_minutes IS NULL) OR
        (start_time_minutes IS NOT NULL AND end_time_minutes IS NOT NULL AND 
         start_time_minutes >= 0 AND end_time_minutes > start_time_minutes)
    ),
    
    UNIQUE(instance_id, template_task_id)
);

-- ============================================================================
-- PERFORMANCE OPTIMIZATION TABLES
-- ============================================================================

-- Template Statistics: Cached metrics for solver optimization
CREATE TABLE template_statistics (
    template_id UUID PRIMARY KEY REFERENCES job_templates(template_id) ON DELETE CASCADE,
    
    -- Cached solver metrics
    variable_density NUMERIC,  -- Variables per constraint ratio
    constraint_complexity NUMERIC,  -- Average constraint complexity
    parallelism_factor NUMERIC,  -- Potential for parallel execution
    
    -- Critical path analysis
    longest_chain_length INTEGER,
    bottleneck_machine_count INTEGER,
    
    -- Performance benchmarks
    last_solve_time_ms INTEGER,
    typical_instances_solved INTEGER,
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT template_stats_positive_metrics CHECK(
        longest_chain_length >= 0 AND 
        bottleneck_machine_count >= 0 AND
        typical_instances_solved >= 0
    )
);

-- Template Dependencies: Machine and resource requirements
CREATE TABLE template_machine_requirements (
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    machine_resource_id UUID NOT NULL REFERENCES test_resources(resource_id),
    
    -- Requirements analysis
    required_capacity INTEGER NOT NULL DEFAULT 1,
    estimated_utilization_pct NUMERIC DEFAULT 0.0,
    is_bottleneck BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (template_id, machine_resource_id),
    
    CONSTRAINT template_machine_req_capacity_positive CHECK(required_capacity > 0),
    CONSTRAINT template_machine_req_utilization_valid CHECK(
        estimated_utilization_pct >= 0.0 AND estimated_utilization_pct <= 100.0
    )
);

-- ============================================================================
-- INDEXES FOR QUERY PERFORMANCE
-- ============================================================================

-- Template querying
CREATE INDEX idx_job_templates_name ON job_templates(name);
CREATE INDEX idx_job_templates_task_count ON job_templates(task_count);
CREATE INDEX idx_job_templates_created_at ON job_templates(created_at);

-- Template task querying
CREATE INDEX idx_template_tasks_template_id ON template_tasks(template_id);
CREATE INDEX idx_template_tasks_position ON template_tasks(template_id, position);
CREATE INDEX idx_template_tasks_department ON template_tasks(department_id);

-- Template task modes querying  
CREATE INDEX idx_template_task_modes_template_task ON template_task_modes(template_task_id);
CREATE INDEX idx_template_task_modes_machine ON template_task_modes(machine_resource_id);
CREATE INDEX idx_template_task_modes_duration ON template_task_modes(duration_minutes);

-- Template precedences querying
CREATE INDEX idx_template_precedences_template ON template_precedences(template_id);
CREATE INDEX idx_template_precedences_predecessor ON template_precedences(predecessor_template_task_id);
CREATE INDEX idx_template_precedences_successor ON template_precedences(successor_template_task_id);

-- Job instance querying
CREATE INDEX idx_job_instances_template_id ON job_instances(template_id);
CREATE INDEX idx_job_instances_due_date ON job_instances(due_date);
CREATE INDEX idx_job_instances_status ON job_instances(status);
CREATE INDEX idx_job_instances_priority ON job_instances(priority DESC);
CREATE INDEX idx_job_instances_customer ON job_instances(customer_id);

-- Instance assignments querying
CREATE INDEX idx_instance_assignments_instance ON instance_task_assignments(instance_id);
CREATE INDEX idx_instance_assignments_template_task ON instance_task_assignments(template_task_id);
CREATE INDEX idx_instance_assignments_machine ON instance_task_assignments(assigned_machine_id);
CREATE INDEX idx_instance_assignments_start_time ON instance_task_assignments(start_time_minutes);

-- Template performance querying
CREATE INDEX idx_template_machine_req_template ON template_machine_requirements(template_id);
CREATE INDEX idx_template_machine_req_machine ON template_machine_requirements(machine_resource_id);
CREATE INDEX idx_template_machine_req_bottleneck ON template_machine_requirements(is_bottleneck) WHERE is_bottleneck = true;

-- ============================================================================
-- HELPER FUNCTIONS FOR TEMPLATE OPERATIONS
-- ============================================================================

-- Function to update template statistics
CREATE OR REPLACE FUNCTION update_template_statistics(p_template_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Update cached task count and durations
    UPDATE job_templates SET
        task_count = (
            SELECT COUNT(*) 
            FROM template_tasks 
            WHERE template_id = p_template_id
        ),
        total_min_duration_minutes = (
            SELECT COALESCE(SUM(min_duration_minutes), 0)
            FROM template_tasks 
            WHERE template_id = p_template_id
        ),
        updated_at = NOW()
    WHERE template_id = p_template_id;
    
    -- Update template task min/max durations
    UPDATE template_tasks SET
        min_duration_minutes = (
            SELECT MIN(duration_minutes)
            FROM template_task_modes
            WHERE template_task_id = template_tasks.template_task_id
        ),
        max_duration_minutes = (
            SELECT MAX(duration_minutes)
            FROM template_task_modes
            WHERE template_task_id = template_tasks.template_task_id
        )
    WHERE template_id = p_template_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get template loading query for OR-Tools
CREATE OR REPLACE FUNCTION get_template_load_data(p_template_id UUID)
RETURNS TABLE (
    template_name TEXT,
    task_id UUID,
    task_name TEXT,
    task_position INTEGER,
    mode_id UUID,
    mode_name TEXT,
    machine_id UUID,
    duration_minutes INTEGER,
    predecessor_id UUID,
    successor_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jt.name as template_name,
        tt.template_task_id as task_id,
        tt.name as task_name,
        tt.position as task_position,
        ttm.template_task_mode_id as mode_id,
        ttm.mode_name,
        ttm.machine_resource_id as machine_id,
        ttm.duration_minutes,
        tp.predecessor_template_task_id as predecessor_id,
        tp.successor_template_task_id as successor_id
    FROM job_templates jt
    JOIN template_tasks tt ON jt.template_id = tt.template_id
    LEFT JOIN template_task_modes ttm ON tt.template_task_id = ttm.template_task_id
    LEFT JOIN template_precedences tp ON jt.template_id = tp.template_id
        AND (tt.template_task_id = tp.predecessor_template_task_id 
             OR tt.template_task_id = tp.successor_template_task_id)
    WHERE jt.template_id = p_template_id
    ORDER BY tt.position, ttm.mode_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC STATISTICS UPDATES
-- ============================================================================

-- Trigger to update template statistics when template tasks change
CREATE OR REPLACE FUNCTION trigger_update_template_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM update_template_statistics(OLD.template_id);
        RETURN OLD;
    ELSE
        PERFORM update_template_statistics(NEW.template_id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER template_tasks_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON template_tasks
    FOR EACH ROW EXECUTE FUNCTION trigger_update_template_stats();

CREATE TRIGGER template_task_modes_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON template_task_modes
    FOR EACH ROW EXECUTE FUNCTION trigger_update_template_stats();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE job_templates IS 'Reusable job templates that define the structure of identical jobs';
COMMENT ON TABLE template_tasks IS 'Tasks within a job template, reused across all instances';
COMMENT ON TABLE template_task_modes IS 'Execution modes for template tasks (machine + duration combinations)';
COMMENT ON TABLE template_precedences IS 'Precedence constraints within job templates';
COMMENT ON TABLE job_instances IS 'Lightweight job instances that reference templates';
COMMENT ON TABLE instance_task_assignments IS 'Solved task assignments linking instances to specific modes';
COMMENT ON TABLE template_statistics IS 'Cached performance metrics for solver optimization';
COMMENT ON TABLE template_machine_requirements IS 'Machine requirements analysis for templates';

COMMENT ON FUNCTION update_template_statistics(UUID) IS 'Recalculates and caches template statistics for performance';
COMMENT ON FUNCTION get_template_load_data(UUID) IS 'Optimized query for loading template data into OR-Tools solver';