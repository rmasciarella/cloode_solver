const { chromium } = require('playwright');

async function testJobTemplateFixed() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Expand Templates section
    console.log('📂 Expanding Templates section...');
    const templatesButton = await page.locator('button:has-text("Templates")').first();
    await templatesButton.click();
    await page.waitForTimeout(500);
    
    // Click on Job Templates
    console.log('🔗 Clicking Job Templates...');
    const jobTemplatesButton = await page.locator('button:has-text("Job Templates")').first();
    await jobTemplatesButton.click();
    await page.waitForTimeout(1000);
    
    // Check if we successfully reached the job template form with corrected fields
    const nameField = await page.$('input[id="name"]');
    const versionField = await page.$('input[id="version"]');
    const constraintsCountField = await page.$('input[id="redundant_constraints_count"]');
    
    console.log('🏷️ Name field found:', !!nameField);
    console.log('📝 Version field found:', !!versionField);
    console.log('🔧 Redundant constraints count field found:', !!constraintsCountField);
    
    if (nameField && versionField && constraintsCountField) {
      console.log('✅ All corrected Job Template fields found!');
      
      // Test form submission with valid data matching the new schema
      console.log('🧪 Testing form submission with corrected schema...');
      
      await page.fill('input[id="name"]', 'Test Manufacturing Template v2');
      await page.fill('input[id="version"]', '2');
      await page.fill('input[id="redundant_constraints_count"]', '3');
      
      // Optional description
      const descField = await page.$('textarea[id="description"]');
      if (descField) {
        await page.fill('textarea[id="description"]', 'Updated template with corrected database schema');
      }
      
      // Take screenshot before submission
      await page.screenshot({ path: 'job_template_fixed_filled.png' });
      console.log('📸 Fixed form filled screenshot taken');
      
      // Listen for network requests to see what gets sent
      const requests = [];
      const responses = [];
      
      page.on('request', request => {
        if (request.url().includes('supabase') && request.method() === 'POST') {
          console.log('📡 Database request:', request.method(), request.url());
          const payload = request.postData();
          if (payload) {
            requests.push({
              url: request.url(),
              method: request.method(),
              payload: payload.substring(0, 400) + (payload.length > 400 ? '...' : '')
            });
            console.log('📝 Request payload:', payload.substring(0, 400));
          }
        }
      });
      
      page.on('response', response => {
        if (response.url().includes('supabase')) {
          responses.push({
            status: response.status(),
            url: response.url()
          });
          console.log('📬 Database response:', response.status(), response.url());
        }
      });
      
      // Try to submit
      const submitButton = await page.$('button[type="submit"]');
      if (submitButton) {
        console.log('🚀 Submitting corrected form...');
        
        await submitButton.click();
        
        // Wait for response
        await page.waitForTimeout(3000);
        
        // Check for success/error messages
        const toastMessages = await page.$$eval('[role="status"], .toast, .alert, [data-sonner-toast]', 
          elements => elements.map(el => el.textContent?.trim()).filter(Boolean));
        
        console.log('📢 Toast messages found:', toastMessages);
        
        // Take screenshot after submission
        await page.screenshot({ path: 'job_template_fixed_submitted.png' });
        console.log('📸 Fixed form submission screenshot taken');
        
        if (toastMessages.some(msg => msg && msg.includes('Success'))) {
          console.log('✅ Form submitted successfully with corrected schema!');
          console.log('🎉 Database schema mismatch has been resolved!');
          
          // Verify the data was actually saved by checking if form was reset
          const nameAfterSubmit = await page.inputValue('input[id="name"]');
          console.log('📝 Form reset check - name field after submit:', nameAfterSubmit || '[empty]');
        } else if (toastMessages.some(msg => msg && msg.includes('Error'))) {
          console.log('❌ Form submission still failed with error');
          console.log('Error details:', toastMessages.filter(msg => msg && msg.includes('Error')));
          console.log('📊 Network summary:');
          console.log('Requests sent:', requests.length);
          console.log('Responses received:', responses);
        } else {
          console.log('⚠️ Form submission result unclear');
          
          // Check if form was reset (success indicator)
          const nameAfterSubmit = await page.inputValue('input[id="name"]');
          if (!nameAfterSubmit || nameAfterSubmit === '') {
            console.log('✅ Form was reset - likely successful submission');
          } else {
            console.log('❓ Form not reset - submission may have failed');
          }
        }
        
        console.log('\n📊 Summary:');
        console.log('Schema corrections made:');
        console.log('✓ Changed from job_optimized_patterns to job_templates table');
        console.log('✓ Removed non-existent fields: task_count, total_min_duration_minutes, critical_path_length_minutes');
        console.log('✓ Added correct database fields: version, symmetry_breaking_enabled, redundant_constraints_count');
        console.log('✓ Updated all references to use template_id instead of pattern_id');
        
      } else {
        console.log('❌ Submit button not found');
      }
    } else {
      console.log('❌ Job Template form fields still missing');
      console.log('Missing fields:', {
        name: !nameField,
        version: !versionField,
        constraintsCount: !constraintsCountField
      });
    }
    
  } catch (error) {
    console.error('❌ Error during fixed form test:', error);
    await page.screenshot({ path: 'job_template_fixed_error.png' });
  } finally {
    await browser.close();
  }
}

testJobTemplateFixed();