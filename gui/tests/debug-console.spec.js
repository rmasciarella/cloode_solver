const { test, expect } = require('@playwright/test');

test('Debug console errors', async ({ page }) => {
  const consoleMessages = [];
  
  // Listen for all console messages
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    console.error('Page error:', error.message);
    console.error('Stack:', error.stack);
  });
  
  console.log('Loading page and checking for errors...');
  
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Wait a bit for any async errors
  await page.waitForTimeout(2000);
  
  // Print all console messages
  console.log(`\n📋 Console messages (${consoleMessages.length}):`);
  consoleMessages.forEach((msg, i) => {
    console.log(`  ${i + 1}. [${msg.type}] ${msg.text}`);
    if (msg.location && msg.location.url) {
      console.log(`     Location: ${msg.location.url}:${msg.location.lineNumber}:${msg.location.columnNumber}`);
    }
  });
  
  // Test clicking the organization section specifically
  console.log('\n🖱️  Testing section click...');
  
  try {
    const orgButton = page.locator('[data-testid="section-organization"]');
    
    const beforeExpanded = await orgButton.getAttribute('aria-expanded');
    console.log(`Before click - aria-expanded: ${beforeExpanded}`);
    
    await orgButton.click();
    await page.waitForTimeout(1000);
    
    const afterExpanded = await orgButton.getAttribute('aria-expanded');
    console.log(`After click - aria-expanded: ${afterExpanded}`);
    
    // Check if departments nav is visible
    const deptVisible = await page.locator('[data-testid="nav-departments"]').isVisible();
    console.log(`Departments nav visible: ${deptVisible}`);
    
  } catch (error) {
    console.error('Click test error:', error.message);
  }
  
  // Take final screenshot
  await page.screenshot({ 
    path: 'gui/test-results/debug-console-final.png',
    fullPage: true 
  });
});