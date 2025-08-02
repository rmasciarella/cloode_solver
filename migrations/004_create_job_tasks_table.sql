-- Create job_tasks table for the Job Tasks form
CREATE TABLE IF NOT EXISTS job_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES job_instances(instance_id) ON DELETE CASCADE,
    template_task_id UUID NOT NULL REFERENCES template_tasks(template_task_id),
    selected_mode_id UUID REFERENCES template_task_modes(template_task_mode_id),
    assigned_machine_id UUID REFERENCES machines(machine_resource_id),
    
    -- Timing data (in minutes)
    start_time_minutes INTEGER CHECK (start_time_minutes >= 0),
    end_time_minutes INTEGER CHECK (end_time_minutes >= 0),
    actual_duration_minutes INTEGER CHECK (actual_duration_minutes >= 0),
    setup_time_minutes INTEGER NOT NULL DEFAULT 0 CHECK (setup_time_minutes >= 0),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure end time is after start time if both are set
    CONSTRAINT valid_time_range CHECK (
        (start_time_minutes IS NULL OR end_time_minutes IS NULL) OR 
        (end_time_minutes > start_time_minutes)
    ),
    
    -- Unique constraint to prevent duplicate task assignments
    CONSTRAINT unique_instance_task UNIQUE (instance_id, template_task_id)
);

-- Create indexes for performance
CREATE INDEX idx_job_tasks_instance_id ON job_tasks(instance_id);
CREATE INDEX idx_job_tasks_template_task_id ON job_tasks(template_task_id);
CREATE INDEX idx_job_tasks_assigned_machine_id ON job_tasks(assigned_machine_id);
CREATE INDEX idx_job_tasks_selected_mode_id ON job_tasks(selected_mode_id);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_tasks_updated_at BEFORE UPDATE
    ON job_tasks FOR EACH ROW EXECUTE PROCEDURE 
    update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE job_tasks IS 'Task assignments for job instances, linking template tasks to specific job runs';
COMMENT ON COLUMN job_tasks.task_id IS 'Unique identifier for the job task assignment';
COMMENT ON COLUMN job_tasks.instance_id IS 'Reference to the job instance this task belongs to';
COMMENT ON COLUMN job_tasks.template_task_id IS 'Reference to the template task being assigned';
COMMENT ON COLUMN job_tasks.selected_mode_id IS 'Optional: specific mode selected for this task execution';
COMMENT ON COLUMN job_tasks.assigned_machine_id IS 'Optional: machine assigned for this task';
COMMENT ON COLUMN job_tasks.start_time_minutes IS 'Scheduled start time in minutes from job start';
COMMENT ON COLUMN job_tasks.end_time_minutes IS 'Scheduled end time in minutes from job start';
COMMENT ON COLUMN job_tasks.actual_duration_minutes IS 'Actual duration taken to complete the task';
COMMENT ON COLUMN job_tasks.setup_time_minutes IS 'Setup time required before task execution';