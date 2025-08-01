"""Extended forms for Fresh Solver GUI.

Additional data entry forms for complex tables.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

# Set up logger
logger = logging.getLogger(__name__)


class MachinesFormMixin:
    """Mixin for machines data entry form."""

    def create_machines_form(self):
        """Create form for machines table."""
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

        # Machine Name
        ttk.Label(fields_frame, text="Machine Name*:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.machine_name_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.machine_name_var, width=50).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Capacity
        ttk.Label(fields_frame, text="Capacity:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.machine_capacity_var = tk.StringVar(value="1")
        ttk.Entry(fields_frame, textvariable=self.machine_capacity_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Cost per hour
        ttk.Label(fields_frame, text="Cost per Hour:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.machine_cost_var = tk.StringVar(value="0.00")
        ttk.Entry(fields_frame, textvariable=self.machine_cost_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Department (dropdown)
        ttk.Label(fields_frame, text="Department:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.machine_dept_var = tk.StringVar()
        self.machine_dept_combo = ttk.Combobox(
            fields_frame, textvariable=self.machine_dept_var, width=30
        )
        self.machine_dept_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        self.load_departments_for_combo(self.machine_dept_combo)

        # Work Cell (dropdown)
        ttk.Label(fields_frame, text="Work Cell:").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.machine_cell_var = tk.StringVar()
        self.machine_cell_combo = ttk.Combobox(
            fields_frame, textvariable=self.machine_cell_var, width=30
        )
        self.machine_cell_combo.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        # Load work cells based on selected department

        # Setup and teardown times
        ttk.Label(fields_frame, text="Setup Time (minutes):").grid(
            row=5, column=0, sticky=tk.W, pady=2
        )
        self.machine_setup_var = tk.StringVar(value="0")
        ttk.Entry(fields_frame, textvariable=self.machine_setup_var, width=10).grid(
            row=5, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Teardown Time (minutes):").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        self.machine_teardown_var = tk.StringVar(value="0")
        ttk.Entry(fields_frame, textvariable=self.machine_teardown_var, width=10).grid(
            row=6, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Machine specifications
        ttk.Label(fields_frame, text="Machine Type:").grid(
            row=7, column=0, sticky=tk.W, pady=2
        )
        self.machine_type_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.machine_type_var, width=30).grid(
            row=7, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Manufacturer:").grid(
            row=8, column=0, sticky=tk.W, pady=2
        )
        self.machine_mfg_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.machine_mfg_var, width=30).grid(
            row=8, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Model:").grid(
            row=9, column=0, sticky=tk.W, pady=2
        )
        self.machine_model_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.machine_model_var, width=30).grid(
            row=9, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Performance metrics
        ttk.Label(fields_frame, text="Efficiency Rating:").grid(
            row=10, column=0, sticky=tk.W, pady=2
        )
        self.machine_efficiency_var = tk.StringVar(value="1.00")
        ttk.Entry(
            fields_frame, textvariable=self.machine_efficiency_var, width=10
        ).grid(row=10, column=1, sticky=tk.W, padx=(10, 0))

        # Active status
        self.machine_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fields_frame, text="Active", variable=self.machine_active_var
        ).grid(row=11, column=1, sticky=tk.W, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(fields_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_machine).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="New", command=self.clear_machine_form).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_machine).pack(
            side=tk.LEFT, padx=5
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_records_list(scrollable_frame, "machines")

    def save_machine(self):
        """Save machine record to database."""
        if not self.validate_machine_form():
            return

        data = {
            "name": self.machine_name_var.get(),
            "capacity": int(self.machine_capacity_var.get()),
            "cost_per_hour": float(self.machine_cost_var.get()),
            "setup_time_minutes": int(self.machine_setup_var.get()),
            "teardown_time_minutes": int(self.machine_teardown_var.get()),
            "machine_type": self.machine_type_var.get(),
            "manufacturer": self.machine_mfg_var.get(),
            "model": self.machine_model_var.get(),
            "efficiency_rating": float(self.machine_efficiency_var.get()),
            "is_active": self.machine_active_var.get(),
        }

        try:
            self.db_manager.execute_query("machines", "insert", data)
            messagebox.showinfo("Success", "Machine saved successfully!")
            self.clear_machine_form()
            self.load_existing_data("machines")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save machine: {str(e)}")

    def validate_machine_form(self) -> bool:
        """Validate machine form data."""
        if not self.machine_name_var.get().strip():
            messagebox.showerror("Validation Error", "Machine name is required")
            return False

        try:
            capacity = int(self.machine_capacity_var.get())
            if capacity < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Validation Error", "Capacity must be a positive integer"
            )
            return False

        try:
            float(self.machine_cost_var.get())
        except ValueError:
            messagebox.showerror(
                "Validation Error", "Cost per hour must be a valid number"
            )
            return False

        return True

    def clear_machine_form(self):
        """Clear machine form fields."""
        self.machine_name_var.set("")
        self.machine_capacity_var.set("1")
        self.machine_cost_var.set("0.00")
        self.machine_dept_var.set("")
        self.machine_cell_var.set("")
        self.machine_setup_var.set("0")
        self.machine_teardown_var.set("0")
        self.machine_type_var.set("")
        self.machine_mfg_var.set("")
        self.machine_model_var.set("")
        self.machine_efficiency_var.set("1.00")
        self.machine_active_var.set(True)

    def delete_machine(self):
        """Delete selected machine."""
        pass


class OperatorsFormMixin:
    """Mixin for operators data entry form."""

    def create_operators_form(self):
        """Create form for operators table."""
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

        # Operator Name
        ttk.Label(fields_frame, text="Operator Name*:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.operator_name_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.operator_name_var, width=50).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Employee Number
        ttk.Label(fields_frame, text="Employee Number:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.operator_emp_num_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.operator_emp_num_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Department
        ttk.Label(fields_frame, text="Department:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.operator_dept_var = tk.StringVar()
        self.operator_dept_combo = ttk.Combobox(
            fields_frame, textvariable=self.operator_dept_var, width=30
        )
        self.operator_dept_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        self.load_departments_for_combo(self.operator_dept_combo)

        # Pay and hours
        ttk.Label(fields_frame, text="Hourly Rate:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.operator_rate_var = tk.StringVar(value="0.00")
        ttk.Entry(fields_frame, textvariable=self.operator_rate_var, width=15).grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Max Hours per Day:").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.operator_hours_day_var = tk.StringVar(value="8")
        ttk.Entry(
            fields_frame, textvariable=self.operator_hours_day_var, width=10
        ).grid(row=4, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(fields_frame, text="Max Hours per Week:").grid(
            row=5, column=0, sticky=tk.W, pady=2
        )
        self.operator_hours_week_var = tk.StringVar(value="40")
        ttk.Entry(
            fields_frame, textvariable=self.operator_hours_week_var, width=10
        ).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))

        # Performance ratings
        ttk.Label(fields_frame, text="Efficiency Rating:").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        self.operator_efficiency_var = tk.StringVar(value="1.00")
        ttk.Entry(
            fields_frame, textvariable=self.operator_efficiency_var, width=10
        ).grid(row=6, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(fields_frame, text="Quality Score:").grid(
            row=7, column=0, sticky=tk.W, pady=2
        )
        self.operator_quality_var = tk.StringVar(value="1.00")
        ttk.Entry(fields_frame, textvariable=self.operator_quality_var, width=10).grid(
            row=7, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Employment status
        ttk.Label(fields_frame, text="Employment Status:").grid(
            row=8, column=0, sticky=tk.W, pady=2
        )
        self.operator_status_var = tk.StringVar(value="active")
        status_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.operator_status_var,
            values=["active", "on_leave", "terminated", "retired"],
            width=15,
        )
        status_combo.grid(row=8, column=1, sticky=tk.W, padx=(10, 0))

        # Active checkbox
        self.operator_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            fields_frame, text="Active", variable=self.operator_active_var
        ).grid(row=9, column=1, sticky=tk.W, padx=(10, 0))

        # Skills section
        ttk.Label(fields_frame, text="Skills:", font=("Arial", 10, "bold")).grid(
            row=10, column=0, sticky=tk.W, pady=(15, 5)
        )

        # Skills management frame
        skills_frame = ttk.LabelFrame(fields_frame, text="Operator Skills", padding="5")
        skills_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Skills listbox with scrollbar
        skills_list_frame = ttk.Frame(skills_frame)
        skills_list_frame.pack(fill=tk.BOTH, expand=True)

        self.operator_skills_listbox = tk.Listbox(skills_list_frame, height=6)
        skills_scrollbar = ttk.Scrollbar(
            skills_list_frame,
            orient=tk.VERTICAL,
            command=self.operator_skills_listbox.yview,
        )
        self.operator_skills_listbox.configure(yscrollcommand=skills_scrollbar.set)

        self.operator_skills_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        skills_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add skill button
        add_skill_frame = ttk.Frame(skills_frame)
        add_skill_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            add_skill_frame, text="Add Skill", command=self.add_operator_skill
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            add_skill_frame, text="Remove Skill", command=self.remove_operator_skill
        ).pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(fields_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_operator).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="New", command=self.clear_operator_form).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_operator).pack(
            side=tk.LEFT, padx=5
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_records_list(scrollable_frame, "operators")

    def add_operator_skill(self):
        """Add skill to operator."""
        # Create dialog for skill selection
        dialog = SkillSelectionDialog(self.root, self.db_manager)
        if dialog.result:
            skill_info = (
                f"{dialog.result['skill_name']} - {dialog.result['proficiency']}"
            )
            self.operator_skills_listbox.insert(tk.END, skill_info)

    def remove_operator_skill(self):
        """Remove selected skill from operator."""
        selection = self.operator_skills_listbox.curselection()
        if selection:
            self.operator_skills_listbox.delete(selection[0])

    def save_operator(self):
        """Save operator record to database."""
        if not self.validate_operator_form():
            return

        data = {
            "name": self.operator_name_var.get(),
            "employee_number": self.operator_emp_num_var.get(),
            "hourly_rate": float(self.operator_rate_var.get()),
            "max_hours_per_day": int(self.operator_hours_day_var.get()),
            "max_hours_per_week": int(self.operator_hours_week_var.get()),
            "efficiency_rating": float(self.operator_efficiency_var.get()),
            "quality_score": float(self.operator_quality_var.get()),
            "employment_status": self.operator_status_var.get(),
            "is_active": self.operator_active_var.get(),
        }

        try:
            self.db_manager.execute_query("operators", "insert", data)
            messagebox.showinfo("Success", "Operator saved successfully!")
            self.clear_operator_form()
            self.load_existing_data("operators")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save operator: {str(e)}")

    def validate_operator_form(self) -> bool:
        """Validate operator form data."""
        if not self.operator_name_var.get().strip():
            messagebox.showerror("Validation Error", "Operator name is required")
            return False

        try:
            rate = float(self.operator_rate_var.get())
            if rate < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Validation Error", "Hourly rate must be a valid positive number"
            )
            return False

        return True

    def clear_operator_form(self):
        """Clear operator form fields."""
        self.operator_name_var.set("")
        self.operator_emp_num_var.set("")
        self.operator_dept_var.set("")
        self.operator_rate_var.set("0.00")
        self.operator_hours_day_var.set("8")
        self.operator_hours_week_var.set("40")
        self.operator_efficiency_var.set("1.00")
        self.operator_quality_var.set("1.00")
        self.operator_status_var.set("active")
        self.operator_active_var.set(True)
        self.operator_skills_listbox.delete(0, tk.END)

    def delete_operator(self):
        """Delete selected operator."""
        pass


class SetupTimesFormMixin:
    """Mixin for setup times data entry form - critical for constraint generation."""

    def create_setup_times_form(self):
        """Create form for template task setup times.

        Exact constraint interface match.
        """
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

        # Info label
        info_label = ttk.Label(
            fields_frame,
            text="Setup Times: Configure time required to change from one "
            "template task to another on a machine",
            font=("Arial", 10, "italic"),
        )
        info_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        # Template selection
        ttk.Label(fields_frame, text="Job Template:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.setup_template_var = tk.StringVar()
        self.setup_template_combo = ttk.Combobox(
            fields_frame, textvariable=self.setup_template_var, width=40
        )
        self.setup_template_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        self.setup_template_combo.bind(
            "<<ComboboxSelected>>", self.on_template_selected
        )
        self.load_templates_for_combo(self.setup_template_combo)

        # From task
        ttk.Label(fields_frame, text="From Template Task:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.setup_from_task_var = tk.StringVar()
        self.setup_from_task_combo = ttk.Combobox(
            fields_frame, textvariable=self.setup_from_task_var, width=40
        )
        self.setup_from_task_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))

        # To task
        ttk.Label(fields_frame, text="To Template Task:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.setup_to_task_var = tk.StringVar()
        self.setup_to_task_combo = ttk.Combobox(
            fields_frame, textvariable=self.setup_to_task_var, width=40
        )
        self.setup_to_task_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))

        # Machine
        ttk.Label(fields_frame, text="Machine:").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.setup_machine_var = tk.StringVar()
        self.setup_machine_combo = ttk.Combobox(
            fields_frame, textvariable=self.setup_machine_var, width=40
        )
        self.setup_machine_combo.grid(row=4, column=1, sticky=tk.W, padx=(10, 0))
        self.load_machines_for_combo(self.setup_machine_combo)

        # Setup time
        ttk.Label(fields_frame, text="Setup Time (minutes)*:").grid(
            row=5, column=0, sticky=tk.W, pady=2
        )
        self.setup_time_var = tk.StringVar(value="0")
        ttk.Entry(fields_frame, textvariable=self.setup_time_var, width=10).grid(
            row=5, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Setup type
        ttk.Label(fields_frame, text="Setup Type:").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        self.setup_type_var = tk.StringVar(value="standard")
        setup_type_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.setup_type_var,
            values=["standard", "complex", "tooling_change", "calibration", "cleaning"],
            width=20,
        )
        setup_type_combo.grid(row=6, column=1, sticky=tk.W, padx=(10, 0))

        # Complexity level
        ttk.Label(fields_frame, text="Complexity Level:").grid(
            row=7, column=0, sticky=tk.W, pady=2
        )
        self.setup_complexity_var = tk.StringVar(value="simple")
        complexity_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.setup_complexity_var,
            values=["simple", "moderate", "complex", "expert_required"],
            width=20,
        )
        complexity_combo.grid(row=7, column=1, sticky=tk.W, padx=(10, 0))

        # Setup cost
        ttk.Label(fields_frame, text="Setup Cost:").grid(
            row=8, column=0, sticky=tk.W, pady=2
        )
        self.setup_cost_var = tk.StringVar(value="0.00")
        ttk.Entry(fields_frame, textvariable=self.setup_cost_var, width=15).grid(
            row=8, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Product family setup (for A→B patterns)
        ttk.Label(fields_frame, text="Product Family From:").grid(
            row=9, column=0, sticky=tk.W, pady=2
        )
        self.setup_family_from_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.setup_family_from_var, width=20).grid(
            row=9, column=1, sticky=tk.W, padx=(10, 0)
        )

        ttk.Label(fields_frame, text="Product Family To:").grid(
            row=10, column=0, sticky=tk.W, pady=2
        )
        self.setup_family_to_var = tk.StringVar()
        ttk.Entry(fields_frame, textvariable=self.setup_family_to_var, width=20).grid(
            row=10, column=1, sticky=tk.W, padx=(10, 0)
        )

        # Quick setup patterns section
        patterns_frame = ttk.LabelFrame(
            fields_frame, text="Quick Setup Patterns", padding="5"
        )
        patterns_frame.grid(
            row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
        )

        ttk.Button(
            patterns_frame,
            text="Product A → B (15 min)",
            command=lambda: self.apply_setup_pattern("A", "B", 15),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            patterns_frame,
            text="Product B → A (30 min)",
            command=lambda: self.apply_setup_pattern("B", "A", 30),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            patterns_frame,
            text="Same Product (5 min)",
            command=lambda: self.apply_setup_pattern("Same", "Same", 5),
        ).pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(fields_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save_setup_time).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="New", command=self.clear_setup_time_form).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_setup_time).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            button_frame, text="Bulk Import", command=self.bulk_import_setup_times
        ).pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_records_list(scrollable_frame, "optimized_task_setup_times")

    def on_template_selected(self, _event):
        """Handle template selection to load template tasks."""
        template_id = self.setup_template_var.get()
        if template_id:
            self.load_template_tasks_for_combos(template_id)

    def load_template_tasks_for_combos(self, _template_id: str):
        """Load template tasks for from/to combo boxes."""
        try:
            # In real implementation, query template_tasks for this template
            # For now, use placeholder data
            tasks = ["Task 1", "Task 2", "Task 3"]  # Placeholder

            self.setup_from_task_combo["values"] = tasks
            self.setup_to_task_combo["values"] = tasks

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template tasks: {str(e)}")

    def apply_setup_pattern(self, from_family: str, to_family: str, minutes: int):
        """Apply quick setup pattern."""
        self.setup_family_from_var.set(from_family)
        self.setup_family_to_var.set(to_family)
        self.setup_time_var.set(str(minutes))

        if from_family == to_family == "Same":
            self.setup_type_var.set("standard")
            self.setup_complexity_var.set("simple")
        elif minutes >= 30:
            self.setup_type_var.set("complex")
            self.setup_complexity_var.set("moderate")
        else:
            self.setup_type_var.set("standard")
            self.setup_complexity_var.set("simple")

    def bulk_import_setup_times(self):
        """Bulk import setup times from file."""
        messagebox.showinfo("Info", "Bulk import feature not yet implemented")

    def save_setup_time(self):
        """Save setup time record - critical for constraint generation."""
        if not self.validate_setup_time_form():
            return

        data = {
            "from_optimized_task_id": self.setup_from_task_var.get(),  # UUID in real
            "to_optimized_task_id": self.setup_to_task_var.get(),
            "machine_resource_id": self.setup_machine_var.get(),
            "setup_time_minutes": int(self.setup_time_var.get()),
            "setup_type": self.setup_type_var.get(),
            "complexity_level": self.setup_complexity_var.get(),
            "setup_cost": float(self.setup_cost_var.get()),
            "product_family_from": self.setup_family_from_var.get(),
            "product_family_to": self.setup_family_to_var.get(),
        }

        try:
            self.db_manager.execute_query("optimized_task_setup_times", "insert", data)
            messagebox.showinfo("Success", "Setup time saved successfully!")
            self.clear_setup_time_form()
            self.load_existing_data("optimized_task_setup_times")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save setup time: {str(e)}")

    def validate_setup_time_form(self) -> bool:
        """Validate setup time form data."""
        if not all(
            [
                self.setup_from_task_var.get(),
                self.setup_to_task_var.get(),
                self.setup_machine_var.get(),
            ]
        ):
            messagebox.showerror(
                "Validation Error", "From task, to task, and machine are required"
            )
            return False

        if self.setup_from_task_var.get() == self.setup_to_task_var.get():
            messagebox.showerror(
                "Validation Error", "From and to tasks cannot be the same"
            )
            return False

        try:
            setup_time = int(self.setup_time_var.get())
            if setup_time < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                "Validation Error", "Setup time must be a non-negative integer"
            )
            return False

        return True

    def clear_setup_time_form(self):
        """Clear setup time form fields."""
        self.setup_template_var.set("")
        self.setup_from_task_var.set("")
        self.setup_to_task_var.set("")
        self.setup_machine_var.set("")
        self.setup_time_var.set("0")
        self.setup_type_var.set("standard")
        self.setup_complexity_var.set("simple")
        self.setup_cost_var.set("0.00")
        self.setup_family_from_var.set("")
        self.setup_family_to_var.set("")

    def delete_setup_time(self):
        """Delete selected setup time."""
        pass


class UtilityMethods:
    """Utility methods for form management."""

    def load_departments_for_combo(self, combo: ttk.Combobox):
        """Load departments for combo box."""
        if not self.db_manager.connected:
            return

        try:
            result = self.db_manager.execute_query("departments", "select")
            dept_names = [
                dept["name"] for dept in result.data if dept.get("is_active", True)
            ]
            combo["values"] = dept_names
        except Exception as e:
            logger.error(f"Failed to load departments: {e}")

    def load_templates_for_combo(self, combo: ttk.Combobox):
        """Load job templates for combo box."""
        if not self.db_manager.connected:
            return

        try:
            result = self.db_manager.execute_query("job_templates", "select")
            template_names = [
                template["name"]
                for template in result.data
                if template.get("is_active", True)
            ]
            combo["values"] = template_names
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    def load_machines_for_combo(self, combo: ttk.Combobox):
        """Load machines for combo box."""
        if not self.db_manager.connected:
            return

        try:
            result = self.db_manager.execute_query("machines", "select")
            machine_names = [
                machine["name"]
                for machine in result.data
                if machine.get("is_active", True)
            ]
            combo["values"] = machine_names
        except Exception as e:
            logger.error(f"Failed to load machines: {e}")


class SkillSelectionDialog:
    """Dialog for selecting operator skills."""

    def __init__(self, parent, db_manager):
        """Initialize skill selection dialog."""
        self.result = None
        self.db_manager = db_manager

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Skill")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_dialog_content()
        self.dialog.wait_window()

    def create_dialog_content(self):
        """Create skill selection dialog content."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Skill selection
        ttk.Label(main_frame, text="Select Skill:").pack(anchor=tk.W)
        self.skill_var = tk.StringVar()
        skill_combo = ttk.Combobox(main_frame, textvariable=self.skill_var, width=40)
        skill_combo.pack(fill=tk.X, pady=(5, 15))

        # Load available skills
        self.load_skills(skill_combo)

        # Proficiency level
        ttk.Label(main_frame, text="Proficiency Level:").pack(anchor=tk.W)
        self.proficiency_var = tk.StringVar(value="COMPETENT")
        proficiency_combo = ttk.Combobox(
            main_frame,
            textvariable=self.proficiency_var,
            values=["NOVICE", "COMPETENT", "PROFICIENT", "EXPERT"],
            width=20,
        )
        proficiency_combo.pack(anchor=tk.W, pady=(5, 15))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Add", command=self.on_add).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(
            side=tk.LEFT, padx=5
        )

    def load_skills(self, combo):
        """Load available skills."""
        if not self.db_manager.connected:
            combo["values"] = ["Skill 1", "Skill 2", "Skill 3"]  # Placeholder
            return

        try:
            result = self.db_manager.execute_query("skills", "select")
            skill_names = [
                skill["name"] for skill in result.data if skill.get("is_active", True)
            ]
            combo["values"] = skill_names
        except Exception:
            combo["values"] = ["Error loading skills"]

    def on_add(self):
        """Handle add button."""
        skill = self.skill_var.get()
        proficiency = self.proficiency_var.get()

        if not skill or not proficiency:
            messagebox.showerror(
                "Error", "Please select both skill and proficiency level"
            )
            return

        self.result = {"skill_name": skill, "proficiency": proficiency}
        self.dialog.destroy()

    def on_cancel(self):
        """Handle cancel button."""
        self.dialog.destroy()
