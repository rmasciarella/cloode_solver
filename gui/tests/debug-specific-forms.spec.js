const { test, expect } = require('@playwright/test');

test('Debug specific broken forms', async ({ page }) => {
  console.log('🔍 Testing specific forms that have issues...');
  
  const errors = [];
  
  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
      console.error(`Console error: ${msg.text()}`);
    }
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    errors.push(error.message);
    console.error(`Page error: ${error.message}`);
  });
  
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Test template precedences
  console.log('\n📋 Testing Template Precedences...');
  await page.click('button:has-text("Templates")');
  await page.waitForTimeout(500);
  await page.click('button:has-text("Template Precedences")');
  await page.waitForTimeout(1000);
  
  let content = await page.locator('main').textContent();
  console.log(`Template Precedences content: "${content?.substring(0, 100)}..."`);
  
  await page.screenshot({ 
    path: 'gui/test-results/debug-template-precedences.png',
    fullPage: true 
  });
  
  // Test setup times
  console.log('\n⏰ Testing Setup Times...');
  await page.click('button:has-text("Scheduling")');
  await page.waitForTimeout(500);
  await page.click('button:has-text("Setup Times")');
  await page.waitForTimeout(2000);
  
  content = await page.locator('main').textContent();
  console.log(`Setup Times content: "${content?.substring(0, 100)}..."`);
  
  const setupForms = await page.locator('form').count();
  const setupInputs = await page.locator('input, textarea, select').count();
  console.log(`Setup Times: ${setupForms} forms, ${setupInputs} inputs`);
  
  await page.screenshot({ 
    path: 'gui/test-results/debug-setup-times.png',
    fullPage: true 
  });
  
  // Test job instances  
  console.log('\n💼 Testing Job Instances...');
  await page.click('button:has-text("Jobs")');
  await page.waitForTimeout(500);
  await page.click('button:has-text("Job Instances")');
  await page.waitForTimeout(2000);
  
  content = await page.locator('main').textContent();
  console.log(`Job Instances content: "${content?.substring(0, 100)}..."`);
  
  const jobForms = await page.locator('form').count();
  const jobInputs = await page.locator('input, textarea, select').count();
  console.log(`Job Instances: ${jobForms} forms, ${jobInputs} inputs`);
  
  await page.screenshot({ 
    path: 'gui/test-results/debug-job-instances.png',
    fullPage: true 
  });
  
  // Test job tasks
  console.log('\n📝 Testing Job Tasks...');
  await page.click('button:has-text("Job Tasks")');
  await page.waitForTimeout(1000);
  
  content = await page.locator('main').textContent();
  console.log(`Job Tasks content: "${content?.substring(0, 100)}..."`);
  
  await page.screenshot({ 
    path: 'gui/test-results/debug-job-tasks.png',
    fullPage: true 
  });
  
  // Report errors
  console.log(`\n❌ Total errors found: ${errors.length}`);
  errors.forEach((error, i) => {
    console.log(`  ${i + 1}. ${error}`);
  });
  
  if (errors.length === 0) {
    console.log('✅ No JavaScript errors found');
  }
});