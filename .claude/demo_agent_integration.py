#!/usr/bin/env python3
"""Demo: Agent-Integrated Constraint Development Workflow.

Shows how the enhanced hook system integrates with your
@agent-⋌༼ •̀ ⌂ •́ ༽⋋ Ortools Model Expert for expert constraint implementation.
"""

import sys
from pathlib import Path

# Add the hooks directory to path
hooks_path = Path(__file__).parent / "hooks"
commands_path = Path(__file__).parent / "commands"
sys.path.extend([str(hooks_path), str(commands_path)])

try:
    from agent_integration import AgentIntegrationHooks
    from constraint_commands import create_enhanced_commands
    from hook_registry import HookRegistry

    print("🤖 **Agent-Integrated Constraint Development Demo**")
    print("=" * 70)

    # Create enhanced commands with agent integration
    registry = HookRegistry()
    commands = create_enhanced_commands(registry)

    # Demo 1: Enhanced /add-constraint with agent recommendation
    print("\n🔧 **Demo 1: Enhanced /add-constraint with Agent Integration**")
    print("Creating Phase 2 advanced skill matching constraint...")

    results = commands.add_constraint("advanced_skill_matching")

    # The output above shows the agent workflow recommendation

    # Demo 2: Show the agent command that would be generated
    print("\n🤖 **Demo 2: Agent Command Generation**")

    constraint_name = "advanced_skill_matching"

    # Create a minimal context for demonstration
    from hook_registry import HookContext

    context = HookContext(
        command="demo_agent_command",
        phase="phase2",
        constraint_name=constraint_name,
        constraint_type=constraint_name,
    )

    agent_command = AgentIntegrationHooks.create_agent_prompt(
        context, "ortools_model_expert"
    )
    agent_name = AgentIntegrationHooks.AVAILABLE_AGENTS["ortools_model_expert"]["name"]

    print(f"For constraint '{constraint_name}', the system would generate:")
    print(f"@agent-{agent_name} [specialized prompt with full context]")
    print("\nPrompt includes:")
    print("  • Template-based architecture context")
    print("  • Phase 2 operator assignment requirements")
    print("  • STANDARDS.md compliance requirements")
    print("  • Integration with existing constraints")
    print("  • Performance optimization targets")

    # Demo 3: Show what happens when you get an agent response
    print("\n📝 **Demo 3: Processing Agent Response**")

    # Simulate an agent response
    # (what you'd get from @agent-⋌༼ •̀ ⌂ •́ ༽⋋ Ortools Model Expert)
    sample_agent_response = '''I'll implement the advanced_skill_matching constraint
for your OR-Tools scheduling system.

Looking at your template-based architecture and Phase 2 requirements,
here's the optimal implementation:

```python
def add_advanced_skill_matching_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    task_ends: TaskEndDict,
    task_operator_assigned: TaskOperatorAssignedDict,
    problem: SchedulingProblem
) -> Optional[Dict[str, cp_model.IntVar]]:
    """Advanced skill matching constraints with proficiency optimization.

    Mathematical formulation:
        For each task t and operator o:
        - If assigned(t,o) = 1 then skill_level(o, required_skill(t)) >= min_level(t)
        - Efficiency(t,o) = base_efficiency * skill_multiplier(o, skill(t))

    Business logic:
        Assigns operators based on skill requirements and optimizes
        for proficiency levels.
        Higher skilled operators complete tasks faster with efficiency bonuses.

    Args:
        model: The CP-SAT model to add constraints to
        task_starts: Dictionary of task start variables
        task_ends: Dictionary of task end variables
        task_operator_assigned: Dictionary of task-operator assignment variables
        problem: Scheduling problem containing all data

    Returns:
        Dictionary of efficiency variables for performance optimization

    Constraints added:
        - Skill requirement satisfaction constraints
        - Efficiency variable bounds based on operator proficiency
        - Mutual exclusion for operators across simultaneous tasks

    Performance considerations:
        - O(n*m*s) complexity where n=tasks, m=operators, s=skills
        - Uses interval variables for efficient no-overlap constraints
        - Template-optimized for O(template_size × instances) scaling
    """
    logger.info("Adding advanced skill matching constraints...")

    efficiency_vars = {}

    # For template-based problems, leverage shared structure
    if problem.is_template_based:
        # Process by template structure for optimal performance
        for instance in problem.job_instances:
            for template_task in problem.job_template.template_tasks:
                task_key = (instance.instance_id, template_task.template_task_id)

                if task_key not in task_starts:
                    continue

                required_skill = template_task.required_skill
                min_skill_level = template_task.min_skill_level

                for operator in problem.operators:
                    op_key = (
                        instance.instance_id,
                        template_task.template_task_id,
                        operator.operator_id
                    )

                    if op_key not in task_operator_assigned:
                        continue

                    # Create efficiency variable
                    efficiency_vars[op_key] = model.NewIntVar(
                        50, 150, f'efficiency_{op_key[0]}_{op_key[1]}_{op_key[2]}'
                    )

                    # Skill matching constraint
                    operator_skill_level = operator.get_skill_level(required_skill)
                    if operator_skill_level < min_skill_level:
                        # Operator cannot be assigned to this task
                        model.Add(task_operator_assigned[op_key] == 0)
                    else:
                        # Set efficiency based on skill level
                        skill_bonus = min(
                            50, (operator_skill_level - min_skill_level) * 10
                        )
                        base_efficiency = 100

                        # Efficiency is set when operator is assigned
                        model.Add(
                            efficiency_vars[op_key] == base_efficiency + skill_bonus
                        ).OnlyEnforceIf(task_operator_assigned[op_key])

                        # Default efficiency when not assigned
                        model.Add(
                            efficiency_vars[op_key] == base_efficiency
                        ).OnlyEnforceIf(task_operator_assigned[op_key].Not())
    else:
        # Legacy job-based processing
        for job in problem.jobs:
            for task in job.tasks:
                task_key = (job.job_id, task.task_id)
                # Similar logic for legacy structure...

    return efficiency_vars
```

**Performance Optimization Notes:**
- Uses template structure for O(template × instances) complexity
- Efficiency variables enable duration optimization based on operator skill
- Integrates seamlessly with your existing capacity and setup time constraints

**Integration Points:**
- Returns efficiency_vars for use in objective function optimization
- Compatible with your unattended task and WorkCell capacity constraints
- Maintains 5-8x template performance improvements

The implementation leverages your template-based architecture for optimal performance
while providing the skill-based operator assignment needed for Phase 2.'''

    # Process the agent response
    processed = commands.process_agent_response(
        "advanced_skill_matching", sample_agent_response
    )

    # Demo 4: Show available agents and their specializations
    print("\n🎯 **Demo 4: Available Agent Specializations**")

    agents = AgentIntegrationHooks.AVAILABLE_AGENTS
    for _agent_key, agent_info in agents.items():
        print(f"\n📋 **{agent_info['name']}**")
        print(f"   • Specializes in: {', '.join(agent_info['specializes_in'])}")
        print(f"   • Best for: {', '.join(agent_info['best_for'])}")

    # Demo 5: Agent recommendation logic
    print("\n🧠 **Demo 5: Agent Recommendation Logic**")

    test_constraints = [
        ("basic_precedence", "No agent needed - simple Phase 1 constraint"),
        (
            "advanced_skill_optimization",
            "OR-Tools Expert - complex Phase 2 optimization",
        ),
        ("template_performance_tuning", "OR-Tools Expert - template optimization"),
        ("multi_objective_pareto", "OR-Tools Expert - complex Phase 3 optimization"),
        ("simple_duration", "No agent needed - basic constraint"),
    ]

    print("Constraint recommendation analysis:")
    for constraint_name, expected in test_constraints:
        # Create mock context for recommendation test
        mock_context = HookContext(
            command="test_recommendation",
            phase="phase1",  # Will be overridden by detection
            constraint_name=constraint_name,
        )

        # Detect phase based on constraint name patterns
        if any(
            keyword in constraint_name for keyword in ["skill", "operator", "advanced"]
        ):
            mock_context.phase = "phase2"
        elif any(
            keyword in constraint_name for keyword in ["multi_objective", "pareto"]
        ):
            mock_context.phase = "phase3"

        recommended = AgentIntegrationHooks.should_use_agent(mock_context)

        agent_name = agents[recommended]["name"] if recommended else "None"
        print(f"  • {constraint_name} → {agent_name}")
        print(f"    Expected: {expected}")

    print("\n" + "=" * 70)
    print("✨ **Agent Integration Benefits:**")

    print("\n🔧 **For Constraint Development:**")
    print("  • Automatic agent recommendation based on constraint complexity")
    print("  • Pre-configured prompts with full project context")
    print("  • Specialized OR-Tools expertise for complex constraints")
    print("  • Template-aware optimization recommendations")

    print("\n⚡ **For Your Phase 2 Development:**")
    print("  • Expert skill-based constraint implementation")
    print("  • Performance optimization for operator assignment")
    print("  • Integration with existing template architecture")
    print("  • Maintains 5-8x performance improvements")

    print("\n🚀 **Enhanced Workflow:**")
    print("  1. `/add-constraint advanced_skill_matching`")
    print("  2. System recommends @agent-⋌༼ •̀ ⌂ •́ ༽⋋ Ortools Model Expert")
    print("  3. Copy/paste generated agent command")
    print("  4. Agent provides expert OR-Tools implementation")
    print("  5. System validates and provides integration guidance")
    print("  6. Save and integrate with automatic standards compliance")

    print("\n🎯 **Perfect for Your Current Phase 2 Development:**")
    print("  • Advanced skill matching constraints")
    print("  • Multi-operator coordination")
    print("  • Shift calendar integration")
    print("  • Operator proficiency optimization")
    print("  • All with maintained template performance gains")

    print("\n" + "=" * 70)
    print("🤖 **Agent Integration Ready!**")
    print("\nYour enhanced `/add-constraint` now automatically:")
    print("  ✅ Recommends appropriate agent for complex constraints")
    print("  ✅ Generates context-rich prompts for OR-Tools expertise")
    print("  ✅ Processes agent responses with validation")
    print("  ✅ Provides integration guidance and file suggestions")
    print("  ✅ Maintains full STANDARDS.md compliance")
    print("  ✅ Preserves template-based performance optimizations")

except ImportError as e:
    print(f"Import error: {e}")
    print("The agent integration modules may need Python path adjustments.")
except Exception as e:
    print(f"Demo error: {e}")
    import traceback

    traceback.print_exc()
