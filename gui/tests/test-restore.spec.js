const { test, expect } = require('@playwright/test');

test('Test basic functionality after restore', async ({ page }) => {
  console.log('Testing restored functionality...');
  
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Take screenshot of current state
  await page.screenshot({ 
    path: 'gui/test-results/restored-state.png',
    fullPage: true 
  });
  
  console.log('Page loaded successfully');
  
  // Check if departments button is visible (should be by default)
  const deptVisible = await page.locator('button').filter({ hasText: 'Departments' }).isVisible();
  console.log(`Departments button visible: ${deptVisible}`);
  
  if (deptVisible) {
    console.log('Clicking departments button...');
    await page.click('button:has-text("Departments")');
    await page.waitForTimeout(1000);
    
    // Check if form appears
    const forms = await page.locator('form').count();
    console.log(`Forms found: ${forms}`);
    
    if (forms > 0) {
      console.log('✅ Basic navigation is working!');
      
      // Try filling a field
      const nameInput = page.locator('input[id="name"], input[name="name"]');
      if (await nameInput.count() > 0) {
        await nameInput.fill('Test Department');
        console.log('✅ Form input is working!');
      }
    }
    
    await page.screenshot({ 
      path: 'gui/test-results/after-departments-click.png',
      fullPage: true 
    });
  }
  
  // Test other navigation items
  const workCellsVisible = await page.locator('button').filter({ hasText: 'Work Cells' }).isVisible();
  console.log(`Work Cells button visible: ${workCellsVisible}`);
  
  if (workCellsVisible) {
    console.log('Testing work cells navigation...');
    await page.click('button:has-text("Work Cells")');
    await page.waitForTimeout(1000);
    
    const forms = await page.locator('form').count();
    console.log(`Work Cells forms found: ${forms}`);
  }
});