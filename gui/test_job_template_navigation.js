const { chromium } = require('playwright');

async function testJobTemplateNavigation() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🌐 Navigating to GUI...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot of initial state
    await page.screenshot({ path: 'gui_initial_navigation.png' });
    console.log('📸 Initial screenshot taken');
    
    // Try direct navigation to job templates
    console.log('🔗 Trying direct navigation to job templates...');
    await page.goto('http://localhost:3000/templates/job-templates');
    await page.waitForLoadState('networkidle');
    
    // Check if we successfully reached the job template form
    const pageTitle = await page.title();
    console.log('📄 Page title:', pageTitle);
    
    // Look for job template form elements
    const formElements = await page.$$eval('form', forms => forms.length);
    console.log('📝 Forms found:', formElements);
    
    // Look for specific job template fields
    const nameField = await page.$('input[id="name"]');
    const taskCountField = await page.$('input[id="task_count"]');
    const durationField = await page.$('input[id="total_min_duration_minutes"]');
    
    console.log('🏷️ Name field found:', !!nameField);
    console.log('📊 Task count field found:', !!taskCountField);
    console.log('⏱️ Duration field found:', !!durationField);
    
    if (nameField && taskCountField && durationField) {
      console.log('✅ Job Template form loaded successfully!');
      
      // Test form submission with valid data
      console.log('🧪 Testing form submission...');
      
      await page.fill('input[id="name"]', 'Test Pattern');
      await page.fill('input[id="task_count"]', '3');
      await page.fill('input[id="total_min_duration_minutes"]', '120'); 
      await page.fill('input[id="critical_path_length_minutes"]', '90');
      
      // Take screenshot before submission
      await page.screenshot({ path: 'job_template_form_filled.png' });
      console.log('📸 Form filled screenshot taken');
      
      // Try to submit
      const submitButton = await page.$('button[type="submit"]');
      if (submitButton) {
        await submitButton.click();
        
        // Wait a bit for response
        await page.waitForTimeout(2000);
        
        // Check for success/error messages
        const toastMessages = await page.$$eval('[role="status"], .toast, .alert', 
          elements => elements.map(el => el.textContent));
        
        console.log('📢 Toast messages:', toastMessages);
        
        // Take screenshot after submission
        await page.screenshot({ path: 'job_template_form_submitted.png' });
        console.log('📸 Form submission screenshot taken');
        
        if (toastMessages.some(msg => msg.includes('Success'))) {
          console.log('✅ Form submitted successfully!');
        } else if (toastMessages.some(msg => msg.includes('Error'))) {
          console.log('❌ Form submission failed with error');
        } else {
          console.log('⚠️ Form submission result unclear');
        }
      }
    } else {
      console.log('❌ Job Template form not found or incomplete');
      
      // Check what's actually on the page
      const bodyText = await page.textContent('body');
      console.log('📄 Page content preview:', bodyText.substring(0, 500));
    }
    
  } catch (error) {
    console.error('❌ Error during navigation test:', error);
    await page.screenshot({ path: 'navigation_error.png' });
  } finally {
    await browser.close();
  }
}

testJobTemplateNavigation();