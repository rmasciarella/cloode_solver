const { test, expect } = require('@playwright/test');

test.describe('Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the homepage successfully', async ({ page }) => {
    // Check that the page loads
    await expect(page).toHaveTitle(/Fresh Solver|nextjs/);
    
    // Check for main heading
    await expect(page.locator('h1')).toBeVisible();
    
    // Check for navigation sidebar
    await expect(page.locator('nav')).toBeVisible();
  });

  test('should navigate through all main sections', async ({ page }) => {
    const sections = [
      { title: 'Organization', items: ['Departments', 'Work Cells', 'Business Calendars'] },
      { title: 'Templates', items: ['Job Templates', 'Template Tasks'] },
      { title: 'Resources', items: ['Machines', 'Operators', 'Skills', 'Sequence Resources'] },
      { title: 'Scheduling', items: ['Setup Times'] },
      { title: 'Jobs', items: ['Job Instances'] }
    ];

    for (const section of sections) {
      // Expand section if collapsed
      const sectionButton = page.locator(`button:has-text("${section.title}")`);
      await sectionButton.click();
      
      // Wait for section to expand
      await page.waitForTimeout(500);
      
      // Test each item in the section
      for (const item of section.items) {
        const navItem = page.locator(`button:has-text("${item}")`);
        if (await navItem.count() > 0) {
          await navItem.click();
          await page.waitForTimeout(1000);
          
          // Check that we navigated successfully
          await expect(page.locator('h2')).toBeVisible();
          
          // Take screenshot for visual verification
          await page.screenshot({ 
            path: `test-results/nav-${item.toLowerCase().replace(/\s+/g, '-')}.png`,
            fullPage: true 
          });
        }
      }
    }
  });

  test('should display proper error handling for missing pages', async ({ page }) => {
    // Try to navigate to a non-existent route
    const response = await page.goto('/non-existent-page');
    expect(response?.status()).toBe(404);
  });
});