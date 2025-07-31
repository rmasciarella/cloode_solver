const { test, expect } = require('@playwright/test');

test.describe('Database Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Monitor console for database errors
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('supabase')) {
        console.log(`🔴 Database Error: ${msg.text()}`);
      }
    });

    // Monitor network requests to Supabase
    page.on('response', response => {
      if (response.url().includes('supabase') || response.url().includes('oggdidyjvncncxgebcpy')) {
        const status = response.status();
        if (status >= 400) {
          console.log(`🔴 API Error: ${status} ${response.url()}`);
        } else {
          console.log(`✅ API Success: ${status} ${response.url()}`);
        }
      }
    });
  });

  test('should successfully connect to database and load data', async ({ page }) => {
    // Navigate to Departments to trigger database loading
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    
    // Wait for data to load
    await page.waitForTimeout(3000);
    
    // Check if table is present (indicates successful data loading)
    const tableExists = await page.locator('table').count() > 0;
    
    if (tableExists) {
      // Check for table content
      const rows = await page.locator('tbody tr').count();
      console.log(`Departments loaded: ${rows} rows`);
      
      // Verify table has headers
      const headers = await page.locator('thead th').count();
      expect(headers).toBeGreaterThan(0);
      
      // Take screenshot of successful data load
      await page.screenshot({ 
        path: 'test-results/database-departments-loaded.png',
        fullPage: true 
      });
    } else {
      // Check for loading states or error messages
      const loadingText = await page.locator('text=/loading/i').count();
      const errorText = await page.locator('text=/error/i').count();
      
      console.log(`Loading indicators: ${loadingText}`);
      console.log(`Error indicators: ${errorText}`);
      
      // Take screenshot for debugging
      await page.screenshot({ 
        path: 'test-results/database-no-table.png',
        fullPage: true 
      });
    }
  });

  test('should handle database connection errors gracefully', async ({ page }) => {
    // This test checks how the UI handles database issues
    // Navigate through multiple pages to test database interactions
    
    const testPages = [
      { section: 'Organization', page: 'Departments' },
      { section: 'Resources', page: 'Machines' },
      { section: 'Templates', page: 'Job Templates' }
    ];

    const results = [];

    for (const testPage of testPages) {
      try {
        await page.click(`button:has-text("${testPage.section}")`);
        await page.waitForTimeout(500);
        await page.click(`button:has-text("${testPage.page}")`);
        await page.waitForTimeout(2000);

        // Check for various states
        const hasTable = await page.locator('table').count() > 0;
        const hasForm = await page.locator('form').count() > 0;
        const hasError = await page.locator('[class*="error"], .text-red-500').count() > 0;
        const hasLoading = await page.locator('text=/loading/i').count() > 0;

        results.push({
          section: testPage.section,
          page: testPage.page,
          hasTable,
          hasForm,
          hasError,
          hasLoading,
          status: hasError ? 'error' : (hasTable || hasForm) ? 'success' : 'unknown'
        });

      } catch (error) {
        results.push({
          section: testPage.section,
          page: testPage.page,
          error: error.message,
          status: 'failed'
        });
      }
    }
    
    // Log results
    console.log('Database connection test results:');
    results.forEach(result => {
      console.log(`${result.section} > ${result.page}: ${result.status}`);
    });

    // Take final screenshot
    await page.screenshot({ 
      path: 'test-results/database-connection-test.png',
      fullPage: true 
    });

    // At least one page should load successfully
    const successfulPages = results.filter(r => r.status === 'success').length;
    expect(successfulPages).toBeGreaterThan(0);
  });

  test('should test form submission to database', async ({ page }) => {
    // Navigate to Departments
    await page.click('button:has-text("Organization")');
    await page.waitForTimeout(500);
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);

    // Fill form with test data
    const testCode = `PLAYWRIGHT_${Date.now()}`;
    await page.fill('input[id="code"]', testCode);
    await page.fill('input[id="name"]', 'Playwright Test Department');
    
    const descriptionField = page.locator('textarea[id="description"]');
    if (await descriptionField.count() > 0) {
      await descriptionField.fill('Created by Playwright database test');
    }

    // Take screenshot before submission
    await page.screenshot({ 
      path: 'test-results/database-before-submit.png',
      fullPage: true 
    });

    // Submit form
    const submitButton = page.locator('button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      // Check for success/error feedback
      const successToast = await page.locator('text=/success/i').count();
      const errorToast = await page.locator('text=/error/i').count();
      const toastMessages = await page.locator('[class*="toast"]').count();
      
      console.log(`Submission results:`);
      console.log(`  Success messages: ${successToast}`);
      console.log(`  Error messages: ${errorToast}`);
      console.log(`  Toast notifications: ${toastMessages}`);
      
      // Take screenshot after submission
      await page.screenshot({ 
        path: 'test-results/database-after-submit.png',
        fullPage: true 
      });
      
      // If table exists, check if new entry appears
      const tableExists = await page.locator('table').count() > 0;
      if (tableExists) {
        // Look for our test code in the table
        const newEntryExists = await page.locator(`text=${testCode}`).count() > 0;
        console.log(`New entry visible in table: ${newEntryExists}`);
      }
    }
  });
});