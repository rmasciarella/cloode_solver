const { chromium } = require('playwright');

async function simpleNavigationTest() {
  console.log('🧭 Testing Navigation Issues...');
  
  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  const issues = [];
  const successes = [];

  try {
    // Navigate to the GUI
    console.log('📍 Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Take screenshot
    await page.screenshot({ path: 'nav_test_initial.png', fullPage: true });
    console.log('📸 Initial screenshot saved');

    // Test if Departments works (should work as it's the default expanded section)
    console.log('\n1. Testing Departments (should work)...');
    try {
      await page.click('button:has-text("Departments")');
      await page.waitForTimeout(1000);
      const heading = await page.locator('h2').textContent();
      console.log(`✅ Departments clicked successfully - heading: ${heading}`);
      successes.push('Departments navigation works');
    } catch (error) {
      console.log(`❌ Departments failed: ${error.message}`);
      issues.push({ section: 'Departments', error: error.message });
    }

    // Test expanding Templates section
    console.log('\n2. Testing Templates section expansion...');
    try {
      // Force click with more aggressive settings
      await page.locator('button:has-text("Templates")').click({ force: true });
      await page.waitForTimeout(1000);
      
      // Check if Templates section is now expanded
      const isExpanded = await page.locator('button:has-text("Job Templates")').isVisible();
      console.log(`✅ Templates section expanded: ${isExpanded}`);
      
      if (isExpanded) {
        successes.push('Templates section expansion works');
        
        // Try clicking Job Templates
        console.log('  Testing Job Templates navigation...');
        await page.locator('button:has-text("Job Templates")').click({ force: true });
        await page.waitForTimeout(1000);
        const heading = await page.locator('h2').textContent();
        console.log(`  ✅ Job Templates navigation works - heading: ${heading}`);
        successes.push('Job Templates navigation works');
      } else {
        issues.push({ section: 'Templates', error: 'Section did not expand' });
      }
    } catch (error) {
      console.log(`❌ Templates section failed: ${error.message}`);
      issues.push({ section: 'Templates', error: error.message });
    }

    // Test Resources section
    console.log('\n3. Testing Resources section expansion...');
    try {
      await page.locator('button:has-text("Resources")').click({ force: true });
      await page.waitForTimeout(1000);
      
      const isExpanded = await page.locator('button:has-text("Machines")').isVisible();
      console.log(`✅ Resources section expanded: ${isExpanded}`);
      
      if (isExpanded) {
        successes.push('Resources section expansion works');
        
        // Try clicking Machines
        console.log('  Testing Machines navigation...');
        await page.locator('button:has-text("Machines")').click({ force: true });
        await page.waitForTimeout(1000);
        const heading = await page.locator('h2').textContent();
        console.log(`  ✅ Machines navigation works - heading: ${heading}`);
        successes.push('Machines navigation works');
      } else {
        issues.push({ section: 'Resources', error: 'Section did not expand' });
      }
    } catch (error) {
      console.log(`❌ Resources section failed: ${error.message}`);
      issues.push({ section: 'Resources', error: error.message });
    }

    // Test going back to Organization section items
    console.log('\n4. Testing Organization section items...');
    try {
      // Organization should already be expanded
      await page.locator('button:has-text("Work Cells")').click({ force: true });
      await page.waitForTimeout(1000);
      const heading = await page.locator('h2').textContent();
      console.log(`✅ Work Cells navigation works - heading: ${heading}`);
      successes.push('Work Cells navigation works');
    } catch (error) {
      console.log(`❌ Work Cells failed: ${error.message}`);
      issues.push({ section: 'Work Cells', error: error.message });
    }

    // Final screenshot
    await page.screenshot({ path: 'nav_test_final.png', fullPage: true });
    console.log('📸 Final screenshot saved');

    // Generate report
    console.log('\n' + '='.repeat(50));
    console.log('📋 NAVIGATION TEST REPORT');
    console.log('='.repeat(50));
    
    console.log(`\n✅ WORKING FEATURES (${successes.length}):`);
    successes.forEach(success => {
      console.log(`  • ${success}`);
    });
    
    console.log(`\n❌ NAVIGATION ISSUES (${issues.length}):`);
    if (issues.length === 0) {
      console.log('  🎉 No navigation issues found!');
    } else {
      issues.forEach((issue, index) => {
        console.log(`  ${index + 1}. ${issue.section}: ${issue.error}`);
      });
    }

    // Let browser stay open for manual inspection
    console.log('\n🔍 Browser staying open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('❌ Critical test failure:', error.message);
    await page.screenshot({ path: 'nav_test_critical_error.png', fullPage: true });
    throw error;
  } finally {
    await browser.close();
    console.log('👋 Browser closed');
  }
}

// Run the test
simpleNavigationTest().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});