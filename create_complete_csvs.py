import pandas as pd
import csv

# Read source data
tasks_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/tasks.csv')
resources_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/resources.csv')
work_cells_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/work_cells.csv')
task_modes_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/task_modes.csv')
skills_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/skills.csv')
task_skill_req_df = pd.read_csv('/Users/quanta/projects/fresh_solver/supabase_data/task_skill_requirements.csv')

# Create mappings
task_id_to_name = dict(zip(tasks_df['task_id'], tasks_df['name']))
resource_id_to_name = dict(zip(resources_df['resource_id'], resources_df['name']))
cell_id_to_name = dict(zip(work_cells_df['cell_id'], work_cells_df['name']))
skill_id_to_name = dict(zip(skills_df['skill_id'], skills_df['name']))

# Process task modes
task_modes_output = []
for _, row in task_modes_df.iterrows():
    task_name = task_id_to_name.get(row['task_id'], '')
    work_cell_name = cell_id_to_name.get(row['cell_resource_id'], '')
    
    # Try to get machine name from resources first, if not found, check work_cells
    machine_name = resource_id_to_name.get(row['machine_resource_id'], '')
    if not machine_name:
        # Check if it's actually a work cell being used as machine
        machine_name = cell_id_to_name.get(row['machine_resource_id'], '')
        if machine_name:
            # Use a shortened version for machine name
            machine_name = machine_name.replace(' ', '_')
    
    duration_minutes = row['duration_15minutes'] * 15
    
    if task_name and work_cell_name and machine_name:
        mode_name = f"{machine_name} Mode"
        task_modes_output.append({
            'task_name': task_name,
            'mode_name': mode_name,
            'work_cell_name': work_cell_name,
            'machine_name': machine_name,
            'duration_minutes': duration_minutes,
            'setup_time_minutes': 0,
            'operators_required': 1,
            'description': f'{task_name} on {machine_name}'
        })

# Write task modes
with open('/Users/quanta/projects/fresh_solver/netlify_upload/task_modes.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['task_name', 'mode_name', 'work_cell_name', 'machine_name', 
                                           'duration_minutes', 'setup_time_minutes', 'operators_required', 'description'])
    writer.writeheader()
    writer.writerows(task_modes_output)

# Process task skill requirements
task_skill_output = []
for _, row in task_skill_req_df.iterrows():
    task_name = task_id_to_name.get(row['task_id'], '')
    skill_name = skill_id_to_name.get(row['skill'], '')
    
    if task_name and skill_name:
        task_skill_output.append({
            'task_name': task_name,
            'skill_name': skill_name,
            'minimum_skill_level': row['min_skill_level'],
            'preferred_skill_level': 3,
            'is_required': 'true'
        })

# Write task skill requirements
with open('/Users/quanta/projects/fresh_solver/netlify_upload/task_skill_requirements.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['task_name', 'skill_name', 'minimum_skill_level', 
                                           'preferred_skill_level', 'is_required'])
    writer.writeheader()
    writer.writerows(task_skill_output)

print(f"Created {len(task_modes_output)} task modes")
print(f"Created {len(task_skill_output)} task skill requirements")