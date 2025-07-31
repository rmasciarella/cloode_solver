-- Optimal Database Schema for Template-Based OR-Tools CP-SAT Solver
-- Designed specifically for the current optimized solver delivering 5-8x performance improvements

-- =============================================================================
-- 1. CORE TEMPLATE STRUCTURE (HOT PATH OPTIMIZATION)
-- =============================================================================

-- Job templates define reusable task patterns for 5-8x performance gains
CREATE TABLE job_templates (
    template_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Performance-critical: blessed parameters for CP-SAT solver
    solver_parameters JSONB, -- Blessed parameters for production use
    
    -- Template metrics for performance tracking
    baseline_performance_seconds DECIMAL(10,3),
    optimized_performance_seconds DECIMAL(10,3),
    speedup_factor DECIMAL(5,2),
    validation_date TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Template tasks - the core reusable structure
CREATE TABLE template_tasks (
    template_task_id UUID PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    name VARCHAR(255) NOT NULL,
    
    -- Solver-specific attributes
    is_unattended BOOLEAN DEFAULT FALSE,
    is_setup BOOLEAN DEFAULT FALSE,
    sequence_id VARCHAR(100), -- For sequence resource reservations (Opto, BAT)
    
    -- Multi-operator support (Phase 2)
    min_operators INTEGER DEFAULT 1,
    max_operators INTEGER DEFAULT 1,
    operator_efficiency_curve VARCHAR(20) DEFAULT 'linear',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 2. MACHINE RESOURCES (MUST BE BEFORE TEMPLATE MODES)
-- =============================================================================

-- Work cells for capacity constraints
CREATE TABLE work_cells (
    cell_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INTEGER DEFAULT 1 CHECK (capacity > 0),
    
    -- WIP limit configuration for Phase 1
    wip_limit INTEGER,
    target_utilization DECIMAL(3,2) DEFAULT 0.85 CHECK (target_utilization BETWEEN 0 AND 1),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Machine resources for constraint generation
CREATE TABLE machines (
    machine_resource_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INTEGER DEFAULT 1 CHECK (capacity > 0),
    cost_per_hour DECIMAL(10,2) DEFAULT 0.00,
    
    -- Work cell organization
    cell_id UUID REFERENCES work_cells(cell_id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Template task modes - machine + duration combinations (NOW AFTER MACHINES)
CREATE TABLE template_task_modes (
    template_task_mode_id UUID PRIMARY KEY,
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    machine_resource_id UUID NOT NULL REFERENCES machines(machine_resource_id),
    
    -- Duration in minutes (converted to 15-minute quarters by solver)
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Template precedences - constraint relationships
CREATE TABLE template_precedences (
    template_precedence_id UUID PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    predecessor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    successor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent self-precedence
    CHECK (predecessor_template_task_id != successor_template_task_id)
);

-- =============================================================================
-- 3. JOB INSTANCES (MINIMIZE LATENESS OBJECTIVE)
-- =============================================================================

-- Lightweight job instances referencing templates
CREATE TABLE job_instances (
    instance_id UUID PRIMARY KEY,
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    description VARCHAR(255) NOT NULL,
    
    -- CRITICAL: Due date for minimize lateness objective function
    due_date TIMESTAMPTZ NOT NULL,
    
    -- Instance status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 4. SOLVED SCHEDULES (SOLUTION STORAGE)
-- =============================================================================

-- Solved schedules storing actual assignments
CREATE TABLE solved_schedules (
    schedule_id UUID PRIMARY KEY,
    
    -- Template context
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    solution_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Solver performance metrics
    solve_time_seconds DECIMAL(10,3) NOT NULL,
    solver_status VARCHAR(50) NOT NULL,
    
    -- Objective values (minimize lateness focus)
    makespan_time_units INTEGER,
    total_lateness_minutes DECIMAL(10,2),
    maximum_lateness_minutes DECIMAL(10,2),
    
    -- Template performance tracking
    instance_count INTEGER NOT NULL,
    speedup_vs_legacy DECIMAL(5,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual task assignments in solved schedule
CREATE TABLE scheduled_tasks (
    scheduled_task_id UUID PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES solved_schedules(schedule_id),
    
    -- Task identification
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id),
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    
    -- Solution values (in 15-minute time units)
    start_time_units INTEGER NOT NULL CHECK (start_time_units >= 0),
    end_time_units INTEGER NOT NULL CHECK (end_time_units > start_time_units),
    
    -- Machine assignment
    assigned_machine_id UUID NOT NULL REFERENCES machines(machine_resource_id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 5. SEQUENCE RESOURCE RESERVATIONS (OPTO, BAT SEQUENCES)
-- =============================================================================

-- Sequence resource reservations (Opto, BAT sequences)
CREATE TABLE sequence_reservations (
    reservation_id UUID PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES solved_schedules(schedule_id),
    
    sequence_id VARCHAR(100) NOT NULL, -- "Opto", "BAT", etc.
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id),
    
    -- Reservation time span (exclusive access)
    reservation_start_time_units INTEGER NOT NULL,
    reservation_end_time_units INTEGER NOT NULL CHECK (reservation_end_time_units > reservation_start_time_units),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- 6. PERFORMANCE-CRITICAL INDEXES
-- =============================================================================

-- Hot path queries for solver performance
CREATE INDEX idx_template_tasks_template_id ON template_tasks(template_id);
CREATE INDEX idx_template_task_modes_template_task_id ON template_task_modes(template_task_id);
CREATE INDEX idx_template_precedences_template_id ON template_precedences(template_id);

-- Job instance queries for constraint generation
CREATE INDEX idx_job_instances_template_id ON job_instances(template_id);
CREATE INDEX idx_job_instances_due_date ON job_instances(due_date);
CREATE INDEX idx_job_instances_status ON job_instances(status);

-- Machine assignment queries
CREATE INDEX idx_template_task_modes_machine_id ON template_task_modes(machine_resource_id);
CREATE INDEX idx_scheduled_tasks_machine_id ON scheduled_tasks(assigned_machine_id);

-- Schedule retrieval optimization
CREATE INDEX idx_solved_schedules_template_id ON solved_schedules(template_id);
CREATE INDEX idx_scheduled_tasks_schedule_id ON scheduled_tasks(schedule_id);
CREATE INDEX idx_scheduled_tasks_instance_task ON scheduled_tasks(instance_id, template_task_id);

-- Sequence resource queries
CREATE INDEX idx_sequence_reservations_sequence_id ON sequence_reservations(sequence_id);
CREATE INDEX idx_sequence_reservations_schedule_id ON sequence_reservations(schedule_id);

-- =============================================================================
-- 7. TEMPLATE PERFORMANCE TRACKING VIEWS
-- =============================================================================

-- Template performance summary for optimization tracking
CREATE VIEW template_performance_summary AS
SELECT 
    jt.template_id,
    jt.name as template_name,
    COUNT(ss.schedule_id) as solve_count,
    AVG(ss.solve_time_seconds) as avg_solve_time,
    AVG(ss.speedup_vs_legacy) as avg_speedup_factor,
    MAX(ss.instance_count) as max_instances_solved,
    AVG(ss.total_lateness_minutes) as avg_total_lateness
FROM job_templates jt
LEFT JOIN solved_schedules ss ON jt.template_id = ss.template_id
GROUP BY jt.template_id, jt.name;

-- Constraint generation optimization view
CREATE VIEW constraint_generation_stats AS
SELECT 
    jt.template_id,
    jt.name,
    COUNT(tt.template_task_id) as task_count,
    COUNT(tm.template_task_mode_id) as mode_count,
    COUNT(tp.template_precedence_id) as precedence_count,
    -- Complexity estimate: O(template_tasks × instances)
    COUNT(tt.template_task_id) * COALESCE(MAX(instance_counts.count), 0) as constraint_complexity
FROM job_templates jt
LEFT JOIN template_tasks tt ON jt.template_id = tt.template_id
LEFT JOIN template_task_modes tm ON tt.template_task_id = tm.template_task_id
LEFT JOIN template_precedences tp ON jt.template_id = tp.template_id
LEFT JOIN (
    SELECT template_id, COUNT(*) as count 
    FROM job_instances 
    GROUP BY template_id
) instance_counts ON jt.template_id = instance_counts.template_id
GROUP BY jt.template_id, jt.name;

-- =============================================================================
-- 8. STORED PROCEDURES FOR SOLVER INTEGRATION
-- =============================================================================

-- Hot path: Load complete template structure for solver
CREATE OR REPLACE FUNCTION load_template_for_solver(p_template_id UUID)
RETURNS TABLE (
    -- Template metadata
    template_name VARCHAR(255),
    solver_parameters JSONB,
    
    -- Template tasks
    task_id UUID,
    task_name VARCHAR(255),
    is_unattended BOOLEAN,
    sequence_id VARCHAR(100),
    
    -- Task modes (machine + duration combinations)
    mode_id UUID,
    machine_id UUID,
    duration_minutes INTEGER,
    
    -- Precedences
    predecessor_task_id UUID,
    successor_task_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jt.name,
        jt.solver_parameters,
        
        tt.template_task_id,
        tt.name,
        tt.is_unattended,
        tt.sequence_id,
        
        tm.template_task_mode_id,
        tm.machine_resource_id,
        tm.duration_minutes,
        
        tp.predecessor_template_task_id,
        tp.successor_template_task_id
        
    FROM job_templates jt
    LEFT JOIN template_tasks tt ON jt.template_id = tt.template_id
    LEFT JOIN template_task_modes tm ON tt.template_task_id = tm.template_task_id
    LEFT JOIN template_precedences tp ON jt.template_id = tp.template_id
    WHERE jt.template_id = p_template_id
    ORDER BY tt.template_task_id, tm.template_task_mode_id;
END;
$$ LANGUAGE plpgsql;

-- Load job instances for template-based solving
CREATE OR REPLACE FUNCTION load_job_instances_for_template(
    p_template_id UUID,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    instance_id UUID,
    description VARCHAR(255),
    due_date TIMESTAMPTZ,
    status VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ji.instance_id,
        ji.description,
        ji.due_date,
        ji.status
    FROM job_instances ji
    WHERE ji.template_id = p_template_id
      AND ji.status IN ('pending', 'scheduled')
    ORDER BY ji.due_date ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Store solved schedule with performance metrics
CREATE OR REPLACE FUNCTION store_solved_schedule(
    p_template_id UUID,
    p_solve_time_seconds DECIMAL(10,3),
    p_solver_status VARCHAR(50),
    p_makespan_time_units INTEGER,
    p_total_lateness_minutes DECIMAL(10,2),
    p_instance_count INTEGER,
    p_speedup_vs_legacy DECIMAL(5,2)
) RETURNS UUID AS $$
DECLARE
    schedule_id UUID;
BEGIN
    INSERT INTO solved_schedules (
        template_id,
        solve_time_seconds,
        solver_status,
        makespan_time_units,
        total_lateness_minutes,
        instance_count,
        speedup_vs_legacy
    ) VALUES (
        p_template_id,
        p_solve_time_seconds,
        p_solver_status,
        p_makespan_time_units,
        p_total_lateness_minutes,
        p_instance_count,
        p_speedup_vs_legacy
    ) RETURNING solved_schedules.schedule_id INTO schedule_id;
    
    RETURN schedule_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE job_templates IS 'Template definitions for 5-8x performance optimization through constraint reuse';
COMMENT ON TABLE template_tasks IS 'Reusable task structure enabling O(template × instances) complexity';
COMMENT ON TABLE template_task_modes IS 'Machine-duration combinations for constraint generation';
COMMENT ON TABLE template_precedences IS 'Template precedence relationships for constraint reuse';
COMMENT ON TABLE job_instances IS 'Lightweight job instances with due dates for minimize lateness objective';
COMMENT ON TABLE solved_schedules IS 'Performance tracking and solution storage for template-based schedules';
COMMENT ON TABLE scheduled_tasks IS 'Individual task assignments in solved schedules';
COMMENT ON TABLE sequence_reservations IS 'Sequence resource reservations (Opto, BAT) for exclusive access constraints';

COMMENT ON COLUMN job_templates.solver_parameters IS 'Blessed CP-SAT parameters for production solving';
COMMENT ON COLUMN job_instances.due_date IS 'Critical for minimize lateness objective function';
COMMENT ON COLUMN template_tasks.sequence_id IS 'Opto/BAT sequence resource identifier for reservations';
COMMENT ON COLUMN template_tasks.is_unattended IS 'Unattended task scheduling capability';
COMMENT ON COLUMN solved_schedules.speedup_vs_legacy IS 'Template performance vs legacy job-shop scheduling';

COMMENT ON FUNCTION load_template_for_solver IS 'Hot path: Single query loads complete template structure for solver';
COMMENT ON FUNCTION store_solved_schedule IS 'Store solution with performance metrics and speedup tracking';