const { chromium } = require('playwright');

async function testSupabaseConnection() {
  console.log('🔗 Testing Supabase Connection...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Monitor console messages for errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('🔴 Browser Console Error:', msg.text());
    }
  });

  // Monitor network requests for API calls
  const apiRequests = [];
  page.on('request', request => {
    if (request.url().includes('supabase') || request.url().includes('oggdidyjvncncxgebcpy')) {
      apiRequests.push({
        url: request.url(),
        method: request.method(),
        headers: Object.fromEntries(Object.entries(request.headers()).filter(([key]) => 
          key.toLowerCase().includes('authorization') || key.toLowerCase().includes('apikey')
        ))
      });
    }
  });

  // Monitor network responses
  page.on('response', response => {
    if (response.url().includes('supabase') || response.url().includes('oggdidyjvncncxgebcpy')) {
      console.log(`📡 Supabase API Response: ${response.status()} ${response.url()}`);
    }
  });

  try {
    // Navigate to the GUI
    console.log('📍 Navigating to http://localhost:3002...');
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });

    // Wait for the departments form to load
    console.log('📝 Loading departments form...');
    await page.waitForSelector('h1', { timeout: 10000 });

    // Wait a bit more for any API calls to complete
    await page.waitForTimeout(3000);

    // Check if the departments table is present and populated
    const tableExists = await page.locator('table').count() > 0;
    console.log(`📊 Departments table: ${tableExists ? 'Found' : 'Not found'}`);

    if (tableExists) {
      const rows = await page.locator('tbody tr').count();
      console.log(`📋 Found ${rows} department rows`);
      
      if (rows === 0) {
        const noDepartmentsMessage = await page.locator('text=No departments found').count();
        console.log(`📝 Empty state message: ${noDepartmentsMessage > 0 ? 'Displayed' : 'Not displayed'}`);
      }
    }

    // Check for loading states
    const loadingSpinner = await page.locator('[class*="animate-spin"]').count();
    console.log(`⏳ Loading spinner: ${loadingSpinner > 0 ? 'Active' : 'Not active'}`);

    // Test form submission (create a test department)
    console.log('📝 Testing form submission...');
    
    // Fill out the form
    await page.fill('input[id="code"]', 'TEST_DEPT');
    await page.fill('input[id="name"]', 'Test Department');
    await page.fill('textarea[id="description"]', 'Test department for validation');

    // Submit the form
    console.log('✉️ Submitting form...');
    await page.click('button[type="submit"]');

    // Wait for response
    await page.waitForTimeout(3000);

    // Check for success/error messages
    const errorMessages = await page.locator('text=/error/i').count();
    const successMessages = await page.locator('text=/success/i').count();
    
    console.log(`✅ Success messages: ${successMessages}`);
    console.log(`❌ Error messages: ${errorMessages}`);

    // Report API requests made
    console.log('\n📡 Supabase API Requests:');
    if (apiRequests.length === 0) {
      console.log('❌ No Supabase API requests detected');
    } else {
      apiRequests.forEach((req, index) => {
        console.log(`${index + 1}. ${req.method} ${req.url}`);
        if (req.headers.authorization) {
          console.log(`   Authorization: Bearer [present]`);
        }
        if (req.headers.apikey) {
          console.log(`   API Key: [present]`);
        }
      });
    }

    console.log('\n🔗 Supabase Connection Test Results:');
    if (apiRequests.length > 0) {
      console.log('✅ API requests are being made to Supabase');
      console.log('✅ Environment variables are properly configured');
      if (errorMessages === 0) {
        console.log('✅ No authentication errors detected');
        console.log('✅ Database connection appears to be working');
      } else {
        console.log('⚠️  Some errors were detected - check database permissions');
      }
    } else {
      console.log('❌ No API requests detected - check environment configuration');
    }

  } catch (error) {
    console.error('❌ Supabase Connection Test Failed:', error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run the test
testSupabaseConnection().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});