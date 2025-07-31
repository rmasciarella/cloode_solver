-- Template-First Database Schema for OR-Tools CP-SAT Solver
-- Optimized for 5-8x performance improvements through template reuse

-- =============================================================================
-- 1. CORE TEMPLATE DEFINITIONS
-- =============================================================================

-- 1.1 Job Templates (Core Template Repository)
CREATE TABLE job_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT DEFAULT 'manufacturing', -- manufacturing, logistics, scheduling
    complexity_tier TEXT DEFAULT 'medium' CHECK(complexity_tier IN ('simple', 'medium', 'complex')),
    
    -- Template performance metadata for solver optimization
    task_count INTEGER NOT NULL DEFAULT 0,
    total_min_duration_quarters INTEGER NOT NULL DEFAULT 0, -- 15-minute intervals
    critical_path_length_quarters INTEGER NOT NULL DEFAULT 0,
    parallelism_factor NUMERIC DEFAULT 1.0, -- Potential for parallel execution
    
    -- Template sharing and versioning
    template_version INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE, -- Template library sharing
    tags TEXT[], -- Searchable tags for template discovery
    
    -- Performance targets for this template complexity
    target_solve_time_simple_ms INTEGER DEFAULT 1000,   -- <1s for 3-5 instances
    target_solve_time_medium_ms INTEGER DEFAULT 10000,  -- <10s for 5-10 instances  
    target_solve_time_complex_ms INTEGER DEFAULT 60000, -- <60s for 10+ instances
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT task_count_positive CHECK(task_count >= 0),
    CONSTRAINT durations_positive CHECK(
        total_min_duration_quarters >= 0 AND 
        critical_path_length_quarters >= 0
    ),
    CONSTRAINT parallelism_valid CHECK(parallelism_factor > 0)
);

-- 1.2 Template Tasks (Optimized for Constraint Reuse)
CREATE TABLE template_tasks (
    template_task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    
    -- Task properties for constraint optimization
    position INTEGER NOT NULL, -- Sequential ordering for symmetry breaking
    department_id TEXT,
    skill_requirements TEXT[], -- Skills needed for Phase 2
    is_unattended BOOLEAN DEFAULT FALSE,
    is_setup BOOLEAN DEFAULT FALSE,
    can_be_parallel BOOLEAN DEFAULT FALSE, -- Parallel execution capability
    
    -- Cached performance data for solver optimization
    min_duration_quarters INTEGER, -- Cached from modes
    max_duration_quarters INTEGER,
    avg_duration_quarters INTEGER,
    mode_count INTEGER DEFAULT 1, -- Number of execution modes
    
    -- Template constraint metadata
    precedence_dependencies INTEGER DEFAULT 0, -- Count of dependencies
    resource_flexibility NUMERIC DEFAULT 1.0,  -- How many machines can run this
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT position_positive CHECK(position >= 0),
    CONSTRAINT durations_valid CHECK(
        min_duration_quarters IS NULL OR min_duration_quarters > 0
    ),
    CONSTRAINT min_max_duration_order CHECK(
        min_duration_quarters IS NULL OR 
        max_duration_quarters IS NULL OR 
        min_duration_quarters <= max_duration_quarters
    ),
    CONSTRAINT flexibility_valid CHECK(resource_flexibility > 0)
);

-- Unique index to prevent duplicate positions within template
CREATE UNIQUE INDEX idx_template_tasks_position_unique 
ON template_tasks(template_id, position);

-- 1.3 Template Task Modes (Machine-Duration Combinations)
CREATE TABLE template_task_modes (
    template_task_mode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    machine_resource_id UUID NOT NULL, -- References machines table
    
    -- Mode execution parameters
    mode_name TEXT NOT NULL, -- "standard", "high_speed", "precision"
    duration_quarters INTEGER NOT NULL, -- Duration in 15-minute intervals
    energy_cost NUMERIC DEFAULT 0.0,
    quality_impact NUMERIC DEFAULT 1.0,
    
    -- Constraint generation optimization
    setup_time_quarters INTEGER DEFAULT 0,
    requires_operator BOOLEAN DEFAULT TRUE,
    batch_size INTEGER DEFAULT 1, -- For batch processing modes
    
    -- Performance hints for solver
    is_preferred BOOLEAN DEFAULT FALSE, -- Hint for solution generation
    estimated_success_rate NUMERIC DEFAULT 1.0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT duration_positive CHECK(duration_quarters > 0),
    CONSTRAINT setup_time_non_negative CHECK(setup_time_quarters >= 0),
    CONSTRAINT quality_impact_positive CHECK(quality_impact > 0),
    CONSTRAINT success_rate_valid CHECK(
        estimated_success_rate >= 0.0 AND estimated_success_rate <= 1.0
    )
);

-- Unique constraint on mode names within a task
CREATE UNIQUE INDEX idx_template_task_modes_unique 
ON template_task_modes(template_task_id, mode_name);

-- 1.4 Template Precedences (Constraint Structure)
CREATE TABLE template_precedences (
    template_precedence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    predecessor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    successor_template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id) ON DELETE CASCADE,
    
    -- Precedence parameters
    precedence_type TEXT DEFAULT 'finish_to_start' CHECK(
        precedence_type IN ('finish_to_start', 'start_to_start', 
                          'finish_to_finish', 'start_to_finish')
    ),
    lag_quarters INTEGER DEFAULT 0, -- Minimum lag time
    is_mandatory BOOLEAN DEFAULT TRUE, -- vs preferred precedence
    
    -- Constraint optimization metadata
    criticality_score NUMERIC DEFAULT 1.0, -- Impact on critical path
    creates_bottleneck BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT no_self_precedence CHECK(
        predecessor_template_task_id != successor_template_task_id
    ),
    CONSTRAINT lag_non_negative CHECK(lag_quarters >= 0),
    CONSTRAINT criticality_positive CHECK(criticality_score >= 0)
);

-- Index for efficient precedence queries during constraint generation
CREATE INDEX idx_template_precedences_traversal 
ON template_precedences(template_id, predecessor_template_task_id, successor_template_task_id);

-- =============================================================================
-- 2. JOB INSTANCES (LIGHTWEIGHT TEMPLATE REFERENCES)
-- =============================================================================

-- 2.1 Job Instances
CREATE TABLE job_instances (
    instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Instance-specific data
    instance_name TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    priority INTEGER DEFAULT 100,
    
    -- Customer/order context
    customer_id TEXT,
    order_number TEXT,
    batch_id TEXT, -- For grouping related instances
    
    -- Scheduling parameters (instance-specific overrides)
    earliest_start_time TIMESTAMPTZ,
    latest_finish_time TIMESTAMPTZ,
    preferred_shift TEXT, -- day, night, weekend
    
    -- Instance status and tracking
    status TEXT DEFAULT 'planned' CHECK(
        status IN ('planned', 'scheduled', 'in_progress', 'completed', 
                  'cancelled', 'on_hold')
    ),
    progress_pct NUMERIC DEFAULT 0.0 CHECK(progress_pct >= 0.0 AND progress_pct <= 100.0),
    
    -- Metadata for solver optimization
    symmetry_group INTEGER, -- For symmetry breaking (identical instances)
    processing_tier TEXT DEFAULT 'standard', -- standard, expedite, bulk
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT priority_positive CHECK(priority > 0),
    CONSTRAINT date_consistency CHECK(
        earliest_start_time IS NULL OR 
        latest_finish_time IS NULL OR
        earliest_start_time <= latest_finish_time
    )
);

-- Efficient queries for template-based instance loading
CREATE INDEX idx_job_instances_template_scheduling 
ON job_instances(template_id, status, due_date, priority DESC)
WHERE status IN ('planned', 'scheduled');

-- Symmetry group index for optimization
CREATE INDEX idx_job_instances_symmetry 
ON job_instances(template_id, symmetry_group) 
WHERE symmetry_group IS NOT NULL;

-- 2.2 Instance Task Assignments (Solved Schedules)
CREATE TABLE instance_task_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id) ON DELETE CASCADE,
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    selected_mode_id UUID NOT NULL REFERENCES template_task_modes(template_task_mode_id),
    
    -- Solved schedule data (populated after solving)
    start_time_quarters INTEGER, -- Solution start time
    end_time_quarters INTEGER,   -- Solution end time
    assigned_machine_id UUID, -- References machines table
    assigned_operator_id UUID, -- References operators table (Phase 2)
    
    -- Solution quality metadata
    was_hinted BOOLEAN DEFAULT FALSE, -- Used solution hint
    assignment_confidence NUMERIC DEFAULT 1.0, -- Solver confidence
    alternative_modes_available INTEGER DEFAULT 0,
    
    -- Performance tracking
    solve_iteration INTEGER DEFAULT 0, -- Which solve iteration produced this
    is_critical_path BOOLEAN DEFAULT FALSE,
    slack_time_quarters INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT times_valid CHECK(
        (start_time_quarters IS NULL AND end_time_quarters IS NULL) OR
        (start_time_quarters IS NOT NULL AND end_time_quarters IS NOT NULL AND 
         start_time_quarters >= 0 AND end_time_quarters > start_time_quarters)
    ),
    CONSTRAINT confidence_valid CHECK(
        assignment_confidence >= 0.0 AND assignment_confidence <= 1.0
    ),
    
    UNIQUE(instance_id, template_task_id)
);

-- High-performance index for schedule queries
CREATE INDEX idx_instance_assignments_schedule 
ON instance_task_assignments(assigned_machine_id, start_time_quarters, end_time_quarters)
WHERE start_time_quarters IS NOT NULL;

-- =============================================================================
-- 3. PARAMETER OPTIMIZATION & MANAGEMENT
-- =============================================================================

-- 3.1 Parameter Configurations (Experimental → Blessed)
CREATE TABLE solver_parameter_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Configuration metadata
    config_name TEXT NOT NULL,
    description TEXT,
    created_by TEXT NOT NULL,
    
    -- Parameter lifecycle
    status TEXT DEFAULT 'experimental' CHECK(
        status IN ('experimental', 'testing', 'blessed', 'production', 'deprecated')
    ),
    
    -- CP-SAT parameters (stored as JSONB for flexibility)
    parameters JSONB NOT NULL,
    
    -- Validation requirements
    min_speedup_required NUMERIC DEFAULT 1.5, -- Minimum improvement to bless
    min_instance_count_tested INTEGER DEFAULT 3,
    max_acceptable_failure_rate NUMERIC DEFAULT 0.05,
    
    -- Performance tracking
    baseline_performance_ms INTEGER,
    best_performance_ms INTEGER,
    average_speedup NUMERIC DEFAULT 1.0,
    test_instance_counts INTEGER[] DEFAULT '{3,5,10}',
    
    -- Blessing metadata
    blessed_date TIMESTAMPTZ,
    blessed_by TEXT,
    production_promotion_date TIMESTAMPTZ,
    blessing_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT speedup_positive CHECK(min_speedup_required > 0),
    CONSTRAINT failure_rate_valid CHECK(
        max_acceptable_failure_rate >= 0.0 AND max_acceptable_failure_rate <= 1.0
    ),
    CONSTRAINT performance_positive CHECK(
        baseline_performance_ms IS NULL OR baseline_performance_ms > 0
    )
);

-- Unique constraint for config names within template
CREATE UNIQUE INDEX idx_parameter_configs_name_unique 
ON solver_parameter_configs(template_id, config_name);

-- Efficient query for active blessed parameters
CREATE INDEX idx_parameter_configs_active 
ON solver_parameter_configs(template_id, status, average_speedup DESC)
WHERE status IN ('blessed', 'production');

-- 3.2 Parameter Validation Results
CREATE TABLE parameter_validation_results (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES solver_parameter_configs(config_id) ON DELETE CASCADE,
    
    -- Test configuration
    instance_count INTEGER NOT NULL,
    repetitions INTEGER DEFAULT 1,
    test_data_seed INTEGER, -- For reproducible tests
    
    -- Performance results
    solve_time_ms INTEGER NOT NULL,
    memory_usage_mb NUMERIC,
    solver_status TEXT NOT NULL,
    objective_value NUMERIC,
    first_solution_time_ms INTEGER DEFAULT 0,
    
    -- Solver statistics
    variable_count INTEGER DEFAULT 0,
    constraint_count INTEGER DEFAULT 0,
    iterations_count INTEGER DEFAULT 0,
    branch_and_bound_nodes INTEGER DEFAULT 0,
    
    -- Validation outcome
    is_successful BOOLEAN NOT NULL,
    meets_performance_target BOOLEAN DEFAULT FALSE,
    speedup_vs_baseline NUMERIC,
    
    -- Detailed results
    error_message TEXT,
    solver_log TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT instance_count_positive CHECK(instance_count > 0),
    CONSTRAINT repetitions_positive CHECK(repetitions > 0),
    CONSTRAINT performance_metrics_positive CHECK(
        solve_time_ms >= 0 AND
        (memory_usage_mb IS NULL OR memory_usage_mb >= 0) AND
        first_solution_time_ms >= 0
    )
);

-- Performance analysis queries
CREATE INDEX idx_validation_results_performance 
ON parameter_validation_results(config_id, instance_count, solve_time_ms)
WHERE is_successful = TRUE;

-- =============================================================================
-- 4. PERFORMANCE BENCHMARKING & TRACKING
-- =============================================================================

-- 4.1 Benchmark Configurations
CREATE TABLE benchmark_configurations (
    benchmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Benchmark scope
    template_ids UUID[], -- Specific templates or NULL for all
    instance_counts INTEGER[] DEFAULT '{1,3,5,10,20}',
    time_limit_seconds INTEGER DEFAULT 300,
    memory_limit_mb INTEGER DEFAULT 2048,
    repetitions INTEGER DEFAULT 3,
    
    -- Benchmark scheduling
    is_automated BOOLEAN DEFAULT FALSE,
    schedule_cron TEXT, -- Cron expression for automated runs
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    -- Performance regression detection
    enable_regression_alerts BOOLEAN DEFAULT TRUE,
    regression_threshold_pct NUMERIC DEFAULT 20.0, -- Alert if >20% slower
    baseline_window_days INTEGER DEFAULT 30,
    
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT time_limit_positive CHECK(time_limit_seconds > 0),
    CONSTRAINT repetitions_positive CHECK(repetitions > 0),
    CONSTRAINT regression_threshold_valid CHECK(regression_threshold_pct > 0)
);

-- 4.2 Benchmark Results (Historical Performance)
CREATE TABLE benchmark_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_id UUID NOT NULL REFERENCES benchmark_configurations(benchmark_id),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Test parameters
    instance_count INTEGER NOT NULL,
    repetition_number INTEGER DEFAULT 1,
    config_id UUID REFERENCES solver_parameter_configs(config_id), -- Which params used
    
    -- Performance metrics
    solve_time_ms INTEGER NOT NULL,
    memory_usage_mb NUMERIC,
    solver_status TEXT NOT NULL,
    objective_value NUMERIC,
    
    -- Detailed solver metrics
    first_solution_time_ms INTEGER DEFAULT 0,
    variable_count INTEGER DEFAULT 0,
    constraint_count INTEGER DEFAULT 0,
    preprocessing_time_ms INTEGER DEFAULT 0,
    solving_time_ms INTEGER DEFAULT 0,
    
    -- Performance analysis
    is_successful BOOLEAN NOT NULL,
    performance_score NUMERIC, -- Normalized performance metric
    baseline_comparison_pct NUMERIC, -- % vs baseline
    meets_target BOOLEAN DEFAULT FALSE,
    
    -- Context
    system_info JSONB, -- CPU, memory, solver version, etc.
    run_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT performance_metrics_valid CHECK(
        solve_time_ms >= 0 AND
        (memory_usage_mb IS NULL OR memory_usage_mb >= 0) AND
        first_solution_time_ms >= 0 AND
        preprocessing_time_ms >= 0 AND
        solving_time_ms >= 0
    )
);

-- Partitioned by month for efficient historical queries
CREATE INDEX idx_benchmark_results_time_series 
ON benchmark_results(template_id, instance_count, run_timestamp DESC)
WHERE is_successful = TRUE;

-- Performance regression detection
CREATE INDEX idx_benchmark_results_regression 
ON benchmark_results(template_id, run_timestamp DESC, baseline_comparison_pct)
WHERE baseline_comparison_pct > 20.0; -- Regression threshold

-- 4.3 Performance Baselines (Reference Points)
CREATE TABLE performance_baselines (
    baseline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Baseline configuration
    baseline_type TEXT DEFAULT 'default' CHECK(
        baseline_type IN ('default', 'legacy', 'target', 'best_known')
    ),
    instance_count INTEGER NOT NULL,
    
    -- Reference performance
    reference_solve_time_ms INTEGER NOT NULL,
    reference_memory_mb NUMERIC,
    reference_config_id UUID REFERENCES solver_parameter_configs(config_id),
    
    -- Baseline metadata
    established_date TIMESTAMPTZ DEFAULT NOW(),
    established_by TEXT NOT NULL,
    measurement_runs INTEGER DEFAULT 1,
    confidence_interval_ms INTEGER, -- 95% confidence interval
    
    -- Baseline validity
    is_active BOOLEAN DEFAULT TRUE,
    valid_until TIMESTAMPTZ,
    superseded_by UUID REFERENCES performance_baselines(baseline_id),
    
    notes TEXT,
    
    CONSTRAINT reference_performance_positive CHECK(
        reference_solve_time_ms > 0 AND
        (reference_memory_mb IS NULL OR reference_memory_mb > 0)
    ),
    CONSTRAINT measurement_runs_positive CHECK(measurement_runs > 0),
    
    UNIQUE(template_id, baseline_type, instance_count)
);

-- =============================================================================
-- 5. TEMPLATE OPTIMIZATION HISTORY (CROSS-SESSION CONTINUITY)
-- =============================================================================

-- 5.1 Optimization Sessions
CREATE TABLE optimization_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Session metadata
    session_name TEXT NOT NULL,
    developer_id TEXT NOT NULL,
    focus_area TEXT NOT NULL, -- "symmetry_breaking", "parameter_tuning", "constraint_optimization"
    
    -- Session objectives
    target_performance_ms INTEGER,
    target_speedup_factor NUMERIC DEFAULT 2.0,
    instance_count_target INTEGER DEFAULT 10,
    
    -- Session tracking
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'active' CHECK(
        status IN ('active', 'completed', 'paused', 'abandoned')
    ),
    
    -- Results summary
    baseline_performance_ms INTEGER,
    final_performance_ms INTEGER,
    achieved_speedup NUMERIC,
    optimization_techniques_applied TEXT[],
    
    -- Cross-session context
    previous_session_id UUID REFERENCES optimization_sessions(session_id),
    next_steps TEXT,
    blockers_encountered TEXT,
    
    session_notes TEXT,
    
    CONSTRAINT target_metrics_positive CHECK(
        target_performance_ms IS NULL OR target_performance_ms > 0
    ),
    CONSTRAINT speedup_target_valid CHECK(target_speedup_factor > 0)
);

-- Index for session continuity queries
CREATE INDEX idx_optimization_sessions_continuity 
ON optimization_sessions(template_id, developer_id, started_at DESC);

-- 5.2 Optimization Techniques Applied
CREATE TABLE optimization_techniques (
    technique_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES optimization_sessions(session_id) ON DELETE CASCADE,
    
    -- Technique details
    technique_name TEXT NOT NULL, -- "job_lexicographical", "parameter_tuning", etc.
    category TEXT NOT NULL, -- "symmetry_breaking", "search_strategy", "constraints"
    description TEXT,
    
    -- Implementation details
    parameters_modified JSONB,
    constraints_added INTEGER DEFAULT 0,
    variables_affected INTEGER DEFAULT 0,
    
    -- Impact measurement
    before_performance_ms INTEGER,
    after_performance_ms INTEGER,
    isolated_improvement_ms INTEGER, -- Impact of this technique alone
    
    -- Technique metadata
    difficulty_level TEXT DEFAULT 'medium' CHECK(
        difficulty_level IN ('easy', 'medium', 'hard', 'expert')
    ),
    implementation_time_minutes INTEGER,
    is_reversible BOOLEAN DEFAULT TRUE,
    
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT performance_valid CHECK(
        before_performance_ms IS NULL OR before_performance_ms > 0
    ),
    CONSTRAINT constraints_variables_non_negative CHECK(
        constraints_added >= 0 AND variables_affected >= 0
    )
);

-- 5.3 Performance Checkpoints
CREATE TABLE performance_checkpoints (
    checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES optimization_sessions(session_id) ON DELETE CASCADE,
    
    -- Checkpoint timing
    checkpoint_name TEXT NOT NULL,
    checkpoint_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Performance snapshot
    current_performance_ms INTEGER NOT NULL,
    baseline_comparison NUMERIC, -- Current vs session baseline
    target_progress_pct NUMERIC, -- Progress toward session target
    
    -- State snapshot
    active_config_id UUID REFERENCES solver_parameter_configs(config_id),
    techniques_applied_count INTEGER DEFAULT 0,
    
    -- Development context
    current_focus TEXT,
    next_planned_optimization TEXT,
    confidence_level TEXT DEFAULT 'medium' CHECK(
        confidence_level IN ('low', 'medium', 'high')
    ),
    
    checkpoint_notes TEXT,
    
    CONSTRAINT current_performance_positive CHECK(current_performance_ms > 0),
    CONSTRAINT progress_valid CHECK(
        target_progress_pct IS NULL OR 
        (target_progress_pct >= 0.0 AND target_progress_pct <= 100.0)
    )
);

-- =============================================================================
-- 6. MULTI-TENANT TEMPLATE LIBRARY
-- =============================================================================

-- 6.1 Template Sharing & Access Control
CREATE TABLE template_access_control (
    access_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id) ON DELETE CASCADE,
    
    -- Access control
    user_id TEXT NOT NULL,
    access_level TEXT NOT NULL CHECK(
        access_level IN ('read', 'write', 'admin', 'owner')
    ),
    
    -- Sharing context
    granted_by TEXT NOT NULL,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Usage tracking
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    
    UNIQUE(template_id, user_id)
);

-- 6.2 Template Usage Analytics
CREATE TABLE template_usage_analytics (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES job_templates(template_id),
    user_id TEXT NOT NULL,
    
    -- Usage type
    action TEXT NOT NULL CHECK(
        action IN ('view', 'clone', 'modify', 'solve', 'benchmark')
    ),
    
    -- Context
    instance_count INTEGER,
    solve_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.3 Template Relationships (Variants & Inheritance)
CREATE TABLE template_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_template_id UUID NOT NULL REFERENCES job_templates(template_id),
    child_template_id UUID NOT NULL REFERENCES job_templates(template_id),
    
    -- Relationship type
    relationship_type TEXT NOT NULL CHECK(
        relationship_type IN ('clone', 'variant', 'improvement', 'specialization')
    ),
    
    -- Relationship metadata
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    change_description TEXT,
    
    -- Performance comparison
    performance_delta_pct NUMERIC, -- Child vs parent performance
    complexity_delta INTEGER DEFAULT 0, -- Task count difference
    
    CONSTRAINT no_self_relationship CHECK(parent_template_id != child_template_id),
    CONSTRAINT complexity_delta_reasonable CHECK(
        complexity_delta >= -1000 AND complexity_delta <= 1000
    )
);

-- =============================================================================
-- 7. PERFORMANCE-CRITICAL INDEXES
-- =============================================================================

-- Template loading optimization (critical path)
CREATE INDEX idx_template_loading_critical 
ON template_tasks(template_id) 
INCLUDE (position, name, min_duration_quarters, max_duration_quarters);

CREATE INDEX idx_template_modes_loading 
ON template_task_modes(template_task_id) 
INCLUDE (mode_name, duration_quarters, machine_resource_id);

-- Instance solving optimization  
CREATE INDEX idx_instance_solving_batch 
ON job_instances(template_id, status) 
INCLUDE (instance_id, due_date, priority)
WHERE status IN ('planned', 'scheduled');

-- Parameter lookup optimization (hot path)
CREATE UNIQUE INDEX idx_blessed_parameters_lookup 
ON solver_parameter_configs(template_id) 
INCLUDE (parameters, average_speedup)
WHERE status = 'production';

-- Performance regression detection
CREATE INDEX idx_performance_regression_monitoring 
ON benchmark_results(template_id, run_timestamp DESC) 
INCLUDE (solve_time_ms, baseline_comparison_pct)
WHERE baseline_comparison_pct > 20.0;

-- =============================================================================
-- 8. MATERIALIZED VIEWS FOR PERFORMANCE
-- =============================================================================

-- Real-time template performance summary
CREATE MATERIALIZED VIEW template_performance_summary AS
SELECT 
    t.template_id,
    t.name,
    t.complexity_tier,
    
    -- Latest benchmark performance
    COALESCE(latest_bench.avg_solve_time_ms, t.target_solve_time_medium_ms) as latest_solve_time_ms,
    COALESCE(latest_bench.avg_speedup, 1.0) as latest_speedup,
    latest_bench.last_benchmark_date,
    
    -- Blessed parameters status
    bp.config_id as blessed_config_id,
    bp.average_speedup as blessed_speedup,
    bp.status as parameter_status,
    
    -- Usage statistics
    usage.total_solves_30d,
    usage.avg_instances_per_solve,
    
    -- Performance trend
    CASE 
        WHEN trend.performance_trend > 1.1 THEN 'improving'
        WHEN trend.performance_trend < 0.9 THEN 'degrading'
        ELSE 'stable'
    END as performance_trend
    
FROM job_templates t
LEFT JOIN (
    SELECT 
        br.template_id,
        AVG(br.solve_time_ms) as avg_solve_time_ms,
        AVG(COALESCE(br.baseline_comparison_pct / 100.0, 1.0)) as avg_speedup,
        MAX(br.run_timestamp) as last_benchmark_date
    FROM benchmark_results br
    WHERE br.run_timestamp > NOW() - INTERVAL '30 days' 
      AND br.is_successful = TRUE
    GROUP BY br.template_id
) latest_bench ON t.template_id = latest_bench.template_id
LEFT JOIN (
    SELECT DISTINCT ON (spc.template_id) 
        spc.template_id, spc.config_id, spc.average_speedup, spc.status
    FROM solver_parameter_configs spc
    WHERE spc.status IN ('blessed', 'production')
    ORDER BY spc.template_id, spc.average_speedup DESC
) bp ON t.template_id = bp.template_id
LEFT JOIN (
    SELECT 
        tu.template_id,
        COUNT(*) as total_solves_30d,
        AVG(CASE WHEN tu.instance_count IS NOT NULL THEN tu.instance_count ELSE 1 END) as avg_instances_per_solve
    FROM template_usage_analytics tu
    WHERE tu.occurred_at > NOW() - INTERVAL '30 days'
      AND tu.action = 'solve'
    GROUP BY tu.template_id
) usage ON t.template_id = usage.template_id
LEFT JOIN (
    SELECT 
        br2.template_id,
        -- Performance trend over last 90 days (recent avg / older avg)
        AVG(CASE WHEN br2.run_timestamp > NOW() - INTERVAL '30 days' 
            THEN br2.solve_time_ms END) / 
        NULLIF(AVG(CASE WHEN br2.run_timestamp BETWEEN NOW() - INTERVAL '90 days' 
                                                 AND NOW() - INTERVAL '30 days'
            THEN br2.solve_time_ms END), 0) as performance_trend
    FROM benchmark_results br2
    WHERE br2.run_timestamp > NOW() - INTERVAL '90 days'
      AND br2.is_successful = TRUE
    GROUP BY br2.template_id
) trend ON t.template_id = trend.template_id;

-- Refresh every hour
CREATE INDEX idx_template_perf_summary_refresh 
ON template_performance_summary(template_id);

-- Template library discovery view
CREATE MATERIALIZED VIEW template_library AS
SELECT 
    t.template_id,
    t.name,
    t.category,
    t.complexity_tier,
    t.task_count,
    t.parallelism_factor,
    t.created_by,
    t.is_public,
    t.tags,
    -- Performance metrics from benchmarks
    COALESCE(b.latest_speedup, 1.0) as current_speedup,
    COALESCE(b.latest_solve_time_ms, t.target_solve_time_medium_ms) as avg_solve_time_ms,
    bp.is_blessed,
    bp.production_ready_date
FROM job_templates t
LEFT JOIN template_performance_summary b ON t.template_id = b.template_id
LEFT JOIN (
    SELECT 
        spc.template_id,
        CASE WHEN spc.status = 'production' THEN TRUE ELSE FALSE END as is_blessed,
        spc.production_promotion_date as production_ready_date
    FROM solver_parameter_configs spc
    WHERE spc.status IN ('blessed', 'production')
) bp ON t.template_id = bp.template_id
WHERE t.is_public = TRUE -- OR t.created_by = current_user (modify based on auth system)
ORDER BY current_speedup DESC, t.updated_at DESC;

-- =============================================================================
-- 9. STORED PROCEDURES FOR OR-TOOLS INTEGRATION
-- =============================================================================

-- Template loading for solving (hot path optimization)
CREATE OR REPLACE FUNCTION load_template_for_solving(
    p_template_id UUID,
    p_max_instances INTEGER DEFAULT 10
) RETURNS TABLE (
    -- Template structure
    template_name TEXT,
    complexity_tier TEXT,
    task_count INTEGER,
    
    -- Template tasks
    task_id UUID,
    task_name TEXT,
    task_position INTEGER,
    min_duration INTEGER,
    max_duration INTEGER,
    
    -- Task modes
    mode_id UUID,
    mode_name TEXT,
    machine_id UUID,
    duration_quarters INTEGER,
    
    -- Precedences
    predecessor_id UUID,
    successor_id UUID,
    lag_quarters INTEGER,
    
    -- Instances to solve
    instance_id UUID,
    instance_name TEXT,
    due_date TIMESTAMPTZ,
    priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jt.name,
        jt.complexity_tier,
        jt.task_count,
        
        tt.template_task_id,
        tt.name,
        tt.position,
        tt.min_duration_quarters,
        tt.max_duration_quarters,
        
        ttm.template_task_mode_id,
        ttm.mode_name,
        ttm.machine_resource_id,
        ttm.duration_quarters,
        
        tp.predecessor_template_task_id,
        tp.successor_template_task_id,
        tp.lag_quarters,
        
        ji.instance_id,
        ji.instance_name,
        ji.due_date,
        ji.priority
        
    FROM job_templates jt
    JOIN template_tasks tt ON jt.template_id = tt.template_id
    LEFT JOIN template_task_modes ttm ON tt.template_task_id = ttm.template_task_id
    LEFT JOIN template_precedences tp ON jt.template_id = tp.template_id
    LEFT JOIN job_instances ji ON jt.template_id = ji.template_id
    WHERE jt.template_id = p_template_id
      AND (ji.instance_id IS NULL OR ji.status IN ('planned', 'scheduled'))
    ORDER BY tt.position, ttm.mode_name, ji.priority DESC, ji.due_date
    LIMIT CASE WHEN p_max_instances > 0 THEN p_max_instances ELSE NULL END;
END;
$$ LANGUAGE plpgsql;

-- Performance tracking function
CREATE OR REPLACE FUNCTION record_solve_performance(
    p_template_id UUID,
    p_instance_count INTEGER,
    p_solve_time_ms INTEGER,
    p_solver_status TEXT,
    p_config_id UUID DEFAULT NULL,
    p_objective_value NUMERIC DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    result_id UUID;
    baseline_time_ms INTEGER;
    comparison_pct NUMERIC;
BEGIN
    -- Get baseline for comparison
    SELECT reference_solve_time_ms INTO baseline_time_ms
    FROM performance_baselines 
    WHERE template_id = p_template_id 
      AND instance_count = p_instance_count
      AND baseline_type = 'default'
      AND is_active = TRUE;
    
    -- Calculate comparison percentage
    IF baseline_time_ms IS NOT NULL AND baseline_time_ms > 0 THEN
        comparison_pct := ((p_solve_time_ms - baseline_time_ms)::NUMERIC / baseline_time_ms) * 100;
    END IF;
    
    -- Insert benchmark result
    INSERT INTO benchmark_results (
        template_id,
        instance_count,
        solve_time_ms,
        solver_status,
        objective_value,
        config_id,
        is_successful,
        baseline_comparison_pct,
        meets_target
    ) VALUES (
        p_template_id,
        p_instance_count,
        p_solve_time_ms,
        p_solver_status,
        p_objective_value,
        p_config_id,
        p_solver_status IN ('OPTIMAL', 'FEASIBLE'),
        comparison_pct,
        p_solve_time_ms <= COALESCE(baseline_time_ms, p_solve_time_ms)
    ) RETURNING result_id INTO result_id;
    
    -- Refresh materialized view if significant result
    IF comparison_pct IS NOT NULL AND ABS(comparison_pct) > 10 THEN
        REFRESH MATERIALIZED VIEW template_performance_summary;
    END IF;
    
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE job_templates IS 'Core template repository optimized for OR-Tools CP-SAT solver performance';
COMMENT ON TABLE template_tasks IS 'Template task structure enabling O(template_size × instances) complexity';
COMMENT ON TABLE template_task_modes IS 'Machine-duration combinations for constraint optimization';
COMMENT ON TABLE template_precedences IS 'Template precedence structure for constraint reuse';

COMMENT ON TABLE job_instances IS 'Lightweight references to templates for instance-specific data';
COMMENT ON TABLE instance_task_assignments IS 'Solved schedules linking instances to template tasks';

COMMENT ON TABLE solver_parameter_configs IS 'CP-SAT parameter lifecycle management: experimental → blessed → production';
COMMENT ON TABLE parameter_validation_results IS 'Performance validation results for parameter tuning';

COMMENT ON TABLE benchmark_configurations IS 'Automated benchmarking configurations for regression detection';
COMMENT ON TABLE benchmark_results IS 'Historical performance tracking and regression analysis';
COMMENT ON TABLE performance_baselines IS 'Reference performance points for comparison';

COMMENT ON TABLE optimization_sessions IS 'Cross-session optimization context for development continuity';
COMMENT ON TABLE optimization_techniques IS 'Applied optimization techniques with performance impact';
COMMENT ON TABLE performance_checkpoints IS 'Development session checkpoints for progress tracking';

COMMENT ON MATERIALIZED VIEW template_performance_summary IS 'Real-time performance summary for all templates';
COMMENT ON MATERIALIZED VIEW template_library IS 'Public template discovery with performance metrics';

COMMENT ON FUNCTION load_template_for_solving IS 'Hot-path optimized template loading for solver';
COMMENT ON FUNCTION record_solve_performance IS 'Performance tracking with automatic baseline comparison';