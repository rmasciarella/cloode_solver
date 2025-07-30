-- Create test tables for fresh solver development
-- These are simplified versions without RLS policies

-- Drop existing test tables if they exist
DROP TABLE IF EXISTS test_task_precedences CASCADE;
DROP TABLE IF EXISTS test_task_modes CASCADE;
DROP TABLE IF EXISTS test_tasks CASCADE;
DROP TABLE IF EXISTS test_jobs CASCADE;
DROP TABLE IF EXISTS test_resources CASCADE;
DROP TABLE IF EXISTS test_work_cells CASCADE;

-- Create test work cells table
CREATE TABLE test_work_cells (
    cell_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1
);

-- Create test resources (machines) table
CREATE TABLE test_resources (
    resource_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id UUID REFERENCES test_work_cells(cell_id),
    name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1,
    cost_per_hour NUMERIC
);

-- Create test jobs table
CREATE TABLE test_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT,
    due_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create test tasks table
CREATE TABLE test_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES test_jobs(job_id),
    name TEXT NOT NULL,
    department_id TEXT,
    is_unattended BOOLEAN DEFAULT FALSE,
    is_setup BOOLEAN DEFAULT FALSE
);

-- Create test task modes table
CREATE TABLE test_task_modes (
    task_mode_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES test_tasks(task_id),
    machine_resource_id UUID REFERENCES test_resources(resource_id),
    duration_minutes INTEGER NOT NULL
);

-- Create test task precedences table
CREATE TABLE test_task_precedences (
    predecessor_task_id UUID REFERENCES test_tasks(task_id),
    successor_task_id UUID REFERENCES test_tasks(task_id),
    PRIMARY KEY (predecessor_task_id, successor_task_id)
);

-- Create indexes for better performance
CREATE INDEX idx_test_tasks_job_id ON test_tasks(job_id);
CREATE INDEX idx_test_task_modes_task_id ON test_task_modes(task_id);
CREATE INDEX idx_test_resources_cell_id ON test_resources(cell_id);