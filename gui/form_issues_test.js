const { chromium } = require('playwright');

async function formIssuesTest() {
  console.log('📝 Testing All Forms for Issues...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  const formResults = [];
  const consoleErrors = [];
  const networkErrors = [];

  // Monitor console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`🔴 Console Error: ${msg.text()}`);
      consoleErrors.push({
        message: msg.text(),
        timestamp: new Date().toISOString()
      });
    }
  });

  // Monitor network errors  
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`🔴 Network Error: ${response.status()} ${response.url()}`);
      networkErrors.push({
        status: response.status(),
        url: response.url(),
        timestamp: new Date().toISOString()
      });
    }
  });

  try {
    // Navigate to the GUI
    console.log('📍 Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

    // Define all forms to test
    const formsToTest = [
      // Organization
      { section: 'Organization', name: 'Departments', button: 'Departments', alreadyExpanded: true },
      { section: 'Organization', name: 'Work Cells', button: 'Work Cells', alreadyExpanded: true },
      { section: 'Organization', name: 'Business Calendars', button: 'Business Calendars', alreadyExpanded: true },
      
      // Templates  
      { section: 'Templates', name: 'Job Templates', button: 'Job Templates', alreadyExpanded: false },
      { section: 'Templates', name: 'Template Tasks', button: 'Template Tasks', alreadyExpanded: false },
      
      // Resources
      { section: 'Resources', name: 'Machines', button: 'Machines', alreadyExpanded: false },
      { section: 'Resources', name: 'Operators', button: 'Operators', alreadyExpanded: false },
      { section: 'Resources', name: 'Skills', button: 'Skills', alreadyExpanded: false },
      { section: 'Resources', name: 'Sequence Resources', button: 'Sequence Resources', alreadyExpanded: false },
      
      // Scheduling
      { section: 'Scheduling', name: 'Setup Times', button: 'Setup Times', alreadyExpanded: false },
      { section: 'Scheduling', name: 'Maintenance Windows', button: 'Maintenance Windows', alreadyExpanded: false },
      
      // Jobs
      { section: 'Jobs', name: 'Job Instances', button: 'Job Instances', alreadyExpanded: false },
    ];

    for (const form of formsToTest) {
      console.log(`\n📋 Testing ${form.name} form...`);
      
      try {
        // Expand section if needed
        if (!form.alreadyExpanded) {
          console.log(`  Expanding ${form.section} section...`);
          await page.locator(`button:has-text("${form.section}")`).click({ force: true });
          await page.waitForTimeout(500);
        }
        
        // Click the form button
        console.log(`  Clicking ${form.button}...`);
        await page.locator(`button:has-text("${form.button}")`).click({ force: true });
        await page.waitForTimeout(2000); // Wait longer for form to load
        
        // Analyze the form
        const pageHeading = await page.locator('h2').textContent().catch(() => 'No heading found');
        const formsCount = await page.locator('form').count();
        const inputsCount = await page.locator('input, textarea, select, [role="combobox"]').count();
        const buttonsCount = await page.locator('button[type="submit"]').count();
        const tablesCount = await page.locator('table').count();
        const loadingSpinners = await page.locator('[class*="animate-spin"], .animate-spin').count();
        const errorMessages = await page.locator('[class*="error"], .text-red-500, .text-red-600, [class*="destructive"]').count();
        
        // Check for specific error patterns
        const hasNoFormError = formsCount === 0;
        const hasLoadingStuck = loadingSpinners > 0;
        const hasErrorMessages = errorMessages > 0;
        
        // Try to get error text if any
        let errorText = '';
        if (hasErrorMessages) {
          try {
            errorText = await page.locator('[class*="error"], .text-red-500, .text-red-600, [class*="destructive"]').first().textContent();
          } catch (e) {
            errorText = 'Error text could not be retrieved';
          }
        }
        
        // Test form interaction if possible
        let formInteractionResult = 'N/A';
        if (formsCount > 0 && !hasLoadingStuck) {
          try {
            const firstInput = page.locator('input[type="text"], input:not([type]), textarea').first();
            if (await firstInput.count() > 0) {
              await firstInput.fill('TEST_VALUE');
              formInteractionResult = 'Success';
            }
          } catch (interactionError) {
            formInteractionResult = `Failed: ${interactionError.message}`;
          }
        }
        
        // Take screenshot
        await page.screenshot({ path: `form_test_${form.name.replace(/\s+/g, '_').toLowerCase()}.png`, fullPage: true });
        
        // Determine overall status
        let status = 'SUCCESS';
        const issues = [];
        
        if (hasNoFormError) {
          status = 'ERROR';
          issues.push('No form found on page');
        }
        if (hasLoadingStuck) {
          status = 'ERROR';
          issues.push('Loading spinner stuck');
        }
        if (hasErrorMessages) {
          status = 'ERROR';
          issues.push(`Error messages present: ${errorText}`);
        }
        if (formsCount > 0 && inputsCount === 0) {
          status = 'WARNING';
          issues.push('Form exists but no inputs found');
        }
        
        const result = {
          section: form.section,
          name: form.name,
          status: status,
          pageHeading: pageHeading,
          formsCount: formsCount,
          inputsCount: inputsCount,
          buttonsCount: buttonsCount,
          tablesCount: tablesCount,
          formInteraction: formInteractionResult,
          issues: issues,
          screenshot: `form_test_${form.name.replace(/\s+/g, '_').toLowerCase()}.png`
        };
        
        formResults.push(result);
        
        console.log(`  Status: ${status}`);
        console.log(`  Heading: ${pageHeading}`);
        console.log(`  Forms: ${formsCount}, Inputs: ${inputsCount}, Tables: ${tablesCount}`);
        if (issues.length > 0) {
          console.log(`  Issues: ${issues.join(', ')}`);
        }
        
      } catch (error) {
        console.log(`  ❌ Critical error testing ${form.name}: ${error.message}`);
        formResults.push({
          section: form.section,
          name: form.name,
          status: 'CRITICAL_ERROR',
          error: error.message,
          screenshot: `form_error_${form.name.replace(/\s+/g, '_').toLowerCase()}.png`
        });
        
        await page.screenshot({ path: `form_error_${form.name.replace(/\s+/g, '_').toLowerCase()}.png`, fullPage: true });
      }
    }

    // Generate comprehensive report
    console.log('\n' + '='.repeat(80));
    console.log('📋 COMPREHENSIVE FORM TESTING REPORT');
    console.log('='.repeat(80));
    
    // Summary statistics
    const successCount = formResults.filter(r => r.status === 'SUCCESS').length;
    const warningCount = formResults.filter(r => r.status === 'WARNING').length;
    const errorCount = formResults.filter(r => r.status === 'ERROR').length;
    const criticalCount = formResults.filter(r => r.status === 'CRITICAL_ERROR').length;
    
    console.log(`\n📊 SUMMARY:`);
    console.log(`  • Total forms tested: ${formResults.length}`);
    console.log(`  • ✅ Working forms: ${successCount}`);
    console.log(`  • ⚠️  Forms with warnings: ${warningCount}`);
    console.log(`  • ❌ Forms with errors: ${errorCount}`);
    console.log(`  • 💥 Forms with critical errors: ${criticalCount}`);
    console.log(`  • 🔴 Console errors: ${consoleErrors.length}`);
    console.log(`  • 🌐 Network errors: ${networkErrors.length}`);
    
    // Detailed results by category
    if (successCount > 0) {
      console.log(`\n✅ WORKING FORMS (${successCount}):`);
      formResults.filter(r => r.status === 'SUCCESS').forEach(result => {
        console.log(`  • ${result.section} > ${result.name}`);
        console.log(`    - ${result.formsCount} forms, ${result.inputsCount} inputs, ${result.tablesCount} tables`);
        console.log(`    - Form interaction: ${result.formInteraction}`);
      });
    }
    
    if (warningCount > 0) {
      console.log(`\n⚠️  FORMS WITH WARNINGS (${warningCount}):`);
      formResults.filter(r => r.status === 'WARNING').forEach(result => {
        console.log(`  • ${result.section} > ${result.name}`);
        console.log(`    - Issues: ${result.issues.join(', ')}`);
        console.log(`    - Screenshot: ${result.screenshot}`);
      });
    }
    
    if (errorCount > 0) {
      console.log(`\n❌ FORMS WITH ERRORS (${errorCount}):`);
      formResults.filter(r => r.status === 'ERROR').forEach(result => {
        console.log(`  • ${result.section} > ${result.name}`);
        console.log(`    - Issues: ${result.issues.join(', ')}`);
        console.log(`    - Screenshot: ${result.screenshot}`);
      });
    }
    
    if (criticalCount > 0) {
      console.log(`\n💥 FORMS WITH CRITICAL ERRORS (${criticalCount}):`);
      formResults.filter(r => r.status === 'CRITICAL_ERROR').forEach(result => {
        console.log(`  • ${result.section} > ${result.name}`);
        console.log(`    - Error: ${result.error}`);
        console.log(`    - Screenshot: ${result.screenshot}`);
      });
    }
    
    if (consoleErrors.length > 0) {
      console.log(`\n🔴 CONSOLE ERRORS (${consoleErrors.length}):`);
      consoleErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.message}`);
      });
    }
    
    if (networkErrors.length > 0) {
      console.log(`\n🌐 NETWORK ERRORS (${networkErrors.length}):`);
      networkErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.status} - ${error.url}`);
      });
    }
    
    console.log('\n' + '='.repeat(80));

  } catch (error) {
    console.error('❌ Critical test failure:', error.message);
    await page.screenshot({ path: 'form_test_critical_failure.png', fullPage: true });
    throw error;
  } finally {
    await browser.close();
    console.log('👋 Browser closed');
  }
}

// Run the test
formIssuesTest().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});