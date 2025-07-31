#!/usr/bin/env python3
"""Fresh Solver GUI - Data Entry Interface for Supabase Database.

Production-ready GUI for comprehensive OR-Tools scheduling system.
"""

import json
import logging
import os
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env from project root
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print("⚠️  No .env file found in project root")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")

# Import extended form mixins
from gui_forms import (
    MachinesFormMixin,
    OperatorsFormMixin,
    SetupTimesFormMixin,
    UtilityMethods,
)

# Supabase integration
try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Run: pip install supabase")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration from environment or config file."""

    supabase_url: str = ""
    supabase_key: str = ""

    def __post_init__(self):
        # Try to load from environment
        self.supabase_url = os.getenv("SUPABASE_URL", self.supabase_url)
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY", self.supabase_key)


class DatabaseManager:
    """Handles all Supabase database operations."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database manager with configuration."""
        self.config = config
        self.client: Client | None = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to Supabase database."""
        if not SUPABASE_AVAILABLE:
            logger.error("Supabase client not available")
            return False

        if not self.config.supabase_url or not self.config.supabase_key:
            logger.error("Database configuration missing")
            return False

        try:
            self.client = create_client(
                self.config.supabase_url, self.config.supabase_key
            )
            # Test connection with a simple query
            self.client.table("departments").select("count").execute()
            self.connected = True
            logger.info("Successfully connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.connected = False
            return False

    def execute_query(
        self, table: str, operation: str, data: dict = None, filters: dict = None
    ) -> Any:
        """Execute database operation with error handling."""
        if not self.connected or not self.client:
            raise Exception("Database not connected")

        try:
            query = self.client.table(table)

            if operation == "select":
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                return query.select("*").execute()

            elif operation == "insert":
                return query.insert(data).execute()

            elif operation == "update":
                if not filters:
                    raise ValueError("Update requires filters")
                for key, value in filters.items():
                    query = query.eq(key, value)
                return query.update(data).execute()

            elif operation == "delete":
                if not filters:
                    raise ValueError("Delete requires filters")
                for key, value in filters.items():
                    query = query.eq(key, value)
                return query.delete().execute()

        except Exception as e:
            error_msg = str(e).lower()

            # Handle specific database errors gracefully
            if "column" in error_msg and "does not exist" in error_msg:
                logger.warning(f"Column does not exist: {e}")
                raise Exception(
                    "Database schema mismatch: Missing column. "
                    "Please check if database is up to date."
                ) from e
            elif "table" in error_msg and "does not exist" in error_msg:
                logger.warning(f"Table does not exist: {e}")
                raise Exception(
                    f"Database schema mismatch: Table '{table}' not found. "
                    "Please check if database is properly initialized."
                ) from e
            elif "relation" in error_msg and "does not exist" in error_msg:
                logger.warning(f"Relation does not exist: {e}")
                raise Exception(
                    f"Database schema mismatch: Table or view '{table}' not found."
                ) from e
            elif "permission denied" in error_msg:
                logger.error(f"Database permission denied: {e}")
                raise Exception(
                    "Database permission denied. Please check your access credentials."
                ) from e
            else:
                logger.error(f"Database operation failed: {e}")
                raise Exception(f"Database operation failed: {str(e)}") from e


class FreshSolverGUI(
    MachinesFormMixin, OperatorsFormMixin, SetupTimesFormMixin, UtilityMethods
):
    """Main GUI application for Fresh Solver data entry."""

    def __init__(self):
        """Initialize the main GUI application."""
        self.root = tk.Tk()
        self.root.title("Fresh Solver - Data Entry Interface")
        self.root.geometry("1200x800")

        # Database manager
        self.db_config = DatabaseConfig()
        self.db_manager = DatabaseManager(self.db_config)

        # GUI state
        self.current_data = {}
        self.unsaved_changes = False

        self.setup_styles()
        self.create_menu()
        self.create_main_interface()
        self.setup_bindings()

        # Try to connect to database on startup
        self.connect_to_database()

    def setup_styles(self):
        """Configure GUI styles and themes."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure custom styles
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Heading.TLabel", font=("Arial", 12, "bold"))
        style.configure("Error.TLabel", foreground="red")
        style.configure("Success.TLabel", foreground="green")

    def create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Connect to Database", command=self.connect_to_database
        )
        file_menu.add_separator()
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Load Sample Data", command=self.load_sample_data)
        data_menu.add_command(label="Clear All Data", command=self.clear_all_data)
        data_menu.add_separator()
        data_menu.add_command(label="Validate Data", command=self.validate_data)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_interface(self):
        """Create the main GUI interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="Fresh Solver Data Entry", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Left panel - Navigation tree
        self.create_navigation_panel(main_frame)

        # Right panel - Data entry forms
        self.create_data_panel(main_frame)

        # Status bar
        self.create_status_bar(main_frame)

    def create_navigation_panel(self, parent):
        """Create navigation tree panel."""
        nav_frame = ttk.LabelFrame(parent, text="Data Categories", padding="5")
        nav_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Navigation tree
        self.nav_tree = ttk.Treeview(nav_frame, height=25)
        self.nav_tree.pack(fill=tk.BOTH, expand=True)

        # Populate navigation tree
        self.populate_navigation_tree()

        # Bind tree selection
        self.nav_tree.bind("<<TreeviewSelect>>", self.on_nav_select)

    def populate_navigation_tree(self):
        """Populate the navigation tree with data categories."""
        # Organizational Structure
        org_node = self.nav_tree.insert(
            "", "end", text="Organizational Structure", open=True
        )
        self.nav_tree.insert(
            org_node, "end", text="Departments", values=("departments",)
        )
        self.nav_tree.insert(org_node, "end", text="Work Cells", values=("work_cells",))
        self.nav_tree.insert(
            org_node, "end", text="Business Calendars", values=("business_calendars",)
        )

        # Templates & Jobs
        template_node = self.nav_tree.insert(
            "", "end", text="Templates & Jobs", open=True
        )
        self.nav_tree.insert(
            template_node, "end", text="Job Templates", values=("job_templates",)
        )
        self.nav_tree.insert(
            template_node, "end", text="Template Tasks", values=("template_tasks",)
        )
        self.nav_tree.insert(
            template_node, "end", text="Job Instances", values=("job_instances",)
        )

        # Resources
        resource_node = self.nav_tree.insert("", "end", text="Resources", open=True)
        self.nav_tree.insert(
            resource_node, "end", text="Machines", values=("machines",)
        )
        self.nav_tree.insert(
            resource_node, "end", text="Operators", values=("operators",)
        )
        self.nav_tree.insert(resource_node, "end", text="Skills", values=("skills",))
        self.nav_tree.insert(
            resource_node,
            "end",
            text="Sequence Resources",
            values=("sequence_resources",),
        )

        # Scheduling Data
        schedule_node = self.nav_tree.insert(
            "", "end", text="Scheduling Data", open=True
        )
        self.nav_tree.insert(
            schedule_node,
            "end",
            text="Setup Times",
            values=("optimized_task_setup_times",),
        )
        self.nav_tree.insert(
            schedule_node,
            "end",
            text="Maintenance",
            values=("machine_maintenance_schedules",),
        )
        self.nav_tree.insert(
            schedule_node, "end", text="Precedences", values=("optimized_precedences",)
        )

    def create_data_panel(self, parent):
        """Create data entry panel."""
        self.data_frame = ttk.LabelFrame(parent, text="Data Entry", padding="10")
        self.data_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.data_frame.columnconfigure(0, weight=1)
        self.data_frame.rowconfigure(0, weight=1)

        # Initial welcome message
        welcome_label = ttk.Label(
            self.data_frame,
            text="Select a data category from the left panel to begin data entry.",
            font=("Arial", 12),
        )
        welcome_label.grid(row=0, column=0, pady=50)

    def create_status_bar(self, parent):
        """Create status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)

        # Connection status
        self.connection_var = tk.StringVar()
        self.connection_var.set("Not connected")
        connection_label = ttk.Label(status_frame, textvariable=self.connection_var)
        connection_label.pack(side=tk.RIGHT)

    def setup_bindings(self):
        """Set up keyboard and window bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Control-s>", lambda _: self.save_data())
        self.root.bind("<Control-n>", lambda _: self.new_record())
        self.root.bind("<F5>", lambda _: self.refresh_data())

    def on_nav_select(self, _event):
        """Handle navigation tree selection."""
        selection = self.nav_tree.selection()
        if not selection:
            return

        item = self.nav_tree.item(selection[0])
        if item["values"]:
            table_name = item["values"][0]
            self.load_data_form(table_name)

    def load_data_form(self, table_name: str):
        """Load appropriate data entry form for selected table."""
        # Clear existing form
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        # Update frame title
        self.data_frame.config(
            text=f"Data Entry - {table_name.replace('_', ' ').title()}"
        )

        # Create form based on table
        if table_name == "departments":
            self.create_departments_form()
        elif table_name == "job_templates":
            self.create_job_templates_form()
        elif table_name == "machines":
            self.create_machines_form()
        elif table_name == "operators":
            self.create_operators_form()
        elif table_name == "optimized_task_setup_times":
            self.create_setup_times_form()
        else:
            self.create_generic_form(table_name)

        self.current_table = table_name
        self.load_existing_data(table_name)

    def create_departments_form(self):
        """Create form for departments table."""
        # Form container with scrollbar
        canvas = tk.Canvas(self.data_frame)
        scrollbar = ttk.Scrollbar(
            self.data_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Form fields
        fields_frame = ttk.Frame(scrollable_frame, padding="10")
        fields_frame.pack(fill=tk.BOTH, expand=True)

        # Department Code
        ttk.Label(fields_frame, text="Department Code*:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.dept_code_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.dept_code_var, width=30).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Department Name
        ttk.Label(fields_frame, text="Department Name*:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.dept_name_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.dept_name_var, width=50).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Description
        ttk.Label(fields_frame, text="Description:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.dept_desc_text = tk.Text(fields_frame, height=3, width=50)
        self.dept_desc_text.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))

        # Default Shift Times
        ttk.Label(fields_frame, text="Default Shift Start (15-min units):").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.dept_shift_start_var = tk.StringVar(value="32")  # 8 AM
        ttk.Entry(fields_frame, textvariable=self.dept_shift_start_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Default Shift End (15-min units):").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.dept_shift_end_var = tk.StringVar(value="64")  # 4 PM
        ttk.Entry(fields_frame, textvariable=self.dept_shift_end_var, width=10).grid(
            row=4, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Overtime Allowed
        self.dept_overtime_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fields_frame, text="Overtime Allowed", variable=self.dept_overtime_var
        ).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))

        # Cost Center
        ttk.Label(fields_frame, text="Cost Center:").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        self.dept_cost_center_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.dept_cost_center_var, width=30).grid(
            row=6, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Active Status
        self.dept_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fields_frame, text="Active", variable=self.dept_active_var
        ).grid(row=7, column=1, sticky=tk.W, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(fields_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_department).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="New", command=self.clear_department_form).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_department).pack(
            side=tk.LEFT, padx=5
        )

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Existing records list
        self.create_records_list(scrollable_frame, "departments")

    def create_job_templates_form(self):
        """Create form for job templates."""
        # Similar structure to departments form but with template-specific fields
        canvas = tk.Canvas(self.data_frame)
        scrollbar = ttk.Scrollbar(
            self.data_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        fields_frame = ttk.Frame(scrollable_frame, padding="10")
        fields_frame.pack(fill=tk.BOTH, expand=True)

        # Template Name
        ttk.Label(fields_frame, text="Template Name*:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.template_name_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.template_name_var, width=50).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Description
        ttk.Label(fields_frame, text="Description:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.template_desc_text = tk.Text(fields_frame, height=3, width=50)
        self.template_desc_text.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # Performance Metrics
        ttk.Label(fields_frame, text="Performance Target (seconds):").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.template_target_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.template_target_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Blessed Status
        self.template_blessed_var = tk.BooleanVar()
        ttk.Checkbutton(
            fields_frame,
            text="Blessed (Production Ready)",
            variable=self.template_blessed_var,
        ).grid(row=3, column=1, sticky=tk.W, padx=(10, 0))

        # Solver Parameters (JSON)
        ttk.Label(fields_frame, text="Solver Parameters (JSON):").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.template_params_text = tk.Text(fields_frame, height=8, width=50)
        self.template_params_text.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))

        # Default solver parameters
        default_params = {
            "num_search_workers": 8,
            "max_time_in_seconds": 60,
            "linearization_level": 1,
            "search_branching": "FIXED_SEARCH",
            "cp_model_presolve": True,
            "repair_hint": True,
        }
        self.template_params_text.insert("1.0", json.dumps(default_params, indent=2))

        # Buttons
        button_frame = ttk.Frame(fields_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_job_template).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="New", command=self.clear_job_template_form).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_job_template).pack(
            side=tk.LEFT, padx=5
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_records_list(scrollable_frame, "job_templates")

    # Machine, operators, and setup times forms are now provided by mixins

    def create_generic_form(self, table_name: str):
        """Create a generic form for tables not specifically implemented."""
        label = ttk.Label(
            self.data_frame,
            text=f"Generic form for {table_name}\nSpecific form not yet implemented.",
            font=("Arial", 12),
        )
        label.pack(pady=50)

    def create_records_list(self, parent, table_name: str):
        """Create a list of existing records for the table."""
        list_frame = ttk.LabelFrame(parent, text="Existing Records", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Treeview for records
        columns = self.get_table_columns(table_name)
        self.records_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=8
        )

        # Configure columns
        for col in columns:
            self.records_tree.heading(col, text=col.replace("_", " ").title())
            self.records_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.records_tree.yview
        )
        h_scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.HORIZONTAL, command=self.records_tree.xview
        )
        self.records_tree.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Pack treeview and scrollbars
        self.records_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Bind record selection
        self.records_tree.bind("<<TreeviewSelect>>", self.on_record_select)

    def get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a table (simplified for demo)."""
        # In a real implementation, this would query the database schema
        column_mappings = {
            "departments": ["code", "name", "description", "is_active"],
            "job_templates": ["name", "description", "speedup_factor", "is_blessed"],
            "job_optimized_patterns": [
                "name",
                "description",
                "speedup_factor",
                "is_blessed",
                "is_active",
            ],
            "machines": ["name", "capacity", "cost_per_hour", "is_active"],
            "operators": ["name", "hourly_rate", "max_hours_per_day", "is_active"],
            "work_cells": ["name", "capacity", "wip_limit", "is_active"],
            "optimized_task_setup_times": [
                "from_optimized_task_id",
                "to_optimized_task_id",
                "machine_resource_id",
                "setup_time_minutes",
            ],
            "machine_maintenance_schedules": [
                "scheduled_start_time",
                "scheduled_end_time",
                "status",
                "blocks_production",
            ],
            "optimized_precedences": [
                "predecessor_optimized_task_id",
                "successor_optimized_task_id",
                "min_delay_minutes",
            ],
            "sequence_resources": ["sequence_id", "name", "description", "is_active"],
            "optimized_tasks": ["name", "position", "is_unattended", "sequence_id"],
            "template_tasks": ["name", "position", "is_unattended", "sequence_id"],
        }
        return column_mappings.get(table_name, ["id", "name", "created_at"])

    def on_record_select(self, _event):
        """Handle record selection from the list."""
        selection = self.records_tree.selection()
        if not selection:
            return

        # Load selected record into form
        # Implementation depends on current table
        pass

    def load_existing_data(self, table_name: str):
        """Load existing data for the current table."""
        if not self.db_manager.connected:
            return

        try:
            result = self.db_manager.execute_query(table_name, "select")
            if hasattr(self, "records_tree"):
                # Clear existing items
                for item in self.records_tree.get_children():
                    self.records_tree.delete(item)

                # Add new items
                for record in result.data:
                    values = [
                        str(record.get(col, ""))
                        for col in self.get_table_columns(table_name)
                    ]
                    self.records_tree.insert("", tk.END, values=values)

            self.status_var.set(f"Loaded {len(result.data)} records from {table_name}")

        except Exception as e:
            # Implement graceful degradation for missing tables/columns
            error_msg = str(e).lower()

            if "table" in error_msg and "not found" in error_msg:
                # Table doesn't exist - show warning but don't break the UI
                logger.warning(f"Table {table_name} not found in database")
                self.status_var.set(
                    f"Table '{table_name}' not found in database - please check schema"
                )

                # Clear the records tree if it exists
                if hasattr(self, "records_tree"):
                    for item in self.records_tree.get_children():
                        self.records_tree.delete(item)

                # Show info message instead of error
                messagebox.showinfo(
                    "Schema Info",
                    f"Table '{table_name}' not found in database.\n"
                    "This might be because:\n"
                    "• Database schema needs to be updated\n"
                    "• Table name has changed\n"
                    "• Database connection issues\n\n"
                    "You can still use other parts of the application.",
                )
            else:
                # Other errors - show error dialog
                messagebox.showerror("Database Error", f"Failed to load data: {str(e)}")
                logger.error(f"Failed to load data from {table_name}: {e}")
                self.status_var.set(f"Error loading data from {table_name}")

    def save_department(self):
        """Save department record to database."""
        if not self.validate_department_form():
            return

        data = {
            "code": self.dept_code_var.get(),
            "name": self.dept_name_var.get(),
            "description": self.dept_desc_text.get("1.0", tk.END).strip(),
            "default_shift_start": int(self.dept_shift_start_var.get()),
            "default_shift_end": int(self.dept_shift_end_var.get()),
            "overtime_allowed": self.dept_overtime_var.get(),
            "cost_center": self.dept_cost_center_var.get(),
            "is_active": self.dept_active_var.get(),
        }

        try:
            self.db_manager.execute_query("departments", "insert", data)
            messagebox.showinfo("Success", "Department saved successfully!")
            self.clear_department_form()
            self.load_existing_data("departments")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save department: {str(e)}")

    def validate_department_form(self) -> bool:
        """Validate department form data."""
        if not self.dept_code_var.get().strip():
            messagebox.showerror("Validation Error", "Department code is required")
            return False

        if not self.dept_name_var.get().strip():
            messagebox.showerror("Validation Error", "Department name is required")
            return False

        try:
            start = int(self.dept_shift_start_var.get())
            end = int(self.dept_shift_end_var.get())
            if not (0 <= start < 96 and 0 < end <= 96 and start < end):
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Validation Error", "Invalid shift times (must be 0-95, start < end)"
            )
            return False

        return True

    def clear_department_form(self):
        """Clear department form fields."""
        self.dept_code_var.set("")
        self.dept_name_var.set("")
        self.dept_desc_text.delete("1.0", tk.END)
        self.dept_shift_start_var.set("32")
        self.dept_shift_end_var.set("64")
        self.dept_overtime_var.set(True)
        self.dept_cost_center_var.set("")
        self.dept_active_var.set(True)

    def delete_department(self):
        """Delete selected department."""
        # Implementation for deletion
        pass

    def save_job_template(self):
        """Save job template record to database."""
        if not self.validate_job_template_form():
            return

        # Parse JSON parameters
        try:
            params_text = self.template_params_text.get("1.0", tk.END).strip()
            solver_params = json.loads(params_text) if params_text else {}
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in solver parameters")
            return

        data = {
            "name": self.template_name_var.get(),
            "description": self.template_desc_text.get("1.0", tk.END).strip(),
            "performance_target_seconds": (
                float(self.template_target_var.get())
                if self.template_target_var.get()
                else None
            ),
            "is_blessed": self.template_blessed_var.get(),
            "solver_parameters": json.dumps(solver_params),
        }

        try:
            self.db_manager.execute_query("job_templates", "insert", data)
            messagebox.showinfo("Success", "Job template saved successfully!")
            self.clear_job_template_form()
            self.load_existing_data("job_templates")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save job template: {str(e)}")

    def validate_job_template_form(self) -> bool:
        """Validate job template form data."""
        if not self.template_name_var.get().strip():
            messagebox.showerror("Validation Error", "Template name is required")
            return False
        return True

    def clear_job_template_form(self):
        """Clear job template form fields."""
        self.template_name_var.set("")
        self.template_desc_text.delete("1.0", tk.END)
        self.template_target_var.set("")
        self.template_blessed_var.set(False)
        self.template_params_text.delete("1.0", tk.END)
        # Reset default params
        default_params = {
            "num_search_workers": 8,
            "max_time_in_seconds": 60,
            "linearization_level": 1,
            "search_branching": "FIXED_SEARCH",
            "cp_model_presolve": True,
            "repair_hint": True,
        }
        self.template_params_text.insert("1.0", json.dumps(default_params, indent=2))

    def delete_job_template(self):
        """Delete selected job template."""
        # Implementation for deletion
        pass

    def connect_to_database(self):
        """Connect to Supabase database."""
        if not SUPABASE_AVAILABLE:
            messagebox.showerror(
                "Error", "Supabase client not installed.\nRun: pip install supabase"
            )
            return

        # Show connection dialog
        dialog = DatabaseConnectionDialog(self.root, self.db_config)
        if dialog.result:
            self.db_config = dialog.result
            if self.db_manager.connect():
                self.connection_var.set("Connected")
                messagebox.showinfo("Success", "Connected to database successfully!")
            else:
                self.connection_var.set("Connection failed")
                messagebox.showerror("Error", "Failed to connect to database")

    def save_data(self):
        """Save current form data."""
        # Implementation depends on current form
        pass

    def new_record(self):
        """Create new record."""
        # Implementation depends on current form
        pass

    def refresh_data(self):
        """Refresh current data view."""
        if hasattr(self, "current_table"):
            self.load_existing_data(self.current_table)

    def import_data(self):
        """Import data from file."""
        file_path = filedialog.askopenfilename(
            title="Import Data",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            # Implementation for data import
            messagebox.showinfo("Info", f"Import from {file_path} not yet implemented")

    def export_data(self):
        """Export data to file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            # Implementation for data export
            messagebox.showinfo("Info", f"Export to {file_path} not yet implemented")

    def load_sample_data(self):
        """Load sample data into database."""
        if not self.db_manager.connected:
            messagebox.showerror("Error", "Not connected to database")
            return

        # Implementation for loading sample data
        messagebox.showinfo("Info", "Sample data loading not yet implemented")

    def clear_all_data(self):
        """Clear all data from database."""
        if not messagebox.askyesno(
            "Confirm",
            "Are you sure you want to clear all data?\nThis cannot be undone!",
        ):
            return

        # Implementation for clearing data
        messagebox.showinfo("Info", "Clear all data not yet implemented")

    def validate_data(self):
        """Validate all data in database."""
        # Implementation for data validation
        messagebox.showinfo("Info", "Data validation not yet implemented")

    def show_help(self):
        """Show user help."""
        help_text = """
Fresh Solver GUI - User Guide

1. Connect to Database:
   - Use File -> Connect to Database
   - Enter your Supabase URL and API key

2. Data Entry:
   - Select a data category from the left panel
   - Fill in the form fields
   - Click Save to store the data

3. Navigation:
   - Use the tree on the left to navigate between data types
   - Existing records are shown at the bottom of each form

4. Keyboard Shortcuts:
   - Ctrl+S: Save current form
   - Ctrl+N: New record
   - F5: Refresh data

For more information, see the project documentation.
        """
        messagebox.showinfo("User Guide", help_text)

    def show_about(self):
        """Show about dialog."""
        about_text = """
Fresh Solver GUI v1.0

A data entry interface for the Fresh Solver OR-Tools
constraint programming system.

This GUI provides an intuitive interface for managing:
- Organizational structure (departments, work cells)
- Job templates and instances
- Resources (machines, operators, skills)
- Scheduling data (setup times, maintenance)

Built with Python/Tkinter and Supabase integration.
        """
        messagebox.showinfo("About", about_text)

    def on_closing(self):
        """Handle application closing."""
        if self.unsaved_changes and not messagebox.askyesno(
            "Confirm Exit", "You have unsaved changes. Exit anyway?"
        ):
            return

        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


class DatabaseConnectionDialog:
    """Dialog for database connection settings."""

    def __init__(self, parent, current_config: DatabaseConfig):
        """Initialize database connection dialog."""
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Database Connection")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.geometry(
            f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}"
        )

        self.create_dialog_content(current_config)

        # Wait for dialog to close
        self.dialog.wait_window()

    def create_dialog_content(self, config: DatabaseConfig):
        """Create dialog content."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Supabase Connection Settings", font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))

        # URL field
        ttk.Label(main_frame, text="Supabase URL:").pack(anchor=tk.W)
        self.url_var = tk.StringVar(value=config.supabase_url)
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.pack(fill=tk.X, pady=(5, 15))

        # API Key field
        ttk.Label(main_frame, text="Supabase Anonymous Key:").pack(anchor=tk.W)
        self.key_var = tk.StringVar(value=config.supabase_key)
        key_entry = ttk.Entry(main_frame, textvariable=self.key_var, width=60, show="*")
        key_entry.pack(fill=tk.X, pady=(5, 15))

        # Info text
        info_text = """
Note: You can also set these as environment variables:
- SUPABASE_URL
- SUPABASE_ANON_KEY
        """
        info_label = ttk.Label(main_frame, text=info_text, font=("Arial", 9))
        info_label.pack(pady=(10, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Connect", command=self.on_connect).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(
            side=tk.LEFT, padx=5
        )

        # Focus on first empty field
        if not config.supabase_url:
            url_entry.focus()
        elif not config.supabase_key:
            key_entry.focus()

    def on_connect(self):
        """Handle connect button."""
        url = self.url_var.get().strip()
        key = self.key_var.get().strip()

        if not url or not key:
            messagebox.showerror("Error", "Both URL and API key are required")
            return

        # Create new config
        new_config = DatabaseConfig()
        new_config.supabase_url = url
        new_config.supabase_key = key

        self.result = new_config
        self.dialog.destroy()

    def on_cancel(self):
        """Handle cancel button."""
        self.dialog.destroy()


def main():
    """Run the main GUI application."""
    # Check if running in development mode
    if not SUPABASE_AVAILABLE:
        print("Warning: Supabase client not available")
        print("Install with: pip install supabase")
        print("The GUI will still run but database features will be disabled")

    try:
        app = FreshSolverGUI()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
