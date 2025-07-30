#!/usr/bin/env python3
"""Quick setup script for Claude Code hooks in the modular solver project."""

import json
import subprocess
import sys
from pathlib import Path


def setup_hooks():
    """Set up recommended Claude Code hooks."""
    # Load recommended hooks
    hooks_file = Path(__file__).parent / "recommended_hooks.json"
    with open(hooks_file) as f:
        config = json.load(f)

    print("🔧 Setting up Claude Code hooks for modular solver...\n")

    # Set up each hook
    for hook in config["hooks"]:
        if not hook.get("enabled", True):
            print(f"⏭️  Skipping disabled hook: {hook['name']}")
            continue

        try:
            cmd = ["claude", "code", "hooks", "add", hook["event"], hook["command"]]

            if "pattern" in hook:
                cmd.extend(["--pattern", hook["pattern"]])

            if "description" in hook:
                cmd.extend(["--description", hook["description"]])

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Added hook: {hook['name']}")
            else:
                print(f"❌ Failed to add hook: {hook['name']}")
                print(f"   Error: {result.stderr}")

        except Exception as e:
            print(f"❌ Error setting up hook {hook['name']}: {e}")

    print("\n📋 Current hooks:")
    subprocess.run(["claude", "code", "hooks", "list"])

    print("\n✨ Setup complete! Hooks are now active.")
    print("\nUseful commands:")
    print("  - List hooks:    claude code hooks list")
    print("  - Disable hook:  claude code hooks disable <hook-id>")
    print("  - Remove hook:   claude code hooks remove <hook-id>")
    print("  - View logs:     claude code hooks logs")


def main():
    """Execute the main setup workflow."""
    # Check if Claude Code is available
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Claude Code CLI not found. Please ensure it's installed and in PATH.")
        sys.exit(1)

    setup_hooks()


if __name__ == "__main__":
    main()
