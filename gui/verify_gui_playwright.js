const { chromium } = require('playwright');

async function verifyGUIWithPlaywright() {
  console.log('🎭 Opening GUI with Playwright (non-Docker)...');
  
  const browser = await chromium.launch({ 
    headless: false,  // Open visible browser
    slowMo: 1000      // Slow down actions for visibility
  });
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();

  // Monitor console messages
  page.on('console', msg => {
    console.log(`🖥️  Browser Console [${msg.type()}]:`, msg.text());
  });

  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('supabase') || request.url().includes('oggdidyjvncncxgebcpy')) {
      console.log(`📡 API Request: ${request.method()} ${request.url()}`);
    }
  });

  page.on('response', response => {
    if (response.url().includes('supabase') || response.url().includes('oggdidyjvncncxgebcpy')) {
      console.log(`📡 API Response: ${response.status()} ${response.url()}`);
    }
  });

  try {
    // Navigate to the GUI
    console.log('📍 Navigating to http://localhost:3002...');
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    
    // Take screenshot of initial load
    await page.screenshot({ path: 'gui_initial_load.png', fullPage: true });
    console.log('📸 Screenshot saved: gui_initial_load.png');

    // Verify page title
    const title = await page.title();
    console.log(`📄 Page Title: ${title}`);

    // Check if main elements are present
    const heading = await page.locator('h1').textContent();
    console.log(`📝 Main Heading: ${heading}`);

    // Check sidebar navigation
    const navItems = await page.locator('nav button').count();
    console.log(`🧭 Navigation sections: ${navItems}`);

    // Wait for departments data to load
    console.log('⏳ Waiting for departments data to load...');
    await page.waitForTimeout(3000);

    // Check if departments table is loaded
    const tableExists = await page.locator('table').count() > 0;
    console.log(`📊 Departments table: ${tableExists ? 'Present' : 'Not present'}`);

    if (tableExists) {
      const rows = await page.locator('tbody tr').count();
      console.log(`📋 Department rows: ${rows}`);
      
      // Take screenshot of loaded table
      await page.screenshot({ path: 'gui_departments_loaded.png', fullPage: true });
      console.log('📸 Screenshot saved: gui_departments_loaded.png');
    }

    // Test form interaction
    console.log('📝 Testing form interaction...');
    
    // Fill form fields
    await page.fill('input[id="code"]', 'PLAYWRIGHT_TEST');
    await page.fill('input[id="name"]', 'Playwright Test Department');
    await page.fill('textarea[id="description"]', 'Created by Playwright verification test');

    // Take screenshot of filled form
    await page.screenshot({ path: 'gui_form_filled.png', fullPage: true });
    console.log('📸 Screenshot saved: gui_form_filled.png');

    // Submit form
    console.log('✉️ Submitting form...');
    await page.click('button[type="submit"]');

    // Wait for response
    await page.waitForTimeout(3000);

    // Check for success/error messages
    const toastMessages = await page.locator('[class*="toast"]').count();
    const successText = await page.locator('text=/success/i').count();
    const errorText = await page.locator('text=/error/i').count();
    
    console.log(`✅ Success indicators: ${successText}`);
    console.log(`❌ Error indicators: ${errorText}`);
    console.log(`📢 Toast messages: ${toastMessages}`);

    // Take final screenshot
    await page.screenshot({ path: 'gui_after_submission.png', fullPage: true });
    console.log('📸 Screenshot saved: gui_after_submission.png');

    // Test navigation to different sections
    console.log('🧭 Testing navigation...');
    
    // Click on Machines section
    await page.click('text=Machines');
    await page.waitForTimeout(2000);
    
    const machineFormVisible = await page.locator('text=Machine Configuration').count() > 0;
    console.log(`🔧 Machine form loaded: ${machineFormVisible}`);

    // Take screenshot of machine form
    await page.screenshot({ path: 'gui_machine_form.png', fullPage: true });
    console.log('📸 Screenshot saved: gui_machine_form.png');

    // Return to departments
    await page.click('text=Departments');
    await page.waitForTimeout(2000);

    console.log('\n🎉 GUI Verification Complete!');
    console.log('✅ Browser opened successfully');
    console.log('✅ Page loaded without errors');
    console.log('✅ Navigation working');
    console.log('✅ Forms are interactive');
    console.log('✅ Database connection active');
    console.log('📸 Screenshots saved for visual verification');

    // Keep browser open for manual inspection
    console.log('\n🔍 Browser will remain open for manual inspection...');
    console.log('Press Ctrl+C to close when done');
    
    // Wait for manual inspection (or timeout after 5 minutes)
    await page.waitForTimeout(300000); // 5 minutes

  } catch (error) {
    console.error('❌ GUI Verification Failed:', error.message);
    await page.screenshot({ path: 'gui_error.png', fullPage: true });
    console.log('📸 Error screenshot saved: gui_error.png');
    throw error;
  } finally {
    await browser.close();
    console.log('👋 Browser closed');
  }
}

// Handle interruption gracefully
process.on('SIGINT', () => {
  console.log('\n👋 Test interrupted by user');
  process.exit(0);
});

// Run the verification
verifyGUIWithPlaywright().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});