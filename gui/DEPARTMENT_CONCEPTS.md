# Department Management Concepts

## Overview
The Department Management system supports hierarchical organizational structures for manufacturing and production scheduling. This document explains the key concepts and their intended use cases.

## Department Hierarchy

### Parent Department vs Child Departments

**Parent Department:**
- A top-level or mid-level department that contains other departments
- Used to create organizational hierarchy (e.g., "Manufacturing" → "Assembly", "Quality Control")
- Inherits scheduling constraints and resource pools from parent
- Examples: "Production", "Engineering", "Quality Assurance"

**Child Departments (Createable Departments):**
- Departments that report to a parent department
- Inherit default shift times, calendars, and policies from parent
- Can override parent settings when needed
- Examples: "Assembly Line A", "Testing Lab 1", "Packaging Station B"

### Hierarchy Benefits:
1. **Resource Inheritance**: Child departments automatically inherit parent resources and constraints
2. **Scheduling Efficiency**: OR-Tools can optimize across department boundaries while respecting hierarchy
3. **Reporting Structure**: Clear organizational reporting for capacity planning
4. **Constraint Propagation**: Parent department constraints (shift times, holidays) flow down to children

### Example Hierarchy:
```
Manufacturing (Parent)
├── Assembly (Child)
│   ├── Assembly Line A (Grandchild)
│   └── Assembly Line B (Grandchild)
├── Quality Control (Child)
│   ├── Incoming Inspection (Grandchild)
│   └── Final Testing (Grandchild)
└── Packaging (Child)
    ├── Packaging Line 1 (Grandchild)
    └── Packaging Line 2 (Grandchild)
```

## Cost Center Code

### What is a Cost Center?
A **Cost Center** is an accounting and management concept used to:
- Track expenses and resource allocation by organizational unit
- Enable financial reporting at department level
- Support budget planning and cost control
- Integrate with ERP/accounting systems

### Current Implementation:
- **Database Field**: `cost_center` (VARCHAR(50), optional)
- **GUI Field**: "Cost Center Code" 
- **Current Status**: ⚠️ **Not mapped to any specific functionality**

### Intended Use Cases:

#### 1. **Financial Integration** (Future Enhancement)
```sql
-- Example: Calculate department costs
SELECT 
    d.name as department_name,
    d.cost_center,
    SUM(ja.actual_cost) as total_cost
FROM departments d
JOIN job_instances ji ON ji.department_id = d.department_id  
JOIN instance_task_assignments ja ON ja.instance_id = ji.instance_id
WHERE d.cost_center = 'CC-PROD-001'
GROUP BY d.name, d.cost_center;
```

#### 2. **Resource Cost Allocation**
- Assign machine time costs to specific cost centers
- Track operator labor costs by department
- Allocate overhead expenses proportionally

#### 3. **Budget Constraint Integration**
```python
# Future OR-Tools integration example
def add_budget_constraints(model, tasks, departments):
    for dept in departments:
        if dept.cost_center and dept.budget_limit:
            dept_tasks = [t for t in tasks if t.department_id == dept.department_id]
            total_cost = sum(task.estimated_cost * task.is_scheduled for task in dept_tasks)
            model.Add(total_cost <= dept.budget_limit)
```

#### 4. **ERP System Integration**
- Map to SAP Cost Centers
- Oracle EBS Cost Center codes  
- Microsoft Dynamics cost tracking
- Custom ERP system integration

### Common Cost Center Naming Conventions:
- **Format**: `CC-[AREA]-[NUMBER]`
- **Examples**:
  - `CC-PROD-001` (Production Cost Center 1)
  - `CC-QC-001` (Quality Control Cost Center 1) 
  - `CC-MAINT-001` (Maintenance Cost Center 1)
  - `CC-ADMIN-001` (Administrative Cost Center 1)

### Recommendations for Implementation:

#### Phase 1: Basic Cost Tracking
1. Populate cost centers for all departments
2. Add cost center to job instance reporting
3. Create basic cost allocation queries

#### Phase 2: Budget Integration  
1. Add budget_limit field to departments table
2. Implement budget constraint checking in solver
3. Add budget utilization reporting

#### Phase 3: ERP Integration
1. API integration with ERP systems
2. Real-time cost center synchronization
3. Advanced financial reporting dashboard

## Time Input Improvements

### New Time Input System
The GUI now supports user-friendly time input with automatic conversion:

#### Input Format:
- **User sees**: `8:00 AM`, `2:30 PM`, `11:45 PM`
- **Database stores**: Integer index (0-95 for 15-minute intervals)
- **Conversion**: Automatic bidirectional conversion

#### Time Slot Mapping:
- **Index 0**: 12:00 AM (00:00)
- **Index 32**: 8:00 AM (08:00) - Default shift start
- **Index 64**: 4:00 PM (16:00) - Default shift end  
- **Index 95**: 11:45 PM (23:45) - Last slot of day

#### Benefits:
1. **User-Friendly**: Natural time format input
2. **Precise**: 15-minute interval accuracy
3. **Consistent**: Same time system across all forms
4. **Validated**: Prevents invalid time entries

### Updated Forms:
- ✅ **Department Form**: Shift start/end times
- ✅ **Business Calendar Form**: Working hours
- 🔄 **Operator Form**: Availability windows (future)
- 🔄 **Maintenance Form**: Maintenance windows (future)

## Database Schema Alignment

### Current Schema Support:
```sql
-- Departments table supports hierarchy
CREATE TABLE departments (
    department_id UUID PRIMARY KEY,
    parent_department_id UUID REFERENCES departments(department_id),
    cost_center VARCHAR(50),  -- Cost center code
    default_shift_start INTEGER DEFAULT 32,  -- 8 AM in 15-minute units  
    default_shift_end INTEGER DEFAULT 64,    -- 4 PM in 15-minute units
    -- ... other fields
);

-- Business calendars support time ranges
CREATE TABLE business_calendars (
    calendar_id UUID PRIMARY KEY,
    default_start_time INTEGER DEFAULT 32,  -- 8 AM
    default_end_time INTEGER DEFAULT 64,    -- 4 PM  
    -- ... other fields
);
```

### Constraint Integration:
The OR-Tools solver uses these time indices directly:
- **Shift Constraints**: `department.default_shift_start` to `department.default_shift_end`
- **Calendar Constraints**: `calendar.default_start_time` to `calendar.default_end_time`  
- **Resource Availability**: Time-based resource constraint generation

This ensures seamless integration between GUI time inputs and solver constraints.