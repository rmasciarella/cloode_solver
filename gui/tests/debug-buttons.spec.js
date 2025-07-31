const { test, expect } = require('@playwright/test');

test('Debug button click', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Get templates button element  
  const templatesButton = page.locator('[data-testid="section-templates"]');
  const buttonExists = await templatesButton.count();
  console.log(`Templates button exists: ${buttonExists}`);
  
  if (buttonExists > 0) {
    const buttonText = await templatesButton.textContent();
    console.log(`Button text: "${buttonText}"`);
    
    const isClickable = await templatesButton.isEnabled();
    console.log(`Button clickable: ${isClickable}`);
    
    // Check aria-expanded before click
    const ariaExpanded = await templatesButton.getAttribute('aria-expanded');
    console.log(`Aria-expanded before: ${ariaExpanded}`);
    
    // Try click
    console.log('Attempting click...');
    await templatesButton.click();
    await page.waitForTimeout(1000);
    
    // Check aria-expanded after click
    const ariaExpandedAfter = await templatesButton.getAttribute('aria-expanded');
    console.log(`Aria-expanded after: ${ariaExpandedAfter}`);
    
    // Check for nav items
    const allNavs = await page.locator('[data-testid*="nav-"]').all();
    console.log(`All nav elements found: ${allNavs.length}`);
    
    for (let i = 0; i < allNavs.length; i++) {
      const testId = await allNavs[i].getAttribute('data-testid');
      const isVisible = await allNavs[i].isVisible();
      console.log(`Nav ${testId}: visible=${isVisible}`);
    }
  }
});