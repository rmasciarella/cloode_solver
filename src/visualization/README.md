# Schedule Visualization Module

This module provides a web-based visualization for scheduling solutions, with full support for high-capacity machines where multiple tasks can run concurrently.

## Features

- **Interactive Gantt Chart**: Visualize tasks on a timeline with machines on the Y-axis
- **High-Capacity Machine Support**: Shows concurrent tasks as stacked bars on machines with capacity > 1
- **Capacity Validation**: Automatically detects and warns when machine capacity is exceeded
- **Rich Tooltips**: Hover over tasks to see detailed information
- **Machine Utilization**: Visual indicators showing how efficiently each machine is used
- **Export Capabilities**: Save the visualization as PNG for reports
- **Responsive Design**: Works on desktop and mobile devices
- **Zoom & Pan**: Navigate large schedules with intuitive controls

## Usage

### 1. Export Schedule Data

```python
from src.solver.data_models import SchedulingSolution, SchedulingProblem
from src.visualization.schedule_exporter import ScheduleExporter

# After solving your scheduling problem
exporter = ScheduleExporter()
exporter.export_to_json(solution, problem, "output/schedule.json")
```

### 2. View the Visualization

#### Option A: Using the built-in server
```bash
python src/visualization/serve.py
# Then open http://localhost:8000 in your browser
```

#### Option B: Direct file access
Simply open `src/visualization/static/index.html` in a modern web browser.

### 3. Load Your Schedule

1. Click the "Load Schedule" button
2. Select your exported JSON file
3. The visualization will automatically render

## Visual Features

### Machine Capacity Indicators

- **Single Capacity (1)**: Tasks appear as single bars
- **High Capacity (>1)**: Multiple tasks can run concurrently, shown as stacked bars
- Machine labels show capacity: "Assembly Station (3)"

### Color Coding

- Each job gets a unique color
- All tasks from the same job share the color
- Legend shows job-color mapping

### Warnings

If tasks exceed machine capacity at any time point, warnings appear at the top of the page with:
- The affected machine
- The time when capacity was exceeded
- List of conflicting tasks

### Controls

- **Zoom In/Out**: Use buttons or mouse wheel
- **Reset Zoom**: Return to default view
- **Show/Hide Labels**: Toggle task labels
- **Show/Hide Grid**: Toggle time grid lines

## File Formats

### JSON Export Format

```json
{
  "tasks": [
    {
      "job_id": 1,
      "job_name": "Assembly A",
      "task_id": 1,
      "task_name": "Cut Parts",
      "machine_id": 1,
      "machine_name": "CNC Machine",
      "machine_capacity": 1,
      "start_time": 0,
      "end_time": 4,
      "duration": 4,
      "color": "#FF6B6B"
    }
  ],
  "machines": [
    {
      "machine_id": 1,
      "machine_name": "CNC Machine",
      "capacity": 1,
      "utilization_percentage": 68.5,
      "total_busy_time": 58
    }
  ],
  "metadata": {
    "total_jobs": 4,
    "total_tasks": 10,
    "makespan": 85,
    "solve_time": 1.234,
    "solver_status": "OPTIMAL",
    "horizon": 85
  },
  "warnings": []
}
```

### CSV Export Format

For spreadsheet analysis, you can also export to CSV:

```python
exporter.export_to_csv(solution, problem, "output/schedule.csv")
```

## Browser Compatibility

The visualization works best on:
- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with SVG and ES6 support

## Development

### File Structure

```
src/visualization/
├── __init__.py
├── schedule_exporter.py    # Python module for exporting data
├── serve.py               # Simple HTTP server
├── README.md             # This file
└── static/
    ├── index.html        # Main HTML page
    ├── schedule_viewer.js # JavaScript visualization logic
    └── styles.css        # Styling
```

### Customization

- **Colors**: Edit the color palette in `schedule_exporter.py`
- **Styling**: Modify `styles.css` for visual appearance
- **Layout**: Adjust margins and dimensions in `schedule_viewer.js`

## Examples

See `examples/visualize_schedule.py` for a complete example that:
1. Creates a sample scheduling problem
2. Generates a solution with concurrent tasks
3. Exports to JSON and CSV
4. Demonstrates capacity warnings