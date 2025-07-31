const { test, expect } = require('@playwright/test');

test.describe('Form Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should handle Department form interactions', async ({ page }) => {
    // Navigate to Departments
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);

    // Check if form is present
    const form = page.locator('form');
    await expect(form).toBeVisible();

    // Fill out the form
    await page.fill('input[id="code"]', 'TEST_DEPT');
    await page.fill('input[id="name"]', 'Test Department');
    
    // Check if description field exists and fill it
    const descriptionField = page.locator('textarea[id="description"]');
    if (await descriptionField.count() > 0) {
      await descriptionField.fill('Test department description');
    }

    // Take screenshot of filled form
    await page.screenshot({ 
      path: 'test-results/department-form-filled.png',
      fullPage: true 
    });

    // Test form validation by clearing required fields
    await page.fill('input[id="code"]', '');
    
    // Try to submit empty form
    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();
      
      // Check for validation messages
      await page.waitForTimeout(1000);
      
      // Look for error indicators
      const errorElements = await page.locator('[class*="error"], .text-red-500, .text-red-600').count();
      console.log(`Form validation errors found: ${errorElements}`);
    }
  });

  test('should handle Machine form interactions', async ({ page }) => {
    // Navigate to Machines
    await page.click('button:has-text("Resources")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Machines")');
    await page.waitForTimeout(1000);

    // Check if form is present
    const form = page.locator('form');
    await expect(form).toBeVisible();

    // Fill out basic machine fields
    const codeField = page.locator('input[id="code"]');
    if (await codeField.count() > 0) {
      await codeField.fill('MACHINE_001');
    }
    
    const nameField = page.locator('input[id="name"]');
    if (await nameField.count() > 0) {
      await nameField.fill('Test Machine');
    }

    // Test dropdown/select interactions
    const dropdowns = page.locator('[role="combobox"]');
    const dropdownCount = await dropdowns.count();
    
    for (let i = 0; i < Math.min(dropdownCount, 2); i++) {
      await dropdowns.nth(i).click();
      await page.waitForTimeout(500);
      
      // Try to select first available option
      const options = page.locator('[role="option"]');
      if (await options.count() > 0) {
        await options.first().click();
      }
      await page.waitForTimeout(500);
    }

    // Take screenshot
    await page.screenshot({ 
      path: 'test-results/machine-form-interaction.png',
      fullPage: true 
    });
  });

  test('should test all form pages for basic functionality', async ({ page }) => {
    const formPages = [
      { section: 'Organization', page: 'Departments' },
      { section: 'Organization', page: 'Work Cells' },
      { section: 'Resources', page: 'Machines' },
      { section: 'Resources', page: 'Operators' },
      { section: 'Templates', page: 'Job Templates' },
      { section: 'Jobs', page: 'Job Instances' }
    ];

    const results = [];

    for (const formPage of formPages) {
      try {
        // Navigate to the page
        await page.click(`button:has-text("${formPage.section}")`);
        await page.waitForTimeout(500);
        await page.click(`button:has-text("${formPage.page}")`);
        await page.waitForTimeout(1000);

        // Check for form presence
        const formExists = await page.locator('form').count() > 0;
        
        // Count input fields
        const inputCount = await page.locator('input, textarea, select, [role="combobox"]').count();
        
        // Check for tables
        const tableExists = await page.locator('table').count() > 0;
        
        // Look for error states
        const errorCount = await page.locator('[class*="error"], .text-red-500, .text-red-600').count();

        results.push({
          section: formPage.section,
          page: formPage.page,
          hasForm: formExists,
          inputCount: inputCount,
          hasTable: tableExists,
          errorCount: errorCount
        });

        // Take screenshot
        await page.screenshot({ 
          path: `test-results/form-${formPage.page.toLowerCase().replace(/\s+/g, '-')}.png`,
          fullPage: true 
        });

      } catch (error) {
        results.push({
          section: formPage.section,
          page: formPage.page,
          error: error.message
        });
      }
    }

    // Log results for analysis
    console.log('Form page analysis results:');
    results.forEach(result => {
      console.log(`${result.section} > ${result.page}:`);
      if (result.error) {
        console.log(`  ❌ Error: ${result.error}`);
      } else {
        console.log(`  📝 Form: ${result.hasForm ? 'Yes' : 'No'}`);
        console.log(`  📊 Inputs: ${result.inputCount}`);
        console.log(`  📋 Table: ${result.hasTable ? 'Yes' : 'No'}`);
        console.log(`  ⚠️  Errors: ${result.errorCount}`);
      }
    });

    // Ensure at least some forms were found
    const formsFound = results.filter(r => r.hasForm).length;
    expect(formsFound).toBeGreaterThan(0);
  });
});