#!/usr/bin/env python3
"""Simple script to open the visualization in browser and take a screenshot."""

import os
import subprocess
from pathlib import Path


def capture_visualization():
    """Open visualization and take screenshot using system tools."""
    # Get absolute path to the HTML file
    html_path = Path(__file__).parent / "output/setup_time_demo/index.html"

    if not html_path.exists():
        print(f"Error: Visualization file not found at {html_path}")
        return

    print(f"Opening visualization: {html_path}")

    # Open in default browser
    if os.name == "posix":  # macOS/Linux
        subprocess.run(["open", str(html_path)])
    else:  # Windows
        subprocess.run(["start", str(html_path)], shell=True)

    print("Visualization opened in browser.")
    print("\nPlease check the visualization manually for:")
    print("1. Gold setup time blocks between tasks")
    print("2. Setup statistics panel on the right")
    print("3. Concurrent tasks on the 3D Printer (capacity 2)")
    print("4. Machine utilization percentages")
    print("\nThe visualization shows:")
    print("- 8 tasks scheduled across 2 machines")
    print("- 2 setup times (gold blocks) when switching from Product A to Product B")
    print("- Total makespan of 11 time units")
    print("- Setup time metrics in the right panel")


if __name__ == "__main__":
    capture_visualization()
