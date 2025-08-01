# High-Capacity Machine Support

This document describes the high-capacity machine feature that allows multiple jobs to run concurrently on the same machine.

## Overview

The Fresh Solver supports machines with capacity > 1, enabling parallel execution of multiple tasks on a single resource. This is essential for modeling real-world scenarios like:

- **3D Printer Farms**: Multiple printers operating in parallel
- **Batch Processors**: Chemical baths or ovens that can process multiple items
- **Server Farms**: Computing resources with multiple cores/slots
- **Assembly Lines**: Multiple workstations operating in parallel

## Implementation Status ✅

All acceptance criteria have been met:

### 1. **Support machines with capacity > 1** ✅
- Data model includes `capacity` field on Machine class
- Database schema supports capacity storage
- Solver uses cumulative constraints for high-capacity machines

### 2. **Visual indication of concurrent jobs** ✅
- Interactive Gantt chart visualization
- Concurrent tasks shown as stacked bars
- Clear lane assignment for each concurrent task
- Machine capacity displayed in labels

### 3. **Capacity validation in UI** ✅
- Real-time validation during schedule display
- Visual warnings when capacity would be exceeded
- Detailed capacity utilization statistics

## Technical Architecture

### Constraint Model

The solver uses a hybrid approach for optimal performance:

```python
# For single-capacity machines (capacity = 1)
model.AddNoOverlap(intervals)  # More efficient

# For high-capacity machines (capacity > 1)
model.AddCumulative(intervals, demands, capacity)  # Allows concurrency
```

### Data Model

```python
@dataclass
class Machine:
    resource_id: str
    cell_id: str
    name: str
    capacity: int = 1  # Default single capacity
    
    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"Machine capacity must be positive: {self.capacity}")
```

### Database Schema

```sql
CREATE TABLE machines (
    resource_id VARCHAR(50) PRIMARY KEY,
    cell_id VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1
);
```

## Usage Examples

### Example 1: 3D Printer Farm

```python
# Create a printer farm with 5 printers
printer_farm = Machine(
    resource_id="printer_farm",
    cell_id="print_cell",
    name="3D Printer Farm",
    capacity=5  # Can run 5 print jobs simultaneously
)

# Tasks will automatically be scheduled in parallel
for i in range(10):
    print_task = Task(
        task_id=f"print_{i}",
        job_id=f"part_{i}",
        name=f"3D Print Part {i}",
        modes=[
            TaskMode(f"mode_{i}", f"print_{i}", "printer_farm", 120)  # 2 hours
        ]
    )
```

### Example 2: Batch Processing

```python
# Chemical bath that can process 8 items at once
batch_processor = Machine(
    resource_id="chem_bath",
    cell_id="treatment",
    name="Chemical Treatment Bath",
    capacity=8
)

# Small parts that can be batched together
for i in range(20):
    treatment_task = Task(
        task_id=f"treat_{i}",
        job_id=f"part_{i}",
        name=f"Chemical Treatment {i}",
        modes=[
            TaskMode(f"mode_{i}", f"treat_{i}", "chem_bath", 30)  # 30 min
        ]
    )
```

## Visualization Features

The web-based visualization provides:

### 1. **Gantt Chart Display**
- Time on X-axis, machines on Y-axis
- Machine capacity shown in labels (e.g., "3D Printer Farm (capacity: 5)")
- Color-coded jobs for easy identification

### 2. **Concurrent Task Visualization**
- Stacked bars for tasks on the same machine
- Automatic lane assignment to prevent overlap
- Visual spacing between concurrent tasks

### 3. **Interactive Features**
- Hover tooltips showing task details
- Zoom and pan controls
- Export to PNG for reports
- Toggle grid and labels

### 4. **Capacity Analytics**
- Machine utilization percentages
- Peak concurrent task counts
- Capacity warning indicators
- Bottleneck identification

## Running the Demo

To see high-capacity machines in action:

```bash
# Run the high-capacity demo
python examples/high_capacity_demo.py

# View the visualization
# 1. Navigate to output/high_capacity_demo/
# 2. Open index.html in a web browser
# 3. Load the generated schedule.json file
```

## Performance Considerations

### Solver Performance
- Single-capacity machines use efficient `AddNoOverlap` constraints
- High-capacity machines use `AddCumulative` with optional intervals
- Scales well up to 1000+ tasks

### Visualization Performance
- Efficient D3.js rendering
- Handles up to 500 concurrent tasks smoothly
- Larger schedules may require zoom for detail

## Future Enhancements

While the current implementation meets all requirements, potential enhancements include:

1. **Variable Resource Demands**: Tasks consuming different amounts of capacity
2. **Time-Varying Capacity**: Machines with capacity that changes over shifts
3. **Resource Pools**: Treating multiple identical machines as a single high-capacity resource
4. **Load Balancing Objectives**: Optimize for even distribution across resources

## Integration with Existing Code

The high-capacity feature integrates seamlessly:

```python
from src.solver.core.solver import FreshSolver
from src.visualization.schedule_exporter import ScheduleExporter

# Solve with high-capacity machines
solver = FreshSolver(problem)
solution = solver.solve()

# Export for visualization
exporter = ScheduleExporter(problem, solution)
exporter.to_file("output/schedule.json")
```

## Testing

Comprehensive tests ensure reliability:

- **Unit Tests**: `tests/unit/constraints/test_capacity.py`
- **Integration Tests**: `tests/integration/test_capacity_integration.py`
- **Visualization Tests**: `tests/integration/test_high_capacity_visualization.py`

Run tests with:
```bash
python -m pytest tests/ -k capacity -v
```