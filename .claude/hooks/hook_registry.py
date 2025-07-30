"""Hook Registry for OR-Tools Development Workflow.

Provides a centralized registry for managing development workflow hooks
following the hook implementation patterns identified for constraint development.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HookContext:
    """Context passed between hooks during workflow execution."""

    # Core workflow information
    command: str
    phase: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Constraint-specific context
    constraint_name: str | None = None
    constraint_type: str | None = None

    # Generated content
    generated_function: str | None = None
    generated_tests: str | None = None
    validation_results: dict[str, Any] = field(default_factory=dict)

    # Quality metrics
    line_count: int | None = None
    compliance_score: float | None = None

    # Extension points for custom data
    metadata: dict[str, Any] = field(default_factory=dict)


class HookRegistry:
    """Central registry for development workflow hooks."""

    def __init__(self):
        self._hooks: dict[str, list[Callable]] = {
            # Constraint Development Lifecycle
            "pre_constraint_creation": [],
            "post_constraint_creation": [],
            "pre_constraint_validation": [],
            "post_constraint_validation": [],
            "constraint_integration": [],
            "post_integration_test": [],
            # Template Optimization Lifecycle
            "template_session_start": [],
            "template_checkpoint": [],
            "template_parameter_tuned": [],
            "template_performance_regression": [],
            "template_optimization_complete": [],
            # Quality Gates
            "pre_commit_validation": [],
            "type_safety_check": [],
            "performance_gate_check": [],
            "phase_transition_validation": [],
            # Workflow Integration
            "command_preprocessing": [],
            "command_postprocessing": [],
            "workflow_orchestration": [],
            "context_enrichment": [],
        }

    def register(self, hook_name: str, hook_function: Callable) -> None:
        """Register a hook function for a specific hook point.

        Args:
            hook_name: Name of the hook point
            hook_function: Function to execute at this hook point

        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append(hook_function)
        logger.debug(f"Registered hook '{hook_function.__name__}' for '{hook_name}'")

    def execute(self, hook_name: str, context: HookContext) -> HookContext:
        """Execute all hooks registered for a specific hook point.

        Args:
            hook_name: Name of the hook point to execute
            context: Context object passed between hooks

        Returns:
            Updated context after all hooks have executed

        """
        if hook_name not in self._hooks:
            logger.warning(f"No hooks registered for '{hook_name}'")
            return context

        logger.debug(f"Executing {len(self._hooks[hook_name])} hooks for '{hook_name}'")

        for hook_function in self._hooks[hook_name]:
            try:
                # Execute hook and update context
                result = hook_function(context)
                if result is not None:
                    context = result

            except Exception as e:
                logger.error(f"Hook '{hook_function.__name__}' failed: {e}")
                # Continue with other hooks, but record the failure
                context.metadata[f"{hook_function.__name__}_error"] = str(e)

        return context

    def list_hooks(self, hook_name: str | None = None) -> dict[str, list[str]]:
        """List all registered hooks.

        Args:
            hook_name: Optional specific hook name to list

        Returns:
            Dictionary mapping hook names to lists of registered function names

        """
        if hook_name:
            if hook_name in self._hooks:
                return {hook_name: [f.__name__ for f in self._hooks[hook_name]]}
            else:
                return {}

        return {
            name: [f.__name__ for f in functions]
            for name, functions in self._hooks.items()
            if functions  # Only include hooks that have registered functions
        }


# Global registry instance for easy access
registry = HookRegistry()


def register_hook(hook_name: str):
    """Decorator for registering hook functions.

    Usage:
        @register_hook('pre_constraint_creation')
        def my_hook(context: HookContext) -> HookContext:
            # Hook implementation
            return context
    """

    def decorator(func: Callable):
        registry.register(hook_name, func)
        return func

    return decorator
