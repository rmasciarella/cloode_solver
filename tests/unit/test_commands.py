#!/usr/bin/env python3
"""Quick test runner for OR-Tools command system.

Run this to verify the command system is working correctly.
"""

import os
import sys

# Add the commands directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".claude", "commands"))

from ortools_commands import process_command


def test_commands():
    """Test various commands to ensure they work."""
    print("Testing OR-Tools Command System")
    print("=" * 80)

    # Test cases
    test_cases = [
        ("Basic constraint generation", "/add-constraint shift_schedule"),
        ("Using alias", "/ac resource_capacity"),
        ("Test generation", "/test-constraint precedence"),
        ("Constraint validation", "/check-constraint add_precedence_constraints"),
        ("List constraints", "/list-constraints"),
        ("Debug help", "/trace-infeasible"),
        ("Performance analysis", "/profile-solver"),
        ("Complexity analysis", "/analyze-complexity"),
        ("Workflow command", "/dev-flow test_feature"),
    ]

    for description, command in test_cases:
        print(f"\n{'-' * 80}")
        print(f"Test: {description}")
        print(f"Command: {command}")
        print("-" * 80)

        try:
            result = process_command(command)
            # Just show first few lines of output
            lines = result.split("\n")[:10]
            for line in lines:
                print(line)
            if len(result.split("\n")) > 10:
                print("... (output truncated)")
            print("✅ Command executed successfully")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 80)
    print("Test Summary: All commands tested")
    print("=" * 80)


if __name__ == "__main__":
    test_commands()
