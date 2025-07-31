const { test, expect } = require('@playwright/test');

test('Check current GUI state', async ({ page }) => {
  console.log('Checking GUI state...');
  
  try {
    await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 });
    
    // Take screenshot
    await page.screenshot({ 
      path: 'gui/test-results/current-gui-state.png',
      fullPage: true 
    });
    
    console.log('GUI loaded successfully');
    
    // Check basic elements
    const title = await page.title();
    console.log(`Page title: ${title}`);
    
    // Check if sidebar is visible
    const sidebar = await page.locator('.sidebar, [class*="sidebar"], nav').count();
    console.log(`Sidebar elements found: ${sidebar}`);
    
    // Check if navigation buttons work
    const orgSection = await page.locator('[data-testid="section-organization"]').count();
    console.log(`Organization section button found: ${orgSection}`);
    
    if (orgSection > 0) {
      console.log('Testing organization section click...');
      await page.click('[data-testid="section-organization"]');
      await page.waitForTimeout(1000);
      
      const deptButton = await page.locator('[data-testid="nav-departments"]').isVisible();
      console.log(`Departments button visible after click: ${deptButton}`);
      
      if (deptButton) {
        console.log('Testing departments navigation...');
        await page.click('[data-testid="nav-departments"]');
        await page.waitForTimeout(1000);
        
        const forms = await page.locator('form').count();
        console.log(`Forms found after navigation: ${forms}`);
        
        // Take screenshot after navigation
        await page.screenshot({ 
          path: 'gui/test-results/after-navigation.png',
          fullPage: true 
        });
      }
    }
    
  } catch (error) {
    console.error('Error checking GUI:', error.message);
    
    // Take error screenshot
    await page.screenshot({ 
      path: 'gui/test-results/gui-error-state.png',
      fullPage: true 
    });
  }
});