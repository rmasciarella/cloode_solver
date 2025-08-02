# Corrected Netlify Mass Upload Order

## CRITICAL: The app has TWO different concepts:
1. **Job Pattern Templates** (e.g., "OB3") - The template/pattern definition
2. **Job Instances** (e.g., "OB3.19", "OB3.20") - Specific jobs created from templates

## Correct Upload Order:

### Phase 1: Foundation (No Dependencies)
1. departments.csv
2. skills.csv
3. sequences.csv
4. business_calendars.csv
5. holiday_calendar.csv
6. maintenance_types.csv

### Phase 2: Job Pattern Templates
7. **First create the Job Pattern Template "OB3"** (manually or via different form)
   - This is NOT in our CSV files - needs to be created in the app first!

### Phase 3: Work Cells & Resources
8. work_cells.csv (depends on departments)
9. machines.csv (depends on work cells existing)
10. operators.csv (depends on departments and skills)

### Phase 4: Template Tasks & Precedences
11. template_tasks.csv (for the OB3 pattern)
12. template_precedences.csv (depends on template tasks)

### Phase 5: Job Instances
13. job_instances.csv (NOW you can upload job instances for template OB3)

### Phase 6: Advanced Configuration
14. task_modes.csv (depends on tasks and machines)
15. task_skill_requirements.csv (depends on tasks and skills)

## Key Insight:
The form showing "template_id" is asking for the PATTERN ID (like "OB3"), not the job UUID. You must create the job pattern template "OB3" in the system BEFORE uploading job instances.