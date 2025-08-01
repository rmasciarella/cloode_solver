#!/usr/bin/env python3
"""Fresh Solver GUI Launcher.

Easy startup script for the data entry interface.
"""

import os
import sys
from pathlib import Path

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


def check_requirements():
    """Check if required packages are installed."""
    import importlib.util

    missing_packages = []

    # Check packages using importlib.util.find_spec
    packages_to_check = [
        ("tkinter", "tkinter"),
        ("supabase", "supabase"),
        ("dotenv", "python-dotenv"),
    ]

    for module_name, package_name in packages_to_check:
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements_gui.txt")
        return False

    print("✅ All required packages are installed")
    return True


def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment configuration...")

    # Check for environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key:
        print("✅ Supabase configuration found in environment variables")
        print(f"   URL: {supabase_url[:50]}...")
        return True
    else:
        print("⚠️  Supabase configuration not found in environment")
        print("   You can still run the GUI and configure connection manually")
        print("   Or set environment variables:")
        print("   export SUPABASE_URL=your_supabase_url")
        print("   export SUPABASE_ANON_KEY=your_anon_key")
        return False


def main():
    """Launch the GUI application."""
    print("🚀 Fresh Solver GUI Launcher")
    print("=" * 50)

    # Check Python version

    print(
        f"✅ Python version: {sys.version_info.major}."
        f"{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # Check requirements
    if not check_requirements():
        return 1

    # Check environment
    check_environment()

    print("\n🎯 Starting Fresh Solver GUI...")
    print("=" * 50)

    try:
        # Import and run the GUI
        from gui_app import main as run_gui

        run_gui()

    except ImportError as e:
        print(f"❌ Failed to import GUI modules: {e}")
        print("   Make sure all files are in the same directory:")
        print("   - gui_app.py")
        print("   - gui_forms.py")
        print("   - run_gui.py")
        return 1

    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        return 1

    print("\n👋 GUI closed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
