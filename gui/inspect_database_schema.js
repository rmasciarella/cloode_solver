const { chromium } = require('playwright');

async function inspectDatabaseSchema() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Listen for all network requests to see what data we can actually fetch
    page.on('response', async response => {
      if (response.url().includes('supabase.co/rest/v1/')) {
        const url = response.url();
        const tableName = url.split('/rest/v1/')[1]?.split('?')[0];
        console.log(`📊 Table: ${tableName}, Status: ${response.status()}`);
        
        if (response.status() === 200 && tableName === 'job_optimized_patterns') {
          try {
            const data = await response.json();
            if (data && data.length > 0) {
              console.log('✅ job_optimized_patterns actual data sample:');
              console.log('Keys:', Object.keys(data[0]));
              console.log('Sample record:', JSON.stringify(data[0], null, 2));
            } else {
              console.log('📝 job_optimized_patterns table exists but is empty');
            }
          } catch (e) {
            console.log('❌ Could not parse job_optimized_patterns response:', e.message);
          }
        }
      }
    });
    
    // Navigate to different sections to trigger table loads
    console.log('🧪 Testing table access...');
    
    // Test departments (we know this works)
    const departmentsButton = await page.locator('button:has-text("Departments")').first();
    await departmentsButton.click();
    await page.waitForTimeout(2000);
    
    // Test Job Templates
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500);
    
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(3000); // Give more time for the data to load
    
    console.log('✅ Schema inspection complete');
    
  } catch (error) {
    console.error('❌ Error during schema inspection:', error);
  } finally {
    await browser.close();
  }
}

inspectDatabaseSchema();