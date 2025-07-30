-- Migration script: Legacy job-based to template-based schema
-- Week 3 Implementation: Safe migration with rollback capability
--
-- This script provides a safe migration path from the existing job-based
-- schema to the new template-based architecture while maintaining backward compatibility

-- ============================================================================
-- MIGRATION SAFETY CHECKS
-- ============================================================================

-- Ensure template schema exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'job_templates') THEN
        RAISE EXCEPTION 'Template schema not found. Run 001_create_template_schema.sql first.';
    END IF;
END $$;

-- Check for existing data that needs migration
DO $$
DECLARE
    legacy_job_count INTEGER;
    legacy_task_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO legacy_job_count FROM test_jobs;
    SELECT COUNT(*) INTO legacy_task_count FROM test_tasks;
    
    RAISE NOTICE 'Found % legacy jobs and % legacy tasks for potential migration', 
                 legacy_job_count, legacy_task_count;
END $$;

-- ============================================================================
-- MIGRATION FUNCTIONS
-- ============================================================================

-- Function to create template from existing job structure
CREATE OR REPLACE FUNCTION migrate_job_to_template(
    p_source_job_id UUID,
    p_template_name TEXT,
    p_template_description TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_template_id UUID;
    v_task_record RECORD;
    v_mode_record RECORD;
    v_prec_record RECORD;
    v_template_task_id UUID;
    v_position INTEGER := 0;
BEGIN
    -- Create job template
    INSERT INTO job_templates (name, description)
    VALUES (p_template_name, COALESCE(p_template_description, 'Migrated from job ' || p_source_job_id))
    RETURNING template_id INTO v_template_id;
    
    RAISE NOTICE 'Created template % with ID %', p_template_name, v_template_id;
    
    -- Migrate tasks
    FOR v_task_record IN 
        SELECT * FROM test_tasks WHERE job_id = p_source_job_id ORDER BY name
    LOOP
        v_position := v_position + 1;
        
        INSERT INTO template_tasks (
            template_id, name, department_id, is_unattended, 
            is_setup, position
        )
        VALUES (
            v_template_id, v_task_record.name, v_task_record.department_id,
            v_task_record.is_unattended, v_task_record.is_setup, v_position
        )
        RETURNING template_task_id INTO v_template_task_id;
        
        -- Migrate task modes
        FOR v_mode_record IN
            SELECT tm.*, r.resource_id as machine_id
            FROM test_task_modes tm
            JOIN test_resources r ON tm.machine_resource_id = r.resource_id
            WHERE tm.task_id = v_task_record.task_id
        LOOP
            INSERT INTO template_task_modes (
                template_task_id, machine_resource_id, duration_minutes, mode_name
            )
            VALUES (
                v_template_task_id, v_mode_record.machine_id, 
                v_mode_record.duration_minutes,
                'mode_' || LOWER(REPLACE(v_task_record.name, ' ', '_')) || '_' || 
                (SELECT name FROM test_resources WHERE resource_id = v_mode_record.machine_id)
            );
        END LOOP;
        
        RAISE NOTICE 'Migrated task % with % modes', v_task_record.name, 
                     (SELECT COUNT(*) FROM test_task_modes WHERE task_id = v_task_record.task_id);
    END LOOP;
    
    -- Migrate precedences (requires task mapping)
    FOR v_prec_record IN
        SELECT tp.*, 
               pred_task.name as pred_name, 
               succ_task.name as succ_name
        FROM test_task_precedences tp
        JOIN test_tasks pred_task ON tp.predecessor_task_id = pred_task.task_id
        JOIN test_tasks succ_task ON tp.successor_task_id = succ_task.task_id
        WHERE pred_task.job_id = p_source_job_id
          AND succ_task.job_id = p_source_job_id
    LOOP
        INSERT INTO template_precedences (
            template_id, predecessor_template_task_id, successor_template_task_id
        )
        SELECT 
            v_template_id,
            pred_template.template_task_id,
            succ_template.template_task_id
        FROM template_tasks pred_template, template_tasks succ_template
        WHERE pred_template.template_id = v_template_id
          AND pred_template.name = v_prec_record.pred_name
          AND succ_template.template_id = v_template_id
          AND succ_template.name = v_prec_record.succ_name;
    END LOOP;
    
    -- Update template statistics
    PERFORM update_template_statistics(v_template_id);
    
    RAISE NOTICE 'Template migration completed for job %', p_source_job_id;
    RETURN v_template_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create job instances from migrated template
CREATE OR REPLACE FUNCTION create_instances_from_template(
    p_template_id UUID,
    p_instance_count INTEGER DEFAULT 1,
    p_base_description TEXT DEFAULT 'Migrated Instance',
    p_hours_between_due_dates NUMERIC DEFAULT 24.0
)
RETURNS UUID[] AS $$
DECLARE
    v_instance_ids UUID[] := '{}';
    v_instance_id UUID;
    v_base_due_date TIMESTAMPTZ;
    i INTEGER;
BEGIN
    v_base_due_date := NOW() + INTERVAL '24 hours';
    
    FOR i IN 1..p_instance_count LOOP
        INSERT INTO job_instances (
            template_id, description, due_date
        )
        VALUES (
            p_template_id,
            p_base_description || ' ' || i,
            v_base_due_date + (INTERVAL '1 hour' * p_hours_between_due_dates * (i - 1))
        )
        RETURNING instance_id INTO v_instance_id;
        
        v_instance_ids := array_append(v_instance_ids, v_instance_id);
    END LOOP;
    
    RAISE NOTICE 'Created % instances from template %', p_instance_count, p_template_id;
    RETURN v_instance_ids;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- AUTOMATED MIGRATION EXECUTION
-- ============================================================================

-- Migration strategy: Convert unique job patterns to templates
DO $$
DECLARE
    v_unique_job RECORD;
    v_template_id UUID;
    v_instance_ids UUID[];
    v_job_signature TEXT;
    v_existing_jobs UUID[];
BEGIN
    RAISE NOTICE 'Starting automated migration of similar jobs to templates...';
    
    -- Find groups of jobs with identical task structures
    -- This is a simplified approach - in production you might want more sophisticated pattern matching
    FOR v_unique_job IN
        WITH job_signatures AS (
            SELECT 
                j.job_id,
                j.description,
                string_agg(t.name || ':' || t.department_id, '|' ORDER BY t.name) as task_signature
            FROM test_jobs j
            JOIN test_tasks t ON j.job_id = t.job_id
            GROUP BY j.job_id, j.description
        ),
        signature_groups AS (
            SELECT 
                task_signature,
                COUNT(*) as job_count,
                array_agg(job_id) as job_ids,
                MIN(description) as sample_description
            FROM job_signatures
            GROUP BY task_signature
        )
        SELECT * FROM signature_groups WHERE job_count >= 1 -- Even single jobs become templates
    LOOP
        v_job_signature := 'Template_' || substring(md5(v_unique_job.task_signature), 1, 8);
        
        RAISE NOTICE 'Processing job group: % jobs with signature %', 
                     v_unique_job.job_count, v_job_signature;
        
        -- Create template from first job in group
        SELECT migrate_job_to_template(
            v_unique_job.job_ids[1],
            v_job_signature,
            'Auto-migrated template: ' || v_unique_job.sample_description
        ) INTO v_template_id;
        
        -- Create instances for all jobs in group
        SELECT create_instances_from_template(
            v_template_id,
            v_unique_job.job_count,
            'Migrated from legacy job',
            2.0  -- 2 hours between due dates
        ) INTO v_instance_ids;
        
        RAISE NOTICE 'Created template % with % instances', v_template_id, array_length(v_instance_ids, 1);
    END LOOP;
    
    RAISE NOTICE 'Automated migration completed successfully';
END $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify migration results
DO $$
DECLARE
    v_template_count INTEGER;
    v_instance_count INTEGER;
    v_legacy_job_count INTEGER;
    v_template_task_count INTEGER;
    v_legacy_task_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_template_count FROM job_templates;
    SELECT COUNT(*) INTO v_instance_count FROM job_instances;
    SELECT COUNT(*) INTO v_legacy_job_count FROM test_jobs;
    SELECT COUNT(*) INTO v_template_task_count FROM template_tasks;
    SELECT COUNT(*) INTO v_legacy_task_count FROM test_tasks;
    
    RAISE NOTICE 'Migration Results:';
    RAISE NOTICE '  Templates created: %', v_template_count;
    RAISE NOTICE '  Instances created: %', v_instance_count;
    RAISE NOTICE '  Legacy jobs: %', v_legacy_job_count;
    RAISE NOTICE '  Template tasks: %', v_template_task_count;
    RAISE NOTICE '  Legacy tasks: %', v_legacy_task_count;
    
    IF v_template_count = 0 THEN
        RAISE WARNING 'No templates were created. Check if test data exists.';
    END IF;
END $$;

-- ============================================================================
-- ROLLBACK PREPARATION
-- ============================================================================

-- Create rollback script (stored as comment for manual execution if needed)
/*
ROLLBACK SCRIPT - Execute manually if migration needs to be reversed:

-- Drop template-specific tables (keep test_ tables)
DROP TABLE IF EXISTS instance_task_assignments CASCADE;
DROP TABLE IF EXISTS job_instances CASCADE;
DROP TABLE IF EXISTS template_machine_requirements CASCADE;
DROP TABLE IF EXISTS template_statistics CASCADE;
DROP TABLE IF EXISTS template_precedences CASCADE;
DROP TABLE IF EXISTS template_task_modes CASCADE;
DROP TABLE IF EXISTS template_tasks CASCADE;
DROP TABLE IF EXISTS job_templates CASCADE;

-- Drop migration functions
DROP FUNCTION IF EXISTS migrate_job_to_template(UUID, TEXT, TEXT);
DROP FUNCTION IF EXISTS create_instances_from_template(UUID, INTEGER, TEXT, NUMERIC);
DROP FUNCTION IF EXISTS update_template_statistics(UUID);
DROP FUNCTION IF EXISTS get_template_load_data(UUID);
DROP FUNCTION IF EXISTS trigger_update_template_stats();

NOTICE: Legacy test_ tables remain intact for continued operation.
*/

-- ============================================================================
-- POST-MIGRATION SETUP
-- ============================================================================

-- Analyze tables for optimal query performance
ANALYZE job_templates;
ANALYZE template_tasks;
ANALYZE template_task_modes;
ANALYZE template_precedences;
ANALYZE job_instances;
ANALYZE instance_task_assignments;

-- Create sample template if no data existed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM job_templates LIMIT 1) THEN
        RAISE NOTICE 'No templates found after migration. Creating sample template for testing...';
        
        -- This would be replaced with actual test data creation
        RAISE NOTICE 'Run template_generator.py to create sample templates.';
    END IF;
END $$;

RAISE NOTICE 'Template schema migration completed successfully!';
RAISE NOTICE 'Legacy tables remain available for backward compatibility.';
RAISE NOTICE 'Use get_template_load_data(template_id) for efficient OR-Tools loading.';