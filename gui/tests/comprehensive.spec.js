const { test, expect } = require('@playwright/test');
const { testData, navigationStructure, selectors, helpers } = require('./fixtures/test-data');

test.describe('Comprehensive GUI Tests', () => {
  let testResults = [];

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    
    // Monitor console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`🔴 Console Error: ${msg.text()}`);
        testResults.push({
          type: 'console_error',
          message: msg.text(),
          timestamp: new Date().toISOString()
        });
      }
    });

    // Monitor network failures
    page.on('response', response => {
      if (response.status() >= 400) {
        console.log(`🔴 Network Error: ${response.status()} ${response.url()}`);
        testResults.push({
          type: 'network_error',
          status: response.status(),
          url: response.url(),
          timestamp: new Date().toISOString()
        });
      }
    });
  });

  test('should test all navigation sections systematically', async ({ page }) => {
    console.log('🔍 Starting comprehensive navigation test...');
    
    const results = [];

    for (const section of navigationStructure) {
      console.log(`\n📁 Testing ${section.title} section...`);
      
      try {
        // Expand section
        await page.click(selectors.navigation.sectionButton(section.title));
        await page.waitForTimeout(500);
        
        for (const item of section.items) {
          console.log(`  🔍 Testing ${item.label}...`);
          
          try {
            // Navigate to page
            await helpers.navigateToPage(page, section.title, item.label);
            
            // Check page elements
            const pageHeading = await page.locator('h2').textContent();
            const formsCount = await page.locator(selectors.forms.form).count();
            const tablesCount = await page.locator(selectors.tables.table).count();
            const inputsCount = await page.locator('input, textarea, select, [role="combobox"]').count();
            
            // Check for errors
            const errorCheck = await helpers.checkValidationErrors(page);
            
            // Take screenshot
            const screenshotPath = await helpers.takeScreenshot(page, `nav-${item.key}`);
            
            const result = {
              section: section.title,
              page: item.label,
              key: item.key,
              pageHeading: pageHeading?.trim(),
              formsCount,
              tablesCount,
              inputsCount,
              hasErrors: errorCheck.hasErrors,
              errorCount: errorCheck.errorCount,
              screenshot: screenshotPath,
              status: 'success'
            };
            
            results.push(result);
            console.log(`    ✅ ${item.label}: ${formsCount} forms, ${tablesCount} tables, ${inputsCount} inputs`);
            
          } catch (error) {
            const errorResult = {
              section: section.title,
              page: item.label,
              key: item.key,
              error: error.message,
              status: 'failed'
            };
            
            results.push(errorResult);
            console.log(`    ❌ ${item.label}: ${error.message}`);
            
            // Take error screenshot
            await helpers.takeScreenshot(page, `nav-error-${item.key}`);
          }
        }
        
      } catch (sectionError) {
        console.log(`❌ Section ${section.title} failed: ${sectionError.message}`);
      }
    }

    // Generate report
    console.log('\n' + '='.repeat(60));
    console.log('📋 NAVIGATION TEST REPORT');
    console.log('='.repeat(60));
    
    const successfulPages = results.filter(r => r.status === 'success');
    const failedPages = results.filter(r => r.status === 'failed');
    
    console.log(`\n✅ SUCCESSFUL PAGES (${successfulPages.length}):`);
    successfulPages.forEach(page => {
      console.log(`  • ${page.section} > ${page.page}`);
      console.log(`    Forms: ${page.formsCount}, Tables: ${page.tablesCount}, Inputs: ${page.inputsCount}`);
      if (page.hasErrors) console.log(`    ⚠️ Errors detected: ${page.errorCount}`);
    });
    
    if (failedPages.length > 0) {
      console.log(`\n❌ FAILED PAGES (${failedPages.length}):`);
      failedPages.forEach(page => {
        console.log(`  • ${page.section} > ${page.page}: ${page.error}`);
      });
    }
    
    console.log(`\n📊 SUMMARY: ${successfulPages.length}/${results.length} pages successful`);
    
    // Ensure majority of pages work
    expect(successfulPages.length).toBeGreaterThan(results.length * 0.7); // At least 70% success rate
  });

  test('should test form interactions across multiple pages', async ({ page }) => {
    console.log('📝 Starting comprehensive form test...');
    
    const formTests = [
      {
        section: 'Organization',
        page: 'Departments',
        data: testData.departments.valid,
        requiredFields: ['code', 'name']
      },
      {
        section: 'Resources',
        page: 'Machines',
        data: testData.machines.valid,
        requiredFields: ['code', 'name']
      },
      {
        section: 'Resources',
        page: 'Operators',
        data: testData.operators.valid,
        requiredFields: ['code', 'name']
      }
    ];

    const formResults = [];

    for (const formTest of formTests) {
      console.log(`\n📝 Testing ${formTest.section} > ${formTest.page} form...`);
      
      try {
        // Navigate to page
        await helpers.navigateToPage(page, formTest.section, formTest.page);
        
        // Check if form exists
        const formExists = await page.locator(selectors.forms.form).count() > 0;
        
        if (!formExists) {
          formResults.push({
            ...formTest,
            status: 'no_form',
            message: 'No form found on page'
          });
          continue;
        }

        // Generate unique test data
        const testCode = helpers.generateTestCode(formTest.data.code);
        const uniqueData = { ...formTest.data, code: testCode };
        
        // Fill form
        await helpers.fillForm(page, uniqueData);
        
        // Take screenshot of filled form
        await helpers.takeScreenshot(page, `form-filled-${formTest.page.toLowerCase().replace(/\s+/g, '-')}`);
        
        // Test form validation - clear required field
        if (formTest.requiredFields.length > 0) {
          const firstRequiredField = formTest.requiredFields[0];
          await page.fill(`input[id="${firstRequiredField}"]`, '');
          
          // Try to submit
          const submitButton = page.locator(selectors.forms.submitButton);
          if (await submitButton.count() > 0) {
            await submitButton.click();
            await page.waitForTimeout(1000);
            
            // Check for validation errors
            const validationCheck = await helpers.checkValidationErrors(page);
            
            formResults.push({
              ...formTest,
              status: 'validation_tested',
              hasValidation: validationCheck.hasErrors,
              validationErrors: validationCheck.errorMessages
            });
            
            console.log(`    ✅ Validation test: ${validationCheck.hasErrors ? 'Working' : 'No errors shown'}`);
            
            // Take screenshot of validation state
            await helpers.takeScreenshot(page, `form-validation-${formTest.page.toLowerCase().replace(/\s+/g, '-')}`);
            
            // Restore valid data and submit
            await page.fill(`input[id="${firstRequiredField}"]`, uniqueData[firstRequiredField]);
            await submitButton.click();
            await page.waitForTimeout(2000);
            
            // Check for success/error feedback
            const successCount = await page.locator(selectors.feedback.successElements).count();
            const errorCount = await page.locator(selectors.feedback.errorElements).count();
            const toastCount = await page.locator(selectors.feedback.toastElements).count();
            
            console.log(`    📊 Submission feedback: Success(${successCount}), Errors(${errorCount}), Toasts(${toastCount})`);
            
            // Take final screenshot
            await helpers.takeScreenshot(page, `form-submitted-${formTest.page.toLowerCase().replace(/\s+/g, '-')}`);
          }
        }
        
      } catch (error) {
        formResults.push({
          ...formTest,
          status: 'failed',
          error: error.message
        });
        console.log(`    ❌ Form test failed: ${error.message}`);
      }
    }

    // Report form test results
    console.log('\n' + '='.repeat(50));
    console.log('📝 FORM TEST REPORT');
    console.log('='.repeat(50));
    
    formResults.forEach(result => {
      console.log(`\n${result.section} > ${result.page}:`);
      console.log(`  Status: ${result.status}`);
      if (result.hasValidation !== undefined) {
        console.log(`  Validation: ${result.hasValidation ? '✅ Working' : '⚠️ No validation shown'}`);
      }
      if (result.error) {
        console.log(`  Error: ${result.error}`);
      }
    });

    // Ensure at least some forms work
    const workingForms = formResults.filter(r => r.status === 'validation_tested').length;
    expect(workingForms).toBeGreaterThan(0);
  });

  test('should perform comprehensive database connectivity test', async ({ page }) => {
    console.log('🔌 Starting database connectivity test...');
    
    const databaseTests = [];

    // Test multiple pages that should load data
    const pagesToTest = [
      { section: 'Organization', page: 'Departments' },
      { section: 'Resources', page: 'Machines' },
      { section: 'Templates', page: 'Job Templates' }
    ];

    for (const pageTest of pagesToTest) {
      console.log(`\n🔍 Testing database connectivity for ${pageTest.section} > ${pageTest.page}...`);
      
      try {
        // Navigate to page
        await helpers.navigateToPage(page, pageTest.section, pageTest.page);
        
        // Wait for potential data loading
        await page.waitForTimeout(3000);
        
        // Check for data indicators
        const hasTable = await page.locator(selectors.tables.table).count() > 0;
        const hasForm = await page.locator(selectors.forms.form).count() > 0;
        const hasLoading = await page.locator(selectors.feedback.loadingElements).count() > 0;
        const hasErrors = await page.locator(selectors.feedback.errorElements).count() > 0;
        
        let tableRows = 0;
        if (hasTable) {
          tableRows = await page.locator(selectors.tables.rows).count();
        }
        
        const result = {
          section: pageTest.section,
          page: pageTest.page,
          hasTable,
          hasForm,
          hasLoading,
          hasErrors,
          tableRows,
          status: hasErrors ? 'error' : (hasTable || hasForm) ? 'success' : 'unknown'
        };
        
        databaseTests.push(result);
        
        console.log(`    📊 Results: Table(${hasTable}), Form(${hasForm}), Loading(${hasLoading}), Errors(${hasErrors})`);
        if (hasTable) console.log(`    📋 Table rows: ${tableRows}`);
        
        // Take screenshot
        await helpers.takeScreenshot(page, `database-${pageTest.page.toLowerCase().replace(/\s+/g, '-')}`);
        
      } catch (error) {
        databaseTests.push({
          section: pageTest.section,
          page: pageTest.page,
          error: error.message,
          status: 'failed'
        });
        console.log(`    ❌ Database test failed: ${error.message}`);
      }
    }

    // Report database results
    console.log('\n' + '='.repeat(50));
    console.log('🔌 DATABASE CONNECTIVITY REPORT');
    console.log('='.repeat(50));
    
    databaseTests.forEach(result => {
      console.log(`\n${result.section} > ${result.page}: ${result.status.toUpperCase()}`);
      if (result.hasTable) console.log(`  📋 Table with ${result.tableRows} rows`);
      if (result.hasForm) console.log(`  📝 Form available`);
      if (result.hasErrors) console.log(`  ⚠️ Errors detected`);
      if (result.error) console.log(`  ❌ Error: ${result.error}`);
    });

    // Ensure database connectivity works for at least one page
    const successfulConnections = databaseTests.filter(r => r.status === 'success').length;
    expect(successfulConnections).toBeGreaterThan(0);
  });

  test.afterAll(async () => {
    // Final test results summary
    if (testResults.length > 0) {
      console.log('\n' + '='.repeat(60));
      console.log('🚨 ISSUES DETECTED DURING TESTING');
      console.log('='.repeat(60));
      
      const consoleErrors = testResults.filter(r => r.type === 'console_error');
      const networkErrors = testResults.filter(r => r.type === 'network_error');
      
      if (consoleErrors.length > 0) {
        console.log(`\n🔴 Console Errors (${consoleErrors.length}):`);
        consoleErrors.forEach((error, index) => {
          console.log(`  ${index + 1}. ${error.message}`);
        });
      }
      
      if (networkErrors.length > 0) {
        console.log(`\n🔴 Network Errors (${networkErrors.length}):`);
        networkErrors.forEach((error, index) => {
          console.log(`  ${index + 1}. ${error.status} - ${error.url}`);
        });
      }
    } else {
      console.log('\n🎉 No issues detected during testing!');
    }
  });
});