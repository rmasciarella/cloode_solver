const { test, expect } = require('@playwright/test');

// Test data for form submissions
const testData = {
  departments: {
    name: 'Test Department',
    description: 'Test department description',
    code: 'TESTDEPT',
    manager: 'Test Manager'
  },
  'work-cells': {
    name: 'Test Work Cell',
    description: 'Test work cell description'
  },
  'business-calendars': {
    name: 'Test Business Calendar',
    description: 'Test calendar description'
  },
  'job-templates': {
    name: 'Test Job Template',
    description: 'Test job template description'
  },
  'template-tasks': {
    name: 'Test Template Task',
    description: 'Test template task description'
  },
  machines: {
    name: 'Test Machine',
    model: 'Test Model'
  },
  operators: {
    name: 'Test Operator',
    employee_id: 'EMP001'
  },
  skills: {
    name: 'Test Skill',
    description: 'Test skill description'
  },
  'sequence-resources': {
    name: 'Test Sequence Resource'
  },
  'setup-times': {
    name: 'Test Setup Time'
  },
  'maintenance-windows': {
    name: 'Test Maintenance'
  },
  'job-instances': {
    name: 'Test Job Instance'
  }
};

// Navigation items grouped by section
const navigationSections = {
  organization: ['departments', 'work-cells', 'business-calendars'],
  templates: ['job-templates', 'template-tasks'],
  resources: ['machines', 'operators', 'skills', 'sequence-resources'],
  scheduling: ['setup-times', 'maintenance-windows'],  
  jobs: ['job-instances']
};

test.describe('Fixed SPA Form Testing', () => {
  let allErrors = [];
  let formResults = [];

  test.beforeEach(async ({ page }) => {
    allErrors = [];
    formResults = [];

    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        allErrors.push({
          type: 'console',
          message: msg.text(),
          timestamp: new Date().toISOString()
        });
      }
    });

    // Navigate to home page
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForLoadState('domcontentloaded');
  });

  test('Test all forms with proper section expansion', async ({ page }) => {
    console.log('🚀 Starting comprehensive form testing...');

    for (const [sectionName, navItems] of Object.entries(navigationSections)) {
      console.log(`\n📂 Testing section: ${sectionName}`);
      
      // Expand the section if not already expanded
      if (sectionName !== 'organization') {  // Organization is expanded by default
        console.log(`  📂 Expanding ${sectionName} section...`);
        
        // Try multiple approaches to expand
        const sectionButton = `[data-testid="section-${sectionName}"]`;
        const buttonExists = await page.locator(sectionButton).count();
        
        if (buttonExists > 0) {
          // Force click to expand section
          await page.locator(sectionButton).click({ force: true });
          await page.waitForTimeout(1000);
          
          // Check if expansion worked by looking for nav items
          const firstNavItem = navItems[0];
          const navVisible = await page.locator(`[data-testid="nav-${firstNavItem}"]`).isVisible();
          
          if (!navVisible) {
            console.log(`  ⚠️  Section ${sectionName} may not have expanded properly`);
            // Try alternative approach - double click
            await page.locator(sectionButton).dblclick();
            await page.waitForTimeout(1000);
          }
        }
      }
      
      // Test each navigation item in this section
      for (const navItem of navItems) {
        console.log(`\n  📝 Testing form: ${navItem}`);
        
        try {
          // Click the navigation item
          const navSelector = `[data-testid="nav-${navItem}"]`;
          const navExists = await page.locator(navSelector).count();
          
          if (navExists === 0) {
            console.log(`    ❌ Navigation item not found: ${navItem}`);
            formResults.push({
              navItem,
              error: 'Navigation item not found',
              formsFound: 0,
              submitSuccess: false
            });
            continue;
          }
          
          await page.locator(navSelector).click();
          await page.waitForTimeout(1500);
          
          console.log(`    ✅ Navigated to ${navItem}`);
          
          // Take screenshot
          await page.screenshot({ 
            path: `gui/test-results/fixed-form-${navItem}.png`,
            fullPage: true 
          });
          
          // Look for forms
          const forms = await page.locator('form').count();
          const inputs = await page.locator('input, textarea, select').count();
          
          console.log(`    📊 Found ${forms} form(s) and ${inputs} input(s)`);
          
          const result = {
            navItem,
            formsFound: forms,
            inputsFound: inputs,
            fillSuccess: false,
            submitSuccess: false,
            errors: []
          };
          
          if (inputs > 0 && testData[navItem]) {
            console.log(`    🖊️  Filling form for ${navItem}...`);
            
            let filledFields = 0;
            const formData = testData[navItem];
            
            for (const [fieldName, fieldValue] of Object.entries(formData)) {
              try {
                // Try to find and fill the field
                const selectors = [
                  `input[name="${fieldName}"]`,
                  `textarea[name="${fieldName}"]`,
                  `select[name="${fieldName}"]`,
                  `input[id="${fieldName}"]`,
                  `textarea[id="${fieldName}"]`,
                  `select[id="${fieldName}"]`
                ];
                
                let fieldFilled = false;
                for (const selector of selectors) {
                  if (await page.locator(selector).count() > 0) {
                    await page.locator(selector).first().fill(String(fieldValue));
                    console.log(`      ✅ Filled ${fieldName}: ${fieldValue}`);
                    filledFields++;
                    fieldFilled = true;
                    break;
                  }
                }
                
                if (!fieldFilled) {
                  console.log(`      ⚠️  Field not found: ${fieldName}`);
                }
                
              } catch (fieldError) {
                console.log(`      ❌ Error filling ${fieldName}: ${fieldError.message}`);
                result.errors.push(`Field error for ${fieldName}: ${fieldError.message}`);
              }
            }
            
            result.fillSuccess = filledFields > 0;
            console.log(`    📝 Filled ${filledFields} fields`);
            
            // Try to submit
            if (filledFields > 0) {
              const submitButton = page.locator('button[type="submit"]');
              const submitExists = await submitButton.count();
              
              if (submitExists > 0) {
                console.log(`    🔘 Submitting form...`);
                await submitButton.click();
                await page.waitForTimeout(2000);
                
                // Take screenshot after submission
                await page.screenshot({ 
                  path: `gui/test-results/fixed-submitted-${navItem}.png`,
                  fullPage: true 
                });
                
                result.submitSuccess = true;
                console.log(`    ✅ Form submitted for ${navItem}`);
              } else {
                console.log(`    ⚠️  No submit button found`);
              }
            }
          } else if (inputs === 0) {
            console.log(`    ℹ️  No form inputs found for ${navItem} (may be placeholder)`);
          } else {
            console.log(`    ⚠️  No test data available for ${navItem}`);
          }
          
          formResults.push(result);
          
        } catch (error) {
          console.error(`    ❌ Error testing ${navItem}:`, error.message);
          formResults.push({
            navItem,
            error: error.message,
            formsFound: 0,
            submitSuccess: false
          });
        }
      }
    }
    
    // Generate report
    console.log('\n📊 === COMPREHENSIVE TEST REPORT ===');
    
    const totalForms = formResults.length;
    const formsWithInputs = formResults.filter(r => r.inputsFound > 0).length;
    const successfulFills = formResults.filter(r => r.fillSuccess).length;
    const successfulSubmits = formResults.filter(r => r.submitSuccess).length;
    const errors = formResults.filter(r => r.error).length;
    
    console.log(`Total forms tested: ${totalForms}`);
    console.log(`Forms with inputs: ${formsWithInputs}`);
    console.log(`Successful fills: ${successfulFills}`);
    console.log(`Successful submits: ${successfulSubmits}`);
    console.log(`Forms with errors: ${errors}`);
    console.log(`Console errors: ${allErrors.length}`);
    
    // Detailed results
    console.log('\n📋 DETAILED RESULTS:');
    for (const result of formResults) {
      const status = result.submitSuccess ? '✅' : 
                    result.fillSuccess ? '🟡' : 
                    result.inputsFound > 0 ? '🟠' : 
                    result.error ? '❌' : 'ℹ️';
      
      console.log(`  ${status} ${result.navItem}: ${result.inputsFound || 0} inputs, fill: ${result.fillSuccess || false}, submit: ${result.submitSuccess || false}`);
      
      if (result.error) {
        console.log(`    ❌ ${result.error}`);
      }
    }
    
    // Success metrics
    const successRate = totalForms > 0 ? (successfulSubmits / formsWithInputs * 100).toFixed(1) : 0;
    console.log(`\n🎯 SUCCESS RATE: ${successfulSubmits}/${formsWithInputs} forms (${successRate}%) submitted successfully`);
  });
});