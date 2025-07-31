const { test, expect } = require('@playwright/test');

test('Debug navigation', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Take screenshot of initial state
  await page.screenshot({ path: 'gui/test-results/debug-initial.png', fullPage: true });
  
  // Get all sections
  const sections = await page.locator('[data-testid*="section-"]').all();
  console.log(`Found ${sections.length} sections`);
  
  for (let i = 0; i < sections.length; i++) {
    const testId = await sections[i].getAttribute('data-testid');
    const text = await sections[i].textContent();
    console.log(`Section ${i}: ${testId} - ${text?.substring(0, 50)}`);
  }
  
  // Try clicking templates section
  console.log('Clicking templates section...');
  await page.click('[data-testid="section-templates"]');
  await page.waitForTimeout(2000);
  
  // Take screenshot after click
  await page.screenshot({ path: 'gui/test-results/debug-after-templates.png', fullPage: true });
  
  // Check all nav items
  const navItems = await page.locator('[data-testid*="nav-"]').all();
  console.log(`Found ${navItems.length} nav items`);
  
  for (let i = 0; i < navItems.length; i++) {
    const testId = await navItems[i].getAttribute('data-testid');
    const isVisible = await navItems[i].isVisible();
    console.log(`Nav ${i}: ${testId} - visible: ${isVisible}`);
  }
});