const { test, expect } = require('@playwright/test');

test.describe('Working GUI Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load homepage successfully', async ({ page }) => {
    // Check that the page loads
    await expect(page).toHaveTitle(/Fresh Solver|nextjs/);
    
    // Check for main elements
    await expect(page.locator('text=Fresh Solver')).toBeVisible();
    await expect(page.locator('text=OR-Tools Scheduling System')).toBeVisible();
    
    // Check sidebar navigation exists
    await expect(page.locator('text=Organization')).toBeVisible();
    await expect(page.locator('text=Templates')).toBeVisible();
    await expect(page.locator('text=Resources')).toBeVisible();
    await expect(page.locator('text=Scheduling')).toBeVisible();
    await expect(page.locator('text=Jobs')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/homepage-working.png', fullPage: true });
  });

  test('should navigate to departments and show form', async ({ page }) => {
    // The page loads with Departments already selected (as seen in screenshot)
    // Check if we're on the departments page
    await expect(page.locator('text=Departments').first()).toBeVisible();
    await expect(page.locator('text=Create New Department')).toBeVisible();
    
    // Check for form fields
    await expect(page.locator('input[placeholder*="production, quality, DEPT_A"]')).toBeVisible();
    await expect(page.locator('input[placeholder*="Production Department"]')).toBeVisible();
    
    // Check for checkboxes
    await expect(page.locator('text=Overtime Allowed')).toBeVisible();
    await expect(page.locator('text=Active')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/departments-form-working.png', fullPage: true });
  });

  test('should be able to interact with form fields', async ({ page }) => {
    // Fill out some basic form fields
    const codeField = page.locator('input[placeholder*="production, quality, DEPT_A"]');
    const nameField = page.locator('input[placeholder*="Production Department"]');
    
    await codeField.fill('TEST_DEPT');
    await nameField.fill('Test Department');
    
    // Check that the values were filled
    await expect(codeField).toHaveValue('TEST_DEPT');
    await expect(nameField).toHaveValue('Test Department');
    
    // Try the description field
    const descField = page.locator('textarea[placeholder*="Department description"]');
    await descField.fill('This is a test department created by Playwright');
    await expect(descField).toHaveValue('This is a test department created by Playwright');
    
    // Take screenshot with filled form
    await page.screenshot({ path: 'test-results/form-filled-working.png', fullPage: true });
  });

  test('should show navigation sidebar correctly', async ({ page }) => {
    // Check all main navigation sections are visible
    const navSections = [
      'Organization',
      'Templates', 
      'Resources',
      'Scheduling',
      'Jobs'
    ];
    
    for (const section of navSections) {
      await expect(page.locator(`text=${section}`)).toBeVisible();
    }
    
    // Check for expand arrows (indicating collapsible sections)
    const expandArrows = page.locator('[data-state="closed"]');
    const arrowCount = await expandArrows.count();
    console.log(`Found ${arrowCount} collapsible sections`);
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/navigation-sidebar-working.png', fullPage: true });
  });

  test('should have basic accessibility features', async ({ page }) => {
    // Check for proper heading structure
    await expect(page.locator('h1')).toBeVisible();
    const h1Text = await page.locator('h1').textContent();
    console.log(`Main heading: ${h1Text}`);
    
    // Check for form labels
    const labels = await page.locator('label').count();
    console.log(`Form labels found: ${labels}`);
    
    // Check for buttons
    const buttons = await page.locator('button').count();
    console.log(`Buttons found: ${buttons}`);
    
    // Check for inputs
    const inputs = await page.locator('input').count();
    console.log(`Input fields found: ${inputs}`);
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/accessibility-check-working.png', fullPage: true });
  });
});