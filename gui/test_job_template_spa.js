const { chromium } = require('playwright');

async function testJobTemplateSPA() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot of initial state
    await page.screenshot({ path: 'spa_initial_state.png' });
    console.log('📸 Initial screenshot taken');
    
    // Expand Templates section
    console.log('📂 Expanding Templates section...');
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500); // Wait for animation
    
    // Take screenshot after expanding
    await page.screenshot({ path: 'spa_templates_expanded.png' });
    console.log('📸 Templates expanded screenshot taken');
    
    // Click on Job Templates
    console.log('🔗 Clicking Job Templates...');
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(1000); // Wait for form to load
    
    // Take screenshot of form
    await page.screenshot({ path: 'spa_job_template_form.png' });
    console.log('📸 Job Template form screenshot taken');
    
    // Check if we successfully reached the job template form
    const pageHeader = await page.textContent('h2');
    console.log('📄 Page header:', pageHeader);
    
    // Look for specific job template fields
    const nameField = await page.$('input[id="name"]');
    const taskCountField = await page.$('input[id="task_count"]');
    const durationField = await page.$('input[id="total_min_duration_minutes"]');
    const criticalPathField = await page.$('input[id="critical_path_length_minutes"]');
    
    console.log('🏷️ Name field found:', !!nameField);
    console.log('📊 Task count field found:', !!taskCountField);
    console.log('⏱️ Duration field found:', !!durationField);
    console.log('🛤️ Critical path field found:', !!criticalPathField);
    
    if (nameField && taskCountField && durationField && criticalPathField) {
      console.log('✅ All required Job Template fields found!');
      
      // Test form submission with valid data
      console.log('🧪 Testing form submission...');
      
      await page.fill('input[id="name"]', 'Test Manufacturing Pattern');
      await page.fill('input[id="task_count"]', '5');
      await page.fill('input[id="total_min_duration_minutes"]', '180'); 
      await page.fill('input[id="critical_path_length_minutes"]', '120');
      
      // Optional description
      const descField = await page.$('textarea[id="description"]');
      if (descField) {
        await page.fill('textarea[id="description"]', 'Test pattern for validation');
      }
      
      // Take screenshot before submission
      await page.screenshot({ path: 'spa_form_filled.png' });
      console.log('📸 Form filled screenshot taken');
      
      // Try to submit
      const submitButton = await page.$('button[type="submit"]');
      if (submitButton) {
        console.log('🚀 Submitting form...');
        
        // Listen for network requests to see what gets sent
        page.on('request', request => {
          if (request.url().includes('supabase') && request.method() === 'POST') {
            console.log('📡 Database request:', request.method(), request.url());
            console.log('📝 Request payload preview:', request.postData()?.substring(0, 200));
          }
        });
        
        page.on('response', response => {
          if (response.url().includes('supabase')) {
            console.log('📬 Database response:', response.status(), response.url());
          }
        });
        
        await submitButton.click();
        
        // Wait for response
        await page.waitForTimeout(3000);
        
        // Check for success/error messages in various locations
        const toastMessages = await page.$$eval('[role="status"], .toast, .alert, [data-sonner-toast]', 
          elements => elements.map(el => el.textContent?.trim()).filter(Boolean));
        
        console.log('📢 Toast messages found:', toastMessages);
        
        // Check console for any errors
        const consoleMessages = [];
        page.on('console', msg => {
          if (msg.type() === 'error') {
            consoleMessages.push(msg.text());
          }
        });
        
        if (consoleMessages.length > 0) {
          console.log('🚨 Console errors:', consoleMessages);
        }
        
        // Take screenshot after submission
        await page.screenshot({ path: 'spa_form_submitted.png' });
        console.log('📸 Form submission screenshot taken');
        
        if (toastMessages.some(msg => msg && msg.includes('Success'))) {
          console.log('✅ Form submitted successfully!');
        } else if (toastMessages.some(msg => msg && msg.includes('Error'))) {
          console.log('❌ Form submission failed with error');
          console.log('Error details:', toastMessages.filter(msg => msg && msg.includes('Error')));
        } else {
          console.log('⚠️ Form submission result unclear - checking form state...');
          
          // Check if form was reset (success indicator)
          const nameAfterSubmit = await page.inputValue('input[id="name"]');
          console.log('📝 Name field after submit:', nameAfterSubmit);
          
          if (!nameAfterSubmit || nameAfterSubmit === '') {
            console.log('✅ Form was reset - likely successful submission');
          }
        }
      } else {
        console.log('❌ Submit button not found');
      }
    } else {
      console.log('❌ Job Template form fields missing');
      console.log('Missing fields:', {
        name: !nameField,
        taskCount: !taskCountField, 
        duration: !durationField,
        criticalPath: !criticalPathField
      });
      
      // Check what form elements are actually present
      const allInputs = await page.$$eval('input', inputs => 
        inputs.map(input => ({ id: input.id, type: input.type, placeholder: input.placeholder }))
      );
      console.log('📋 All input fields found:', allInputs);
    }
    
  } catch (error) {
    console.error('❌ Error during SPA test:', error);
    await page.screenshot({ path: 'spa_error.png' });
  } finally {
    await browser.close();
  }
}

testJobTemplateSPA();