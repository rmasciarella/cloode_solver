const { chromium } = require('playwright');

async function testTableExistence() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Test different table access patterns
    const tablesToTest = [
      'departments',
      'job_optimized_patterns', 
      'optimized_precedences',
      'optimized_tasks',
      'job_instances'
    ];
    
    for (const tableName of tablesToTest) {
      console.log(`\n🧪 Testing table: ${tableName}`);
      
      let responseReceived = false;
      
      page.on('response', async response => {
        if (response.url().includes(`/${tableName}?`) || response.url().includes(`/${tableName}`)) {
          responseReceived = true;
          try {
            const responseText = await response.text();
            if (response.status() === 200) {
              const data = JSON.parse(responseText);
              console.log(`✅ ${tableName}: EXISTS (${data.length} records)`);
              if (data.length > 0) {
                console.log(`   Sample columns: ${Object.keys(data[0]).join(', ')}`);
              }
            } else {
              console.log(`❌ ${tableName}: ERROR ${response.status()}`);
              console.log(`   Response: ${responseText}`);
            }
          } catch (e) {
            console.log(`❓ ${tableName}: Could not parse response`);
          }
        }
      });
      
      // Make a simple request to each table by evaluating JS
      await page.evaluate(async (table) => {
        try {
          const response = await fetch(`/api/test-table/${table}`);
          return response.status();
        } catch (e) {
          // Try direct supabase URL pattern
          const supabaseUrl = `https://oggdidyjvncncxgebcpy.supabase.co/rest/v1/${table}?limit=1`;
          const headers = {
            'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nZ2RpZHlqdm5jbmN4Z2ViY3B5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc5MDI3NzEsImV4cCI6MjA1MzQ3ODc3MX0.uYOSgHbVX5xNnGPe7yjQo2JbcePJC6tRKhAUEBs1n0Y',
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nZ2RpZHlqdm5jbmN4Z2ViY3B5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc5MDI3NzEsImV4cCI6MjA1MzQ3ODc3MX0.uYOSgHbVX5xNnGPe7yjQo2JbcePJC6tRKhAUEBs1n0Y'
          };
          
          const response = await fetch(supabaseUrl, { headers });
          return response.status();
        }
      }, tableName);
      
      await page.waitForTimeout(1000);
      
      if (!responseReceived) {
        console.log(`⚠️ ${tableName}: No response received`);
      }
    }
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

testTableExistence();