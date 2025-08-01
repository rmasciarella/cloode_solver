const { test, expect } = require('@playwright/test');

test.describe('Fixed Navigation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000); // Let the page settle
  });

  test('should navigate through all sections correctly', async ({ page }) => {
    console.log('🔧 Testing FIXED navigation...');
    
    // Test data based on the actual navigation structure
    const sections = [
      {
        title: 'Organization',
        testId: 'section-organization',
        items: [
          { key: 'departments', label: 'Departments' },
          { key: 'work-cells', label: 'Work Cells' },
          { key: 'business-calendars', label: 'Business Calendars' }
        ]
      },
      {
        title: 'Resources', 
        testId: 'section-resources',
        items: [
          { key: 'machines', label: 'Machines' },
          { key: 'operators', label: 'Operators' },
          { key: 'skills', label: 'Skills' }
        ]
      }
    ];

    for (const section of sections) {
      console.log(`\n📁 Testing ${section.title} section...`);
      
      // Click section header to expand it
      const sectionButton = page.locator(`[data-testid="${section.testId}"]`);
      await expect(sectionButton).toBeVisible();
      
      // Check if section is expanded
      const isExpanded = await sectionButton.getAttribute('aria-expanded');
      console.log(`${section.title} expanded: ${isExpanded}`);
      
      if (isExpanded !== 'true') {
        await sectionButton.click();
        await page.waitForTimeout(500); // Wait for animation
      }
      
      // Test each navigation item
      for (const item of section.items) {
        console.log(`  🔍 Testing ${item.label}...`);
        
        const navButton = page.locator(`[data-testid="nav-${item.key}"]`);
        await expect(navButton).toBeVisible();
        
        await navButton.click();
        await page.waitForTimeout(1000);
        
        // Verify we navigated to the correct page
        const pageHeading = page.locator('h2');
        await expect(pageHeading).toContainText(item.label, { timeout: 5000 });
        
        console.log(`    ✅ ${item.label} navigation successful`);
        
        // Take screenshot
        await page.screenshot({ 
          path: `test-results/fixed-nav-${item.key}.png`,
          fullPage: true 
        });
      }
    }
    
    console.log('✅ FIXED navigation test completed successfully!');
  });

  test('should handle Work Cells navigation specifically', async ({ page }) => {
    console.log('🔧 Testing Work Cells navigation fix...');
    
    // Expand Organization section first
    const orgSection = page.locator('[data-testid="section-organization"]');
    await expect(orgSection).toBeVisible();
    
    const isExpanded = await orgSection.getAttribute('aria-expanded');
    if (isExpanded !== 'true') {
      await orgSection.click();
      await page.waitForTimeout(500);
    }
    
    // Now click Work Cells
    const workCellsButton = page.locator('[data-testid="nav-work-cells"]');
    await expect(workCellsButton).toBeVisible();
    await workCellsButton.click();
    await page.waitForTimeout(1000);
    
    // Verify we're on Work Cells page
    await expect(page.locator('h2')).toContainText('Work Cells');
    
    // Check for form presence
    const form = page.locator('form');
    await expect(form).toBeVisible();
    
    console.log('✅ Work Cells navigation FIXED!');
    await page.screenshot({ path: 'test-results/work-cells-fixed.png', fullPage: true });
  });

  test('should test form interactions on multiple pages', async ({ page }) => {
    console.log('🔧 Testing form interactions...');
    
    const testPages = [
      { section: 'organization', item: 'departments', name: 'Departments' },
      { section: 'organization', item: 'work-cells', name: 'Work Cells' },
      { section: 'resources', item: 'machines', name: 'Machines' }
    ];
    
    for (const testPage of testPages) {
      console.log(`\n📝 Testing ${testPage.name} form...`);
      
      // Expand section
      await page.locator(`[data-testid="section-${testPage.section}"]`).click();
      await page.waitForTimeout(500);
      
      // Navigate to page
      await page.locator(`[data-testid="nav-${testPage.item}"]`).click();
      await page.waitForTimeout(1000);
      
      // Check for form
      const form = page.locator('form');
      const hasForm = await form.count() > 0;
      
      if (hasForm) {
        // Count form elements
        const inputs = await page.locator('input').count();
        const textareas = await page.locator('textarea').count();
        const selects = await page.locator('select, [role="combobox"]').count();
        
        console.log(`  📊 ${testPage.name}: ${inputs} inputs, ${textareas} textareas, ${selects} selects`);
        
        // Try to fill first input
        const firstInput = page.locator('input[type="text"], input:not([type])').first();
        if (await firstInput.count() > 0) {
          await firstInput.fill(`TEST_${testPage.item.toUpperCase()}`);
          console.log(`  ✏️ Successfully filled input field`);
        }
        
        await page.screenshot({ 
          path: `test-results/form-test-${testPage.item}.png`,
          fullPage: true 
        });
      } else {
        console.log(`  ⚠️ No form found on ${testPage.name} page`);
      }
    }
    
    console.log('✅ Form interaction tests completed!');
  });
});