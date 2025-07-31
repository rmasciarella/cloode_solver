const { chromium } = require('playwright');

async function checkDatabaseTables() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI to test database tables...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Listen for network requests to see what tables are being accessed
    const tableRequests = [];
    
    page.on('request', request => {
      if (request.url().includes('supabase.co/rest/v1/')) {
        const url = request.url();
        const tableName = url.split('/rest/v1/')[1]?.split('?')[0];
        if (tableName && !tableRequests.includes(tableName)) {
          tableRequests.push(tableName);
          console.log(`📊 Found table access: ${tableName}`);
        }
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('supabase.co/rest/v1/')) {
        const url = response.url();
        const tableName = url.split('/rest/v1/')[1]?.split('?')[0];
        console.log(`📬 Response for ${tableName}: ${response.status()}`);
      }
    });
    
    // Test departments (we know this works)
    console.log('\n🧪 Testing departments table (known working):');
    const departmentsButton = await page.locator('button:has-text("Departments")').first();
    await departmentsButton.click();
    await page.waitForTimeout(2000);
    
    // Test work cells
    console.log('\n🧪 Testing work cells table:');
    const workCellsButton = await page.locator('button:has-text("Work Cells")').first();
    if (workCellsButton) {
      await workCellsButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Try to expand Templates section to see what happens
    console.log('\n🧪 Testing Templates section:');
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(1000);
    
    // Try Job Templates
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    if (jobTemplatesButton) {
      await jobTemplatesButton.click();
      await page.waitForTimeout(2000);
    }
    
    console.log('\n📊 Summary of table access attempts:');
    console.log('Tables accessed:', tableRequests);
    
    // Take final screenshot
    await page.screenshot({ path: 'database_tables_test.png' });
    console.log('📸 Database tables test screenshot taken');
    
  } catch (error) {
    console.error('❌ Error during database table check:', error);
  } finally {
    await browser.close();
  }
}

checkDatabaseTables();