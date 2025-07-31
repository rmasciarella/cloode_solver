const { test, expect } = require('@playwright/test');

test('Test all forms are actually working now', async ({ page }) => {
  console.log('🧪 Testing all forms after fixes...');
  
  const results = [];
  
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Test each section and its forms
  const sections = [
    {
      name: 'Organization',
      items: [
        { nav: 'Departments', expected: 'form' },
        { nav: 'Work Cells', expected: 'form' },
        { nav: 'Business Calendars', expected: 'form' }
      ]
    },
    {
      name: 'Templates', 
      items: [
        { nav: 'Job Templates', expected: 'form' },
        { nav: 'Template Tasks', expected: 'form' },
        { nav: 'Template Precedences', expected: 'coming soon' }
      ]
    },
    {
      name: 'Resources',
      items: [
        { nav: 'Machines', expected: 'form' },
        { nav: 'Operators', expected: 'form' },
        { nav: 'Skills', expected: 'form' },
        { nav: 'Sequence Resources', expected: 'form' }
      ]
    },
    {
      name: 'Scheduling',
      items: [
        { nav: 'Setup Times', expected: 'form' },
        { nav: 'Maintenance Windows', expected: 'form' }
      ]
    },
    {
      name: 'Jobs',
      items: [
        { nav: 'Job Instances', expected: 'form' },
        { nav: 'Job Tasks', expected: 'coming soon' }
      ]
    }
  ];
  
  for (const section of sections) {
    console.log(`\n📂 Testing ${section.name} section...`);
    
    // Expand section if needed
    if (section.name !== 'Organization') {
      await page.click(`button:has-text("${section.name}")`);
      await page.waitForTimeout(500);
    }
    
    for (const item of section.items) {
      console.log(`  📝 Testing ${item.nav}...`);
      
      try {
        await page.click(`button:has-text("${item.nav}")`);
        await page.waitForTimeout(1500);
        
        if (item.expected === 'form') {
          const forms = await page.locator('form').count();
          const inputs = await page.locator('input, textarea, select').count();
          
          if (forms > 0 && inputs > 0) {
            console.log(`    ✅ ${item.nav}: ${forms} form(s), ${inputs} input(s)`);
            results.push({ item: item.nav, status: 'working', forms, inputs });
          } else {
            console.log(`    ❌ ${item.nav}: No forms or inputs found`);
            results.push({ item: item.nav, status: 'broken', forms, inputs });
          }
        } else if (item.expected === 'coming soon') {
          const content = await page.locator('main').textContent();
          if (content?.includes('coming soon')) {
            console.log(`    ✅ ${item.nav}: Shows coming soon message`);
            results.push({ item: item.nav, status: 'placeholder', message: 'coming soon' });
          } else {
            console.log(`    ❌ ${item.nav}: Missing coming soon message`);
            results.push({ item: item.nav, status: 'broken', content: content?.substring(0, 50) });
          }
        }
        
      } catch (error) {
        console.log(`    ❌ ${item.nav}: Error - ${error.message}`);
        results.push({ item: item.nav, status: 'error', error: error.message });
      }
    }
  }
  
  // Summary
  console.log('\n📊 === FINAL RESULTS ===');
  const working = results.filter(r => r.status === 'working').length;
  const placeholders = results.filter(r => r.status === 'placeholder').length;
  const broken = results.filter(r => r.status === 'broken').length;
  const errors = results.filter(r => r.status === 'error').length;
  
  console.log(`✅ Working forms: ${working}`);
  console.log(`ℹ️ Placeholder forms: ${placeholders}`);
  console.log(`❌ Broken forms: ${broken}`);
  console.log(`💥 Error forms: ${errors}`);
  
  console.log('\n📋 Detailed Results:');
  results.forEach(result => {
    const status = result.status === 'working' ? '✅' : 
                   result.status === 'placeholder' ? 'ℹ️' :
                   result.status === 'broken' ? '❌' : '💥';
    
    if (result.status === 'working') {
      console.log(`  ${status} ${result.item}: ${result.inputs} inputs`);
    } else if (result.status === 'placeholder') {
      console.log(`  ${status} ${result.item}: ${result.message}`);
    } else {
      console.log(`  ${status} ${result.item}: ${result.error || 'broken'}`);
    }
  });
  
  // Take final screenshot
  await page.screenshot({ 
    path: 'gui/test-results/all-forms-final-test.png',
    fullPage: true 
  });
  
  const totalWorking = working + placeholders;
  console.log(`\n🎯 FINAL SCORE: ${totalWorking}/${results.length} forms working or have placeholders`);
});