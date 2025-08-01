# Fresh Solver GUI - Data Entry Interface

A comprehensive GUI application for managing data in the Fresh Solver OR-Tools constraint programming system.

## Features

### 🏢 Organizational Structure
- **Departments**: Manage organizational hierarchy with shift times and cost centers
- **Work Cells**: Configure production cells with capacity and WIP limits
- **Business Calendars**: Set up working hours and holiday schedules

### 📋 Templates & Jobs
- **Job Templates**: Create reusable job patterns for 5-8x performance improvements
- **Template Tasks**: Define tasks within templates with department assignments
- **Job Instances**: Create actual jobs based on templates

### 🔧 Resources
- **Machines**: Manage production machines with capacity, costs, and maintenance
- **Operators**: Track human resources with skills and availability
- **Skills**: Define capabilities required for task execution
- **Sequence Resources**: Manage exclusive access resources (Opto, BAT, etc.)

### ⚙️ Scheduling Data
- **Setup Times**: Configure changeover times between tasks (critical for constraints)
- **Maintenance**: Schedule planned maintenance windows
- **Precedences**: Define task dependencies within templates

## Installation

### Requirements
- Python 3.7 or higher
- Supabase account with database access

### Setup Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements_gui.txt
   ```

2. **Configure Database Connection**
   
   **Option A: .env File (Recommended)**
   - The GUI automatically loads from `.env` file in the project root
   - Your `.env` file is already configured with Supabase credentials
   - No additional setup required!
   
   **Option B: Environment Variables**
   ```bash
   export SUPABASE_URL="your_supabase_project_url"
   export SUPABASE_ANON_KEY="your_supabase_anon_key"
   ```
   
   **Option C: Manual Configuration**
   - The GUI will prompt for connection details on startup if no configuration found

3. **Run the Application**
   ```bash
   # Using the launcher (recommended)
   python run_gui.py
   
   # Or directly
   python gui_app.py
   ```

## Usage Guide

### Getting Started

1. **Connect to Database**
   - Database connection is automatic when using the `.env` file (already configured)
   - Or use `File → Connect to Database` to configure manually
   - Enter your Supabase URL and anonymous key if needed

2. **Navigate Data Categories**
   - Use the tree view on the left to select data types
   - Each category shows a specialized data entry form

3. **Enter Data**
   - Fill out form fields (required fields marked with *)
   - Click "Save" to store data in the database
   - Use "New" to clear the form for new entries

### Key Features

#### Department Management
- Set up organizational hierarchy
- Configure default shift times (in 15-minute units)
- Manage cost centers and overtime policies

#### Template Performance Optimization
- Create job templates for reusable patterns
- Configure blessed CP-SAT solver parameters
- Track performance metrics and speedup factors

#### Setup Times (Critical for Solver)
- Define changeover times between template tasks
- Support for product family patterns (A→B = 15 min, B→A = 30 min)
- Complexity levels and cost tracking

#### Machine Resource Management
- Track machine capacity and costs
- Integrate with maintenance scheduling
- Department and work cell assignments

### Keyboard Shortcuts
- `Ctrl+S`: Save current form
- `Ctrl+N`: New record
- `F5`: Refresh data view

## Database Schema Integration

The GUI is designed to work with the comprehensive Fresh Solver database schema including:

- ✅ **16 Critical Performance Indexes** for fast data access
- ✅ **Production-Ready Stored Procedures** for solver integration
- ✅ **Template Performance Tracking** with regression detection
- ✅ **Comprehensive Maintenance System** beyond basic windows
- ✅ **Setup Times Tables** with exact constraint interface match

## Architecture

### Core Components

1. **gui_app.py**: Main application with core forms
2. **gui_forms.py**: Extended forms for complex tables
3. **run_gui.py**: Launcher script with environment checking

### Design Patterns

- **Mixin Architecture**: Modular form components
- **Database Manager**: Centralized Supabase operations
- **Validation Framework**: Form-specific data validation
- **Error Handling**: Comprehensive exception management

### Data Flow

```
User Input → Form Validation → Database Manager → Supabase → Schema Tables
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify Supabase URL and key
   - Check network connectivity
   - Ensure database permissions

2. **Import Errors**
   - Run `pip install -r requirements_gui.txt`
   - Check Python version (3.7+ required)

3. **Form Validation Errors**
   - Required fields must be filled
   - Numeric fields require valid numbers
   - Time fields use 15-minute units (0-95)

### Debug Mode

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Adding New Forms

1. Create form class in `gui_forms.py`
2. Add mixin to `FreshSolverGUI` class
3. Update navigation tree in `populate_navigation_tree()`
4. Add table columns in `get_table_columns()`

### Database Schema Changes

The GUI automatically adapts to schema changes through:
- Dynamic column detection
- Flexible form generation
- Generic fallback forms

## Performance Considerations

### Optimized for Large Datasets
- Lazy loading of dropdown data
- Paginated record lists
- Efficient query patterns

### Template Mode Support
- 5-8x performance improvements
- Blessed parameter management
- Performance regression detection

## Security

### Data Protection
- Read-only anonymous key usage
- Input validation and sanitization
- SQL injection prevention through Supabase client

### Best Practices
- Store credentials in environment variables
- Use least-privilege database access
- Regular security updates

## Contributing

### Code Style
- Follow PEP 8 conventions
- Use type hints for new functions
- Add docstrings for public methods

### Testing
- Test forms with sample data
- Validate database operations
- Check error handling paths

## Support

For issues and questions:
1. Check this documentation
2. Review error logs
3. Consult the main Fresh Solver documentation
4. Create GitHub issues for bugs

## License

This GUI is part of the Fresh Solver project and follows the same licensing terms.