const { test, expect } = require('@playwright/test');

test('Debug section expansion', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  
  console.log('Initial state...');
  let navItems = await page.locator('[data-testid*="nav-"]').all();
  console.log(`Visible nav items: ${navItems.length}`);
  
  // Click Templates section (note the capital T)
  console.log('Clicking Templates section...');
  await page.click('[data-testid="section-templates"]');  // lowercase as per the page.tsx
  await page.waitForTimeout(1000);
  
  console.log('After clicking templates...');
  navItems = await page.locator('[data-testid*="nav-"]:visible').all();
  console.log(`Visible nav items: ${navItems.length}`);
  
  for (let i = 0; i < navItems.length; i++) {
    const testId = await navItems[i].getAttribute('data-testid');
    console.log(`Visible nav: ${testId}`);
  }
  
  // Try to click job-templates if visible
  const jobTemplatesVisible = await page.locator('[data-testid="nav-job-templates"]').isVisible();
  console.log(`Job templates visible: ${jobTemplatesVisible}`);
  
  if (jobTemplatesVisible) {
    await page.click('[data-testid="nav-job-templates"]');
    console.log('Clicked job templates successfully');
    
    const forms = await page.locator('form').count();
    console.log(`Forms found: ${forms}`);
  }
});