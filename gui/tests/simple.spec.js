const { test, expect } = require('@playwright/test');

test.describe('Simple Test', () => {
  test('should load the homepage', async ({ page }) => {
    console.log('Starting test...');
    await page.goto('http://localhost:3000');
    console.log('Page loaded...');
    
    // Check that the page loads
    await expect(page).toHaveTitle(/.*/, { timeout: 10000 });
    console.log('Title check passed...');
    
    // Take screenshot
    await page.screenshot({ path: 'test-results/simple-test.png' });
    console.log('Screenshot taken...');
  });
});