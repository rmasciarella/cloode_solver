const { chromium } = require('playwright');

async function debugRealErrors() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Listen for all console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('🚨 Browser Console Error:', msg.text());
      }
    });
    
    // Listen for network errors with detailed responses
    page.on('response', async response => {
      if (response.status() >= 400) {
        try {
          const responseText = await response.text();
          console.log(`❌ Network Error ${response.status()} ${response.url()}:`);
          console.log('Response:', responseText);
        } catch (e) {
          console.log(`❌ Network Error ${response.status()} ${response.url()}: Could not read response`);
        }
      }
    });
    
    // Navigate to Job Templates and try to create one
    console.log('🧪 Testing Job Template creation...');
    
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500);
    
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(1000);
    
    // Fill form
    await page.fill('input[id="name"]', 'Debug Error Test');
    await page.fill('textarea[id="description"]', 'Testing to see actual error');
    await page.fill('input[id="task_count"]', '2');
    await page.fill('input[id="total_min_duration_minutes"]', '90');
    await page.fill('input[id="critical_path_length_minutes"]', '60');
    
    console.log('✅ Form filled, submitting...');
    
    // Submit and wait for errors
    const submitButton = await page.$('button[type="submit"]');
    if (submitButton) {
      await submitButton.click();
      
      // Wait longer to capture all errors
      await page.waitForTimeout(5000);
      
      console.log('⏰ Waited 5 seconds for errors to appear');
    }
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

debugRealErrors();