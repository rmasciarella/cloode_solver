#!/usr/bin/env python3
"""Demonstration of Enhanced Constraint Commands with Hook Integration.

This demonstrates the new constraint development lifecycle hooks that automate:
- Constraint function generation following STANDARDS.md
- Automated test generation with GIVEN-WHEN-THEN pattern
- Standards compliance validation
- Integration recommendations

Usage:
    python .claude/demo_enhanced_commands.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the hook system components
sys.path.insert(0, str(project_root / ".claude"))

from commands.constraint_commands import create_enhanced_commands  # noqa: E402
from hooks.hook_registry import registry  # noqa: E402


def demo_add_constraint():
    """Demonstrate enhanced /add-constraint command."""
    print("🔧 **Demo: Enhanced /add-constraint Command**\n")

    # Create enhanced commands instance
    commands = create_enhanced_commands(registry)

    # Test Phase 2 constraint creation (matching your current development)
    print("Creating Phase 2 skill-based constraint...")
    results = commands.add_constraint("advanced_skill_matching")

    return results


def demo_test_constraint():
    """Demonstrate enhanced /test-constraint command."""
    print("\n🧪 **Demo: Enhanced /test-constraint Command**\n")

    commands = create_enhanced_commands(registry)
    results = commands.test_constraint("advanced_skill_matching")

    print(f"Generated test file path: {results.get('test_file_path')}")
    print("\nTest preview:")
    print("```python")
    test_code = results.get("generated_tests", "")
    print(test_code[:500] + "..." if len(test_code) > 500 else test_code)
    print("```")

    return results


def demo_check_constraint():
    """Demonstrate enhanced /check-constraint command."""
    print("\n✅ **Demo: Enhanced /check-constraint Command**\n")

    # Sample constraint function for validation
    sample_constraint = '''def add_skill_validation_constraints(
    model: cp_model.CpModel,
    task_starts: TaskStartDict,
    task_ends: TaskEndDict,
    task_operator_assigned: TaskOperatorAssignedDict,
    problem: SchedulingProblem
) -> None:
    """Skill validation constraints.

    Mathematical formulation:
        For each task t and operator o: if assigned(t,o) then skill_match(t,o) = 1

    Business logic:
        Only assign operators who have required skills for the task.

    Constraints added:
        - Skill matching constraints for all task-operator pairs

    Performance considerations:
        - O(n*m) where n=tasks, m=operators
    """
    for task_key, task in problem.tasks.items():
        for operator in problem.operators:
            # Add skill matching constraint
            pass'''

    commands = create_enhanced_commands(registry)
    results = commands.check_constraint("skill_validation", sample_constraint)

    score = results.get("compliance_score", 0.0)
    print(f"Compliance Score: {score:.1%}")

    validation = results.get("validation_results", {})
    print("\nValidation Results:")
    for key, value in validation.items():
        if isinstance(value, bool):
            print(f"  • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")
        elif isinstance(value, int | float):
            print(f"  • {key.replace('_', ' ').title()}: {value}")

    recommendations = results.get("recommendations", [])
    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  • {rec}")

    return results


def demo_hook_system():
    """Demonstrate the hook system capabilities."""
    print("\n🔗 **Demo: Hook System Overview**\n")

    # Show registered hooks
    hooks = registry.list_hooks()
    print("Registered Hooks:")
    for hook_name, functions in hooks.items():
        if functions:  # Only show hooks that have functions
            print(f"  • {hook_name}: {len(functions)} functions")
            for func_name in functions:
                print(f"    - {func_name}")

    print(f"\nTotal Hook Points: {len([h for h in hooks.values() if h])}")
    print(f"Total Hook Functions: {sum(len(funcs) for funcs in hooks.values())}")


def main():
    """Run all demonstrations."""
    print("🚀 **Enhanced Constraint Development Lifecycle Demo**")
    print("=" * 60)

    try:
        # Demo the main commands
        demo_add_constraint()
        demo_test_constraint()
        demo_check_constraint()
        demo_hook_system()

        print("\n" + "=" * 60)
        print("✨ **Demo Complete!**")
        print("\nThe enhanced constraint commands provide:")
        print("  • Automated constraint function generation")
        print("  • Auto-generated comprehensive test suites")
        print("  • Real-time STANDARDS.md compliance validation")
        print("  • Intelligent file location suggestions")
        print("  • Extensible hook system for custom workflows")
        print("\nTo use in your workflow:")
        print("  1. Copy the enhanced commands to your development environment")
        print("  2. Use `/add-constraint <name>` for automated constraint creation")
        print("  3. Follow the suggested file locations and recommendations")
        print("  4. Extend with custom hooks as needed")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
