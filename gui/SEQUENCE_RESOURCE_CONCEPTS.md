# Sequence Resource Concepts

## Overview
Sequence Resources represent specialized equipment, processes, or capabilities that require exclusive or controlled access during manufacturing operations. These are critical bottleneck resources that must be scheduled carefully to optimize throughput.

## Key Concepts

### **Capacity vs Max Concurrent Jobs**

#### **Capacity** 
- **Definition**: The total quantity/units of the resource available
- **Examples**:
  - **Testing Station**: 3 units (3 identical test setups)
  - **Oven**: 2 units (2 identical ovens)  
  - **Inspection Bay**: 1 unit (single specialized inspection station)
  - **Quality Control Lab**: 4 units (4 QC workstations)

#### **Max Concurrent Jobs**
- **Definition**: Maximum number of jobs that can use this resource simultaneously
- **Constraint**: Cannot exceed Capacity, but can be less for operational reasons

#### **Key Differences**:
```
Capacity = Physical units available
Max Concurrent Jobs = Operational scheduling limit

Examples:
- Capacity: 3, Max Concurrent: 2 → Have 3 units but only schedule 2 jobs at once
- Capacity: 1, Max Concurrent: 1 → Single exclusive resource  
- Capacity: 4, Max Concurrent: 4 → Full utilization allowed
```

#### **When Max Concurrent < Capacity**:
- **Maintenance Buffer**: Reserve 1 unit for maintenance
- **Quality Control**: Keep 1 unit for rush/priority jobs
- **Operator Limitations**: Not enough trained operators for all units
- **Power/Utility Constraints**: Can't run all units simultaneously

### **Resource Types**

#### **1. Exclusive Resources**
- **Definition**: Only ONE job can use the resource at a time
- **Characteristics**:
  - Capacity = 1, Max Concurrent = 1
  - Complete ownership during usage
  - No sharing or parallel access
- **Examples**:
  - **Opto**: Optical testing equipment (single precision instrument)
  - **BAT**: Battery testing station (requires exclusive access)
  - **Final QC**: Final quality inspection (one product at a time)
  - **Calibration Station**: Precision calibration equipment

#### **2. Shared Resources**  
- **Definition**: Multiple jobs can use the resource simultaneously up to capacity
- **Characteristics**:
  - Capacity ≥ 1, Max Concurrent ≤ Capacity
  - Jobs share the resource concurrently
  - Each job gets partial resource allocation
- **Examples**:
  - **Curing Oven**: Multiple products can cure together
  - **Paint Booth**: Multiple items painted in same batch
  - **Drying Chamber**: Multiple parts dry simultaneously
  - **Assembly Table**: Multiple operators work on different products

#### **3. Pooled Resources**
- **Definition**: Resource pool where jobs draw from available units
- **Characteristics**:
  - Capacity > 1, Max Concurrent = Capacity (typically)
  - Jobs allocated to any available unit in the pool
  - Dynamic assignment based on availability
- **Examples**:
  - **Test Stations**: Pool of 5 identical test setups
  - **Packaging Lines**: 3 interchangeable packaging stations
  - **QC Workstations**: Pool of quality control stations
  - **General Assembly**: Multiple identical workstations

## OR-Tools Constraint Integration

### **Exclusive Resources**:
```python
# Only one job can use the resource at any time
for resource in exclusive_resources:
    for time_slot in time_slots:
        model.Add(sum(job_uses_resource[job, resource, time_slot] 
                     for job in jobs) <= 1)
```

### **Shared Resources**:
```python  
# Multiple jobs can share up to max_concurrent limit
for resource in shared_resources:
    for time_slot in time_slots:
        model.Add(sum(job_uses_resource[job, resource, time_slot] 
                     for job in jobs) <= resource.max_concurrent_jobs)
```

### **Pooled Resources**:
```python
# Jobs assigned to any available unit in the pool
for resource in pooled_resources:
    for time_slot in time_slots:
        model.Add(sum(job_uses_resource[job, resource, time_slot] 
                     for job in jobs) <= resource.capacity)
```

## Setup and Teardown Times

### **Setup Time**
- **Purpose**: Time required to prepare resource for a specific job
- **Examples**:
  - Tool changeover: 15 minutes
  - Machine calibration: 30 minutes  
  - Test fixture setup: 5 minutes
  - Material loading: 10 minutes

### **Teardown Time**
- **Purpose**: Time required to clean/reset resource after job completion
- **Examples**:
  - Equipment cleaning: 10 minutes
  - Tool removal: 5 minutes
  - Results recording: 15 minutes
  - Quality verification: 20 minutes

### **OR-Tools Integration**:
```python
# Setup constraint: job can't start until setup is complete
model.Add(job_start[job] >= resource_setup_start[resource] + setup_time)

# Teardown constraint: resource not available until teardown complete  
model.Add(resource_available[resource] >= job_end[job] + teardown_time)
```

## Common Sequence Resource Examples

### **Manufacturing Examples**:
```
Resource: "Opto"
- Type: Exclusive (precision optical testing)
- Capacity: 1
- Max Concurrent: 1  
- Setup: 5 min (calibration)
- Teardown: 2 min (cleaning)

Resource: "Curing Oven"  
- Type: Shared
- Capacity: 12 (slots)
- Max Concurrent: 10 (reserve 2 for maintenance)
- Setup: 10 min (temperature stabilization)
- Teardown: 5 min (cooling)

Resource: "QC Stations"
- Type: Pooled  
- Capacity: 4 (identical stations)
- Max Concurrent: 4
- Setup: 3 min (test preparation)
- Teardown: 7 min (documentation)
```

## Best Practices

### **Resource Planning**:
1. **Identify Bottlenecks**: Focus on resources that limit throughput
2. **Capacity Planning**: Size capacity based on demand analysis
3. **Buffer Management**: Keep max_concurrent < capacity for flexibility
4. **Maintenance Windows**: Schedule regular maintenance slots

### **Constraint Optimization**:
1. **Priority Scheduling**: Use priority field for conflict resolution
2. **Utilization Targets**: Set realistic utilization goals (80-90%)
3. **Setup Minimization**: Group similar jobs to reduce setup times
4. **Load Balancing**: Distribute work across pooled resources

### **Form Field Guidelines**:
- **Capacity**: Physical resource units available
- **Max Concurrent Jobs**: Operational scheduling limit  
- **Resource Type**: Choose based on usage pattern
- **Setup/Teardown**: Include all preparation and cleanup time
- **Priority**: Higher values win resource conflicts
- **Utilization Target**: Realistic percentage for optimization