const { chromium } = require('playwright');

async function debugJobTemplateError() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Capture detailed network responses
    const networkErrors = [];
    
    page.on('response', async response => {
      if (response.url().includes('supabase') && response.status() >= 400) {
        try {
          const responseText = await response.text();
          networkErrors.push({
            status: response.status(),
            url: response.url(),
            headers: await response.allHeaders(),
            body: responseText
          });
          console.log(`🚨 Error Response (${response.status()}):`, responseText);
        } catch (e) {
          console.log(`🚨 Error Response (${response.status()}): Unable to read response body`);
        }
      }
    });
    
    // Navigate to Job Templates
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500);
    
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(1000);
    
    // Fill form with minimal required data
    await page.fill('input[id="name"]', 'Debug Test Pattern');
    await page.fill('input[id="task_count"]', '1');
    await page.fill('input[id="total_min_duration_minutes"]', '60');
    await page.fill('input[id="critical_path_length_minutes"]', '60');
    await page.fill('input[id="redundant_constraints_count"]', '0');
    
    // Try to submit
    const submitButton = await page.$('button[type="submit"]');
    if (submitButton) {
      console.log('🚀 Submitting form...');
      await submitButton.click();
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      console.log('📊 Detailed Network Errors:');
      networkErrors.forEach((error, index) => {
        console.log(`\nError ${index + 1}:`);
        console.log(`Status: ${error.status}`);
        console.log(`URL: ${error.url}`);
        console.log(`Response Body: ${error.body}`);
      });
    }
    
  } catch (error) {
    console.error('❌ Error during debug:', error);
  } finally {
    await browser.close();
  }
}

debugJobTemplateError();