const { chromium } = require('playwright');

async function testActualSchema() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Job Templates
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500);
    
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(1000);
    
    console.log('🧪 Testing minimal fields only...');
    
    // Test with just core fields that must exist
    const testFields = [
      { name: 'name', value: 'Schema Test Pattern' },
      { name: 'description', value: 'Testing actual schema' },
      // Skip task_count for now
      // { name: 'task_count', value: '1' },
    ];
    
    let networkResponse = null;
    
    page.on('response', async response => {
      if (response.url().includes('job_optimized_patterns') && response.status() >= 400) {
        try {
          const responseText = await response.text();
          networkResponse = {
            status: response.status(),
            body: responseText
          };
          console.log(`🚨 Error Response (${response.status()}):`, responseText);
        } catch (e) {
          console.log(`🚨 Error Response (${response.status()}): Unable to read response body`);
        }
      }
    });
    
    // Fill only minimal fields
    for (const field of testFields) {
      const element = await page.$(`input[id="${field.name}"], textarea[id="${field.name}"]`);
      if (element) {
        await page.fill(`input[id="${field.name}"], textarea[id="${field.name}"]`, field.value);
        console.log(`✅ Filled ${field.name}: ${field.value}`);
      } else {
        console.log(`❌ Field ${field.name} not found`);
      }
    }
    
    // Try to submit with minimal data
    const submitButton = await page.$('button[type="submit"]');
    if (submitButton) {
      console.log('🚀 Submitting with minimal fields...');
      await submitButton.click();
      await page.waitForTimeout(3000);
      
      if (networkResponse) {
        console.log('📊 Response Details:', networkResponse);
      } else {
        console.log('✅ No error - submission might have worked!');
      }
    }
    
  } catch (error) {
    console.error('❌ Error during schema test:', error);
  } finally {
    await browser.close();
  }
}

testActualSchema();