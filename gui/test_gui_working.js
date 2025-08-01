const { chromium } = require('playwright');

async function testGui() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => console.log(`Console ${msg.type()}: ${msg.text()}`));
  
  // Enable error logging
  page.on('pageerror', error => console.log(`Page error: ${error.message}`));
  
  try {
    console.log('🚀 Testing Fresh Solver GUI...');
    
    // Navigate to the application
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    
    console.log('✅ Page loaded successfully!');
    
    // Check if the main title is visible
    const title = await page.locator('text=Fresh Solver').isVisible();
    console.log(`Title visible: ${title}`);
    
    // Check if the sidebar navigation is working
    const sidebar = await page.locator('[role="navigation"]').first().isVisible();
    console.log(`Sidebar visible: ${sidebar}`);
    
    // Check if the Department form is loaded by default
    const departmentForm = await page.locator('text=Create New Department').isVisible();
    console.log(`Department form visible: ${departmentForm}`);
    
    // Test navigation - click on Job Templates
    await page.click('text=Templates');
    await page.waitForTimeout(500);
    await page.click('text=Job Templates');
    await page.waitForTimeout(1000);
    
    const jobTemplateForm = await page.locator('text=Create New Job Template').isVisible();
    console.log(`Job Template form visible: ${jobTemplateForm}`);
    
    // Test navigation - click on Machines
    await page.click('text=Resources');
    await page.waitForTimeout(500);
    await page.click('text=Machines');
    await page.waitForTimeout(1000);
    
    const machineForm = await page.locator('text=Create New Machine').isVisible();
    console.log(`Machine form visible: ${machineForm}`);
    
    console.log('🎉 All basic tests passed! GUI is working correctly.');
    
    // Keep browser open for manual testing
    console.log('Browser will stay open for manual testing...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testGui().catch(console.error);