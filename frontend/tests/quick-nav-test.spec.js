const { test, expect } = require('@playwright/test');

test('Quick navigation test', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Test templates section
  console.log('Testing templates section...');
  await page.click('[data-testid="section-templates"]');
  await page.waitForTimeout(1000);
  
  // Check if job-templates is visible
  const jobTemplates = await page.locator('[data-testid="nav-job-templates"]').count();
  console.log(`Job templates visible: ${jobTemplates}`);
  
  if (jobTemplates > 0) {
    await page.click('[data-testid="nav-job-templates"]');
    console.log('Successfully clicked job templates');
    
    // Check for forms
    const forms = await page.locator('form').count();
    console.log(`Forms found: ${forms}`);
  }
  
  // Test resources section  
  console.log('Testing resources section...');
  await page.click('[data-testid="section-resources"]');
  await page.waitForTimeout(1000);
  
  const machines = await page.locator('[data-testid="nav-machines"]').count();
  console.log(`Machines visible: ${machines}`);
  
  if (machines > 0) {
    await page.click('[data-testid="nav-machines"]');
    console.log('Successfully clicked machines');
  }
});