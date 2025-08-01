-- Initial RLS Setup for Fresh Solver Project
-- Phase 1: Basic authentication structure with permissive policies

-- Enable RLS on all main tables but with very permissive policies initially
-- This allows gradual tightening without breaking existing functionality

-- Departments table
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;

-- PERMISSIVE POLICY: Allow all operations for authenticated users (including service role)
-- This essentially maintains current behavior while RLS is technically enabled
CREATE POLICY "departments_permissive_all" ON departments
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Allow public access in development (can be removed in production)
CREATE POLICY "departments_public_read" ON departments
  FOR SELECT
  TO anon
  USING (true);

-- Work Cells table
ALTER TABLE work_cells ENABLE ROW LEVEL SECURITY;

CREATE POLICY "work_cells_permissive_all" ON work_cells
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "work_cells_public_read" ON work_cells
  FOR SELECT
  TO anon
  USING (true);

-- Machine Resources table
ALTER TABLE machine_resources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "machine_resources_permissive_all" ON machine_resources
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "machine_resources_public_read" ON machine_resources
  FOR SELECT
  TO anon
  USING (true);

-- Job Templates table
ALTER TABLE job_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_templates_permissive_all" ON job_templates
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "job_templates_public_read" ON job_templates
  FOR SELECT
  TO anon
  USING (true);

-- Job Template Tasks table
ALTER TABLE job_template_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_template_tasks_permissive_all" ON job_template_tasks
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "job_template_tasks_public_read" ON job_template_tasks
  FOR SELECT
  TO anon
  USING (true);

-- Task Dependencies table
ALTER TABLE task_dependencies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "task_dependencies_permissive_all" ON task_dependencies
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "task_dependencies_public_read" ON task_dependencies
  FOR SELECT
  TO anon
  USING (true);

-- Job Instances table
ALTER TABLE job_instances ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_instances_permissive_all" ON job_instances
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "job_instances_public_read" ON job_instances
  FOR SELECT
  TO anon
  USING (true);

-- Job Instance Tasks table
ALTER TABLE job_instance_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_instance_tasks_permissive_all" ON job_instance_tasks
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "job_instance_tasks_public_read" ON job_instance_tasks
  FOR SELECT
  TO anon
  USING (true);

-- Task Assignments table
ALTER TABLE task_assignments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "task_assignments_permissive_all" ON task_assignments
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "task_assignments_public_read" ON task_assignments
  FOR SELECT
  TO anon
  USING (true);

-- Operators table
ALTER TABLE operators ENABLE ROW LEVEL SECURITY;

CREATE POLICY "operators_permissive_all" ON operators
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "operators_public_read" ON operators
  FOR SELECT
  TO anon
  USING (true);

-- Skills table
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "skills_permissive_all" ON skills
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "skills_public_read" ON skills
  FOR SELECT
  TO anon
  USING (true);

-- Operator Skills table
ALTER TABLE operator_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "operator_skills_permissive_all" ON operator_skills
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "operator_skills_public_read" ON operator_skills
  FOR SELECT
  TO anon
  USING (true);

-- Task Skill Requirements table
ALTER TABLE task_skill_requirements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "task_skill_requirements_permissive_all" ON task_skill_requirements
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "task_skill_requirements_public_read" ON task_skill_requirements
  FOR SELECT
  TO anon
  USING (true);

-- Shift Calendars table
ALTER TABLE shift_calendars ENABLE ROW LEVEL SECURITY;

CREATE POLICY "shift_calendars_permissive_all" ON shift_calendars
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "shift_calendars_public_read" ON shift_calendars
  FOR SELECT
  TO anon
  USING (true);

-- Shift Calendar Periods table
ALTER TABLE shift_calendar_periods ENABLE ROW LEVEL SECURITY;

CREATE POLICY "shift_calendar_periods_permissive_all" ON shift_calendar_periods
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "shift_calendar_periods_public_read" ON shift_calendar_periods
  FOR SELECT
  TO anon
  USING (true);

-- Create a basic users table for future use (not enforced yet)
CREATE TABLE IF NOT EXISTS auth_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'operator', 'user')),
  department_id UUID REFERENCES departments(department_id),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on auth_users (will be used for future user management)
ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "auth_users_permissive_all" ON auth_users
  FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Comments documenting the phased approach
COMMENT ON TABLE departments IS 'RLS Phase 1: Permissive policies - all operations allowed for authenticated users';
COMMENT ON TABLE work_cells IS 'RLS Phase 1: Permissive policies - gradual security rollout';
COMMENT ON TABLE machine_resources IS 'RLS Phase 1: Permissive policies - maintains existing GUI functionality';
COMMENT ON TABLE auth_users IS 'RLS Phase 1: Basic user structure for future role-based access control';