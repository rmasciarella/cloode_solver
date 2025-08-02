-- =====================================================================================
-- ORDERED BASE SCHEMA FOR OPTIMIZED SOLVER
-- This adjusted schema ensures tables are created in correct dependency order
-- =====================================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================================================
-- CORE TEMPLATE STRUCTURE (HOT PATH OPTIMIZATION)
-- =====================================================================================

-- 1. DEPARTMENTS AND ORGANIZATIONAL STRUCTURE
CREATE TABLE IF NOT EXISTS departments (
    department_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    parent_department_id UUID REFERENCES departments(department_id),
    cost_center TEXT,
    default_shift_start INTEGER DEFAULT 32, -- 8 AM in 15-minute units
    default_shift_end INTEGER DEFAULT 64,   -- 4 PM in 15-minute units
    overtime_allowed BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. BUSINESS CALENDARS
CREATE TABLE IF NOT EXISTS business_calendars (
    calendar_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    timezone TEXT DEFAULT 'UTC',
    default_start_time INTEGER DEFAULT 32, -- 8 AM in 15-minute units
    default_end_time INTEGER DEFAULT 64,   -- 4 PM in 15-minute units
    working_days_mask INTEGER DEFAULT 31,  -- Monday-Friday (bits 0-4)
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. SEQUENCE RESOURCES
CREATE TABLE IF NOT EXISTS sequence_resources (
    sequence_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    department_id UUID REFERENCES departments(department_id),
    setup_time_minutes INTEGER DEFAULT 0,
    teardown_time_minutes INTEGER DEFAULT 0,
    max_concurrent_jobs INTEGER DEFAULT 1,
    resource_type TEXT DEFAULT 'exclusive',
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SKILLS
CREATE TABLE IF NOT EXISTS skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    department_id UUID REFERENCES departments(department_id),
    complexity_level TEXT DEFAULT 'basic',
    training_hours_required INTEGER DEFAULT 0,
    certification_required BOOLEAN DEFAULT false,
    certification_expires_after_months INTEGER,
    market_hourly_rate NUMERIC,
    skill_scarcity_level TEXT DEFAULT 'common',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. OPERATORS
CREATE TABLE IF NOT EXISTS operators (
    operator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    employee_number TEXT,
    department_id UUID REFERENCES departments(department_id),
    hourly_rate NUMERIC DEFAULT 25.00,
    max_hours_per_day INTEGER DEFAULT 8,
    max_hours_per_week INTEGER DEFAULT 40,
    overtime_rate_multiplier NUMERIC DEFAULT 1.5,
    employment_status TEXT DEFAULT 'active',
    efficiency_rating NUMERIC DEFAULT 1.0,
    quality_score NUMERIC DEFAULT 1.0,
    safety_score NUMERIC DEFAULT 1.0,
    hire_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================================
-- CORE TEMPLATE STRUCTURE
-- =====================================================================================

-- Job templates define reusable task patterns
CREATE TABLE IF NOT EXISTS job_optimized_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    task_count INTEGER DEFAULT 0,
    total_min_duration_minutes INTEGER DEFAULT 0,
    critical_path_length_minutes INTEGER DEFAULT 0,
    solver_parameters JSONB DEFAULT '{}'::jsonb,
    baseline_performance_seconds NUMERIC,
    optimized_performance_seconds NUMERIC,
    speedup_factor NUMERIC,
    last_benchmarked_at TIMESTAMPTZ,
    performance_target_seconds NUMERIC,
    optimization_techniques_applied TEXT[],
    symmetry_breaking_enabled BOOLEAN DEFAULT false,
    redundant_constraints_count INTEGER DEFAULT 0,
    is_blessed BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optimized tasks
CREATE TABLE IF NOT EXISTS optimized_tasks (
    optimized_task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES job_optimized_patterns(pattern_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER DEFAULT 1,
    department_id UUID REFERENCES departments(department_id),
    is_unattended BOOLEAN DEFAULT FALSE,
    is_setup BOOLEAN DEFAULT FALSE,
    sequence_id TEXT REFERENCES sequence_resources(sequence_id),
    min_operators INTEGER DEFAULT 1,
    max_operators INTEGER DEFAULT 1,
    operator_efficiency_curve TEXT DEFAULT 'linear',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Work cells (must come before machines)
CREATE TABLE IF NOT EXISTS work_cells (
    cell_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    capacity INTEGER DEFAULT 1 CHECK (capacity > 0),
    department_id UUID REFERENCES departments(department_id),
    wip_limit INTEGER,
    target_utilization NUMERIC DEFAULT 0.85,
    flow_priority INTEGER DEFAULT 1,
    floor_location TEXT,
    cell_type TEXT DEFAULT 'production',
    calendar_id UUID REFERENCES business_calendars(calendar_id),
    average_throughput_per_hour NUMERIC,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Machine resources (now after work_cells)
CREATE TABLE IF NOT EXISTS machines (
    machine_resource_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    capacity INTEGER DEFAULT 1 CHECK (capacity > 0),
    cost_per_hour NUMERIC DEFAULT 0.00,
    department_id UUID REFERENCES departments(department_id),
    cell_id UUID NOT NULL REFERENCES work_cells(cell_id),
    setup_time_minutes INTEGER DEFAULT 0,
    teardown_time_minutes INTEGER DEFAULT 0,
    maintenance_window_start INTEGER,
    maintenance_window_end INTEGER,
    last_maintenance_date DATE,
    next_maintenance_due DATE,
    maintenance_interval_hours INTEGER DEFAULT 720,
    machine_type TEXT,
    manufacturer TEXT,
    model TEXT,
    year_installed INTEGER,
    efficiency_rating NUMERIC DEFAULT 1.0,
    average_utilization_percent NUMERIC,
    uptime_target_percent NUMERIC DEFAULT 95,
    calendar_id UUID REFERENCES business_calendars(calendar_id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Critical missing table: optimized_task_modes
CREATE TABLE IF NOT EXISTS optimized_task_modes (
    optimized_task_mode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    optimized_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id) ON DELETE CASCADE,
    machine_resource_id UUID NOT NULL REFERENCES machines(machine_resource_id),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task setup times
CREATE TABLE IF NOT EXISTS optimized_task_setup_times (
    setup_time_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_optimized_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id) ON DELETE CASCADE,
    to_optimized_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id) ON DELETE CASCADE,
    machine_resource_id UUID NOT NULL REFERENCES machines(machine_resource_id),
    setup_time_minutes INTEGER NOT NULL CHECK (setup_time_minutes >= 0),
    setup_type TEXT DEFAULT 'standard',
    complexity_level TEXT DEFAULT 'simple',
    requires_operator_skill TEXT,
    requires_certification BOOLEAN DEFAULT false,
    requires_supervisor_approval BOOLEAN DEFAULT false,
    setup_cost NUMERIC DEFAULT 0.00,
    efficiency_impact_percent NUMERIC DEFAULT 0.00,
    product_family_from TEXT,
    product_family_to TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (from_optimized_task_id != to_optimized_task_id)
);

-- Task precedences
CREATE TABLE IF NOT EXISTS optimized_precedences (
    precedence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES job_optimized_patterns(pattern_id) ON DELETE CASCADE,
    predecessor_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id) ON DELETE CASCADE,
    successor_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (predecessor_task_id != successor_task_id)
);


-- Job instances
CREATE TABLE IF NOT EXISTS job_instances (
    instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES job_optimized_patterns(pattern_id),
    pattern_id UUID REFERENCES job_optimized_patterns(pattern_id),
    name TEXT NOT NULL,
    description TEXT,
    department_id UUID,
    priority INTEGER DEFAULT 1,
    due_date TIMESTAMPTZ,
    earliest_start_date TIMESTAMPTZ DEFAULT NOW(),
    customer_order_id TEXT,
    batch_id TEXT,
    quantity INTEGER DEFAULT 1,
    estimated_cost NUMERIC,
    actual_cost NUMERIC,
    revenue_value NUMERIC,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'in_progress', 'completed')),
    estimated_duration_hours NUMERIC,
    actual_duration_hours NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Solved schedules
CREATE TABLE IF NOT EXISTS solved_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES job_optimized_patterns(pattern_id),
    solution_timestamp TIMESTAMPTZ DEFAULT NOW(),
    solve_time_seconds DECIMAL(10,3) NOT NULL,
    solver_status VARCHAR(50) NOT NULL,
    makespan_time_units INTEGER,
    total_lateness_minutes DECIMAL(10,2),
    maximum_lateness_minutes DECIMAL(10,2),
    instance_count INTEGER NOT NULL,
    speedup_vs_legacy DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    scheduled_task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES solved_schedules(schedule_id),
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id),
    optimized_task_id UUID NOT NULL REFERENCES optimized_tasks(optimized_task_id),
    start_time_units INTEGER NOT NULL CHECK (start_time_units >= 0),
    end_time_units INTEGER NOT NULL CHECK (end_time_units > start_time_units),
    assigned_machine_id UUID NOT NULL REFERENCES machines(machine_resource_id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sequence reservations
CREATE TABLE IF NOT EXISTS sequence_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES solved_schedules(schedule_id),
    sequence_id VARCHAR(100) NOT NULL,
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id),
    reservation_start_time_units INTEGER NOT NULL,
    reservation_end_time_units INTEGER NOT NULL CHECK (reservation_end_time_units > reservation_start_time_units),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================================
-- PERFORMANCE-CRITICAL INDEXES
-- =====================================================================================

CREATE INDEX IF NOT EXISTS idx_optimized_tasks_pattern_id ON optimized_tasks(pattern_id);
CREATE INDEX IF NOT EXISTS idx_optimized_tasks_position ON optimized_tasks(position);
CREATE INDEX IF NOT EXISTS idx_optimized_tasks_department_id ON optimized_tasks(department_id);
CREATE INDEX IF NOT EXISTS idx_optimized_task_modes_optimized_task_id ON optimized_task_modes(optimized_task_id);
CREATE INDEX IF NOT EXISTS idx_optimized_task_setup_times_from_task ON optimized_task_setup_times(from_optimized_task_id);
CREATE INDEX IF NOT EXISTS idx_optimized_task_setup_times_to_task ON optimized_task_setup_times(to_optimized_task_id);
CREATE INDEX IF NOT EXISTS idx_optimized_task_setup_times_machine ON optimized_task_setup_times(machine_resource_id);
CREATE INDEX IF NOT EXISTS idx_optimized_precedences_pattern_id ON optimized_precedences(pattern_id);
CREATE INDEX IF NOT EXISTS idx_optimized_precedences_predecessor ON optimized_precedences(predecessor_task_id);
CREATE INDEX IF NOT EXISTS idx_optimized_precedences_successor ON optimized_precedences(successor_task_id);
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code); 
CREATE INDEX IF NOT EXISTS idx_departments_parent_id ON departments(parent_department_id);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active);
CREATE INDEX IF NOT EXISTS idx_work_cells_department_id ON work_cells(department_id);
CREATE INDEX IF NOT EXISTS idx_work_cells_is_active ON work_cells(is_active);
CREATE INDEX IF NOT EXISTS idx_machines_department_id ON machines(department_id);
CREATE INDEX IF NOT EXISTS idx_machines_cell_id ON machines(cell_id);
CREATE INDEX IF NOT EXISTS idx_machines_is_active ON machines(is_active);
CREATE INDEX IF NOT EXISTS idx_business_calendars_is_default ON business_calendars(is_default);
CREATE INDEX IF NOT EXISTS idx_business_calendars_is_active ON business_calendars(is_active);
CREATE INDEX IF NOT EXISTS idx_skills_department_id ON skills(department_id);
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
CREATE INDEX IF NOT EXISTS idx_skills_complexity_level ON skills(complexity_level);
CREATE INDEX IF NOT EXISTS idx_skills_is_active ON skills(is_active);
CREATE INDEX IF NOT EXISTS idx_operators_department_id ON operators(department_id);
CREATE INDEX IF NOT EXISTS idx_operators_employee_number ON operators(employee_number);
CREATE INDEX IF NOT EXISTS idx_operators_employment_status ON operators(employment_status);
CREATE INDEX IF NOT EXISTS idx_operators_is_active ON operators(is_active);
CREATE INDEX IF NOT EXISTS idx_sequence_resources_department_id ON sequence_resources(department_id);
CREATE INDEX IF NOT EXISTS idx_sequence_resources_resource_type ON sequence_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_sequence_resources_is_active ON sequence_resources(is_active);
CREATE INDEX IF NOT EXISTS idx_job_instances_pattern_id ON job_instances(pattern_id);
CREATE INDEX IF NOT EXISTS idx_job_instances_template_id ON job_instances(template_id);
CREATE INDEX IF NOT EXISTS idx_job_instances_due_date ON job_instances(due_date);
CREATE INDEX IF NOT EXISTS idx_job_instances_status ON job_instances(status);
CREATE INDEX IF NOT EXISTS idx_optimized_task_modes_machine_id ON optimized_task_modes(machine_resource_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_machine_id ON scheduled_tasks(assigned_machine_id);
CREATE INDEX IF NOT EXISTS idx_solved_schedules_pattern_id ON solved_schedules(pattern_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_schedule_id ON scheduled_tasks(schedule_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_instance_task ON scheduled_tasks(instance_id, optimized_task_id);
CREATE INDEX IF NOT EXISTS idx_sequence_reservations_sequence_id ON sequence_reservations(sequence_id);
CREATE INDEX IF NOT EXISTS idx_sequence_reservations_schedule_id ON sequence_reservations(schedule_id);

-- =====================================================================================
-- PERFORMANCE TRACKING VIEWS
-- =====================================================================================

CREATE OR REPLACE VIEW template_performance_summary AS
SELECT 
    jop.pattern_id,
    jop.name as pattern_name,
    COUNT(ss.schedule_id) as solve_count,
    AVG(ss.solve_time_seconds) as avg_solve_time,
    AVG(ss.speedup_vs_legacy) as avg_speedup_factor,
    MAX(ss.instance_count) as max_instances_solved,
    AVG(ss.total_lateness_minutes) as avg_total_lateness,
    MIN(ss.solve_time_seconds) as best_solve_time,
    MAX(ss.solve_time_seconds) as worst_solve_time,
    COUNT(DISTINCT ji.instance_id) as total_instances_processed
FROM job_optimized_patterns jop
LEFT JOIN solved_schedules ss ON jop.pattern_id = ss.pattern_id
LEFT JOIN job_instances ji ON jop.pattern_id = COALESCE(ji.pattern_id, ji.template_id)
GROUP BY jop.pattern_id, jop.name;

CREATE OR REPLACE VIEW constraint_generation_stats AS
SELECT 
    jop.pattern_id,
    jop.name,
    COUNT(ot.optimized_task_id) as task_count,
    COUNT(otm.optimized_task_mode_id) as mode_count,
    COUNT(op.precedence_id) as precedence_count,
    COUNT(ot.optimized_task_id) * COALESCE(MAX(instance_counts.count), 0) as constraint_complexity
FROM job_optimized_patterns jop
LEFT JOIN optimized_tasks ot ON jop.pattern_id = ot.pattern_id
LEFT JOIN optimized_task_modes otm ON ot.optimized_task_id = otm.optimized_task_id
LEFT JOIN optimized_precedences op ON jop.pattern_id = op.pattern_id
LEFT JOIN (
    SELECT COALESCE(pattern_id, template_id) as pattern_id, COUNT(*) as count 
    FROM job_instances 
    WHERE pattern_id IS NOT NULL OR template_id IS NOT NULL
    GROUP BY COALESCE(pattern_id, template_id)
) instance_counts ON jop.pattern_id = instance_counts.pattern_id
GROUP BY jop.pattern_id, jop.name;

-- =====================================================================================
-- FUNCTION IMPLEMENTATIONS
-- =====================================================================================

CREATE OR REPLACE FUNCTION load_pattern_for_solver(p_pattern_id UUID)
RETURNS TABLE (
    pattern_name TEXT,
    solver_parameters JSONB,
    task_id UUID,
    task_name TEXT,
    is_unattended BOOLEAN,
    sequence_id TEXT,
    mode_id UUID,
    machine_id UUID,
    duration_minutes INTEGER,
    predecessor_task_id UUID,
    successor_task_id UUID
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jop.name,
        jop.solver_parameters,
        ot.optimized_task_id,
        ot.name,
        ot.is_unattended,
        ot.sequence_id,
        otm.optimized_task_mode_id,
        otm.machine_resource_id,
        otm.duration_minutes,
        op.predecessor_task_id,
        op.successor_task_id
    FROM job_optimized_patterns jop
    LEFT JOIN optimized_tasks ot ON jop.pattern_id = ot.pattern_id
    LEFT JOIN optimized_task_modes otm ON ot.optimized_task_id = otm.optimized_task_id
    LEFT JOIN optimized_precedences op ON jop.pattern_id = op.pattern_id
    WHERE jop.pattern_id = p_pattern_id
    ORDER BY ot.optimized_task_id, otm.optimized_task_mode_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION store_solved_schedule(
    p_pattern_id UUID,
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
        pattern_id,
        solve_time_seconds,
        solver_status,
        makespan_time_units,
        total_lateness_minutes,
        instance_count,
        speedup_vs_legacy
    ) VALUES (
        p_pattern_id,
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

-- =====================================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================================

ALTER TABLE optimized_task_modes ENABLE ROW LEVEL SECURITY;
ALTER TABLE solved_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE sequence_reservations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all access for optimized_task_modes" ON optimized_task_modes FOR ALL USING (true);
CREATE POLICY "Enable all access for solved_schedules" ON solved_schedules FOR ALL USING (true);
CREATE POLICY "Enable all access for scheduled_tasks" ON scheduled_tasks FOR ALL USING (true);
CREATE POLICY "Enable all access for sequence_reservations" ON sequence_reservations FOR ALL USING (true);

-- =====================================================================================
-- DOCUMENTATION COMMENTS
-- =====================================================================================

COMMENT ON TABLE job_optimized_patterns IS 'Pattern definitions for performance optimization through constraint reuse';
COMMENT ON TABLE optimized_tasks IS 'Reusable task structure enabling O(pattern × instances) complexity';
COMMENT ON TABLE optimized_task_modes IS 'Machine-duration combinations for constraint generation';
COMMENT ON TABLE optimized_task_setup_times IS 'Setup time constraints between optimized tasks on specific machines';
COMMENT ON TABLE optimized_precedences IS 'Pattern precedence relationships for constraint reuse';
COMMENT ON TABLE job_instances IS 'Lightweight job instances with due dates for minimize lateness objective';
COMMENT ON TABLE solved_schedules IS 'Performance tracking and solution storage for pattern-based schedules';
COMMENT ON TABLE scheduled_tasks IS 'Individual task assignments in solved schedules';
COMMENT ON TABLE sequence_reservations IS 'Sequence resource reservations (Opto, BAT) for exclusive access constraints';
COMMENT ON TABLE departments IS 'Organizational departments with hierarchical structure and shift scheduling';
COMMENT ON TABLE work_cells IS 'Production work cells with capacity and WIP constraints';
COMMENT ON TABLE machines IS 'Machine resources with maintenance schedules and efficiency tracking';
COMMENT ON TABLE business_calendars IS 'Working time calendars with timezone and working days configuration';
COMMENT ON TABLE operators IS 'Human resources with skills, ratings, and work hour constraints';
COMMENT ON TABLE skills IS 'Skill definitions with complexity levels and certification requirements';
COMMENT ON TABLE sequence_resources IS 'Exclusive access resources like Opto, BAT sequences with setup/teardown times';

COMMENT ON FUNCTION load_pattern_for_solver IS 'Hot path: Single query loads complete pattern structure for solver';
COMMENT ON FUNCTION store_solved_schedule IS 'Store solution with performance metrics and speedup tracking';

