const { chromium } = require('playwright');

async function debugGui() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Listen for console messages and errors
  page.on('console', msg => {
    console.log(`Console ${msg.type()}: ${msg.text()}`);
  });
  
  page.on('pageerror', error => {
    console.log(`Page error: ${error.message}`);
  });
  
  try {
    console.log('Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    console.log('Getting page content and status...');
    const title = await page.title();
    const url = page.url();
    
    console.log('Title:', title);
    console.log('URL:', url);
    
    // Check if there are any React error boundaries or error messages
    const errorElements = await page.$$('*[data-error], .error, .alert-error');
    if (errorElements.length > 0) {
      console.log('Found error elements on page');
      for (let element of errorElements) {
        const text = await element.textContent();
        console.log('Error text:', text);
      }
    }
    
    // Check if main content loaded
    const bodyText = await page.$eval('body', el => el.textContent);
    console.log('Body has content:', bodyText.length > 100);
    
    if (bodyText.length < 100) {
      console.log('Page seems to be blank. Checking for React app root...');
      const reactRoot = await page.$('#__next, #root, [data-reactroot]');
      console.log('React root found:', !!reactRoot);
    }
    
    // Wait to see the page
    await page.waitForTimeout(3000);
    
  } catch (error) {
    console.error('Error during debugging:', error.message);
  }
  
  await browser.close();
}

debugGui();