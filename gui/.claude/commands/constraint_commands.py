"""Enhanced Constraint Commands with Hook Integration.

Provides enhanced /add-constraint and related commands that integrate with
the constraint development lifecycle hooks for automated workflow.
"""

import logging
from pathlib import Path
from typing import Any

from hooks.agent_integration import (
    AgentIntegrationHooks,
    create_agent_workflow_command,
    process_agent_constraint_response,
)
from hooks.constraint_lifecycle import ConstraintLifecycleHooks
from hooks.hook_registry import HookContext, HookRegistry

logger = logging.getLogger(__name__)


class EnhancedConstraintCommands:
    """Enhanced constraint commands with automated workflow hooks."""

    def __init__(self, hook_registry: HookRegistry):
        """Initialize enhanced constraint commands with hook registry.

        Args:
            hook_registry: Registry for constraint lifecycle hooks

        """
        self.hooks = hook_registry
        self.project_root = Path.cwd()

    def add_constraint(
        self, constraint_name: str, use_agent: bool = None, **kwargs
    ) -> dict[str, Any]:
        """Enhanced /add-constraint with full lifecycle automation.

        Args:
            constraint_name: Name of constraint to create (e.g., 'skill_matching')
            use_agent: Whether to use agent assistance (auto-detected if None)
            **kwargs: Additional options (force_phase, custom_template, etc.)

        Returns:
            Dictionary containing generated constraint, tests, and validation results

        """
        # Create hook context
        context = HookContext(
            command="add_constraint",
            constraint_name=constraint_name,
            phase=kwargs.get("force_phase", "auto"),
        )

        logger.info(f"Starting enhanced constraint creation for '{constraint_name}'")

        try:
            # PRE-CREATION HOOKS
            context = self.hooks.execute("pre_constraint_creation", context)

            # CONSTRAINT GENERATION
            constraint_function = self._generate_constraint_function(context)
            context.generated_function = constraint_function

            # POST-CREATION HOOKS (generates tests, validation)
            context = self.hooks.execute("post_constraint_creation", context)

            # CONSTRAINT VALIDATION
            context = self.hooks.execute("pre_constraint_validation", context)
            validation_results = self._validate_constraint(context)
            context.validation_results.update(validation_results)
            context = self.hooks.execute("post_constraint_validation", context)

            # Prepare results
            results = {
                "constraint_function": context.generated_function,
                "generated_tests": context.generated_tests,
                "validation_results": context.validation_results,
                "compliance_score": context.compliance_score,
                "phase": context.phase,
                "recommendations": context.metadata.get("recommendations", []),
                "suggested_files": self._suggest_file_locations(context),
            }

            # Check if agent assistance is recommended or requested
            agent_workflow_available = context.metadata.get(
                "agent_workflow_available", False
            )

            if use_agent or (use_agent is None and agent_workflow_available):
                # Add agent workflow information to results
                results["agent_workflow"] = {
                    "recommended_agent": context.metadata.get("recommended_agent"),
                    "agent_prompt": context.metadata.get("agent_prompt"),
                    "agent_command": self._create_agent_invocation(context),
                }

            # Display results (including agent recommendations)
            self._display_constraint_results(results)

            return results

        except Exception as e:
            logger.error(f"Enhanced constraint creation failed: {e}")
            return {"error": str(e), "context": context}

    def _generate_constraint_function(self, context: HookContext) -> str:
        """Generate the constraint function using lifecycle hooks."""
        return ConstraintLifecycleHooks.generate_constraint_template(
            context.constraint_name, context.phase
        )

    def _validate_constraint(self, context: HookContext) -> dict[str, Any]:
        """Validate constraint against STANDARDS.md."""
        if not context.generated_function:
            return {"error": "No constraint function to validate"}

        return ConstraintLifecycleHooks.generate_standards_checklist(
            context.constraint_name, context.generated_function
        )

    def _create_agent_invocation(self, context: HookContext) -> str:
        """Create the agent invocation command string."""
        recommended_agent = context.metadata.get(
            "recommended_agent", "ortools_model_expert"
        )
        return create_agent_workflow_command(context.constraint_name, recommended_agent)

    def _suggest_file_locations(self, context: HookContext) -> dict[str, str]:
        """Suggest where to save generated files."""
        constraint_name = context.constraint_name
        phase = context.phase

        return {
            "constraint_file": f"src/solver/constraints/{phase}/{constraint_name}.py",
            "test_file": f"tests/unit/constraints/{phase}/test_{constraint_name}.py",
            "integration_test": f"tests/integration/test_{phase}_integration.py",
        }

    def _display_constraint_results(self, results: dict[str, Any]) -> None:
        """Display formatted results to user."""
        constraint_name = (
            results.get("constraint_function", "")
            .split("def add_")[1]
            .split("_constraints")[0]
            if "def add_" in results.get("constraint_function", "")
            else "unknown"
        )
        phase = results.get("phase", "unknown")
        score = results.get("compliance_score", 0.0)

        print("\n🔧 **Enhanced Constraint Creation Results**")
        print(f"📋 Constraint: `{constraint_name}` (Phase: {phase})")
        print(f"✅ Compliance Score: {score:.1%}")

        # Display compliance status
        if score >= 1.0:
            print("🎉 **EXCELLENT** - Full STANDARDS.md compliance!")
        elif score >= 0.8:
            print("⚠️  **GOOD** - Minor improvements needed")
        else:
            print("❌ **NEEDS WORK** - Multiple compliance issues")

        # Show validation details
        validation = results.get("validation_results", {})
        print("\n📊 **Validation Details:**")
        naming_status = "✅" if validation.get("naming_convention") else "❌"
        print(f"   • Naming Convention: {naming_status}")
        line_count = validation.get("line_count", 0)
        line_status = "✅" if validation.get("line_count", 31) <= 30 else "❌ >30 lines"
        print(f"   • Line Count: {line_count} ({line_status})")
        print(f"   • Type Hints: {'✅' if validation.get('type_hints') else '❌'}")
        print(f"   • Return Type: {'✅' if validation.get('return_type') else '❌'}")
        docstring_status = "✅" if validation.get("docstring_complete") else "❌"
        print(f"   • Complete Docstring: {docstring_status}")

        # Show recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print("\n💡 **Recommendations:**")
            for rec in recommendations:
                print(f"   • {rec}")

        # Show suggested file locations
        files = results.get("suggested_files", {})
        print("\n📁 **Suggested File Locations:**")
        for file_type, path in files.items():
            print(f"   • {file_type}: `{path}`")

        # Show agent workflow if available
        agent_workflow = results.get("agent_workflow")
        if agent_workflow:
            agent_name = AgentIntegrationHooks.AVAILABLE_AGENTS[
                agent_workflow["recommended_agent"]
            ]["name"]
            print("\n🤖 **Agent Workflow Available:**")
            print(f"   • Recommended: @agent-{agent_name}")
            agent_best_for = AgentIntegrationHooks.AVAILABLE_AGENTS[
                agent_workflow["recommended_agent"]
            ]["best_for"]
            specializations = ", ".join(agent_best_for)
            print(f"   • Specializes in: {specializations}")
            print("   • Command ready: Copy agent invocation below")

        print("\n🚀 **Next Steps:**")
        if agent_workflow:
            print(
                "   1. **Option A - Agent Assisted**: "
                "Use the agent command below for expert implementation"
            )
            print(
                "   2. **Option B - Manual**: "
                "Save generated template and implement manually"
            )
            print("   3. Save generated tests")
            print(f"   4. Run `/check-constraint {constraint_name}` for validation")
            print("   5. Add to solver.py when ready")
        else:
            print("   1. Save constraint function to suggested location")
            print("   2. Save generated tests")
            print(
                f"   3. Run `/check-constraint {constraint_name}` for final validation"
            )
            print("   4. Add to solver.py when ready")

        # Display the actual generated code
        constraint_code = results.get("constraint_function", "")
        if constraint_code:
            print("\n```python")
            print("# Generated Constraint Function:")
            print(
                constraint_code[:1000] + "..."
                if len(constraint_code) > 1000
                else constraint_code
            )
            print("```")

        test_code = results.get("generated_tests", "")
        if test_code:
            print("\n```python")
            print("# Generated Tests (preview):")
            print(test_code[:800] + "..." if len(test_code) > 800 else test_code)
            print("```")

        # Display agent command if available
        if agent_workflow:
            print("\n🤖 **Agent Command (Copy & Execute):**")
            print("```")
            print(agent_workflow["agent_command"])
            print("```")

    def test_constraint(self, constraint_name: str) -> dict[str, Any]:
        """Enhanced /test-constraint command."""
        # This would integrate with existing test generation
        # For now, delegate to the lifecycle hooks

        phase = ConstraintLifecycleHooks.detect_constraint_phase(constraint_name)
        tests = ConstraintLifecycleHooks.generate_constraint_tests(
            constraint_name, phase
        )

        test_file_path = f"tests/unit/constraints/{phase}/test_{constraint_name}.py"
        return {
            "generated_tests": tests,
            "test_file_path": test_file_path,
        }

    def check_constraint(
        self, constraint_name: str, function_code: str = None
    ) -> dict[str, Any]:
        """Enhanced /check-constraint command."""
        if not function_code:
            # Try to read from suggested location
            phase = ConstraintLifecycleHooks.detect_constraint_phase(constraint_name)
            constraint_file = (
                self.project_root
                / f"src/solver/constraints/{phase}/{constraint_name}.py"
            )

            if constraint_file.exists():
                function_code = constraint_file.read_text()
            else:
                return {"error": f"No constraint function found for {constraint_name}"}

        # Run validation through hooks
        context = HookContext(
            command="check_constraint",
            constraint_name=constraint_name,
            generated_function=function_code,
        )

        context = self.hooks.execute("pre_constraint_validation", context)

        checklist = ConstraintLifecycleHooks.generate_standards_checklist(
            constraint_name, function_code
        )
        context.validation_results = checklist

        context = self.hooks.execute("post_constraint_validation", context)

        return {
            "validation_results": context.validation_results,
            "compliance_score": context.compliance_score,
            "recommendations": context.metadata.get("recommendations", []),
        }

    def process_agent_response(
        self, constraint_name: str, agent_response: str
    ) -> dict[str, Any]:
        """Process agent response for constraint implementation.

        Args:
            constraint_name: Name of the constraint the agent implemented
            agent_response: The agent's response with constraint implementation
            **kwargs: Additional processing options

        Returns:
            Dictionary with processed implementation and validation results

        """
        logger.info(f"Processing agent response for '{constraint_name}'")

        try:
            # Process the agent response
            processed = process_agent_constraint_response(
                agent_response, constraint_name
            )

            # If we got a good implementation, provide integration guidance
            if processed.get("constraint_implementation"):
                phase = ConstraintLifecycleHooks.detect_constraint_phase(
                    constraint_name
                )

                suggested_file = f"src/solver/constraints/{phase}/{constraint_name}.py"
                test_file = f"tests/unit/constraints/{phase}/test_{constraint_name}.py"
                processed["integration_guidance"] = {
                    "suggested_file": suggested_file,
                    "test_file": test_file,
                    "next_steps": [
                        "Save agent implementation to suggested file location",
                        "Run generated tests to validate functionality",
                        "Add import to solver.py Phase section",
                        "Run integration tests to ensure compatibility",
                    ],
                }

                # Display results
                self._display_agent_results(processed, constraint_name)

            return processed

        except Exception as e:
            logger.error(f"Agent response processing failed: {e}")
            return {"error": str(e)}

    def _display_agent_results(
        self, results: dict[str, Any], constraint_name: str
    ) -> None:
        """Display agent implementation results to user."""
        print("\n🤖 **Agent Implementation Results**")
        print(f"📋 Constraint: `{constraint_name}`")

        if results.get("constraint_implementation"):
            print("✅ **Implementation Received**")

            # Show validation if available
            if results.get("agent_compliance_score"):
                score = results["agent_compliance_score"]
                print(f"📊 Compliance Score: {score:.1%}")

                if score >= 0.9:
                    print("🎉 **EXCELLENT** - Agent implementation meets standards!")
                elif score >= 0.7:
                    print("⚠️  **GOOD** - Minor standards adjustments may be needed")
                else:
                    print(
                        "❌ **NEEDS REVISION** - "
                        "Implementation needs significant improvement"
                    )

            # Show integration guidance
            if results.get("integration_guidance"):
                guidance = results["integration_guidance"]
                print("\n📁 **Integration:**")
                print(f"   • Save to: `{guidance['suggested_file']}`")
                print(f"   • Tests: `{guidance['test_file']}`")

                print("\n🚀 **Next Steps:**")
                for i, step in enumerate(guidance["next_steps"], 1):
                    print(f"   {i}. {step}")

            # Show implementation preview
            impl = results["constraint_implementation"]
            print("\n```python")
            print("# Agent Implementation (preview):")
            print(impl[:1200] + "..." if len(impl) > 1200 else impl)
            print("```")

        else:
            print(
                "❌ **No Implementation Found** - Agent response may need clarification"
            )

        # Show additional recommendations
        if results.get("performance_recommendations"):
            print("\n⚡ **Performance Notes**: Found optimization recommendations")
        if results.get("integration_notes"):
            print("🔗 **Integration Notes**: Found integration guidance")
        if results.get("followup_needed"):
            print(
                "🔄 **Followup Needed**: "
                "Agent indicated additional clarification required"
            )


# Create global instance for easy access
def create_enhanced_commands(hook_registry: HookRegistry) -> EnhancedConstraintCommands:
    """Create enhanced commands with hook integration."""
    return EnhancedConstraintCommands(hook_registry)
