const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  console.log('🌐 Navigating to Fresh Solver app...');
  await page.goto('https://tiny-tapioca-72f6c6.netlify.app');
  
  console.log('🔍 Looking for Resources menu...');
  
  try {
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    
    // Try to click Resources dropdown
    const resourcesButton = await page.$('button:text("Resources")');
    if (resourcesButton) {
      await resourcesButton.click();
      console.log('✅ Clicked Resources dropdown');
      
      // Wait for dropdown to open
      await page.waitForTimeout(500);
      
      // Click on Operators
      const operatorsButton = await page.$('button:text("Operators")');
      if (operatorsButton) {
        await operatorsButton.click();
        console.log('✅ Clicked Operators');
      }
    } else {
      console.log('⚠️  Resources button not found, trying direct navigation...');
      // Try direct navigation or look for mobile menu
      const mobileMenu = await page.$('button svg.lucide-menu');
      if (mobileMenu) {
        await mobileMenu.click();
        await page.waitForTimeout(500);
      }
    }
  } catch (error) {
    console.log('⚠️  Navigation failed:', error.message);
  }
  
  // Wait a bit for the page to load
  await page.waitForTimeout(3000);
  
  console.log('📋 Checking page content...');
  
  // Check if the error message is present
  const errorElement = await page.$('text=Failed to fetch operators');
  
  if (errorElement) {
    console.log('❌ ERROR STILL PRESENT: "Failed to fetch operators" found on page');
  } else {
    console.log('✅ SUCCESS: No error message found!');
  }
  
  // Check if the form is present
  const formTitle = await page.$('h3:has-text("Create New Operator")');
  if (formTitle) {
    console.log('✅ Operator form is visible');
  }
  
  // Check if operators table is present
  const operatorsHeader = await page.$('h3:has-text("Operators")');
  if (operatorsHeader) {
    console.log('✅ Operators section is visible');
  }
  
  // Take a screenshot for verification
  await page.screenshot({ path: 'operators-page-test.png', fullPage: true });
  console.log('📸 Screenshot saved as operators-page-test.png');
  
  await browser.close();
})();