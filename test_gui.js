const { chromium } = require('playwright');

async function testGui() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000');
    
    console.log('Page loaded, taking screenshot...');
    await page.screenshot({ path: 'gui-screenshot.png' });
    
    console.log('Getting page title and content...');
    const title = await page.title();
    const content = await page.content();
    
    console.log('Title:', title);
    console.log('Page loaded successfully!');
    
    // Wait a bit to see the page
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('Error:', error.message);
    
    // Try to get error details
    const content = await page.content();
    console.log('Page content:', content.substring(0, 1000) + '...');
  }
  
  await browser.close();
}

testGui();