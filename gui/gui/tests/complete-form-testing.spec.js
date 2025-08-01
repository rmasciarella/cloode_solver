const { test, expect } = require('@playwright/test');

// Test data for form submissions
const testData = {
  businessCalendar: {
    name: 'Test Business Calendar',
    description: 'Test calendar description',
    timezone: 'America/New_York',
    default_start_time: '08:00',
    default_end_time: '17:00'
  },
  department: {
    name: 'Test Department',
    description: 'Test department description',
    code: 'TESTDEPT',
    manager: 'Test Manager'
  },
  machine: {
    name: 'Test Machine',
    model: 'Test Model',
    manufacturer: 'Test Manufacturer',
    capacity: '100',
    status: 'active'
  },
  workCell: {
    name: 'Test Work Cell',
    description: 'Test work cell description',
    location: 'Test Location',
    capacity: '50'
  },
  operator: {
    name: 'Test Operator',
    employee_id: 'EMP001',
    email: 'test@example.com',
    phone: '555-0123',
    status: 'active'
  },
  skill: {
    name: 'Test Skill',
    description: 'Test skill description',
    category: 'Technical',
    level: 'Intermediate'
  },
  maintenanceType: {
    name: 'Test Maintenance',
    description: 'Test maintenance description',
    estimated_duration: '120',
    frequency: 'monthly'
  },
  jobTemplate: {
    name: 'Test Job Template',
    description: 'Test job template description',
    priority: '5',
    estimated_duration: '240'
  },
  templateTask: {
    name: 'Test Template Task',
    description: 'Test template task description',
    estimated_duration: '60',
    sequence_order: '1'
  },
  jobInstance: {
    name: 'Test Job Instance',
    description: 'Test job instance description',
    priority: '3',
    due_date: '2024-12-31'
  },
  setupTime: {
    name: 'Test Setup Time',
    from_task_type: 'Type A',
    to_task_type: 'Type B',
    setup_time_minutes: '30'
  },
  sequenceResource: {
    name: 'Test Sequence Resource',
    resource_type: 'Machine',
    capacity: '10',
    availability: 'always'
  }
};

// List of all form pages to test
const formPages = [
  { path: '/', name: 'Home', hasForm: false },
  { path: '/business-calendars', name: 'Business Calendars', hasForm: true, formData: testData.businessCalendar },
  { path: '/departments', name: 'Departments', hasForm: true, formData: testData.department },
  { path: '/machines', name: 'Machines', hasForm: true, formData: testData.machine },
  { path: '/work-cells', name: 'Work Cells', hasForm: true, formData: testData.workCell },
  { path: '/operators', name: 'Operators', hasForm: true, formData: testData.operator },
  { path: '/skills', name: 'Skills', hasForm: true, formData: testData.skill },
  { path: '/maintenance-types', name: 'Maintenance Types', hasForm: true, formData: testData.maintenanceType },
  { path: '/job-templates', name: 'Job Templates', hasForm: true, formData: testData.jobTemplate },
  { path: '/template-tasks', name: 'Template Tasks', hasForm: true, formData: testData.templateTask },
  { path: '/job-instances', name: 'Job Instances', hasForm: true, formData: testData.jobInstance },
  { path: '/setup-times', name: 'Setup Times', hasForm: true, formData: testData.setupTime },
  { path: '/sequence-resources', name: 'Sequence Resources', hasForm: true, formData: testData.sequenceResource }
];

test.describe('Complete GUI Form Testing', () => {
  // Track all errors found during testing
  let allErrors = [];
  let consoleErrors = [];
  let networkErrors = [];

  test.beforeEach(async ({ page }) => {
    // Reset error arrays for each test
    allErrors = [];
    consoleErrors = [];
    networkErrors = [];

    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const error = {
          type: 'console',
          message: msg.text(),
          location: msg.location(),
          timestamp: new Date().toISOString()
        };
        consoleErrors.push(error);
        allErrors.push(error);
      }
    });

    // Listen for uncaught exceptions
    page.on('pageerror', error => {
      const pageError = {
        type: 'page_error',
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      };
      allErrors.push(pageError);
    });

    // Listen for network failures
    page.on('response', response => {
      if (response.status() >= 400) {
        const networkError = {
          type: 'network',
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
          timestamp: new Date().toISOString()
        };
        networkErrors.push(networkError);
        allErrors.push(networkError);
      }
    });
  });

  // Test navigation to each page
  test('Navigate to all pages and check for errors', async ({ page }) => {
    console.log('🚀 Starting navigation tests...');
    
    for (const formPage of formPages) {
      console.log(`📍 Testing navigation to: ${formPage.name} (${formPage.path})`);
      
      try {
        // Navigate to the page
        await page.goto(formPage.path, { waitUntil: 'networkidle', timeout: 30000 });
        
        // Wait for page to be fully loaded
        await page.waitForLoadState('domcontentloaded');
        
        // Take screenshot for debugging
        await page.screenshot({ 
          path: `gui/test-results/navigation-${formPage.name.toLowerCase().replace(/\s+/g, '-')}.png`,
          fullPage: true 
        });
        
        // Check if page loaded successfully
        const title = await page.title();
        console.log(`✅ Successfully loaded: ${formPage.name} - Title: ${title}`);
        
        // Wait a bit to catch any delayed errors
        await page.waitForTimeout(2000);
        
      } catch (error) {
        console.error(`❌ Navigation error for ${formPage.name}:`, error.message);
        allErrors.push({
          type: 'navigation',
          page: formPage.name,
          path: formPage.path,
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Report navigation errors
    if (allErrors.length > 0) {
      console.log(`\n⚠️  Found ${allErrors.length} navigation errors:`);
      allErrors.forEach(error => console.log(`  - ${error.type}: ${error.message}`));
    } else {
      console.log('\n✅ All pages navigated successfully!');
    }
  });

  // Test form submissions on each page
  test('Submit forms on all pages and check for errors', async ({ page }) => {
    console.log('🚀 Starting form submission tests...');
    
    for (const formPage of formPages.filter(p => p.hasForm)) {
      console.log(`📝 Testing form submission on: ${formPage.name}`);
      
      try {
        // Navigate to the page
        await page.goto(formPage.path, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForLoadState('domcontentloaded');
        
        // Look for form elements
        const forms = await page.locator('form').count();
        console.log(`  Found ${forms} form(s) on ${formPage.name}`);
        
        if (forms === 0) {
          console.log(`  ⚠️  No forms found on ${formPage.name}`);
          continue;
        }
        
        // Fill out the form with test data
        for (const [fieldName, fieldValue] of Object.entries(formPage.formData)) {
          try {
            // Try different selectors for the field
            const selectors = [
              `input[name="${fieldName}"]`,
              `textarea[name="${fieldName}"]`,
              `select[name="${fieldName}"]`,
              `input[id="${fieldName}"]`,
              `textarea[id="${fieldName}"]`,
              `select[id="${fieldName}"]`,
              `input[placeholder*="${fieldName}"]`,
              `textarea[placeholder*="${fieldName}"]`
            ];
            
            let fieldFound = false;
            for (const selector of selectors) {
              if (await page.locator(selector).count() > 0) {
                const element = page.locator(selector).first();
                const tagName = await element.evaluate(el => el.tagName.toLowerCase());
                
                if (tagName === 'select') {
                  await element.selectOption(fieldValue);
                } else {
                  await element.fill(fieldValue);
                }
                
                console.log(`    ✅ Filled ${fieldName}: ${fieldValue}`);
                fieldFound = true;
                break;
              }
            }
            
            if (!fieldFound) {
              console.log(`    ⚠️  Field not found: ${fieldName}`);
            }
            
          } catch (fieldError) {
            console.log(`    ❌ Error filling ${fieldName}: ${fieldError.message}`);
            allErrors.push({
              type: 'form_field',
              page: formPage.name,
              field: fieldName,
              message: fieldError.message,
              timestamp: new Date().toISOString()
            });
          }
        }
        
        // Take screenshot before submission
        await page.screenshot({ 
          path: `gui/test-results/form-filled-${formPage.name.toLowerCase().replace(/\s+/g, '-')}.png`,
          fullPage: true 
        });
        
        // Look for submit button and submit form
        const submitSelectors = [
          'button[type="submit"]',
          'input[type="submit"]',
          'button:has-text("Submit")',
          'button:has-text("Save")',
          'button:has-text("Create")',
          'button:has-text("Add")'
        ];
        
        let submitFound = false;
        for (const selector of submitSelectors) {
          if (await page.locator(selector).count() > 0) {
            console.log(`    🔘 Found submit button: ${selector}`);
            
            // Click submit and wait for response
            await Promise.all([
              page.waitForResponse(response => response.status() !== 0, { timeout: 10000 }).catch(() => null),
              page.locator(selector).first().click()
            ]);
            
            console.log(`    ✅ Form submitted on ${formPage.name}`);
            submitFound = true;
            
            // Wait for any post-submission effects
            await page.waitForTimeout(3000);
            
            // Take screenshot after submission
            await page.screenshot({ 
              path: `gui/test-results/form-submitted-${formPage.name.toLowerCase().replace(/\s+/g, '-')}.png`,
              fullPage: true 
            });
            
            break;
          }
        }
        
        if (!submitFound) {
          console.log(`    ⚠️  No submit button found on ${formPage.name}`);
          allErrors.push({
            type: 'form_submit',
            page: formPage.name,
            message: 'No submit button found',
            timestamp: new Date().toISOString()
          });
        }
        
      } catch (error) {
        console.error(`❌ Form submission error on ${formPage.name}:`, error.message);
        allErrors.push({
          type: 'form_submission',
          page: formPage.name,
          message: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Generate comprehensive error report
    console.log('\n📊 === COMPREHENSIVE ERROR REPORT ===');
    console.log(`Total errors found: ${allErrors.length}`);
    
    if (allErrors.length > 0) {
      // Group errors by type
      const errorsByType = allErrors.reduce((acc, error) => {
        acc[error.type] = acc[error.type] || [];
        acc[error.type].push(error);
        return acc;
      }, {});
      
      for (const [type, errors] of Object.entries(errorsByType)) {
        console.log(`\n${type.toUpperCase()} ERRORS (${errors.length}):`);
        errors.forEach(error => {
          console.log(`  - ${error.page || 'Unknown'}: ${error.message}`);
        });
      }
      
      // Write detailed error report to file
      const errorReport = {
        summary: {
          totalErrors: allErrors.length,
          errorsByType: Object.keys(errorsByType).map(type => ({
            type,
            count: errorsByType[type].length
          })),
          timestamp: new Date().toISOString()
        },
        errors: allErrors
      };
      
      await page.evaluate((report) => {
        console.log('PLAYWRIGHT_ERROR_REPORT:', JSON.stringify(report, null, 2));
      }, errorReport);
      
    } else {
      console.log('\n✅ NO ERRORS FOUND! All forms submitted successfully.');
    }
  });

  // Test accessibility on all pages
  test('Check accessibility on all pages', async ({ page }) => {
    console.log('🚀 Starting accessibility tests...');
    
    for (const formPage of formPages) {
      try {
        await page.goto(formPage.path, { waitUntil: 'networkidle', timeout: 30000 });
        
        // Check for basic accessibility issues
        const issues = [];
        
        // Check for images without alt text
        const imgsWithoutAlt = await page.locator('img:not([alt])').count();
        if (imgsWithoutAlt > 0) {
          issues.push(`${imgsWithoutAlt} images without alt text`);
        }
        
        // Check for form inputs without labels
        const inputsWithoutLabels = await page.locator('input:not([aria-label]):not([aria-labelledby])').count();
        const associatedInputs = await page.locator('input[id] ~ label[for], label input').count();
        const unlabeledInputs = inputsWithoutLabels - associatedInputs;
        if (unlabeledInputs > 0) {
          issues.push(`${unlabeledInputs} form inputs without proper labels`);
        }
        
        if (issues.length > 0) {
          console.log(`  ⚠️  Accessibility issues on ${formPage.name}:`);
          issues.forEach(issue => console.log(`    - ${issue}`));
          
          allErrors.push({
            type: 'accessibility',
            page: formPage.name,
            issues: issues,
            timestamp: new Date().toISOString()
          });
        } else {
          console.log(`  ✅ No accessibility issues found on ${formPage.name}`);
        }
        
      } catch (error) {
        console.error(`❌ Accessibility check error on ${formPage.name}:`, error.message);
      }
    }
  });
});