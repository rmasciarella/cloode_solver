#!/usr/bin/env python3
"""Use Playwright to capture and check the setup time visualization."""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def capture_visualization():
    """Capture the setup time visualization using Playwright."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set viewport size for better capture
        await page.set_viewport_size({"width": 1400, "height": 900})

        # Navigate to the visualization
        file_path = Path("output/setup_time_demo/index.html").absolute()
        await page.goto(f"file://{file_path}")

        # Wait for the visualization to load
        await page.wait_for_timeout(2000)

        # Take screenshot
        screenshot_path = "output/setup_time_demo/visualization_check.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to: {screenshot_path}")

        # Check for key elements
        print("\nChecking visualization elements:")

        # Check if chart is visible
        chart_visible = await page.is_visible("#ganttChart")
        print(f"✓ Gantt chart visible: {chart_visible}")

        # Check for task rectangles
        task_count = await page.locator(".task-rect").count()
        print(f"✓ Task rectangles found: {task_count}")

        # Check for setup rectangles (gold blocks)
        setup_count = await page.locator(".setup-rect").count()
        print(f"✓ Setup time blocks found: {setup_count}")

        # Check if metadata panel is visible
        metadata_visible = await page.is_visible("#metadataPanel")
        print(f"✓ Metadata panel visible: {metadata_visible}")

        # Check if machine stats are visible
        machine_stats_visible = await page.is_visible("#machineStats")
        print(f"✓ Machine stats visible: {machine_stats_visible}")

        # Check if setup stats are visible
        setup_stats_visible = await page.is_visible("#setupStats")
        print(f"✓ Setup stats panel visible: {setup_stats_visible}")

        # Get setup statistics values
        if setup_stats_visible:
            total_setup = await page.text_content("#totalSetupTime")
            num_setups = await page.text_content("#numSetups")
            avg_setup = await page.text_content("#avgSetupTime")
            setup_percentage = await page.text_content("#setupPercentage")

            print("\nSetup Statistics:")
            print(f"  - Total Setup Time: {total_setup}")
            print(f"  - Number of Setups: {num_setups}")
            print(f"  - Average Setup Time: {avg_setup}")
            print(f"  - Setup as % of Makespan: {setup_percentage}")

        # Check for warnings (should be none)
        warnings_visible = await page.is_visible("#warningsPanel")
        print(f"\n✓ Warnings panel visible: {warnings_visible} (should be False)")

        # Check machine utilization
        print("\nMachine Utilization:")
        machine_items = await page.locator(".machine-stat-item").all()
        for item in machine_items:
            label = await item.locator(".machine-stat-label").text_content()
            utilization = await item.locator(".utilization-text").text_content()
            print(f"  - {label}: {utilization}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_visualization())
