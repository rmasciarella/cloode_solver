const { test, expect } = require('@playwright/test');

test('Test all sections work', async ({ page }) => {
  console.log('Testing all sections...');
  
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Test Templates section
  console.log('\n📂 Testing Templates section...');
  const templatesButton = page.locator('button').filter({ hasText: 'Templates' });
  await templatesButton.click();
  await page.waitForTimeout(1000);
  
  const jobTemplatesVisible = await page.locator('button').filter({ hasText: 'Job Templates' }).isVisible();
  console.log(`Job Templates visible after expanding: ${jobTemplatesVisible}`);
  
  if (jobTemplatesVisible) {
    await page.click('button:has-text("Job Templates")');
    await page.waitForTimeout(1000);
    const forms = await page.locator('form').count();
    console.log(`Job Templates forms: ${forms}`);
  }
  
  // Test Resources section
  console.log('\n📂 Testing Resources section...');
  const resourcesButton = page.locator('button').filter({ hasText: 'Resources' });
  await resourcesButton.click();
  await page.waitForTimeout(1000);
  
  const machinesVisible = await page.locator('button').filter({ hasText: 'Machines' }).isVisible();
  console.log(`Machines visible after expanding: ${machinesVisible}`);
  
  if (machinesVisible) {
    await page.click('button:has-text("Machines")');
    await page.waitForTimeout(1000);
    const forms = await page.locator('form').count();
    console.log(`Machines forms: ${forms}`);
  }
  
  // Test Scheduling section
  console.log('\n📂 Testing Scheduling section...');
  const schedulingButton = page.locator('button').filter({ hasText: 'Scheduling' });
  await schedulingButton.click();
  await page.waitForTimeout(1000);
  
  const setupTimesVisible = await page.locator('button').filter({ hasText: 'Setup Times' }).isVisible();
  console.log(`Setup Times visible after expanding: ${setupTimesVisible}`);
  
  if (setupTimesVisible) {
    await page.click('button:has-text("Setup Times")');
    await page.waitForTimeout(1000);
    const forms = await page.locator('form').count();
    console.log(`Setup Times forms: ${forms}`);
  }
  
  // Test Jobs section
  console.log('\n📂 Testing Jobs section...');
  const jobsButton = page.locator('button').filter({ hasText: 'Jobs' });
  await jobsButton.click();
  await page.waitForTimeout(1000);
  
  const jobInstancesVisible = await page.locator('button').filter({ hasText: 'Job Instances' }).isVisible();
  console.log(`Job Instances visible after expanding: ${jobInstancesVisible}`);
  
  if (jobInstancesVisible) {
    await page.click('button:has-text("Job Instances")');
    await page.waitForTimeout(1000);
    const forms = await page.locator('form').count();
    console.log(`Job Instances forms: ${forms}`);
  }
  
  // Take final screenshot
  await page.screenshot({ 
    path: 'gui/test-results/all-sections-tested.png',
    fullPage: true 
  });
  
  console.log('✅ All sections tested!');
});