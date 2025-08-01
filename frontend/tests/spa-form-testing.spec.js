const { test, expect } = require('@playwright/test');

// Test data for form submissions
const testData = {
  departments: {
    name: 'Test Department',
    description: 'Test department description',
    code: 'TESTDEPT',
    manager: 'Test Manager'
  },
  machines: {
    name: 'Test Machine',
    model: 'Test Model',
    manufacturer: 'Test Manufacturer',
    capacity: '100',
    status: 'active'
  },
  'work-cells': {
    name: 'Test Work Cell',
    description: 'Test work cell description',
    location: 'Test Location',
    capacity: '50'
  },
  'business-calendars': {
    name: 'Test Business Calendar',
    description: 'Test calendar description',
    timezone: 'America/New_York',
    default_start_time: '08:00',
    default_end_time: '17:00'
  },
  operators: {
    name: 'Test Operator',
    employee_id: 'EMP001',
    email: 'test@example.com',
    phone: '555-0123',
    status: 'active'
  },
  skills: {
    name: 'Test Skill',
    description: 'Test skill description',
    category: 'Technical',
    level: 'Intermediate'
  },
  'sequence-resources': {
    name: 'Test Sequence Resource',
    resource_type: 'Machine',
    capacity: '10',
    availability: 'always'
  },
  'maintenance-windows': {
    name: 'Test Maintenance',
    description: 'Test maintenance description',
    estimated_duration: '120',
    frequency: 'monthly'
  },
  'job-templates': {
    name: 'Test Job Template',
    description: 'Test job template description',
    priority: '5',
    estimated_duration: '240'
  },
  'template-tasks': {
    name: 'Test Template Task',
    description: 'Test template task description',
    estimated_duration: '60',
    sequence_order: '1'
  },
  'job-instances': {
    name: 'Test Job Instance',
    description: 'Test job instance description',
    priority: '3',
    due_date: '2024-12-31'
  },
  'setup-times': {
    name: 'Test Setup Time',
    from_task_type: 'Type A',
    to_task_type: 'Type B',
    setup_time_minutes: '30'
  }
};

// Navigation items to test based on the actual SPA structure
const navigationItems = [
  'departments',
  'work-cells', 
  'business-calendars',
  'job-templates',
  'template-tasks',
  'machines',
  'operators',
  'skills',
  'sequence-resources',
  'setup-times',
  'maintenance-windows',
  'job-instances'
];

test.describe('SPA Form Testing', () => {
  let allErrors = [];
  let formResults = [];

  test.beforeEach(async ({ page }) => {
    // Reset error tracking
    allErrors = [];
    formResults = [];

    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const error = {
          type: 'console',
          message: msg.text(),
          location: msg.location(),
          timestamp: new Date().toISOString()
        };
        allErrors.push(error);
      }
    });

    // Listen for network errors
    page.on('response', response => {
      if (response.status() >= 400) {
        const error = {
          type: 'network',
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
          timestamp: new Date().toISOString()
        };
        allErrors.push(error);
      }
    });

    // Navigate to home page and wait for it to load
    await page.goto('/', { waitUntil: 'networkidle' });
    await page.waitForLoadState('domcontentloaded');
  });

  test('Test all SPA forms navigation and submission', async ({ page }) => {
    console.log('🚀 Starting SPA form testing...');

    for (const navItem of navigationItems) {
      console.log(`\n📝 Testing form: ${navItem}`);
      
      try {
        // Navigate using sidebar - expand the correct section based on the nav item
        let sectionToExpand = '';
        if (['departments', 'work-cells', 'business-calendars'].includes(navItem)) {
          sectionToExpand = 'organization';
        } else if (['job-templates', 'template-tasks'].includes(navItem)) {
          sectionToExpand = 'templates';
        } else if (['machines', 'operators', 'skills', 'sequence-resources'].includes(navItem)) {
          sectionToExpand = 'resources';
        } else if (['setup-times', 'maintenance-windows'].includes(navItem)) {
          sectionToExpand = 'scheduling';
        } else if (['job-instances'].includes(navItem)) {
          sectionToExpand = 'jobs';
        }
        
        if (sectionToExpand) {
          console.log(`    📂 Expanding section: ${sectionToExpand}`);
          await page.click(`[data-testid="section-${sectionToExpand}"]`, { timeout: 5000 });
          await page.waitForTimeout(500); // Wait for expansion animation
        }
        
        // Click the specific navigation item
        const navSelector = `[data-testid="nav-${navItem}"]`;
        await page.waitForSelector(navSelector, { timeout: 10000 });
        await page.click(navSelector);
        
        // Wait for form to load
        await page.waitForTimeout(1000);
        
        // Take screenshot of loaded form
        await page.screenshot({ 
          path: `gui/test-results/spa-form-${navItem}.png`,
          fullPage: true 
        });
        
        console.log(`  ✅ Navigated to ${navItem}`);
        
        // Look for form elements
        const forms = await page.locator('form').count();
        const inputs = await page.locator('input, textarea, select').count();
        
        console.log(`  📊 Found ${forms} form(s) and ${inputs} input(s)`);
        
        const result = {
          navItem,
          formsFound: forms,
          inputsFound: inputs,
          fillSuccess: false,
          submitSuccess: false,
          errors: []
        };
        
        if (inputs > 0) {
          // Try to fill form with test data
          const formData = testData[navItem];
          if (formData) {
            console.log(`  🖊️  Filling form for ${navItem}...`);
            
            let filledFields = 0;
            for (const [fieldName, fieldValue] of Object.entries(formData)) {
              try {
                // Try various selectors for the field
                const selectors = [
                  `input[name="${fieldName}"]`,
                  `textarea[name="${fieldName}"]`,
                  `select[name="${fieldName}"]`,
                  `input[id="${fieldName}"]`,
                  `textarea[id="${fieldName}"]`,
                  `select[id="${fieldName}"]`,
                  `input[placeholder*="${fieldName}"]`,
                  `textarea[placeholder*="${fieldName}"]`,
                  `[data-testid="${fieldName}"]`,
                  `[data-testid="${fieldName}-input"]`
                ];
                
                let fieldFilled = false;
                for (const selector of selectors) {
                  try {
                    if (await page.locator(selector).count() > 0) {
                      const element = page.locator(selector).first();
                      const tagName = await element.evaluate(el => el.tagName.toLowerCase());
                      
                      if (tagName === 'select') {
                        await element.selectOption(fieldValue);
                      } else {
                        await element.fill(fieldValue);
                      }
                      
                      console.log(`    ✅ Filled ${fieldName}: ${fieldValue}`);
                      filledFields++;
                      fieldFilled = true;
                      break;
                    }
                  } catch (fieldError) {
                    // Continue to next selector
                    continue;
                  }
                }
                
                if (!fieldFilled) {
                  console.log(`    ⚠️  Field not found: ${fieldName}`);
                }
                
              } catch (fieldError) {
                console.log(`    ❌ Error filling ${fieldName}: ${fieldError.message}`);
                result.errors.push(`Field error for ${fieldName}: ${fieldError.message}`);
              }
            }
            
            result.fillSuccess = filledFields > 0;
            console.log(`  📝 Filled ${filledFields} fields`);
            
            // Take screenshot after filling
            await page.screenshot({ 
              path: `gui/test-results/spa-form-filled-${navItem}.png`,
              fullPage: true 
            });
            
            // Try to submit form
            const submitSelectors = [
              'button[type="submit"]',
              'input[type="submit"]',
              'button:has-text("Submit")',
              'button:has-text("Save")',
              'button:has-text("Create")',
              'button:has-text("Add")',
              '[data-testid="submit-button"]',
              '[data-testid="save-button"]'
            ];
            
            let submitFound = false;
            for (const selector of submitSelectors) {
              try {
                if (await page.locator(selector).count() > 0) {
                  console.log(`    🔘 Found submit button: ${selector}`);
                  
                  // Click submit
                  await page.locator(selector).first().click();
                  
                  // Wait for response
                  await page.waitForTimeout(2000);
                  
                  // Take screenshot after submission
                  await page.screenshot({ 
                    path: `gui/test-results/spa-form-submitted-${navItem}.png`,
                    fullPage: true 
                  });
                  
                  console.log(`    ✅ Form submitted for ${navItem}`);
                  result.submitSuccess = true;
                  submitFound = true;
                  break;
                }
              } catch (submitError) {
                console.log(`    ❌ Submit error: ${submitError.message}`);
                result.errors.push(`Submit error: ${submitError.message}`);
              }
            }
            
            if (!submitFound) {
              console.log(`    ⚠️  No submit button found for ${navItem}`);
              result.errors.push('No submit button found');
            }
          } else {
            console.log(`    ⚠️  No test data available for ${navItem}`);
          }
        } else {
          console.log(`    ⚠️  No form inputs found for ${navItem}`);
        }
        
        formResults.push(result);
        
      } catch (error) {
        console.error(`❌ Error testing ${navItem}:`, error.message);
        formResults.push({
          navItem,
          formsFound: 0,
          inputsFound: 0,
          fillSuccess: false,
          submitSuccess: false,
          errors: [error.message]
        });
        allErrors.push({
          type: 'test_error',
          navItem,
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Generate comprehensive report
    console.log('\n📊 === SPA FORM TESTING REPORT ===');
    console.log(`Total forms tested: ${formResults.length}`);
    
    const successfulFills = formResults.filter(r => r.fillSuccess).length;
    const successfulSubmits = formResults.filter(r => r.submitSuccess).length;
    const formsWithInputs = formResults.filter(r => r.inputsFound > 0).length;
    
    console.log(`Forms with inputs: ${formsWithInputs}`);
    console.log(`Successful form fills: ${successfulFills}`);
    console.log(`Successful form submits: ${successfulSubmits}`);
    console.log(`Total errors: ${allErrors.length}`);
    
    // Detailed results
    console.log('\n📋 DETAILED RESULTS:');
    formResults.forEach(result => {
      const status = result.submitSuccess ? '✅' : 
                    result.fillSuccess ? '🟡' : 
                    result.inputsFound > 0 ? '🟠' : '❌';
      
      console.log(`  ${status} ${result.navItem}: ${result.inputsFound} inputs, fill: ${result.fillSuccess}, submit: ${result.submitSuccess}`);
      
      if (result.errors.length > 0) {
        result.errors.forEach(error => console.log(`    ❌ ${error}`));
      }
    });
    
    if (allErrors.length > 0) {
      console.log('\n⚠️  ERRORS FOUND:');
      allErrors.forEach(error => {
        console.log(`  - ${error.type}: ${error.message} ${error.navItem ? `(${error.navItem})` : ''}`);
      });
    }
    
    // Write detailed report
    await page.evaluate((report) => {
      console.log('SPA_FORM_TEST_REPORT:', JSON.stringify({
        summary: {
          totalForms: report.formResults.length,
          formsWithInputs: report.formResults.filter(r => r.inputsFound > 0).length,
          successfulFills: report.formResults.filter(r => r.fillSuccess).length,
          successfulSubmits: report.formResults.filter(r => r.submitSuccess).length,
          totalErrors: report.allErrors.length
        },
        results: report.formResults,
        errors: report.allErrors
      }, null, 2));
    }, { formResults, allErrors });
  });
});