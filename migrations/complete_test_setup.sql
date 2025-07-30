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


-- Insert test data for fresh solver

-- Insert work cells
INSERT INTO test_work_cells (cell_id, name, capacity) VALUES
('36730fb1-eee4-4788-9f6c-2adff5d52dc7', 'Cell A', 2),
('43d482f1-b7e4-4ceb-9aba-89a132b0820d', 'Cell B', 1);

-- Insert machines
INSERT INTO test_resources (resource_id, cell_id, name, resource_type, capacity, cost_per_hour) VALUES
('9881a89e-5c2e-4ce5-8878-61202ebe7ca3', '36730fb1-eee4-4788-9f6c-2adff5d52dc7', 'Machine 1', 'machine', 1, 100.00),
('374dc95b-cfae-4062-a3ff-56e58afdee95', '36730fb1-eee4-4788-9f6c-2adff5d52dc7', 'Machine 2', 'machine', 1, 120.00),
('3d9550b0-2413-49ab-9ad8-4c693a2ed77f', '43d482f1-b7e4-4ceb-9aba-89a132b0820d', 'Machine 3', 'machine', 1, 80.00);

-- Insert jobs
INSERT INTO test_jobs (job_id, description, due_date) VALUES
('382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'Test Job 1 - Linear Workflow', '2025-08-01T00:02:13.487348+00:00'),
('89741086-266c-4261-b3d2-39cf9f1dd109', 'Test Job 2 - Diamond Workflow', '2025-08-02T00:02:13.487348+00:00');

-- Insert tasks for Job 1 (Linear workflow)
INSERT INTO test_tasks (task_id, job_id, name, department_id, is_unattended, is_setup) VALUES
('75dc92bb-3218-4b63-b791-f480b0440ce7', '382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'J1-T1: Setup', 'dept_a', false, true),
('7ddce8a5-a8fa-44cb-a036-211a1b544975', '382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'J1-T2: Process A', 'dept_a', false, false),
('66a69e18-8839-4bf0-9b76-f81e2c32cde1', '382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'J1-T3: Process B', 'dept_b', true, false),
('d742c69f-45d1-4252-8fdf-36515e37e94c', '382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'J1-T4: Process C', 'dept_a', false, false),
('3746d432-0935-4b26-8991-26ebd2b0e4a5', '382c7ad9-7df2-44ec-ae86-bd73cb45ffac', 'J1-T5: Cleanup', 'dept_b', false, false);

-- Insert tasks for Job 2 (Diamond workflow)
INSERT INTO test_tasks (task_id, job_id, name, department_id, is_unattended, is_setup) VALUES
('730a7563-0376-48cf-885e-d1dabae74f62', '89741086-266c-4261-b3d2-39cf9f1dd109', 'J2-T1: Initial Setup', 'dept_a', false, true),
('45425b7b-e517-44d6-bdb4-175cd6543106', '89741086-266c-4261-b3d2-39cf9f1dd109', 'J2-T2: Branch A', 'dept_a', false, false),
('9e671e01-3869-4b04-ae6c-138b2ac3f374', '89741086-266c-4261-b3d2-39cf9f1dd109', 'J2-T3: Branch B', 'dept_b', true, false),
('e3147436-276e-4dff-afed-275113ed7520', '89741086-266c-4261-b3d2-39cf9f1dd109', 'J2-T4: Merge Process', 'dept_a', false, false),
('8a5d08b3-0c53-443e-801a-ee64012bae92', '89741086-266c-4261-b3d2-39cf9f1dd109', 'J2-T5: Final Assembly', 'dept_b', false, false);

-- Insert task modes for Job 1
INSERT INTO test_task_modes (task_id, machine_resource_id, duration_minutes) VALUES
-- Task 1: Can run on machines 1 or 2
('75dc92bb-3218-4b63-b791-f480b0440ce7', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 30),
('75dc92bb-3218-4b63-b791-f480b0440ce7', '374dc95b-cfae-4062-a3ff-56e58afdee95', 25),
-- Task 2: Only on machine 1
('7ddce8a5-a8fa-44cb-a036-211a1b544975', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 45),
-- Task 3: Can run on any machine (unattended)
('66a69e18-8839-4bf0-9b76-f81e2c32cde1', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 60),
('66a69e18-8839-4bf0-9b76-f81e2c32cde1', '374dc95b-cfae-4062-a3ff-56e58afdee95', 60),
('66a69e18-8839-4bf0-9b76-f81e2c32cde1', '3d9550b0-2413-49ab-9ad8-4c693a2ed77f', 75),
-- Task 4: Machines 2 or 3
('d742c69f-45d1-4252-8fdf-36515e37e94c', '374dc95b-cfae-4062-a3ff-56e58afdee95', 40),
('d742c69f-45d1-4252-8fdf-36515e37e94c', '3d9550b0-2413-49ab-9ad8-4c693a2ed77f', 50),
-- Task 5: Only on machine 3
('3746d432-0935-4b26-8991-26ebd2b0e4a5', '3d9550b0-2413-49ab-9ad8-4c693a2ed77f', 20);

-- Insert task modes for Job 2
INSERT INTO test_task_modes (task_id, machine_resource_id, duration_minutes) VALUES
-- Task 1: Setup on machine 1
('730a7563-0376-48cf-885e-d1dabae74f62', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 15),
-- Task 2: Branch A on machines 1 or 2
('45425b7b-e517-44d6-bdb4-175cd6543106', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 35),
('45425b7b-e517-44d6-bdb4-175cd6543106', '374dc95b-cfae-4062-a3ff-56e58afdee95', 30),
-- Task 3: Branch B (unattended) on machine 3
('9e671e01-3869-4b04-ae6c-138b2ac3f374', '3d9550b0-2413-49ab-9ad8-4c693a2ed77f', 90),
-- Task 4: Merge on machine 2
('e3147436-276e-4dff-afed-275113ed7520', '374dc95b-cfae-4062-a3ff-56e58afdee95', 55),
-- Task 5: Final assembly on machines 1 or 3
('8a5d08b3-0c53-443e-801a-ee64012bae92', '9881a89e-5c2e-4ce5-8878-61202ebe7ca3', 40),
('8a5d08b3-0c53-443e-801a-ee64012bae92', '3d9550b0-2413-49ab-9ad8-4c693a2ed77f', 45);

-- Insert precedences for Job 1 (Linear: 1->2->3->4->5)
INSERT INTO test_task_precedences (predecessor_task_id, successor_task_id) VALUES
('75dc92bb-3218-4b63-b791-f480b0440ce7', '7ddce8a5-a8fa-44cb-a036-211a1b544975'),
('7ddce8a5-a8fa-44cb-a036-211a1b544975', '66a69e18-8839-4bf0-9b76-f81e2c32cde1'),
('66a69e18-8839-4bf0-9b76-f81e2c32cde1', 'd742c69f-45d1-4252-8fdf-36515e37e94c'),
('d742c69f-45d1-4252-8fdf-36515e37e94c', '3746d432-0935-4b26-8991-26ebd2b0e4a5');

-- Insert precedences for Job 2 (Diamond: 1->2,3; 2,3->4; 4->5)
INSERT INTO test_task_precedences (predecessor_task_id, successor_task_id) VALUES
('730a7563-0376-48cf-885e-d1dabae74f62', '45425b7b-e517-44d6-bdb4-175cd6543106'),
('730a7563-0376-48cf-885e-d1dabae74f62', '9e671e01-3869-4b04-ae6c-138b2ac3f374'),
('45425b7b-e517-44d6-bdb4-175cd6543106', 'e3147436-276e-4dff-afed-275113ed7520'),
('9e671e01-3869-4b04-ae6c-138b2ac3f374', 'e3147436-276e-4dff-afed-275113ed7520'),
('e3147436-276e-4dff-afed-275113ed7520', '8a5d08b3-0c53-443e-801a-ee64012bae92');
