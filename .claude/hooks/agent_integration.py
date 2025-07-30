"""Agent Integration Hooks for OR-Tools Development.

Provides hooks that can invoke specific agents for constraint implementation,
combining automated workflow with expert agent knowledge.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from hook_registry import HookContext, register_hook

logger = logging.getLogger(__name__)


@dataclass
class AgentWorkflowContext:
    """Context for agent-assisted workflows."""

    # Agent configuration
    agent_name: str
    agent_prompt: str

    # Workflow context
    hook_context: HookContext

    # Agent execution results
    agent_response: str | None = None
    agent_success: bool = False

    # Integration metadata
    workflow_type: str = "constraint_implementation"
    requires_followup: bool = False
    followup_actions: list = field(default_factory=list)


class AgentIntegrationHooks:
    """Collection of hooks for integrating with specialized agents."""

    # Registry of available agents and their capabilities
    AVAILABLE_AGENTS = {
        "ortools_model_expert": {
            "name": "⋌༼ •̀ ⌂ •́ ༽⋋ Ortools Model Expert",
            "specializes_in": [
                "constraint_implementation",
                "model_optimization",
                "cp_sat_performance",
                "variable_formulation",
                "solver_debugging",
            ],
            "best_for": [
                "complex_constraint_logic",
                "performance_optimization",
                "solver_parameter_tuning",
                "constraint_reformulation",
            ],
        },
        "implementation_specialist": {
            "name": "implementation-specialist",
            "specializes_in": [
                "clean_code_implementation",
                "design_patterns",
                "maintainable_architecture",
            ],
            "best_for": [
                "code_structure_optimization",
                "design_pattern_application",
                "code_quality_improvement",
            ],
        },
    }

    @staticmethod
    def should_use_agent(context: HookContext) -> str | None:
        """Determine if an agent should be used and which one."""
        # Complex Phase 2/3 constraints benefit from OR-Tools expert
        if context.phase in ["phase2", "phase3"]:
            return "ortools_model_expert"

        # Performance-critical constraints
        if any(
            keyword in context.constraint_name
            for keyword in ["optimization", "performance", "efficiency", "advanced"]
        ):
            return "ortools_model_expert"

        # Template-related constraints
        if "template" in context.constraint_name:
            return "ortools_model_expert"

        return None

    @staticmethod
    def create_agent_prompt(context: HookContext, agent_name: str) -> str:
        """Create specialized prompt for the agent based on context."""
        base_context = f"""
Implement {context.constraint_name} constraint for OR-Tools CP-SAT scheduling solver.

**Project Context:**
- Template-based optimization system with 5-8x performance improvements
- Current phase: {context.phase}
- Constraint type: {context.constraint_type}
- Following STANDARDS.md requirements (≤30 lines, full type safety)

**Requirements:**
- Function name: add_{context.constraint_name}_constraints
- Must integrate with existing template-based architecture
- Maintain performance optimizations
- Include comprehensive docstring with mathematical formulation
- Follow centralized type aliases from TEMPLATES.md

**Integration Points:**
- Works with existing Phase 1 constraints (capacity, setup_time, unattended)
- Must support both template-based and legacy job workflows
- Performance target: maintain sub-linear scaling for template instances
"""

        if agent_name == "ortools_model_expert":
            specific_prompt = f"""
**OR-Tools Expertise Needed:**
- Optimal CP-SAT constraint formulation for {context.constraint_name}
- Variable creation strategy (IntVar vs BoolVar vs IntervalVar)
- Constraint efficiency considerations
- Integration with existing OR-Tools model structure
- Solver parameter recommendations for this constraint type

**Template Performance Considerations:**
- Leverage O(template_size × instances) complexity patterns
- Consider symmetry breaking opportunities
- Optimize for parallel job instances with shared template structure
- Minimize variable explosion in large instance counts

**Expected Output:**
Complete constraint function implementation following STANDARDS.md patterns,
with focus on CP-SAT solver efficiency and template optimization compatibility.
"""
        else:
            specific_prompt = """
**Implementation Focus:**
- Clean, maintainable constraint implementation
- Proper error handling and edge case management
- Integration with existing codebase patterns
- Code quality and readability optimization
"""

        return base_context + specific_prompt

    @staticmethod
    def process_agent_response(
        agent_response: str, context: HookContext
    ) -> dict[str, Any]:
        """Process agent response and extract actionable components."""
        result = {
            "constraint_implementation": None,
            "additional_variables": None,
            "integration_notes": None,
            "performance_recommendations": None,
            "followup_needed": False,
        }

        # Try to extract code blocks
        import re

        code_blocks = re.findall(r"```python\n(.*?)\n```", agent_response, re.DOTALL)
        if code_blocks:
            # Use the largest code block as the main implementation
            result["constraint_implementation"] = max(code_blocks, key=len)

        # Extract specific sections
        if "Additional variables:" in agent_response:
            result["additional_variables"] = "Found additional variable recommendations"

        if "Performance:" in agent_response or "Optimization:" in agent_response:
            result["performance_recommendations"] = (
                "Found performance optimization suggestions"
            )

        if "Integration:" in agent_response or "Next steps:" in agent_response:
            result["integration_notes"] = "Found integration guidance"

        # Determine if followup is needed
        if any(
            phrase in agent_response.lower()
            for phrase in [
                "needs clarification",
                "additional context",
                "follow up",
                "unclear",
            ]
        ):
            result["followup_needed"] = True

        return result


# Hook implementations with agent integration


@register_hook("post_constraint_creation")
def agent_assisted_constraint_implementation(context: HookContext) -> HookContext:
    """Enhance constraint creation with agent expertise when beneficial."""
    # Determine if agent assistance would be beneficial
    recommended_agent = AgentIntegrationHooks.should_use_agent(context)

    if not recommended_agent:
        logger.info(f"No agent assistance needed for {context.constraint_name}")
        return context

    logger.info(f"Recommending {recommended_agent} for {context.constraint_name}")

    # Create agent workflow context
    agent_prompt = AgentIntegrationHooks.create_agent_prompt(context, recommended_agent)

    # Store agent recommendation in context for user decision
    context.metadata["recommended_agent"] = recommended_agent
    context.metadata["agent_prompt"] = agent_prompt
    context.metadata["agent_workflow_available"] = True

    # Add agent integration guidance to recommendations
    existing_recs = context.metadata.get("recommendations", [])
    agent_name = AgentIntegrationHooks.AVAILABLE_AGENTS[recommended_agent]["name"]
    existing_recs.append(
        f"💡 Consider using @agent-{agent_name} for expert constraint implementation"
    )
    existing_recs.append(
        f"   Agent specializes in: {', '.join(AgentIntegrationHooks.AVAILABLE_AGENTS[recommended_agent]['best_for'])}"
    )
    context.metadata["recommendations"] = existing_recs

    return context


@register_hook("constraint_integration")
def validate_agent_implementation(context: HookContext) -> HookContext:
    """Validate agent-generated constraint implementation."""
    if not context.metadata.get("agent_implementation"):
        return context

    # Validate agent implementation against standards
    agent_code = context.metadata["agent_implementation"]

    # Run the same validation as regular constraints
    from constraint_lifecycle import ConstraintLifecycleHooks

    validation = ConstraintLifecycleHooks.generate_standards_checklist(
        context.constraint_name, agent_code
    )

    # Store agent implementation validation separately
    context.metadata["agent_validation_results"] = validation

    # Check if agent implementation meets standards
    total_checks = 9
    passed = sum(
        [
            validation["naming_convention"],
            validation["line_count"] <= 30,
            validation["type_hints"],
            validation["return_type"],
            validation["docstring_complete"],
            validation["mathematical_formulation"],
            validation["business_logic"],
            validation["constraints_listed"],
            validation["performance_notes"],
        ]
    )

    agent_compliance_score = passed / total_checks
    context.metadata["agent_compliance_score"] = agent_compliance_score

    if agent_compliance_score >= 0.9:
        context.metadata["agent_implementation_approved"] = True
        logger.info(
            f"Agent implementation for {context.constraint_name} meets standards"
        )
    else:
        context.metadata["agent_implementation_approved"] = False
        context.metadata["agent_needs_revision"] = True
        logger.warning(
            f"Agent implementation needs revision (score: {agent_compliance_score:.1%})"
        )

    return context


# Helper functions for agent workflow integration


def create_agent_workflow_command(
    constraint_name: str, agent_name: str = "ortools_model_expert"
) -> str:
    """Create a command string for invoking an agent with proper context."""
    context = HookContext(
        command="agent_assisted_constraint", constraint_name=constraint_name
    )

    # Detect phase and create prompt
    from constraint_lifecycle import ConstraintLifecycleHooks

    context.phase = ConstraintLifecycleHooks.detect_constraint_phase(constraint_name)
    context.constraint_type = constraint_name

    agent_prompt = AgentIntegrationHooks.create_agent_prompt(context, agent_name)

    # Format as agent invocation
    agent_display_name = AgentIntegrationHooks.AVAILABLE_AGENTS[agent_name]["name"]

    return f"@agent-{agent_display_name} {agent_prompt}"


def process_agent_constraint_response(
    agent_response: str, constraint_name: str
) -> dict[str, Any]:
    """Process agent response for constraint implementation."""
    context = HookContext(
        command="process_agent_response", constraint_name=constraint_name
    )

    # Process the agent response
    processed = AgentIntegrationHooks.process_agent_response(agent_response, context)

    # If we got a good implementation, validate it
    if processed["constraint_implementation"]:
        context.metadata["agent_implementation"] = processed[
            "constraint_implementation"
        ]
        context = validate_agent_implementation(context)
        processed.update(context.metadata)

    return processed
