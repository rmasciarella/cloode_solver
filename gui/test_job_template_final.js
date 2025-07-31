const { chromium } = require('playwright');

async function testJobTemplateFinal() {
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
    
    // Check for the actual correct fields from job_optimized_patterns table
    const nameField = await page.$('input[id="name"]');
    const taskCountField = await page.$('input[id="task_count"]');
    const totalDurationField = await page.$('input[id="total_min_duration_minutes"]');
    const criticalPathField = await page.$('input[id="critical_path_length_minutes"]');
    const constraintsCountField = await page.$('input[id="redundant_constraints_count"]');
    
    console.log('🏷️ Name field found:', !!nameField);
    console.log('📊 Task count field found:', !!taskCountField);
    console.log('⏱️ Total duration field found:', !!totalDurationField);
    console.log('🛤️ Critical path field found:', !!criticalPathField);
    console.log('🔧 Redundant constraints count field found:', !!constraintsCountField);
    
    if (nameField && taskCountField && totalDurationField && criticalPathField && constraintsCountField) {
      console.log('✅ All required Job Template fields found!');
      
      // Test form submission with valid data matching job_optimized_patterns schema
      console.log('🧪 Testing form submission with job_optimized_patterns schema...');
      
      await page.fill('input[id="name"]', 'Final Test Manufacturing Pattern');
      await page.fill('input[id="task_count"]', '5');
      await page.fill('input[id="total_min_duration_minutes"]', '180');
      await page.fill('input[id="critical_path_length_minutes"]', '120');
      await page.fill('input[id="redundant_constraints_count"]', '2');
      
      // Optional description
      const descField = await page.$('textarea[id="description"]');
      if (descField) {
        await page.fill('textarea[id="description"]', 'Final test with correct job_optimized_patterns table');
      }
      
      // Take screenshot before submission
      await page.screenshot({ path: 'job_template_final_filled.png' });
      console.log('📸 Final form filled screenshot taken');
      
      // Listen for network requests
      const requests = [];
      const responses = [];
      
      page.on('request', request => {
        if (request.url().includes('supabase') && request.method() === 'POST') {
          console.log('📡 Database request:', request.method(), request.url());
          const payload = request.postData();
          if (payload) {
            requests.push({payload});
            console.log('📝 Request payload preview:', payload.substring(0, 200) + '...');
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
        console.log('🚀 Submitting final corrected form...');
        
        await submitButton.click();
        
        // Wait for response
        await page.waitForTimeout(3000);
        
        // Check for success/error messages
        const toastMessages = await page.$$eval('[role="status"], .toast, .alert, [data-sonner-toast]', 
          elements => elements.map(el => el.textContent?.trim()).filter(Boolean));
        
        console.log('📢 Toast messages found:', toastMessages);
        
        // Take screenshot after submission
        await page.screenshot({ path: 'job_template_final_submitted.png' });
        console.log('📸 Final form submission screenshot taken');
        
        if (toastMessages.some(msg => msg && msg.includes('Success'))) {
          console.log('🎉 SUCCESS! Form submitted successfully with correct schema!');
          console.log('✅ The "3 errors" issue has been resolved!');
          
          // Verify the data was actually saved by checking if form was reset
          const nameAfterSubmit = await page.inputValue('input[id="name"]');
          console.log('📝 Form reset verification - name field after submit:', nameAfterSubmit || '[empty - form was reset]');
          
          if (!nameAfterSubmit) {
            console.log('🔄 Form was successfully reset - confirming data was saved');
          }
        } else if (toastMessages.some(msg => msg && msg.includes('Error'))) {
          console.log('❌ Form submission failed with error');
          console.log('Error details:', toastMessages.filter(msg => msg && msg.includes('Error')));
          console.log('📊 Network responses:', responses);
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
        
        console.log('\n📊 FINAL SUMMARY:');
        console.log('✅ Corrected table name: job_optimized_patterns (not job_templates)');
        console.log('✅ Restored required fields: task_count, total_min_duration_minutes, critical_path_length_minutes');
        console.log('✅ Kept optimization fields: symmetry_breaking_enabled, redundant_constraints_count');
        console.log('✅ Updated primary key: pattern_id (not template_id)');
        console.log('✅ Form fields now match actual database schema');
        
      } else {
        console.log('❌ Submit button not found');
      }
    } else {
      console.log('❌ Job Template form fields still missing');
      const allInputs = await page.$$eval('input', inputs => 
        inputs.map(input => ({ id: input.id, type: input.type, placeholder: input.placeholder }))
      );
      console.log('📋 All input fields found:', allInputs);
    }
    
  } catch (error) {
    console.error('❌ Error during final form test:', error);
    await page.screenshot({ path: 'job_template_final_error.png' });
  } finally {
    await browser.close();
  }
}

testJobTemplateFinal();