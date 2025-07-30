"""Constraint Development Lifecycle Hooks.

Implements hooks for automating constraint development workflow:
- Pre/post constraint creation
- Automated test generation
- Standards compliance validation
- Integration safety checks
"""

import logging
from typing import Any

from hook_registry import HookContext, register_hook

logger = logging.getLogger(__name__)


class ConstraintLifecycleHooks:
    """Collection of hooks for constraint development lifecycle."""

    @staticmethod
    def detect_constraint_phase(constraint_name: str) -> str:
        """Detect which phase a constraint belongs to based on name patterns."""
        phase_patterns = {
            "phase1": [
                "duration",
                "precedence",
                "assignment",
                "no_overlap",
                "capacity",
                "setup_time",
                "unattended",
                "weekend",
                "workcell",
                "template",
            ],
            "phase2": [
                "skill",
                "operator",
                "shift",
                "resource",
                "availability",
                "proficiency",
                "multi_operator",
            ],
            "phase3": [
                "preemption",
                "deadline",
                "multi_objective",
                "wip_limit",
                "lateness",
                "cost",
                "priority",
            ],
        }

        constraint_lower = constraint_name.lower()
        for phase, keywords in phase_patterns.items():
            if any(keyword in constraint_lower for keyword in keywords):
                return phase

        return "phase1"  # Default to phase1 if unclear

    @staticmethod
    def generate_constraint_template(constraint_name: str, phase: str) -> str:
        """Generate constraint function template following STANDARDS.md."""
        # Import statements based on phase
        if phase == "phase2":
            imports = """from ortools.sat.python import cp_model
from typing import Dict, List, Tuple, Optional
from src.solver.models.problem import SchedulingProblem
from src.solver.types import (
    TaskStartDict,
    TaskEndDict,
    TaskOperatorAssignedDict,
    OperatorKey,
    TaskKey
)"""
        else:
            imports = """from ortools.sat.python import cp_model
from typing import Dict, List, Tuple, Optional
from src.solver.models.problem import SchedulingProblem
from src.solver.types import (
    TaskStartDict,
    TaskEndDict,
    TaskIntervalDict,
    TaskKey,
    MachineKey
)"""

        # Function signature based on phase
        if phase == "phase2":
            signature = f"""def add_{constraint_name}_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    task_ends: TaskEndDict,
    task_operator_assigned: TaskOperatorAssignedDict,
    problem: SchedulingProblem
) -> Optional[Dict[str, cp_model.IntVar]]"""
        else:
            signature = f"""def add_{constraint_name}_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    task_ends: TaskEndDict,
    problem: SchedulingProblem
) -> None"""

        # Generate complete template
        template = f'''{imports}


{signature}:
    """{constraint_name.replace("_", " ").title()} constraints for OR-Tools scheduling.

    Mathematical formulation:
        TODO: Specify mathematical constraints

    Business logic:
        TODO: Explain business rule this constraint enforces

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        {"task_operator_assigned: Dictionary of task-operator assignment variables" if phase == "phase2" else ""}
        problem: Scheduling problem containing all data

    {"Returns:" if phase == "phase2" else ""}
        {"Optional dictionary of additional variables created (e.g., efficiency_vars)" if phase == "phase2" else ""}

    Constraints added:
        - TODO: List specific constraints added to model

    Performance considerations:
        - TODO: Complexity analysis (e.g., O(n*m) where n=tasks, m=operators)

    Type safety:
        - All parameters properly typed with centralized aliases
        - {"Returns Optional[Dict] for additional variables" if phase == "phase2" else "Returns None as per STANDARDS.md for constraint functions"}
    """
    logger.info(f"Adding {constraint_name} constraints...")

    # TODO: Implement constraint logic here
    # Follow pattern:
    # for task_key in problem.tasks:
    #     # Add constraints for this task
    #     pass

    {"# Return additional variables if created (Phase 2 pattern)" if phase == "phase2" else ""}
    {"return None  # or return created_variables_dict" if phase == "phase2" else ""}'''

        return template

    @staticmethod
    def generate_constraint_tests(constraint_name: str, phase: str) -> str:
        """Generate unit tests following GIVEN-WHEN-THEN pattern."""
        test_template = f'''"""Unit tests for {constraint_name} constraints.

Tests follow GIVEN-WHEN-THEN pattern as specified in STANDARDS.md.
"""

import pytest
from ortools.sat.python import cp_model

from src.solver.constraints.{phase}.{constraint_name} import add_{constraint_name}_constraints
from src.solver.models.problem import SchedulingProblem
from tests.conftest import create_test_problem


class Test{constraint_name.title().replace("_", "")}Constraints:
    """Test suite for {constraint_name} constraints."""

    def test_{constraint_name}_basic_functionality(self):
        """Test that {constraint_name} constraints work correctly."""
        # GIVEN: A model with test data
        model = cp_model.CpModel()
        problem = create_test_problem(
            num_jobs=2,
            num_tasks_per_job=3,
            {"num_operators=2," if phase == "phase2" else ""}
            num_machines=2
        )

        # Create required variables
        task_starts = {{}}
        task_ends = {{}}
        {"task_operator_assigned = {}" if phase == "phase2" else ""}

        for job in problem.jobs:
            for task in job.tasks:
                key = (job.job_id, task.task_id)
                task_starts[key] = model.NewIntVar(0, 100, f'start_{{key[0]}}_{{key[1]}}')
                task_ends[key] = model.NewIntVar(0, 100, f'end_{{key[0]}}_{{key[1]}}')

                {"# Create operator assignment variables" if phase == "phase2" else ""}
                {"for operator in problem.operators:" if phase == "phase2" else ""}
                    {"op_key = (key[0], key[1], operator.operator_id)" if phase == "phase2" else ""}
                    {"task_operator_assigned[op_key] = model.NewIntVar(0, 1, f'assigned_{op_key[0]}_{op_key[1]}_{op_key[2]}')" if phase == "phase2" else ""}

        # WHEN: Adding {constraint_name} constraints
        {"result = " if phase == "phase2" else ""}add_{constraint_name}_constraints(
            model=model,
            task_starts=task_starts,
            task_ends=task_ends,
            {"task_operator_assigned=task_operator_assigned," if phase == "phase2" else ""}
            problem=problem
        )

        # THEN: Solver finds valid solution
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        {"assert result is not None  # Should return additional variables" if phase == "phase2" else ""}

        # Verify constraint behavior
        # TODO: Add specific assertions for constraint behavior

    def test_{constraint_name}_edge_cases(self):
        """Test {constraint_name} with edge cases."""
        # GIVEN: Edge case scenario (e.g., single task, no valid assignments)
        model = cp_model.CpModel()
        problem = create_test_problem(num_jobs=1, num_tasks_per_job=1)

        # Create minimal variables
        task_starts = {{(1, 1): model.NewIntVar(0, 10, 'start_1_1')}}
        task_ends = {{(1, 1): model.NewIntVar(0, 10, 'end_1_1')}}
        {"task_operator_assigned = {}" if phase == "phase2" else ""}

        # WHEN: Adding constraints with edge case
        {"result = " if phase == "phase2" else ""}add_{constraint_name}_constraints(
            model, task_starts, task_ends, {"task_operator_assigned, " if phase == "phase2" else ""}problem
        )

        # THEN: Should handle edge case gracefully
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # Should either solve or be infeasible for valid reason
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.INFEASIBLE]

    def test_{constraint_name}_integration(self):
        """Test {constraint_name} integration with other constraints."""
        # GIVEN: Model with multiple constraint types
        model = cp_model.CpModel()
        problem = create_test_problem(num_jobs=3, num_tasks_per_job=2)

        # Create variables
        task_starts = {{}}
        task_ends = {{}}
        {"task_operator_assigned = {}" if phase == "phase2" else ""}

        for job in problem.jobs:
            for task in job.tasks:
                key = (job.job_id, task.task_id)
                task_starts[key] = model.NewIntVar(0, 50, f'start_{{key[0]}}_{{key[1]}}')
                task_ends[key] = model.NewIntVar(0, 50, f'end_{{key[0]}}_{{key[1]}}')
                # Add duration constraint
                model.Add(task_ends[key] == task_starts[key] + 5)  # 5 time units duration

        # WHEN: Adding multiple constraints including {constraint_name}
        {"result = " if phase == "phase2" else ""}add_{constraint_name}_constraints(
            model, task_starts, task_ends, {"task_operator_assigned, " if phase == "phase2" else ""}problem
        )

        # THEN: Integration should work correctly
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # Verify no conflicts between constraints
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            # Check that solution respects all constraints
            for key, start_var in task_starts.items():
                start_time = solver.Value(start_var)
                end_time = solver.Value(task_ends[key])
                assert end_time >= start_time  # Basic duration constraint'''

        return test_template

    @staticmethod
    def generate_standards_checklist(
        constraint_name: str, function_code: str
    ) -> dict[str, Any]:
        """Generate STANDARDS.md compliance checklist."""
        checklist = {
            "naming_convention": False,
            "line_count": 0,
            "type_hints": False,
            "return_type": False,
            "docstring_complete": False,
            "mathematical_formulation": False,
            "business_logic": False,
            "constraints_listed": False,
            "performance_notes": False,
            "suggestions": [],
        }

        lines = function_code.split("\n")

        # Check naming convention
        if f"def add_{constraint_name}_constraints(" in function_code:
            checklist["naming_convention"] = True
        else:
            checklist["suggestions"].append(
                "Function name should follow pattern: add_<constraint_type>_constraints"
            )

        # Count non-empty lines excluding docstring
        in_docstring = False
        code_lines = 0
        for line in lines:
            stripped = line.strip()
            if '"""' in stripped:
                in_docstring = not in_docstring
                continue
            if not in_docstring and stripped and not stripped.startswith("#"):
                code_lines += 1

        checklist["line_count"] = code_lines
        if code_lines > 30:
            checklist["suggestions"].append(
                f"Function has {code_lines} lines, should be ≤30 (excluding docstring)"
            )

        # Check type hints
        if "-> None" in function_code or "-> Optional[Dict" in function_code:
            checklist["return_type"] = True
        if (
            ": cp_model.CpModel" in function_code
            and ": SchedulingProblem" in function_code
        ):
            checklist["type_hints"] = True

        # Check docstring sections
        if "Mathematical formulation:" in function_code:
            checklist["mathematical_formulation"] = True
        if "Business logic:" in function_code:
            checklist["business_logic"] = True
        if "Constraints added:" in function_code:
            checklist["constraints_listed"] = True
        if "Performance considerations:" in function_code:
            checklist["performance_notes"] = True

        checklist["docstring_complete"] = all(
            [
                checklist["mathematical_formulation"],
                checklist["business_logic"],
                checklist["constraints_listed"],
                checklist["performance_notes"],
            ]
        )

        return checklist


# Register the lifecycle hooks
@register_hook("pre_constraint_creation")
def setup_constraint_context(context: HookContext) -> HookContext:
    """Set up context for constraint creation."""
    if not context.constraint_name:
        logger.warning("No constraint name provided")
        return context

    # Detect phase and set up context
    phase = ConstraintLifecycleHooks.detect_constraint_phase(context.constraint_name)
    context.phase = phase
    context.constraint_type = context.constraint_name

    # Set up naming pattern validation
    expected_name = f"add_{context.constraint_name}_constraints"
    context.metadata["expected_function_name"] = expected_name
    context.metadata["phase"] = phase

    logger.info(
        f"Setting up constraint creation for '{context.constraint_name}' (Phase: {phase})"
    )
    return context


@register_hook("post_constraint_creation")
def generate_constraint_artifacts(context: HookContext) -> HookContext:
    """Generate tests and validation artifacts after constraint creation."""
    if not context.constraint_name or not context.generated_function:
        return context

    # Generate unit tests
    tests = ConstraintLifecycleHooks.generate_constraint_tests(
        context.constraint_name, context.phase
    )
    context.generated_tests = tests

    # Generate standards compliance checklist
    checklist = ConstraintLifecycleHooks.generate_standards_checklist(
        context.constraint_name, context.generated_function
    )
    context.validation_results = checklist

    logger.info(
        f"Generated tests and validation checklist for '{context.constraint_name}'"
    )
    return context


@register_hook("pre_constraint_validation")
def prepare_validation_context(context: HookContext) -> HookContext:
    """Prepare context for constraint validation."""
    if context.generated_function:
        # Count lines for validation
        lines = context.generated_function.split("\n")
        context.line_count = len(
            [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
        )

    return context


@register_hook("post_constraint_validation")
def finalize_constraint_validation(context: HookContext) -> HookContext:
    """Finalize constraint validation and provide recommendations."""
    if not context.validation_results:
        return context

    # Calculate compliance score
    checklist = context.validation_results
    total_checks = 9  # Number of boolean checks in standards
    passed_checks = sum(
        [
            checklist.get("naming_convention", False),
            checklist.get("line_count", 31) <= 30,
            checklist.get("type_hints", False),
            checklist.get("return_type", False),
            checklist.get("docstring_complete", False),
            checklist.get("mathematical_formulation", False),
            checklist.get("business_logic", False),
            checklist.get("constraints_listed", False),
            checklist.get("performance_notes", False),
        ]
    )

    context.compliance_score = passed_checks / total_checks

    # Add recommendations based on score
    if context.compliance_score < 0.8:
        context.metadata["recommendations"] = [
            "Review STANDARDS.md for complete compliance requirements",
            "Add missing docstring sections",
            "Ensure all parameters have type hints",
        ]
    elif context.compliance_score < 1.0:
        context.metadata["recommendations"] = [
            "Minor improvements needed for full compliance",
            "Consider adding performance optimizations",
        ]
    else:
        context.metadata["recommendations"] = [
            "Excellent! Constraint meets all STANDARDS.md requirements"
        ]

    return context
