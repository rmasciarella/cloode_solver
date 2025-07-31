const { test, expect } = require('@playwright/test');

test('Simple department deletion feature test', async ({ page }) => {
  console.log('🗑️ Testing department deletion features...');
  
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
  
  // Navigate to Departments
  await page.click('text=Departments');
  await page.waitForTimeout(2000);
  
  // Look for the deactivate button we added
  const deactivateButton = await page.locator('button:has-text("Deactivate")').count();
  const reactivateButton = await page.locator('button:has-text("Reactivate")').count();
  
  console.log(`Deactivate buttons found: ${deactivateButton}`);
  console.log(`Reactivate buttons found: ${reactivateButton}`);
  
  await page.screenshot({ 
    path: 'simple-deletion-test.png',
    fullPage: true 
  });
  
  if (deactivateButton > 0 || reactivateButton > 0) {
    console.log('✅ SUCCESS: Deactivation functionality is available!');
    console.log('💡 Users can now deactivate departments instead of deleting them');
  } else {
    console.log('❌ Deactivation buttons not found');
  }
});