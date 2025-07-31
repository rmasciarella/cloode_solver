const { test, expect } = require('@playwright/test');

test.describe('Console Error Detection', () => {
  let consoleErrors = [];
  let networkErrors = [];

  test.beforeEach(async ({ page }) => {
    // Reset error arrays for each test
    consoleErrors = [];
    networkErrors = [];

    // Monitor console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const error = {
          message: msg.text(),
          location: msg.location(),
          timestamp: new Date().toISOString()
        };
        consoleErrors.push(error);
        console.log(`🔴 Console Error: ${msg.text()}`);
      }
    });

    // Monitor network failures
    page.on('response', response => {
      if (response.status() >= 400) {
        const error = {
          status: response.status(),
          url: response.url(),
          timestamp: new Date().toISOString()
        };
        networkErrors.push(error);
        console.log(`🔴 Network Error: ${response.status()} ${response.url()}`);
      }
    });

    // Monitor page errors
    page.on('pageerror', error => {
      const pageError = {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      };
      consoleErrors.push(pageError);
      console.log(`🔴 Page Error: ${error.message}`);
    });
  });

  test('should detect console errors across all GUI pages', async ({ page }) => {
    console.log('🔍 Starting console error detection across all pages...');
    
    // Navigate to home page
    await page.goto('/');
    await page.waitForTimeout(2000);
    console.log('📍 Tested: Home page');

    // Define all navigation items to test
    const navigationItems = [
      { section: 'Organization', items: ['Departments', 'Work Cells', 'Business Calendars'] },
      { section: 'Templates', items: ['Job Templates', 'Template Tasks'] },
      { section: 'Resources', items: ['Machines', 'Operators', 'Skills', 'Sequence Resources'] },
      { section: 'Scheduling', items: ['Setup Times'] },
      { section: 'Jobs', items: ['Job Instances'] }
    ];

    let testedPages = 0;
    let successfulPages = 0;

    for (const section of navigationItems) {
      console.log(`\n📁 Testing ${section.section} section...`);
      
      try {
        // Click section to expand
        const sectionButton = page.locator(`button:has-text("${section.section}")`);
        if (await sectionButton.count() > 0) {
          await sectionButton.click();
          await page.waitForTimeout(1000);
        }

        for (const item of section.items) {
          testedPages++;
          console.log(`  🔍 Testing ${item}...`);
          
          try {
            // Click navigation item
            const itemButton = page.locator(`button:has-text("${item}")`);
            if (await itemButton.count() > 0) {
              await itemButton.click();
              await page.waitForTimeout(3000); // Wait for page to load
              
              // Take screenshot for reference
              await page.screenshot({ 
                path: `test-results/console-test-${item.toLowerCase().replace(/\s+/g, '-')}.png`,
                fullPage: true 
              });
              
              successfulPages++;
              console.log(`    ✅ ${item}: Page loaded successfully`);
            } else {
              console.log(`    ⚠️ ${item}: Navigation button not found`);
            }
          } catch (error) {
            console.log(`    ❌ ${item}: ${error.message}`);
          }
        }
      } catch (sectionError) {
        console.log(`❌ Section ${section.section} failed: ${sectionError.message}`);
      }
    }

    // Report results
    console.log('\n' + '='.repeat(70));
    console.log('🚨 CONSOLE ERROR DETECTION REPORT');
    console.log('='.repeat(70));
    console.log(`📊 Pages tested: ${testedPages} | Successful: ${successfulPages}`);
    
    if (consoleErrors.length > 0) {
      console.log(`\n🔴 CONSOLE ERRORS FOUND (${consoleErrors.length}):`);
      consoleErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.message}`);
        if (error.location) {
          console.log(`     Location: ${error.location.url || 'unknown'}:${error.location.lineNumber || '?'}`);
        }
        if (error.stack) {
          console.log(`     Stack: ${error.stack.substring(0, 100)}...`);
        }
      });
    } else {
      console.log('\n🎉 NO CONSOLE ERRORS DETECTED!');
    }

    if (networkErrors.length > 0) {
      console.log(`\n🔴 NETWORK ERRORS FOUND (${networkErrors.length}):`);
      networkErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.status} - ${error.url}`);
      });
    } else {
      console.log('\n🎉 NO NETWORK ERRORS DETECTED!');
    }

    // Save detailed error report
    const errorReport = {
      timestamp: new Date().toISOString(),
      pagesThank: testedPages,
      successfulPages: successfulPages,
      consoleErrors: consoleErrors,
      networkErrors: networkErrors
    };

    const fs = require('fs');
    fs.writeFileSync('console-error-report.json', JSON.stringify(errorReport, null, 2));
    console.log('\n📄 Detailed error report saved to: console-error-report.json');

    // Test should not fail if errors are found - we want to capture them
    console.log('\n✅ Console error detection completed successfully');
  });
});