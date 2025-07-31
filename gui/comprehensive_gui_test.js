const { chromium } = require('playwright');

async function comprehensiveGUITest() {
  console.log('🔍 Starting Comprehensive GUI Testing...');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  // Collect all issues found
  const issues = [];
  const successfulPages = [];
  
  // Monitor console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`🔴 Console Error: ${msg.text()}`);
      issues.push({
        type: 'console_error',
        message: msg.text(),
        page: 'global'
      });
    }
  });

  // Monitor network failures
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`🔴 Network Error: ${response.status()} ${response.url()}`);
      issues.push({
        type: 'network_error',
        status: response.status(),
        url: response.url(),
        page: 'global'
      });
    }
  });

  try {
    // Navigate to the GUI
    console.log('📍 Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Take initial screenshot
    await page.screenshot({ path: 'test_initial_load.png', fullPage: true });
    console.log('📸 Initial load screenshot saved');

    // Define all navigation sections and their items
    const navigationSections = [
      {
        title: 'Organization',
        items: [
          { key: 'departments', label: 'Departments' },
          { key: 'work-cells', label: 'Work Cells' },
          { key: 'business-calendars', label: 'Business Calendars' },
        ]
      },
      {
        title: 'Templates',
        items: [
          { key: 'job-templates', label: 'Job Templates' },
          { key: 'template-tasks', label: 'Template Tasks' },
          { key: 'template-precedences', label: 'Template Precedences' },
        ]
      },
      {
        title: 'Resources',
        items: [
          { key: 'machines', label: 'Machines' },
          { key: 'operators', label: 'Operators' },
          { key: 'skills', label: 'Skills' },
          { key: 'sequence-resources', label: 'Sequence Resources' },
        ]
      },
      {
        title: 'Scheduling',
        items: [
          { key: 'setup-times', label: 'Setup Times' },
          { key: 'maintenance-windows', label: 'Maintenance Windows' },
        ]
      },
      {
        title: 'Jobs',
        items: [
          { key: 'job-instances', label: 'Job Instances' },
          { key: 'job-tasks', label: 'Job Tasks' },
        ]
      },
    ];

    // Test each section and page
    for (const section of navigationSections) {
      console.log(`\n📁 Testing ${section.title} section...`);
      
      try {
        // Expand the section
        const sectionButton = page.locator(`button:has-text("${section.title}")`);
        const isExpanded = await page.locator(`button:has-text("${section.title}") + div`).isVisible().catch(() => false);
        
        if (!isExpanded) {
          await sectionButton.click();
          await page.waitForTimeout(500);
        }
        
        console.log(`✅ ${section.title} section expanded`);
        
        // Test each item in the section
        for (const item of section.items) {
          console.log(`  🔍 Testing ${item.label} page...`);
          
          try {
            // Click the navigation item
            const navItem = page.locator(`button:has-text("${item.label}")`);
            await navItem.click();
            await page.waitForTimeout(1000);
            
            // Check if the page loaded correctly
            const pageHeading = await page.locator('h2').textContent();
            console.log(`    📄 Page heading: ${pageHeading}`);
            
            // Look for forms
            const formsCount = await page.locator('form').count();
            console.log(`    📝 Forms found: ${formsCount}`);
            
            // Look for inputs
            const inputsCount = await page.locator('input, textarea, select, [role="combobox"]').count();
            console.log(`    📋 Input fields found: ${inputsCount}`);
            
            // Look for tables
            const tablesCount = await page.locator('table').count();
            console.log(`    📊 Tables found: ${tablesCount}`);
            
            // Look for error messages or crash indicators
            const errorElements = await page.locator('[class*="error"], [class*="toast"], .text-red-500, .text-red-600').count();
            
            if (errorElements > 0) {
              console.log(`    ⚠️ Potential error elements found: ${errorElements}`);
              const errorText = await page.locator('[class*="error"], [class*="toast"], .text-red-500, .text-red-600').first().textContent().catch(() => 'Unknown error');
              issues.push({
                type: 'ui_error',
                page: item.label,
                section: section.title,
                message: errorText
              });
            }
            
            // Take screenshot of each page
            await page.screenshot({ path: `test_${item.key.replace(/-/g, '_')}.png`, fullPage: true });
            console.log(`    📸 Screenshot saved: test_${item.key.replace(/-/g, '_')}.png`);
            
            // Test form interaction if form exists
            if (formsCount > 0) {
              try {
                // Try to fill first text input
                const firstInput = page.locator('input[type="text"], input:not([type])').first();
                if (await firstInput.count() > 0) {
                  await firstInput.fill('TEST_DATA');
                  console.log(`    ✏️ Successfully filled first input field`);
                }
                
                // Try to interact with first select/combobox
                const firstSelect = page.locator('[role="combobox"]').first();
                if (await firstSelect.count() > 0) {
                  await firstSelect.click();
                  await page.waitForTimeout(500);
                  console.log(`    📋 Successfully clicked first dropdown`);
                }
              } catch (formError) {
                console.log(`    ⚠️ Form interaction failed: ${formError.message}`);
                issues.push({
                  type: 'form_interaction_error',
                  page: item.label,
                  section: section.title,
                  message: formError.message
                });
              }
            }
            
            successfulPages.push({
              section: section.title,
              page: item.label,
              forms: formsCount,
              inputs: inputsCount,
              tables: tablesCount
            });
            
            console.log(`    ✅ ${item.label} page tested successfully`);
            
          } catch (pageError) {
            console.log(`    ❌ Failed to test ${item.label} page: ${pageError.message}`);
            issues.push({
              type: 'page_load_error',
              page: item.label,
              section: section.title,
              message: pageError.message
            });
            
            // Take error screenshot
            await page.screenshot({ path: `test_error_${item.key.replace(/-/g, '_')}.png`, fullPage: true });
          }
        }
        
      } catch (sectionError) {
        console.log(`❌ Failed to test ${section.title} section: ${sectionError.message}`);
        issues.push({
          type: 'section_error',
          section: section.title,
          message: sectionError.message
        });
      }
    }

    // Generate comprehensive report
    console.log('\n' + '='.repeat(60));
    console.log('📋 COMPREHENSIVE GUI TEST REPORT');
    console.log('='.repeat(60));
    
    console.log(`\n✅ SUCCESSFUL PAGES (${successfulPages.length}):`);
    successfulPages.forEach(page => {
      console.log(`  • ${page.section} > ${page.page} (${page.forms} forms, ${page.inputs} inputs, ${page.tables} tables)`);
    });
    
    console.log(`\n❌ ISSUES FOUND (${issues.length}):`);
    if (issues.length === 0) {
      console.log('  🎉 No issues found! All pages working correctly.');
    } else {
      issues.forEach((issue, index) => {
        console.log(`  ${index + 1}. [${issue.type.toUpperCase()}] ${issue.page || issue.section || 'Global'}`);
        console.log(`     ${issue.message}`);
        if (issue.status) console.log(`     Status: ${issue.status}`);
        if (issue.url) console.log(`     URL: ${issue.url}`);
      });
    }
    
    console.log(`\n📊 SUMMARY:`);
    console.log(`  • Total pages tested: ${successfulPages.length}`);
    console.log(`  • Total issues found: ${issues.length}`);
    console.log(`  • Success rate: ${Math.round((successfulPages.length / (successfulPages.length + issues.filter(i => i.type === 'page_load_error').length)) * 100)}%`);
    
    // Categorize issues
    const issuesByType = {};
    issues.forEach(issue => {
      issuesByType[issue.type] = (issuesByType[issue.type] || 0) + 1;
    });
    
    console.log(`\n🏷️ ISSUE BREAKDOWN:`);
    Object.entries(issuesByType).forEach(([type, count]) => {
      console.log(`  • ${type.replace(/_/g, ' ').toUpperCase()}: ${count}`);
    });

    console.log('\n' + '='.repeat(60));

  } catch (error) {
    console.error('❌ Test execution failed:', error.message);
    await page.screenshot({ path: 'test_critical_error.png', fullPage: true });
    throw error;
  } finally {
    await browser.close();
    console.log('👋 Browser closed');
  }
}

// Run the comprehensive test
comprehensiveGUITest().catch(error => {
  console.error('Critical test failure:', error);
  process.exit(1);
});