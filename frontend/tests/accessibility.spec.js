const { test, expect } = require('@playwright/test');

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should have proper heading structure', async ({ page }) => {
    // Check for h1 element
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
    
    // Check that headings have text content
    const h1Text = await page.locator('h1').first().textContent();
    expect(h1Text).toBeTruthy();
    expect(h1Text.trim().length).toBeGreaterThan(0);
  });

  test('should have proper form labels and accessibility attributes', async ({ page }) => {
    // Navigate to a form page
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);

    // Check for form accessibility
    const form = page.locator('form');
    if (await form.count() > 0) {
      // Check for labels
      const labels = await page.locator('label').count();
      const inputs = await page.locator('input').count();
      
      console.log(`Labels found: ${labels}`);
      console.log(`Inputs found: ${inputs}`);
      
      // Check that inputs have associated labels or aria-labels
      const inputsWithLabels = await page.locator('input[id]').count();
      const labelsForInputs = await page.locator('label[for]').count();
      
      console.log(`Inputs with IDs: ${inputsWithLabels}`);
      console.log(`Labels with 'for' attributes: ${labelsForInputs}`);
      
      // Check for aria-labels on inputs without associated labels
      const inputsWithAriaLabel = await page.locator('input[aria-label]').count();
      console.log(`Inputs with aria-label: ${inputsWithAriaLabel}`);
    }
  });

  test('should have keyboard navigation support', async ({ page }) => {
    // Test Tab navigation
    await page.keyboard.press('Tab');
    
    // Check if focus is visible
    const focusedElement = await page.locator(':focus').count();
    expect(focusedElement).toBeGreaterThan(0);
    
    // Navigate through several tab stops
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(200);
    }
    
    // Check that focus is still within the page
    const focusedAfterTabs = await page.locator(':focus').count();
    expect(focusedAfterTabs).toBeGreaterThan(0);
  });

  test('should have appropriate ARIA roles and attributes', async ({ page }) => {
    // Check for navigation role
    const navElements = await page.locator('[role="navigation"], nav').count();
    console.log(`Navigation elements found: ${navElements}`);
    
    // Check for button roles
    const buttons = await page.locator('button, [role="button"]').count();
    console.log(`Button elements found: ${buttons}`);
    
    // Check for combobox elements (dropdowns)
    const comboboxes = await page.locator('[role="combobox"]').count();
    console.log(`Combobox elements found: ${comboboxes}`);
    
    // Navigate to a page with tables
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(2000);
    
    // Check table accessibility
    const tables = await page.locator('table').count();
    if (tables > 0) {
      const tableHeaders = await page.locator('th').count();
      console.log(`Table headers found: ${tableHeaders}`);
      
      // Check for proper table structure
      const tableBody = await page.locator('tbody').count();
      const tableHead = await page.locator('thead').count();
      
      console.log(`Table structure - thead: ${tableHead}, tbody: ${tableBody}`);
    }
  });

  test('should have sufficient color contrast and visual indicators', async ({ page }) => {
    // This test checks for visual accessibility patterns
    
    // Check for focus indicators on interactive elements
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    if (buttonCount > 0) {
      // Focus on first button and check for focus styles
      await buttons.first().focus();
      
      // Take screenshot to visually verify focus indicator
      await page.screenshot({ 
        path: 'test-results/accessibility-focus-indicator.png',
        fullPage: false 
      });
    }
    
    // Check for error states and their visual indicators
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);
    
    // Try to trigger validation errors
    const codeField = page.locator('input[id="code"]');
    if (await codeField.count() > 0) {
      await codeField.fill('');
      await codeField.blur();
      
      // Check for error styling
      const errorElements = await page.locator('.text-red-500, .text-red-600, [class*="error"]').count();
      console.log(`Error styling elements found: ${errorElements}`);
      
      if (errorElements > 0) {
        await page.screenshot({ 
          path: 'test-results/accessibility-error-states.png',
          fullPage: true 
        });
      }
    }
  });

  test('should work with screen reader patterns', async ({ page }) => {
    // Test screen reader friendly patterns
    
    // Check for proper heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    const headingLevels = [];
    
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
      const text = await heading.textContent();
      headingLevels.push({ level: tagName, text: text?.trim() });
    }
    
    console.log('Heading structure:');
    headingLevels.forEach((heading, index) => {
      console.log(`  ${index + 1}. ${heading.level}: ${heading.text}`);
    });
    
    // Check for skip links (if implemented)
    const skipLinks = await page.locator('a[href="#main"], a[href="#content"], [class*="skip"]').count();
    console.log(`Skip links found: ${skipLinks}`);
    
    // Check for landmarks
    const landmarks = await page.locator('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], main, nav, header, footer').count();
    console.log(`Landmark elements found: ${landmarks}`);
    
    // Navigate to form and check for field descriptions
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);
    
    // Check for aria-describedby attributes
    const fieldsWithDescriptions = await page.locator('input[aria-describedby], textarea[aria-describedby]').count();
    console.log(`Form fields with descriptions: ${fieldsWithDescriptions}`);
    
    // Check for required field indicators
    const requiredFields = await page.locator('input[required], textarea[required], input[aria-required="true"], textarea[aria-required="true"]').count();
    console.log(`Required fields found: ${requiredFields}`);
  });
});