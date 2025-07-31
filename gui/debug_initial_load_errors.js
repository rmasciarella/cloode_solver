const { chromium } = require('playwright');

async function debugInitialLoadErrors() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    
    // Listen for all console messages from the start
    const consoleMessages = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push({
        type: msg.type(),
        text: text,
        timestamp: new Date().toISOString()
      });
      
      if (msg.type() === 'error') {
        console.log(`🚨 Console Error [${new Date().toISOString()}]:`, text);
      }
    });
    
    // Listen for network requests and responses
    const networkActivity = [];
    page.on('request', request => {
      if (request.url().includes('supabase')) {
        networkActivity.push({
          type: 'request',
          method: request.method(),
          url: request.url(),
          timestamp: new Date().toISOString()
        });
      }
    });
    
    page.on('response', async response => {
      if (response.url().includes('supabase')) {
        let responseBody = '';
        try {
          responseBody = await response.text();
        } catch (e) {
          responseBody = '[Could not read response]';
        }
        
        networkActivity.push({
          type: 'response',
          status: response.status(),
          url: response.url(),
          body: responseBody,
          timestamp: new Date().toISOString()
        });
        
        if (response.status() >= 400) {
          console.log(`❌ Network Error [${new Date().toISOString()}] ${response.status()} ${response.url()}:`);
          console.log('Response:', responseBody);
        }
      }
    });
    
    await page.goto('http://localhost:3000');
    console.log('✅ Initial page loaded');
    
    // Wait for initial load to complete
    await page.waitForLoadState('networkidle');
    console.log('✅ Network idle reached');
    
    // Navigate through different sections to trigger all forms
    console.log('🧪 Testing Departments...');
    const departmentsButton = await page.locator('button:has-text("Departments")').first();
    await departmentsButton.click();
    await page.waitForTimeout(2000);
    
    console.log('🧪 Testing Templates section...');
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(1000);
    
    console.log('🧪 Testing Template Precedences...');
    const precedencesButton = await page.locator('button:has-text("Template Precedences")').first();
    if (precedencesButton) {
      await precedencesButton.click();
      await page.waitForTimeout(2000);
    } else {
      console.log('⚠️ Template Precedences button not found');
    }
    
    console.log('🧪 Testing Job Templates...');
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(2000);
    
    // Wait a bit more to capture any delayed errors
    await page.waitForTimeout(3000);
    
    console.log('\\n📊 SUMMARY:');
    console.log(`Total console messages: ${consoleMessages.length}`);
    console.log(`Console errors: ${consoleMessages.filter(m => m.type === 'error').length}`);
    console.log(`Network requests: ${networkActivity.filter(a => a.type === 'request').length}`);
    console.log(`Network errors: ${networkActivity.filter(a => a.type === 'response' && a.status >= 400).length}`);
    
    if (consoleMessages.filter(m => m.type === 'error').length > 0) {
      console.log('\\n🚨 ALL CONSOLE ERRORS:');
      consoleMessages.filter(m => m.type === 'error').forEach((msg, i) => {
        console.log(`${i + 1}. [${msg.timestamp}] ${msg.text}`);
      });
    }
    
    if (networkActivity.filter(a => a.type === 'response' && a.status >= 400).length > 0) {
      console.log('\\n❌ ALL NETWORK ERRORS:');
      networkActivity.filter(a => a.type === 'response' && a.status >= 400).forEach((activity, i) => {
        console.log(`${i + 1}. [${activity.timestamp}] ${activity.status} ${activity.url}`);
        console.log(`   Response: ${activity.body}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

debugInitialLoadErrors();