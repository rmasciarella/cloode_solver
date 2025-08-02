# Netlify Mass Upload Order

## IMPORTANT: Upload files in this exact order to avoid dependency errors

### 1. Foundation Data (No Dependencies)
- [ ] departments.csv
- [ ] skills.csv
- [ ] sequences.csv
- [ ] business_calendars.csv
- [ ] holiday_calendar.csv
- [ ] maintenance_types.csv

### 2. Work Cells (Depends on Departments)
- [ ] work_cells.csv

### 3. Resources (Depends on Work Cells)
- [ ] machines.csv (ONLY AFTER work_cells are uploaded!)
- [ ] operators.csv (Depends on Departments and Skills)

### 4. Templates (Depends on basic data)
- [ ] job_templates.csv
- [ ] template_tasks.csv (Depends on Departments, Sequences)
- [ ] template_precedences.csv (Depends on template_tasks)

### 5. Advanced Configurations (Depends on Tasks and Resources)
- [ ] task_modes.csv (Depends on Tasks, Work Cells, Machines)
- [ ] task_skill_requirements.csv (Depends on Tasks, Skills)

## Common Issues:
1. Machines MUST be uploaded AFTER work cells exist
2. Work cells reference department IDs that must exist
3. Task modes need both tasks and machines to exist
4. All UUID references must point to existing records

## Current Problem:
The machines.csv upload is failing because work cells haven't been created yet. 
Upload work_cells.csv first, then try machines.csv again.